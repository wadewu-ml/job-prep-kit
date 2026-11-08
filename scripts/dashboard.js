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
  document.getElementById('visible-count').textContent = rows.length === 1 && filter === 'current' ? `当前 ${visible} 条` : `显示 ${visible} / ${rows.length} 条`;
  document.getElementById('opportunity-title').textContent = filter === 'closed' ? '历史与不再跟进的记录' : (filter === 'all' ? '全部岗位' : '当前岗位');
  document.getElementById('empty').hidden = visible > 0;
  filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
}
filters.forEach(button => button.addEventListener('click', () => { filter = button.dataset.filter; applyFilter(); }));
if (search) search.addEventListener('input', applyFilter);
function revealLinkedJob() {
  const target = document.getElementById(location.hash.slice(1));
  const row = target && target.closest('.opportunity');
  if (!row) return;
  search.value = '';
  filter = row.dataset.group === 'closed' ? 'closed' : 'current';
  applyFilter();
  target.scrollIntoView({block: 'start'});
}
window.addEventListener('hashchange', revealLinkedJob);
document.querySelectorAll('a[href^="#job-"],a[href^="#prep-"]').forEach(anchor => anchor.addEventListener('click', () => {
  if (anchor.hash === location.hash) revealLinkedJob();
}));
if (rows.length) { applyFilter(); revealLinkedJob(); }
const generated = document.querySelector('[data-generated]');
if (new Date().toDateString() !== new Date(generated.dataset.generated).toDateString()) document.getElementById('stale').hidden = false;
