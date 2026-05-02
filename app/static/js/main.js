// Filtre formunu URL parametreleri ile güncelle
document.addEventListener('DOMContentLoaded', function () {
  const filterForm = document.getElementById('filter-form');
  if (filterForm) {
    filterForm.addEventListener('change', function (e) {
      if (e.target.tagName === 'SELECT') {
        filterForm.submit();
      }
    });
  }
});
