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

document.getElementById('loadMore').addEventListener('click', ()=>{ PAGE++; renderPage(); });

// debounce helper
function debounce(fn, wait=250){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), wait); }}

document.getElementById('search').addEventListener('input', debounce(applyFiltersAndRender, 200));
document.getElementById('sort').addEventListener('change', applyFiltersAndRender);

fetchJSON();
