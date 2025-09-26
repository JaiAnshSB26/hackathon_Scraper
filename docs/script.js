// Use a relative path so the page works when served from GitHub Pages under
// https://<user>.github.io/<repo>/ (absolute paths starting with '/' break
// when the site is hosted under a repo subpath).
const DATA_PATH = 'scraper_flask/data/hackathons.json';
const RAW_FALLBACK = `https://raw.githubusercontent.com/JaiAnshSB26/hackathon_Scraper/main/scraper_flask/data/hackathons.json`;

let ALL = [];
let VISIBLE = [];
let PAGE = 0;
const PAGE_SIZE = 24;

function $id(id){return document.getElementById(id)}

function setStatus(text){$id('status').textContent = text}

async function fetchJSON(){
  setStatus('Fetching data...');
  try{
    let res = await fetch(DATA_PATH, {cache:'no-store'});
    if(!res.ok) res = await fetch(RAW_FALLBACK, {cache:'no-store'});
    if(!res.ok) throw new Error('HTTP '+res.status);
    const data = await res.json();
    ALL = Array.isArray(data) ? data : [];
    setStatus(`Loaded ${ALL.length} entries`);
    applyFiltersAndRender();
  }catch(err){
    console.error(err);
    setStatus('Failed to load data — check workflow or JSON path');
  }
}

function renderCards(items, append=false){
  const grid = $id('grid');
  if(!append) grid.innerHTML = '';
  if(items.length === 0 && !append){
    grid.innerHTML = '<div class="card"><p>No hackathons found.</p></div>';
    return;
  }

  items.forEach(h => {
    const card = document.createElement('article');
    card.className = 'card';
    const title = document.createElement('h3');
    title.textContent = h.title || 'Untitled';
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = h.date || '';
    const desc = document.createElement('p');
    desc.textContent = h.description || '';
    const a = document.createElement('a');
    a.className = 'btn';
    a.href = h.link || '#';
    a.textContent = 'Open';
    a.target = '_blank';

    card.appendChild(title);
    card.appendChild(meta);
    if(desc.textContent) card.appendChild(desc);
    card.appendChild(a);
    grid.appendChild(card);
  });
}

function applyFiltersAndRender(){
  const q = $id('search').value.trim().toLowerCase();
  const sort = $id('sort').value;

  VISIBLE = ALL.filter(h => {
    if(!q) return true;
    const hay = `${h.title || ''} ${h.date || ''} ${h.link || ''}`.toLowerCase();
    return hay.includes(q);
  });

  if(sort === 'alpha') VISIBLE.sort((a,b)=> (a.title||'').localeCompare(b.title||''));
  else if(sort === 'oldest') VISIBLE.reverse();
  else VISIBLE = VISIBLE; // newest as-is (data order)

  PAGE = 0;
  renderPage();
  $id('counts').textContent = `${VISIBLE.length} results`;
}

function renderPage(){
  const start = PAGE * PAGE_SIZE;
  const end = start + PAGE_SIZE;
  const pageItems = VISIBLE.slice(start, end);
  const append = PAGE > 0;
  renderCards(pageItems, append);
  $id('loadMore').style.display = end < VISIBLE.length ? '' : 'none';
}

document.getElementById('loadMore').addEventListener('click', ()=>{ 
  PAGE++; 
  renderPage(); 
  // Smooth scroll to new content after a brief delay
  setTimeout(()=> {
    const cards = document.querySelectorAll('.card');
    if(cards.length > PAGE_SIZE) {
      const targetCard = cards[PAGE * PAGE_SIZE];
      if(targetCard) {
        targetCard.scrollIntoView({behavior:'smooth', block:'start'});
      }
    }
  }, 150);
});

// Enhanced scroll effects for gradient transitions
let scrollTimeout;
function handleScroll(){
  const scrollY = window.scrollY;
  const threshold = 200;
  
  if(scrollY > threshold) {
    document.body.classList.add('scrolled');
  } else {
    document.body.classList.remove('scrolled');
  }
  
  // Add subtle parallax effect to header
  const header = document.querySelector('.site-header');
  if(header && scrollY < 400) {
    header.style.transform = `translateY(${scrollY * 0.3}px)`;
    header.style.opacity = Math.max(0.3, 1 - scrollY / 600);
  }
}

window.addEventListener('scroll', ()=> {
  clearTimeout(scrollTimeout);
  scrollTimeout = setTimeout(handleScroll, 10);
});

// Add card animation on render
function animateCards(){
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, i) => {
    if(!card.classList.contains('animated')) {
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      setTimeout(()=> {
        card.style.transition = 'all 0.5s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
        card.classList.add('animated');
      }, i * 50);
    }
  });
}

// Override renderCards to include animations
const originalRenderCards = renderCards;
renderCards = function(items, append=false) {
  originalRenderCards(items, append);
  setTimeout(animateCards, 50);
};

// debounce helper
function debounce(fn, wait=250){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), wait); }}

document.getElementById('search').addEventListener('input', debounce(applyFiltersAndRender, 200));
document.getElementById('sort').addEventListener('change', applyFiltersAndRender);

fetchJSON();
