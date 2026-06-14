// CodeBridge from Bunchhh — content.js
// Injected into Claude.ai, ChatGPT, Gemini

(function () {
  'use strict';

  let WORKSPACE_ID = null;
  let PROJECT      = null;
  let badge        = null;

  // ── Selectors per platform ──────────────────────────────────
  const HOST = location.hostname;
  const INPUT_SEL =
    HOST.includes('claude.ai')   ? 'div[contenteditable="true"]' :
    HOST.includes('chatgpt.com') ? 'div[contenteditable="true"], #prompt-textarea' :
                                    'div[contenteditable="true"]';

  function getInput() {
    return document.querySelector(INPUT_SEL);
  }

  // ── Inject text into AI input ───────────────────────────────
  function injectText(text) {
    const el = getInput();
    if (!el) {
      alert('Click into the AI chat input first, then try again.');
      return;
    }
    el.focus();
    const sel   = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('insertText', false, text);
    el.dispatchEvent(new InputEvent('input', {bubbles: true}));
  }

  // ── Create badge ────────────────────────────────────────────
  function createBadge(wsId, project) {
    if (badge) badge.remove();

    badge = document.createElement('div');
    badge.id = 'cb-badge';
    badge.style.cssText = `
      position: fixed; bottom: 76px; right: 14px;
      z-index: 999999;
      background: #0C0F0A;
      border: 1px solid rgba(168,212,144,0.3);
      border-radius: 12px;
      padding: 10px 14px;
      font-family: 'Segoe UI', sans-serif;
      font-size: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      min-width: 190px;
      user-select: none;
    `;

    badge.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
        <span style="font-size:14px">⚡</span>
        <span style="color:#E4EDD8;font-weight:600;font-size:12px">CodeBridge</span>
        <span style="font-size:9px;color:#3D4A30">by Bunchhh</span>
        <div style="margin-left:auto;width:5px;height:5px;border-radius:50%;
                    background:#A8D490;animation:cbpulse 2s ease infinite"></div>
      </div>
      <div style="font-size:10px;color:#3D4A30;font-family:monospace;margin-bottom:8px">
        ${wsId} · ${project}
      </div>
      <button id="cb-attach" style="
        width:100%;padding:7px 10px;border-radius:7px;border:none;cursor:pointer;
        background:linear-gradient(135deg,#A8D490,#4A8A30);
        color:#0C0F0A;font-size:11px;font-weight:700;
        font-family:'Segoe UI',sans-serif;margin-bottom:5px">
        📎 Attach workspace
      </button>
      <button id="cb-hide" style="
        width:100%;background:none;border:none;
        color:#3D4A30;font-size:10px;cursor:pointer;
        font-family:'Segoe UI',sans-serif">
        hide
      </button>
      <style>
        @keyframes cbpulse{0%,100%{opacity:.4}50%{opacity:1}}
      </style>
    `;

    document.body.appendChild(badge);

    document.getElementById('cb-attach').addEventListener('click', () => {
      chrome.runtime.sendMessage({type: 'CB_REQUEST_ATTACH'});
      document.getElementById('cb-attach').textContent = 'Loading files...';
    });

    document.getElementById('cb-hide').addEventListener('click', () => {
      badge.style.display = 'none';
      createMini();
    });
  }

  // ── Mini button ─────────────────────────────────────────────
  function createMini() {
    const m = document.createElement('button');
    m.id = 'cb-mini';
    m.textContent = '⚡';
    m.style.cssText = `
      position:fixed;bottom:76px;right:14px;z-index:999999;
      width:34px;height:34px;border-radius:50%;
      background:linear-gradient(135deg,#A8D490,#4A8A30);
      border:none;cursor:pointer;font-size:15px;
      box-shadow:0 2px 12px rgba(0,0,0,0.4);
    `;
    m.onclick = () => { m.remove(); badge.style.display = 'block'; };
    document.body.appendChild(m);
  }

  // ── File picker modal ────────────────────────────────────────
  function showPicker(files) {
    const old = document.getElementById('cb-picker');
    if (old) old.remove();

    const modal = document.createElement('div');
    modal.id    = 'cb-picker';
    modal.style.cssText = `
      position:fixed;inset:0;z-index:9999999;
      background:rgba(0,0,0,0.65);
      display:flex;align-items:center;justify-content:center;
    `;
    modal.innerHTML = `
      <div style="background:#0C0F0A;border:1px solid rgba(168,212,144,0.2);
                  border-radius:14px;padding:18px;width:340px;max-height:420px;
                  font-family:'Segoe UI',sans-serif;display:flex;flex-direction:column;gap:10px">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:13px;font-weight:600;color:#E4EDD8">⚡ Select files to attach</span>
          <button id="cb-picker-close" style="background:none;border:none;color:#6B7A60;cursor:pointer;font-size:18px">×</button>
        </div>
        <div style="overflow-y:auto;flex:1;display:flex;flex-direction:column;gap:3px">
          ${files.map(f => `
            <label style="display:flex;align-items:center;gap:8px;padding:5px 8px;
              background:rgba(255,255,255,0.02);border-radius:6px;cursor:pointer;
              font-size:11px;color:#6B7A60;font-family:monospace">
              <input type="checkbox" data-path="${f}" style="accent-color:#A8D490"> ${f}
            </label>
          `).join('')}
        </div>
        <button id="cb-picker-attach" style="
          padding:9px;background:linear-gradient(135deg,#A8D490,#4A8A30);
          border:none;border-radius:8px;color:#0C0F0A;
          font-size:12px;font-weight:700;cursor:pointer;
          font-family:'Segoe UI',sans-serif">
          Attach selected files
        </button>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('cb-picker-close').onclick = () => modal.remove();
    modal.onclick = e => { if (e.target === modal) modal.remove(); };

    document.getElementById('cb-picker-attach').onclick = () => {
      const checked = [...modal.querySelectorAll('input:checked')].map(i => i.dataset.path);
      if (!checked.length) return;
      chrome.runtime.sendMessage({type: 'CB_REQUEST_ATTACH', files: checked});
      modal.remove();
    };
  }

  // ── Listen from popup & background ──────────────────────────
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === 'CB_CONNECTED') {
      WORKSPACE_ID = msg.workspace_id;
      PROJECT      = msg.project;
      createBadge(WORKSPACE_ID, PROJECT);
    }

    if (msg.type === 'CB_DISCONNECTED') {
      if (badge) badge.remove();
      const mini = document.getElementById('cb-mini');
      if (mini) mini.remove();
      WORKSPACE_ID = null;
    }

    if (msg.type === 'CB_INJECT') {
      injectText(msg.context);
      if (badge) document.getElementById('cb-attach').textContent = '📎 Attach workspace';
    }

    if (msg.type === 'CB_PICK_FILES') {
      showPicker(msg.files || []);
    }
  });

  // ── Init ─────────────────────────────────────────────────────
  async function init() {
    const d = await chrome.storage.local.get(['connected','workspace_id','project']);
    if (d.connected && d.workspace_id) {
      WORKSPACE_ID = d.workspace_id;
      PROJECT      = d.project;
      // Wait for page load
      setTimeout(() => createBadge(WORKSPACE_ID, PROJECT), 1500);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
