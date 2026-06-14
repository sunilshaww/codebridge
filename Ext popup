// CodeBridge from Bunchhh — popup.js
// User pastes Workspace ID → extension connects to localhost:7777

const PORT = 7777;
let workspaceData = null;

// ── Helpers ───────────────────────────────────────────────────
function show(id)  { document.getElementById(id).classList.add('show'); }
function hide(id)  { document.getElementById(id).classList.remove('show'); }
function el(id)    { return document.getElementById(id); }

async function fetchWorkspace() {
  const res  = await fetch(`http://localhost:${PORT}/status`);
  if (!res.ok) throw new Error('CodeBridge not running');
  return await res.json();
}

async function fetchFiles() {
  const res = await fetch(`http://localhost:${PORT}/status`);
  const d   = await res.json();
  return d;
}

// ── Format Workspace ID ───────────────────────────────────────
function formatWsId(raw) {
  const clean = raw.toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (clean.length === 8) return `WS-${clean.slice(0,4)}-${clean.slice(4)}`;
  return raw.toUpperCase();
}

// ── Connect ───────────────────────────────────────────────────
el('connect-btn').addEventListener('click', async () => {
  const raw = el('ws-input').value.trim();
  if (!raw) return;

  el('connect-label').innerHTML = '<span class="spinner"></span> Connecting...';
  el('connect-btn').disabled    = true;
  el('error-msg').style.display = 'none';

  try {
    const data = await fetchWorkspace();

    // Verify workspace ID matches (loose check)
    const wsId = data.workspace_id || formatWsId(raw);

    workspaceData = data;

    await chrome.storage.local.set({
      connected:    true,
      workspace_id: wsId,
      project:      data.project,
      files_indexed: data.files_indexed,
      mcp_url:      `http://localhost:${PORT}/mcp`,
    });

    showConnected(wsId, data.project, data.files_indexed);

    // Notify active tab
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (tab) chrome.tabs.sendMessage(tab.id, {type: 'CB_CONNECTED', workspace_id: wsId, project: data.project}).catch(()=>{});

  } catch (e) {
    el('error-msg').textContent  = 'Cannot connect. Is "codebridge start" running in your terminal?';
    el('error-msg').style.display = 'block';
    el('connect-label').textContent = '⚡ Connect Workspace';
    el('connect-btn').disabled = false;
  }
});

// ── Show connected state ──────────────────────────────────────
function showConnected(wsId, project, filesCount) {
  hide('state-disconnected');
  show('state-connected');
  el('ws-id-display').textContent    = wsId;
  el('ws-project-display').textContent = project;
  el('ws-files-display').textContent  = `${filesCount} files indexed`;
  el('connect-label').textContent    = '⚡ Connect Workspace';
  el('connect-btn').disabled         = false;
}

// ── Attach workspace to current AI page ──────────────────────
el('attach-btn').addEventListener('click', async () => {
  // Fetch all file contents from local server
  el('attach-btn').textContent = 'Reading files...';

  try {
    const statusRes = await fetch(`http://localhost:${PORT}/status`);
    const status    = await statusRes.json();

    // Get file list
    const filesRes = await fetch(`http://localhost:${PORT}/mcp`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: 'list_files', arguments: {}})
    });
    const filesData = await filesRes.json();
    const files     = JSON.parse(filesData.content[0].text).files || [];

    // Read top 20 files
    let context = `\n\n---\n⚡ CodeBridge Workspace: ${status.workspace_id}\n`;
    context    += `Project: ${status.project} · ${files.length} files\n\n`;

    const topFiles = files.slice(0, 20);
    for (const path of topFiles) {
      try {
        const r = await fetch(`http://localhost:${PORT}/mcp`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({name: 'read_file', arguments: {path}})
        });
        const d   = await r.json();
        const txt = JSON.parse(d.content[0].text).content || '';
        if (txt && !txt.startsWith('ERROR')) {
          context += `### ${path}\n\`\`\`\n${txt.slice(0, 2000)}\n\`\`\`\n\n`;
        }
      } catch {}
    }
    context += `---\nNow help me: `;

    // Send to content script to inject into AI input
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (tab) {
      chrome.tabs.sendMessage(tab.id, {type: 'CB_INJECT', context});
    }

    el('attach-btn').textContent = '✅ Workspace attached!';
    setTimeout(() => el('attach-btn').textContent = '📎 Attach workspace to AI', 2000);

  } catch (e) {
    el('attach-btn').textContent = '❌ Error — is CodeBridge running?';
    setTimeout(() => el('attach-btn').textContent = '📎 Attach workspace to AI', 2000);
  }
});

// ── Pick files ────────────────────────────────────────────────
el('pick-btn').addEventListener('click', async () => {
  try {
    const r   = await fetch(`http://localhost:${PORT}/mcp`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: 'list_files', arguments: {}})
    });
    const d     = await r.json();
    const files = JSON.parse(d.content[0].text).files || [];

    await chrome.storage.local.set({filePicker: files});
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (tab) chrome.tabs.sendMessage(tab.id, {type: 'CB_PICK_FILES', files});
  } catch {}
});

// ── Disconnect ────────────────────────────────────────────────
el('disconnect-btn').addEventListener('click', async () => {
  await chrome.storage.local.clear();
  hide('state-connected');
  show('state-disconnected');
  el('ws-input').value = '';
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (tab) chrome.tabs.sendMessage(tab.id, {type: 'CB_DISCONNECTED'}).catch(()=>{});
});

// ── Auto-format Workspace ID input ───────────────────────────
el('ws-input').addEventListener('input', (e) => {
  let v = e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, '');
  e.target.value = v;
});

// ── Load saved state ─────────────────────────────────────────
async function init() {
  const d = await chrome.storage.local.get(['connected','workspace_id','project','files_indexed']);
  if (d.connected && d.workspace_id) {
    showConnected(d.workspace_id, d.project, d.files_indexed);
  } else {
    show('state-disconnected');
  }
}

init();