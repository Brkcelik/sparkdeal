import logging
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

logger = logging.getLogger(__name__)

_scheduler = None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # WAL modunu etkinleştir — eş zamanlı yazma güvenliği için
    with app.app_context():
        from sqlalchemy import event, text
        from sqlalchemy.engine import Engine
        import sqlite3

        @event.listens_for(Engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.close()

    # Jinja2 filtresi: para birimine göre fiyat formatı
    @app.template_filter('price')
    def price_filter(value, currency='TRY'):
        if value is None:
            return '—'
        if currency == 'USD':
            return f'${value:,.2f}'
        if currency == 'EUR':
            return f'€{value:,.2f}'
        formatted = f'{value:,.2f}'
        formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f'{formatted} ₺'

    @app.template_filter('discount_pct')
    def discount_pct_filter(value):
        if value is None:
            return ''
        return f'%{value:.0f}'

    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.products import bp as products_bp
    from app.routes.deals import bp as deals_bp
    from app.routes.sources import bp as sources_bp
    from app.routes.scrape_runs import bp as scrape_runs_bp
    from app.routes.alerts import bp as alerts_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(deals_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(scrape_runs_bp)
    app.register_blueprint(alerts_bp)

    _register_cli(app)
    _start_scheduler(app)

    return app


def _start_scheduler(app):
    global _scheduler
    # Werkzeug reloader çift process açar — sadece ana process'te başlat
    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return
    if _scheduler is not None and _scheduler.running:
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.executors.pool import ThreadPoolExecutor

        executors = {'default': ThreadPoolExecutor(max_workers=2)}
        sch = BackgroundScheduler(executors=executors, daemon=True)

        def make_job(name, app_ref):
            def _job():
                with app_ref.app_context():
                    from app.services.scraper_service import run_scrape
                    try:
                        run_scrape(name)
                        logger.info("Periyodik tarama tamamlandı: %s", name)
                    except Exception as exc:
                        logger.error("Periyodik tarama hatası (%s): %s", name, exc)
            return _job

        with app.app_context():
            from app.models import Source, ScrapeTarget
            sources = Source.query.filter_by(is_active=True).all()
            for src in sources:
                targets = ScrapeTarget.query.filter_by(
                    source_id=src.id, is_active=True
                ).all()
                intervals = [t.scrape_interval_minutes for t in targets
                             if t.scrape_interval_minutes]
                interval = min(intervals) if intervals else 360

                sch.add_job(
                    make_job(src.name, app),
                    trigger='interval',
                    minutes=interval,
                    id=f'scrape_{src.name.lower()}',
                    max_instances=1,
                    replace_existing=True,
                )
                logger.info("Zamanlayıcı: %s — her %d dakikada", src.name, interval)

        sch.start()
        _scheduler = sch
        logger.info("APScheduler başlatıldı (%d görev)", len(sch.get_jobs()))
    except ImportError:
        logger.warning("APScheduler kurulu değil — periyodik tarama devre dışı. pip install APScheduler")
    except Exception as exc:
        logger.error("Zamanlayıcı başlatılamadı: %s", exc)


def _register_cli(app):
    import click

    @app.cli.command('scrape')
    @click.argument('source_name')
    def scrape_cmd(source_name):
        """Belirtilen kaynağı tara. Örnek: flask scrape steam"""
        from app.services.scraper_service import run_scrape
        from app.scrapers.registry import list_scrapers

        if source_name == 'all':
            sources = list_scrapers()
        else:
            sources = [source_name]

        for name in sources:
            click.echo(f"[>] {name} taranıyor...")
            try:
                run = run_scrape(name)
                click.echo(
                    f"  [OK] {run.status} - {run.found_count} urun, "
                    f"{run.new_product_count} yeni, {run.updated_product_count} guncellendi"
                )
            except ValueError as exc:
                click.echo(f"  [HATA] {exc}", err=True)

    @app.cli.command('list-scrapers')
    def list_scrapers_cmd():
        """Kayıtlı scraper'ları listele."""
        from app.scrapers.registry import list_scrapers
        for name in list_scrapers():
            click.echo(f"  - {name}")

    @app.cli.command('compute-stats')
    def compute_stats_cmd():
        """Tüm ürünler için fiyat istatistiklerini hesapla."""
        from app.services.stats_service import compute_all_stats
        from app import db
        count = compute_all_stats()
        db.session.commit()
        click.echo(f"  [OK] {count} urun icin istatistik hesaplandi")
