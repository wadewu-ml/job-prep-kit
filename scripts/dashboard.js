const search = document.getElementById('search');
const rows = [...document.querySelectorAll('.opportunity')];
const filters = [...document.querySelectorAll('[data-filter]')];
let filter = 'current';
function applyFilter() {
  const query = search.value.toLocaleLowerCase().trim();
  rows.forEach(row => {
    const group = row.dataset.group;
    const inScope = filter === 'all' || (filter === 'current' ? group !== 'closed' : filter === group);
    row.hidden = !inScope || !row.textContent.toLocaleLowerCase().includes(query);
  });
  const visible = rows.filter(row => !row.hidden).length;
  document.getElementById('visible-count').textContent = `显示 ${visible} / ${rows.length} 条`;
  document.getElementById('opportunity-title').textContent = filter === 'closed' ? '已结束的记录' : (filter === 'all' ? '全部机会记录' : '值得继续看的机会');
  document.getElementById('empty').hidden = visible > 0;
  filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
}
filters.forEach(button => button.addEventListener('click', () => { filter = button.dataset.filter; applyFilter(); }));
if (search) search.addEventListener('input', applyFilter);
function revealLinkedJob() {
  const row = rows.find(item => '#' + item.id === location.hash);
  if (!row) return;
  search.value = '';
  filter = row.dataset.group === 'closed' ? 'closed' : 'current';
  applyFilter();
  row.querySelector('details').open = true;
  row.scrollIntoView({block: 'start'});
}
window.addEventListener('hashchange', revealLinkedJob);
document.querySelectorAll('a[href^="#job-"]').forEach(anchor => anchor.addEventListener('click', () => {
  if (anchor.hash === location.hash) revealLinkedJob();
}));
if (rows.length) { applyFilter(); revealLinkedJob(); }
const generated = document.querySelector('[data-generated]');
if (new Date().toDateString() !== new Date(generated.dataset.generated).toDateString()) document.getElementById('stale').hidden = false;
