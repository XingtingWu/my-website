'use strict';
// Link the map and its text descriptions for pointer and keyboard exploration.
const researchOverview = document.querySelector('.landscape-overview');
if (researchOverview) {
  const interestLinks = [...researchOverview.querySelectorAll('[data-interest]')];
  const linkedElements = [...researchOverview.querySelectorAll('[data-interest], [data-interest-area], [data-interest-copy]')];
  let hoveredInterest = null;
  let focusedInterest = null;
  const highlightInterest = () => {
    const active = hoveredInterest || focusedInterest;
    linkedElements.forEach(element => {
      const interest = element.dataset.interest || element.dataset.interestArea || element.dataset.interestCopy;
      element.classList.toggle('is-active', interest === active);
    });
  };
  interestLinks.forEach(link => {
    link.addEventListener('pointerenter', event => {
      if (event.pointerType === 'touch') return;
      hoveredInterest = link.dataset.interest;
      highlightInterest();
    });
    link.addEventListener('pointerleave', () => { hoveredInterest = null; highlightInterest(); });
    link.addEventListener('focus', () => { focusedInterest = link.dataset.interest; highlightInterest(); });
    link.addEventListener('blur', () => { focusedInterest = null; highlightInterest(); });
  });
}

// Show every method without JavaScript; enhance to a keyboard-accessible tab set.
const methodsExplorer = document.querySelector('[data-methods-explorer]');
if (methodsExplorer) {
  const tabList = methodsExplorer.querySelector('.method-tabs');
  const tabs = [...tabList.querySelectorAll('button')];
  const panels = [...methodsExplorer.querySelectorAll('.method-exploration')];
  tabList.setAttribute('role', 'tablist');
  tabList.setAttribute('aria-label', 'Research methods');
  tabs.forEach((tab, index) => {
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', panels[index].id);
    panels[index].setAttribute('role', 'tabpanel');
    panels[index].setAttribute('aria-labelledby', tab.id);
    panels[index].tabIndex = 0;
  });
  const selectMethod = (index, moveFocus = false) => {
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
    });
    if (moveFocus) tabs[index].focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectMethod(index));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); selectMethod(next, true); }
    });
  });
  selectMethod(0);
  methodsExplorer.classList.add('is-enhanced');
  tabList.hidden = false;
}

const visitorMapImage = document.querySelector('#visitor-map-image');
if (visitorMapImage) {
  const showMapFailure = () => {
    visitorMapImage.hidden = true;
    document.querySelector('#visitor-map-unavailable').hidden = false;
  };
  visitorMapImage.addEventListener('error', showMapFailure);
  if (visitorMapImage.complete && visitorMapImage.naturalWidth === 0) showMapFailure();
}

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
