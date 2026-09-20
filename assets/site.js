'use strict';
const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#main-nav');
if (menuButton && navigation) {
  menuButton.hidden = false;
  const closeMenu = () => { navigation.classList.remove('is-open'); menuButton.setAttribute('aria-expanded', 'false'); };
  menuButton.addEventListener('click', () => {
    const open = navigation.classList.toggle('is-open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  navigation.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && navigation.classList.contains('is-open')) { closeMenu(); menuButton.focus(); } });
  window.matchMedia('(min-width: 761px)').addEventListener('change', closeMenu);
}

const filters = document.querySelector('#publication-filters');
if (filters) {
  filters.hidden = false;
  const search = document.querySelector('#publication-search');
  const type = document.querySelector('#publication-type');
  const year = document.querySelector('#publication-year');
  const papers = [...document.querySelectorAll('.publication')];
  const normalize = text => text.normalize('NFKD').toLowerCase().replace(/[\u0300-\u036f]/g, '');
  const update = () => {
    const query = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let count = 0;
    papers.forEach(paper => {
      const text = normalize(paper.textContent);
      const match = query.every(word => text.includes(word)) && (!type.value || paper.dataset.type === type.value) && (!year.value || paper.dataset.year === year.value);
      paper.hidden = !match;
      if (match) count++;
    });
    document.querySelectorAll('.pub-year').forEach(group => { group.hidden = ![...group.querySelectorAll('.publication')].some(paper => !paper.hidden); });
    document.querySelector('#publication-count').textContent = `${count} of ${papers.length} publications`;
    document.querySelector('#no-publications').hidden = count > 0;
  };
  filters.addEventListener('input', update);
  filters.addEventListener('change', update);
  filters.addEventListener('submit', event => event.preventDefault());
  filters.addEventListener('reset', () => { requestAnimationFrame(update); });
}

const lightbox = document.querySelector('#image-dialog');
if (lightbox && typeof lightbox.showModal === 'function') {
  let opener;
  document.querySelectorAll('a[data-image]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault(); opener = link;
    const image = lightbox.querySelector('img');
    image.src = link.href;
    image.alt = link.querySelector('img').alt;
    lightbox.querySelector('p').textContent = link.dataset.caption || image.alt;
    lightbox.showModal();
  }));
  lightbox.querySelector('button').addEventListener('click', () => lightbox.close());
  lightbox.addEventListener('click', event => { if (event.target === lightbox) { const r = lightbox.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) lightbox.close(); } });
  lightbox.addEventListener('close', () => { if (opener) opener.focus(); });
}
