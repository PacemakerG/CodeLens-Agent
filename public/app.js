'use strict';

// ── State ─────────────────────────────────────────────────────────────────────
let currentDate    = null;
let currentEntryId = null;
let searchTimeout  = null;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const dateSelect    = document.getElementById('date-select');
const searchInput   = document.getElementById('search');
const requestList   = document.getElementById('request-list');
const detailEmpty   = document.getElementById('detail-empty');
const detailContent = document.getElementById('detail-content');
const detailMeta    = document.getElementById('detail-meta');

const TAB_IDS = ['response', 'req-headers', 'req-body', 'res-headers'];
const tabBtns  = document.querySelectorAll('.tab-btn');
const tabPanels = {
  response:    document.getElementById('tab-response'),
  'req-headers': document.getElementById('tab-req-headers'),
  'req-body':  document.getElementById('tab-req-body'),
  'res-headers': document.getElementById('tab-res-headers'),
};

// ── Utility ───────────────────────────────────────────────────────────────────

function fmtTime(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  return d.toTimeString().slice(0, 8);
}

function methodClass(method) {
  const m = (method || '').toUpperCase();
  if (m === 'POST')   return 'method-post';
  if (m === 'GET')    return 'method-get';
  if (m === 'DELETE') return 'method-delete';
  return 'method-other';
}

function statusClass(code) {
  if (!code) return 'status-other';
  if (code >= 200 && code < 300) return 'status-ok';
  if (code >= 400) return 'status-err';
  return 'status-other';
}

// ── JSON syntax highlighting ──────────────────────────────────────────────────

function highlightJson(value) {
  let str;
  try {
    str = JSON.stringify(value, null, 2);
  } catch {
    return escapeHtml(String(value));
  }
  // Tokenize using regex — order matters
  return str.replace(
    /("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    match => {
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          // JSON key
          return `<span class="json-key">${escapeHtml(match)}</span>`;
        }
        return `<span class="json-str">${escapeHtml(match)}</span>`;
      }
      if (/true|false/.test(match)) return `<span class="json-bool">${match}</span>`;
      if (/null/.test(match))       return `<span class="json-null">${match}</span>`;
      return `<span class="json-num">${match}</span>`;
    }
  );
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderJsonBlock(data, rawText) {
  const div = document.createElement('div');
  div.className = 'content-block';

  const pre = document.createElement('pre');
  pre.className = 'json-view';

  if (data === null || data === undefined) {
    pre.textContent = '(empty)';
  } else if (typeof data === 'object') {
    pre.innerHTML = highlightJson(data);
  } else {
    pre.textContent = String(data);
  }

  const copyBtn = document.createElement('button');
  copyBtn.className = 'copy-btn';
  copyBtn.textContent = 'Copy';
  copyBtn.addEventListener('click', () => {
    const text = rawText ?? (typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data ?? ''));
    navigator.clipboard.writeText(text).then(() => {
      copyBtn.textContent = 'Copied!';
      copyBtn.classList.add('copied');
      setTimeout(() => { copyBtn.textContent = 'Copy'; copyBtn.classList.remove('copied'); }, 1500);
    });
  });

  div.appendChild(pre);
  div.appendChild(copyBtn);
  return div;
}

// ── Tabs ──────────────────────────────────────────────────────────────────────

function activateTab(tabId) {
  tabBtns.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  Object.entries(tabPanels).forEach(([id, panel]) => {
    panel.classList.toggle('active', id === tabId);
  });
}

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => activateTab(btn.dataset.tab));
});

// ── Request list ──────────────────────────────────────────────────────────────

async function loadRequestList(date, q) {
  if (!date) return;
  currentDate = date;

  let url = `/api/requests?date=${encodeURIComponent(date)}`;
  if (q) url += `&q=${encodeURIComponent(q)}`;

  requestList.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    const res = await fetch(url);
    const entries = await res.json();

    if (entries.length === 0) {
      requestList.innerHTML = `<div class="empty-state">No requests for ${date}.</div>`;
      return;
    }

    requestList.innerHTML = '';
    for (const e of entries) {
      const row = document.createElement('div');
      row.className = 'request-row';
      row.dataset.id = e.id;
      if (e.id === currentEntryId) row.classList.add('active');

      const sc = e.status_code;
      const duration = e.duration_ms != null ? `${e.duration_ms}ms` : '—';

      row.innerHTML = `
        <span class="req-time">${fmtTime(e.timestamp)}</span>
        <span class="method-badge ${methodClass(e.method)}">${e.method || '—'}</span>
        <span class="req-path" title="${escapeHtml(e.path || '')}">${escapeHtml(e.path || '—')}</span>
        <span class="req-status ${statusClass(sc)}">${sc || '—'}</span>
        <span class="req-duration">${duration}</span>
        ${e.response_type === 'stream' ? '<span class="stream-badge">SSE</span>' : ''}
      `;

      row.addEventListener('click', () => selectRequest(e.id, date));
      requestList.appendChild(row);
    }
  } catch (err) {
    requestList.innerHTML = `<div class="empty-state">Error: ${escapeHtml(err.message)}</div>`;
  }
}

// ── Request detail ────────────────────────────────────────────────────────────

