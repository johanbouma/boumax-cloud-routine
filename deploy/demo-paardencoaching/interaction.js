const header = document.querySelector('#site-header');
const menuButton = document.querySelector('.menu-toggle');
const mobileMenu = document.querySelector('#mobile-menu');

function setHeaderState() {
  header?.classList.toggle('is-sticky', window.scrollY > 72);
}
window.addEventListener('scroll', setHeaderState, { passive: true });
setHeaderState();

function setMenu(open) {
  document.body.classList.toggle('menu-open', open);
  menuButton?.setAttribute('aria-expanded', String(open));
  menuButton?.setAttribute('aria-label', open ? 'Menu sluiten' : 'Menu openen');
  if (mobileMenu) mobileMenu.inert = !open;
}
menuButton?.addEventListener('click', () => setMenu(!document.body.classList.contains('menu-open')));
mobileMenu?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
window.addEventListener('keydown', event => {
  if (event.key === 'Escape') setMenu(false);
});

const mirror = document.querySelector('.mirror-visual');
const slider = mirror?.querySelector('input[type="range"]');
slider?.addEventListener('pointermove', event => {
  const bounds = mirror.getBoundingClientRect();
  const x = Math.max(0, Math.min(bounds.width, event.clientX - bounds.left));
  const y = Math.max(0, Math.min(bounds.height, event.clientY - bounds.top));
  mirror.style.setProperty('--lens-x', `${x}px`);
  mirror.style.setProperty('--lens-y', `${y}px`);
});
slider?.addEventListener('input', () => mirror.style.setProperty('--lens-x', `${slider.value}%`));

const form = document.querySelector('#demo-form');
function showDemoFeedback(event) {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const feedback = form.querySelector('.form-feedback');
  if (feedback) feedback.hidden = false;
}
form?.addEventListener('submit', event => event.preventDefault());
form?.querySelector('.form-button')?.addEventListener('click', showDemoFeedback);
