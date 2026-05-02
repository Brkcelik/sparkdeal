from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import ScrapeRun, Source

bp = Blueprint('scrape_runs', __name__)


@bp.route('/scrape-runs')
def list():
    page = request.args.get('page', 1, type=int)
    source_id = request.args.get('source_id', type=int)
    status = request.args.get('status', '')

    query = ScrapeRun.query
    if source_id:
        query = query.filter_by(source_id=source_id)
    if status:
        query = query.filter_by(status=status)

    runs = query.order_by(ScrapeRun.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    sources = Source.query.order_by(Source.name).all()

    return render_template(
        'scrape_runs/list.html',
        runs=runs,
        sources=sources,
        source_filter=source_id,
        status_filter=status,
    )


@bp.route('/scrape-runs/trigger/<source_name>', methods=['POST'])
def trigger(source_name):
    from app.services.scraper_service import run_scrape
    try:
        run = run_scrape(source_name)
        if run.status == 'skipped':
            flash(f'{source_name} kaynağı pasif, atlandı.', 'warning')
        else:
            flash(
                f'{source_name} taraması tamamlandı: '
                f'{run.found_count} ürün, '
                f'{run.new_product_count} yeni, '
                f'{run.updated_product_count} güncellendi.',
                'success',
            )
    except Exception as exc:
        flash(f'{source_name} taraması başarısız: {exc}', 'error')

    next_url = request.form.get('next') or url_for('scrape_runs.list')
    return redirect(next_url)
