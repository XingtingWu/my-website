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

const visitorLocations = document.querySelector('[data-visitor-locations]');
if (visitorLocations) {
  const production = ['www.xingtingwu.com', 'xingtingwu.com', 'xingtingwu.github.io'].includes(location.hostname);
  const feed = production
    ? 'https://raw.githubusercontent.com/XingtingWu/my-website/visitor-data/data/visitors.json'
    : 'data/visitors.json';
  const positions = JSON.parse(document.querySelector('#visitor-country-positions').textContent);
  let visitorData = JSON.parse(document.querySelector('#visitor-initial-data').textContent);
  const choice = visitorLocations.querySelector('#visitor-country-choice');
  const pins = visitorLocations.querySelector('.visitor-pins');
  const updated = visitorLocations.querySelector('.visitor-updated');
  const ns = 'http://www.w3.org/2000/svg';
  let activeCode = choice.value;
  const showTime = (iso, fallback = false) => {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return;
    const time = document.createElement('time');
    time.dateTime = iso;
    time.textContent = new Intl.DateTimeFormat('en', {dateStyle: 'medium', timeStyle: 'short'}).format(date);
    updated.replaceChildren(document.createTextNode(fallback ? 'Last available update ' : 'Updated '), time);
  };
  const selectCountry = code => {
    const country = visitorData.countries.find(c => c.code === code);
    if (!country) return;
    activeCode = code;
    choice.value = code;
    pins.querySelectorAll('[data-country-code]').forEach(pin => {
      const selected = pin.dataset.countryCode === code;
      pin.classList.toggle('is-active', selected);
      pin.setAttribute('aria-pressed', String(selected));
    });
    visitorLocations.querySelector('.visitor-selection strong').textContent = country.visits.toLocaleString('en');
  };
  const bindPins = () => pins.querySelectorAll('[data-country-code]').forEach(pin => {
    const select = () => selectCountry(pin.dataset.countryCode);
    pin.addEventListener('pointerenter', select);
    pin.addEventListener('focus', select);
    pin.addEventListener('click', select);
    pin.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(); }
    });
  });
  const renderMap = data => {
    visitorData = data;
    const options = data.countries.map(c => {
      const option = document.createElement('option');
      option.value = c.code; option.textContent = c.name; return option;
    });
    choice.replaceChildren(...options);
    const markers = data.countries.filter(c => positions[c.code]).map(c => {
      const [x, y] = positions[c.code];
      const pin = document.createElementNS(ns, 'g');
      pin.setAttribute('class', 'visitor-pin');
      pin.setAttribute('transform', `translate(${x} ${y})`);
      pin.dataset.countryCode = c.code;
      pin.setAttribute('role', 'button'); pin.setAttribute('tabindex', '0');
      pin.setAttribute('aria-label', `${c.name}: ${c.visits.toLocaleString('en')} recorded visits`);
      for (const [className, radius] of [['pin-target', 30], ['pin-halo', 14], ['pin-dot', 5]]) {
        const circle = document.createElementNS(ns, 'circle');
        circle.setAttribute('class', className); circle.setAttribute('r', radius); pin.append(circle);
      }
      const label = document.createElementNS(ns, 'text');
      label.setAttribute('x', '15'); label.setAttribute('y', '5'); label.textContent = c.name; pin.append(label);
      return pin;
    });
    pins.replaceChildren(...markers);
    bindPins();
    selectCountry(data.countries.some(c => c.code === activeCode) ? activeCode : data.countries[0].code);
    visitorLocations.querySelector('.visitor-period').textContent = data.period_start.slice(0, 4);
    showTime(data.updated_at);
  };
  bindPins();
  choice.addEventListener('change', () => selectCountry(choice.value));
  showTime(visitorData.updated_at);
  const refreshLocations = async () => {
    if (document.hidden) return;
    try {
      const response = await fetch(feed, {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error('Visitor feed unavailable');
      const data = await response.json();
      if (data.schema_version !== 1 || !Array.isArray(data.countries) || !data.countries.length ||
          Number.isNaN(Date.parse(data.updated_at)) || !/^\d{4}-\d{2}-\d{2}$/.test(data.period_start) ||
          !data.countries.every(c => typeof c.name === 'string' && c.name.length <= 80 && /^[A-Z]{2}$/.test(c.code) &&
            Number.isSafeInteger(c.visits) && c.visits >= 0)) throw new Error('Invalid visitor feed');
      renderMap(data);
    } catch {
      showTime(updated.querySelector('time').dateTime, true);
    }
  };
  refreshLocations();
  setInterval(refreshLocations, 5 * 60 * 1000);
  // Keep the existing counter on Contact only. Local previews never record visits.
  if (production) {
    const counter = new Image(1, 1);
    counter.alt = '';
    counter.hidden = true;
    counter.referrerPolicy = 'origin';
    counter.src = 'https://mapmyvisitors.com/map.png?cl=c2cfb6&w=900&t=n&d=ZteC6Fab8depnYwiaWMsptE8t1EYXOeIAhAFBdEGdp8&co=f1f2e9&ct=243e34';
    visitorLocations.append(counter);
  }
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