async function selectRequest(id, date) {
  // Highlight row
  document.querySelectorAll('.request-row').forEach(r => r.classList.remove('active'));
  const row = document.querySelector(`.request-row[data-id="${id}"]`);
  if (row) row.classList.add('active');

  currentEntryId = id;

  try {
    const res = await fetch(`/api/requests/${encodeURIComponent(id)}?date=${encodeURIComponent(date)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const entry = await res.json();
    renderDetail(entry);
  } catch (err) {
    showDetailEmpty(`Error loading request: ${err.message}`);
  }
}

function renderDetail(entry) {
  detailEmpty.hidden = true;
  detailContent.hidden = false;

  // ── Meta header ──
  const sc = entry.status_code;
  const scClass = statusClass(sc);
  detailMeta.innerHTML = `
    <span class="method-badge meta-method ${methodClass(entry.method)}">${entry.method || '—'}</span>
    <span class="meta-path">${escapeHtml(entry.path || '—')}</span>
    <span class="${scClass === 'status-ok' ? 'meta-status-ok' : 'meta-status-err'}">${sc || '—'}</span>
    <span>${entry.duration_ms != null ? entry.duration_ms + 'ms' : '—'}</span>
    <span>${entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ''}</span>
    <span class="meta-id">${entry.id || ''}</span>
  `;

  // ── Request Headers ──
  tabPanels['req-headers'].innerHTML = '';
  tabPanels['req-headers'].appendChild(renderJsonBlock(entry.request_headers));

  // ── Request Body ──
  tabPanels['req-body'].innerHTML = '';
  tabPanels['req-body'].appendChild(renderJsonBlock(entry.request_body));

  // ── Response Headers ──
  tabPanels['res-headers'].innerHTML = '';
  tabPanels['res-headers'].appendChild(renderJsonBlock(entry.response_headers));

  // ── Response ──
  tabPanels['response'].innerHTML = '';
  if (entry.response_type === 'stream') {
    renderStreamResponse(entry, tabPanels['response']);
  } else {
    tabPanels['response'].appendChild(renderJsonBlock(entry.response_body));
  }

  activateTab('response');
}

function renderStreamResponse(entry, container) {
  // Assembled text
  const assembledDiv = document.createElement('div');
  assembledDiv.className = 'content-block';

  const textEl = document.createElement('div');
  textEl.className = 'assembled-text';
  textEl.textContent = entry.response_assembled || '(empty)';

  const copyBtn = document.createElement('button');
  copyBtn.className = 'copy-btn';
  copyBtn.textContent = 'Copy';
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(entry.response_assembled || '').then(() => {
      copyBtn.textContent = 'Copied!';
      copyBtn.classList.add('copied');
      setTimeout(() => { copyBtn.textContent = 'Copy'; copyBtn.classList.remove('copied'); }, 1500);
    });
  });

  assembledDiv.appendChild(textEl);
  assembledDiv.appendChild(copyBtn);
  container.appendChild(assembledDiv);

  // Raw chunks toggle
  if (entry.stream_chunks && entry.stream_chunks.length > 0) {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'chunks-toggle';
    toggleBtn.textContent = `Show raw chunks (${entry.stream_chunks.length})`;

    const chunksEl = document.createElement('div');
    chunksEl.className = 'raw-chunks';
    chunksEl.appendChild(renderJsonBlock(entry.stream_chunks,
      entry.stream_chunks.map((c, i) => `[chunk ${i}]\n${c}`).join('\n---\n')
    ));

    toggleBtn.addEventListener('click', () => {
      const open = chunksEl.classList.toggle('open');
      toggleBtn.textContent = open
        ? `Hide raw chunks (${entry.stream_chunks.length})`
        : `Show raw chunks (${entry.stream_chunks.length})`;
    });

    container.appendChild(toggleBtn);
    container.appendChild(chunksEl);
  }
}

function showDetailEmpty(msg) {
  detailEmpty.textContent = msg || 'Select a request to view details';
  detailEmpty.hidden = false;
  detailContent.hidden = true;
}

// ── Date selector ─────────────────────────────────────────────────────────────

async function initDates() {
  try {
    const res = await fetch('/api/dates');
    const dates = await res.json();

    if (dates.length === 0) {
      requestList.innerHTML = '<div class="empty-state">No logs found. Start the proxy to begin recording.</div>';
      return;
    }

    dateSelect.innerHTML = '';
    for (const d of dates) {
      const opt = document.createElement('option');
      opt.value = d;
      opt.textContent = d;
      dateSelect.appendChild(opt);
    }

    // Auto-select latest date
    dateSelect.value = dates[0];
    loadRequestList(dates[0], '');
  } catch (err) {
    requestList.innerHTML = `<div class="empty-state">Cannot reach server: ${escapeHtml(err.message)}</div>`;
  }
}

dateSelect.addEventListener('change', () => {
  currentEntryId = null;
  showDetailEmpty();
  loadRequestList(dateSelect.value, searchInput.value.trim());
});

// ── Search ────────────────────────────────────────────────────────────────────

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    loadRequestList(currentDate, searchInput.value.trim());
  }, 300);
});

// ── Bootstrap ─────────────────────────────────────────────────────────────────
initDates();
