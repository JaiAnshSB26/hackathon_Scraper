const DATA_PATH = '/scraper_flask/data/hackathons.json';

async function loadData(){
  const status = document.getElementById('status');
  const list = document.getElementById('list');
  try{
    status.textContent = 'Fetching JSON...';
    const res = await fetch(DATA_PATH, {cache: 'no-store'});
    if(!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    status.textContent = `Loaded ${data.length} entries`;
    renderList(data);
  }catch(e){
    console.error(e);
    status.textContent = 'Failed to load data — check path or run the workflow';
  }
}

function renderList(items){
  const list = document.getElementById('list');
  list.innerHTML = '';
  items.forEach(h => {
    const li = document.createElement('li');
    li.className = 'hackathon';
    const title = document.createElement('h3');
    title.textContent = h.title || 'Untitled';
    const date = document.createElement('div');
    date.textContent = h.date || '';
    const a = document.createElement('a');
    a.href = h.link || '#';
    a.textContent = 'Open';
    a.target = '_blank';
    li.appendChild(title);
    li.appendChild(date);
    li.appendChild(a);
    list.appendChild(li);
  });
}

// search
document.getElementById('search').addEventListener('input', function(e){
  const q = e.target.value.toLowerCase();
  const all = Array.from(document.querySelectorAll('.hackathon'));
  all.forEach(el => {
    const text = el.innerText.toLowerCase();
    el.style.display = text.includes(q) ? '' : 'none';
  });
});

loadData();
