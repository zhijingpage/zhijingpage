'use strict';

const citations = {
  assemlm: `@article{jing2026assemlm,
  title = {{AssemLM}: A Spatial Reasoning Multimodal Large Language Model for Robotic Assembly},
  author = {Jing, Zhi and Qiao, Jinbin and Lu, Ouyang and Ao, Jicong and Qiu, Shuang and Xu, Huazhe and Jiang, Yu-Gang and Bai, Chenjia},
  journal = {arXiv preprint arXiv:2604.08983},
  year = {2026},
  url = {https://arxiv.org/abs/2604.08983}
}`,
  vqmemory: `@article{wang2026vqmemory,
  title = {Beyond Short-Horizon: {VQ-Memory} for Robust Long-Horizon Manipulation in Non-Markovian Simulation Benchmarks},
  author = {Wang, Honghui and Jing, Zhi and Ao, Jicong and Song, Shiji and Li, Xuelong and Huang, Gao and Bai, Chenjia},
  journal = {arXiv preprint arXiv:2603.09513},
  year = {2026},
  url = {https://arxiv.org/abs/2603.09513}
}`,
  humanoidgen: `@inproceedings{jing2025humanoidgen,
  title = {{HumanoidGen}: Data Generation for Bimanual Dexterous Manipulation via {LLM} Reasoning},
  author = {Jing, Zhi and Yang, Siyuan and Ao, Jicong and Xiao, Ting and Jiang, Yu-Gang and Bai, Chenjia},
  booktitle = {Advances in Neural Information Processing Systems},
  volume = {38},
  doi = {10.52202/085713-5220},
  year = {2025},
  url = {https://papers.nips.cc/paper_files/paper/2025/hash/e4ef7454447baa15a424314e6284441b-Abstract-Conference.html}
}`
};

const motionLink = document.querySelector('.motion-open');
const motionDialog = document.querySelector('#motion-dialog');
const film = motionDialog.querySelector('video');
motionLink.addEventListener('click', event => {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  motionDialog.showModal();
  film.play().catch(() => { /* Native play controls remain available. */ });
});
motionDialog.querySelector('.close-dialog').addEventListener('click', () => motionDialog.close());
motionDialog.addEventListener('close', () => {
  film.pause();
  motionLink.focus();
});

let selectedFilter = 'all';
const search = document.querySelector('#publication-search');
const papers = [...document.querySelectorAll('.publication')];
const filterButtons = [...document.querySelectorAll('[data-filter]')];
function filterPublications() {
  const query = search.value.toLocaleLowerCase().trim();
  let visible = 0;
  papers.forEach(paper => {
    const matchesTopic = selectedFilter === 'all' || paper.dataset.topic === selectedFilter;
    const matchesSearch = paper.textContent.toLocaleLowerCase().includes(query);
    paper.hidden = !(matchesTopic && matchesSearch);
    if (!paper.hidden) visible++;
  });
  document.querySelector('.empty-state').hidden = visible > 0;
  document.querySelector('.filter-status').textContent = `${visible} publication${visible === 1 ? '' : 's'} shown`;
}
filterButtons.forEach(button => button.addEventListener('click', () => {
  selectedFilter = button.dataset.filter;
  filterButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  filterPublications();
}));
search.addEventListener('input', filterPublications);

const dialog = document.querySelector('#citation-dialog');
const citationText = document.querySelector('#citation-content');
const copyStatus = document.querySelector('.copy-status');
const copyButton = document.querySelector('#copy-citation');
let citationTrigger;
document.querySelectorAll('[data-cite]').forEach(button => button.addEventListener('click', () => {
  citationTrigger = button;
  citationText.textContent = citations[button.dataset.cite];
  copyStatus.textContent = '';
  copyButton.textContent = 'Copy BibTeX';
  dialog.showModal();
}));
dialog.querySelector('.close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});
dialog.addEventListener('close', () => citationTrigger?.focus());
copyButton.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(citationText.textContent);
    copyButton.textContent = 'Copied ✓';
    copyStatus.textContent = 'BibTeX copied to your clipboard.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(citationText);
    selection.removeAllRanges();
    selection.addRange(range);
    citationText.focus();
    copyStatus.textContent = 'Text selected. Press Ctrl+C or ⌘C to copy.';
  }
});

const sectionLinks = [...document.querySelectorAll('.site-header nav a')];
const sections = sectionLinks.map(link => document.querySelector(link.hash));
const header = document.querySelector('.site-header');
function updateNavigation() {
  const threshold = header.getBoundingClientRect().height + 42;
  const isAtEnd = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
  const visible = sections.filter(section => section.getBoundingClientRect().top <= threshold);
  let current = visible[visible.length - 1] || sections[0];
  if (isAtEnd) {
    // The final two sections can share the same bottom-most scroll position.
    const linked = sections.find(section => '#' + section.id === window.location.hash);
    const targetTop = linked?.getBoundingClientRect().top;
    current = targetTop >= 0 && targetTop < window.innerHeight ? linked : sections[sections.length - 1];
  }
  for (const link of sectionLinks) {
    if (link.hash === '#' + current.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
}

let scrollUpdateQueued = false;
function scheduleNavigationUpdate() {
  if (scrollUpdateQueued) return;
  scrollUpdateQueued = true;
  requestAnimationFrame(() => {
    updateNavigation();
    scrollUpdateQueued = false;
  });
}
window.addEventListener('scroll', scheduleNavigationUpdate, { passive: true });
window.addEventListener('resize', scheduleNavigationUpdate);
window.addEventListener('load', updateNavigation);
window.addEventListener('hashchange', scheduleNavigationUpdate);
updateNavigation();
document.querySelector('#current-year').textContent = String(new Date().getFullYear());
