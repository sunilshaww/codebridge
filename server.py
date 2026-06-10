"""
CodeBridge — Connect your project to any AI.
One command. One code. Any model.
"""

import os, json, subprocess, socket, threading
import webbrowser, random, string
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ── State ──────────────────────────────────────────────────
PROJECT = os.getcwd()
CODE    = "CB-" + ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=4)) + \
          "-" + ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=4))
PORT    = 7777
LOG     = []   # change history

IGNORE  = {"__pycache__", "node_modules", ".git", "venv",
           ".next", "dist", "build", ".env"}
EXTS    = {".py",".js",".ts",".jsx",".tsx",".json",".yaml",
           ".yml",".md",".txt",".html",".css",".sh",".toml"}

# ── File tools ─────────────────────────────────────────────
def get_files():
    out = []
    for root, dirs, files in os.walk(PROJECT):
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in EXTS:
                rel = os.path.relpath(os.path.join(root, f), PROJECT)
                out.append(rel.replace("\\", "/"))
    return out[:80]

def read_file(path):
    full = os.path.join(PROJECT, path.replace("/", os.sep))
    if not os.path.exists(full):
        return f"ERROR: File not found — {path}"
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    full = os.path.join(PROJECT, path.replace("/", os.sep))
    if not os.path.abspath(full).startswith(os.path.abspath(PROJECT)):
        return "ERROR: Cannot write outside project."
    # Backup
    if os.path.exists(full):
        open(full + ".bak", "w").write(open(full).read())
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)
    LOG.append({"action": "fixed", "file": path})
    return f"OK: {path} saved."

def run_cmd(cmd):
    SAFE = ["python","pytest","npm","node","pip","git","ls","cat","echo","uvicorn","celery"]
    if not any(cmd.strip().startswith(s) for s in SAFE):
        return f"ERROR: Command not allowed — {cmd}"
    try:
        r = subprocess.run(cmd, shell=True, cwd=PROJECT,
                           capture_output=True, text=True, timeout=30)
        LOG.append({"action": "ran", "cmd": cmd})
        return (r.stdout + r.stderr)[-2000:]
    except Exception as e:
        return f"ERROR: {e}"

def undo(path):
    full = os.path.join(PROJECT, path.replace("/", os.sep))
    bak  = full + ".bak"
    if not os.path.exists(bak):
        return f"ERROR: No backup for {path}"
    open(full, "w").write(open(bak).read())
    os.remove(bak)
    return f"OK: {path} restored."

# ── MCP tool definitions ────────────────────────────────────
TOOLS = [
    {
        "name": "list_files",
        "description": "List all code files in the connected project.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "read_file",
        "description": "Read a file from the project. Always read before fixing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "e.g. src/main.py"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write a fix to a file. Always provide the COMPLETE file content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "run_command",
        "description": "Run a terminal command (python, pytest, npm, git...).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "undo",
        "description": "Undo the last AI fix to a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    }
]

def run_tool(name, args):
    if name == "list_files":  return {"files": get_files()}
    if name == "read_file":   return {"content": read_file(args.get("path",""))}
    if name == "write_file":  return {"result": write_file(args.get("path",""), args.get("content",""))}
    if name == "run_command": return {"output": run_cmd(args.get("command",""))}
    if name == "undo":        return {"result": undo(args.get("path",""))}
    return {"error": f"Unknown tool: {name}"}

# ── HTTP server ─────────────────────────────────────────────
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def json(self, data, code=200):
        b = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.cors(); self.end_headers(); self.wfile.write(b)

    def body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_GET(self):
        p = urlparse(self.path).path

        if p in ("/", "/index.html"):
            h = dashboard()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(h.encode())

        elif p == "/mcp":
            # MCP discovery — what AI platforms call first
            self.json({
                "name": "CodeBridge",
                "version": "1.0.0",
                "connection_code": CODE,
                "description": "Your project is connected. I can read files, write fixes, run commands.",
                "tools": TOOLS
            })

        elif p == "/status":
            self.json({
                "connected": True,
                "code": CODE,
                "project": os.path.basename(PROJECT),
                "path": PROJECT,
                "files": len(get_files()),
                "log": LOG[-10:]
            })

        else:
            self.json({"error": "not found"}, 404)

    def do_POST(self):
        p = urlparse(self.path).path
        b = self.body()

        if p == "/mcp":
            # AI platform calls a tool
            name = b.get("name") or b.get("tool", "")
            args = b.get("arguments") or b.get("input") or {}
            result = run_tool(name, args)
            self.json({"content": [{"type": "text", "text": json.dumps(result)}]})

        else:
            self.json({"error": "not found"}, 404)


# ── Dashboard HTML ──────────────────────────────────────────
def dashboard():
    ip = socket.gethostbyname(socket.gethostname())
    files = get_files()
    file_tags = "".join(
        f'<span style="padding:3px 10px;background:rgba(255,255,255,0.04);'
        f'border:1px solid rgba(255,255,255,0.08);border-radius:20px;'
        f'font-size:11px;font-family:monospace;color:#8B9E7A">{f}</span>'
        for f in files[:20]
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CodeBridge ⚡</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0D0F0B;color:#C4CDB8;font-family:'DM Sans',sans-serif;
     min-height:100vh;padding:24px 16px;max-width:560px;margin:0 auto}}
h1{{font-size:22px;font-weight:600;color:#E4EDD8;margin-bottom:4px}}
.mono{{font-family:'DM Mono',monospace}}
.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
       border-radius:12px;padding:18px;margin-bottom:14px}}
.tag-green{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;
            background:rgba(116,180,100,0.1);border:1px solid rgba(116,180,100,0.3);color:#74B464}}
.code-box{{background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);
           border-radius:10px;padding:16px;text-align:center}}
.big-code{{font-size:32px;font-weight:600;letter-spacing:5px;color:#A8D490;
           font-family:'DM Mono',monospace}}
.step{{display:flex;gap:12px;align-items:flex-start;padding:10px 0;
       border-bottom:1px solid rgba(255,255,255,0.04)}}
.step:last-child{{border-bottom:none}}
.num{{width:24px;height:24px;border-radius:50%;background:rgba(168,212,144,0.1);
      border:1px solid rgba(168,212,144,0.3);display:flex;align-items:center;
      justify-content:center;font-size:11px;color:#A8D490;flex-shrink:0;font-weight:600}}
.label{{font-size:13px;color:#E4EDD8;font-weight:500;margin-bottom:2px}}
.sub{{font-size:12px;color:#6B7A60}}
.files{{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}}
.log-item{{font-size:12px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);
           font-family:'DM Mono',monospace;color:#8B9E7A}}
@keyframes pulse{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}
.live-dot{{width:7px;height:7px;border-radius:50%;background:#74B464;
           animation:pulse 2s ease infinite;display:inline-block;margin-right:6px}}
</style>
</head><body>

<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
  <div style="display:flex;align-items:center;gap:10px">
    <div style="width:34px;height:34px;background:linear-gradient(135deg,#A8D490,#4A8A30);
                border-radius:9px;display:flex;align-items:center;justify-content:center;
                font-size:17px">⚡</div>
    <div>
      <h1>CodeBridge</h1>
      <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em">by <a href='https://bunchhh.com' style='color:#A8D490;text-decoration:none;font-weight:600'>Bunchhh</a> • AI CONNECTOR</div>
    </div>
  </div>
  <span class="tag-green"><span class="live-dot"></span>LIVE</span>
</div>

<!-- Project -->
<div class="card">
  <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em;margin-bottom:8px">CONNECTED PROJECT</div>
  <div style="font-size:16px;font-weight:600;color:#E4EDD8">{os.path.basename(PROJECT)}</div>
  <div class="mono" style="font-size:11px;color:#6B7A60;margin-top:2px">{PROJECT}</div>
  <div style="font-size:12px;color:#74B464;margin-top:6px">{len(files)} files indexed</div>
</div>

<!-- Connection Code -->
<div class="card" style="border-color:rgba(168,212,144,0.2)">
  <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em;margin-bottom:10px">YOUR CONNECTION CODE</div>
  <div class="code-box">
    <div class="big-code">{CODE}</div>
    <div style="font-size:11px;color:#6B7A60;margin-top:8px">Paste this into Claude / ChatGPT / Gemini</div>
  </div>
</div>

<!-- How to connect -->
<div class="card">
  <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em;margin-bottom:12px">HOW TO CONNECT YOUR AI</div>

  <div class="step">
    <div class="num">1</div>
    <div>
      <div class="label">Open Claude.ai / ChatGPT / Gemini</div>
      <div class="sub">Any free account works</div>
    </div>
  </div>

  <div class="step">
    <div class="num">2</div>
    <div>
      <div class="label">Add MCP integration</div>
      <div class="sub" style="margin-bottom:6px">Settings → Integrations → Add MCP</div>
      <div style="display:flex;align-items:center;gap:8px">
        <code style="font-size:11px;background:rgba(0,0,0,0.4);padding:4px 10px;
                     border-radius:6px;color:#A8D490;font-family:'DM Mono',monospace">
          http://{ip}:{PORT}/mcp
        </code>
        <button onclick="navigator.clipboard.writeText('http://{ip}:{PORT}/mcp');this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',2000)"
          style="padding:4px 12px;border-radius:6px;background:rgba(168,212,144,0.1);
                 border:1px solid rgba(168,212,144,0.3);color:#A8D490;font-size:11px;cursor:pointer">
          Copy
        </button>
      </div>
    </div>
  </div>

  <div class="step">
    <div class="num">3</div>
    <div>
      <div class="label">See the ⚡ logo appear</div>
      <div class="sub">That means AI is connected to your project</div>
    </div>
  </div>

  <div class="step">
    <div class="num" style="background:rgba(116,180,100,0.15);border-color:rgba(116,180,100,0.4);color:#74B464">✓</div>
    <div>
      <div class="label" style="color:#74B464">Talk to AI — it fixes your code directly</div>
      <div class="sub">No copy-paste. Changes save automatically.</div>
    </div>
  </div>
</div>

<!-- Files -->
<div class="card">
  <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em;margin-bottom:10px">PROJECT FILES AI CAN SEE</div>
  <div class="files">{file_tags if file_tags else '<span style="color:#3D4A30;font-size:12px">No code files found</span>'}</div>
</div>

<!-- Change log -->
<div class="card" id="log-card">
  <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em;margin-bottom:10px">AI CHANGE LOG</div>
  <div id="log-body" style="font-size:12px;color:#3D4A30">No changes yet.</div>
</div>

<!-- What AI can do -->
<div class="card">
  <div style="font-size:10px;color:#3D4A30;letter-spacing:.1em;margin-bottom:10px">WHAT AI CAN DO NOW</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
    {"".join(f'<div style="padding:8px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:8px;font-size:12px"><span style="color:#A8D490">{icon}</span> <span style="color:#C4CDB8">{label}</span></div>' for icon, label in [("📄","Read any file"),("✏️","Write fixes"),("🔍","Search code"),("▶️","Run commands"),("↩️","Undo changes"),("📱","Mobile control")])}
  </div>
</div>

<div style="text-align:center;font-size:11px;color:#2D3A20;padding:20px 0">
  CodeBridge by <a href='https://bunchhh.com' style='color:#A8D490;text-decoration:none'>Bunchhh</a> · <a href='https://bunchhh.com' style='color:#6B7A60;text-decoration:none'>Visit Bunchhh</a> · Press Ctrl+C to stop
</div>

<script>
async function refreshLog() {{
  const r = await fetch('/status');
  const d = await r.json();
  const el = document.getElementById('log-body');
  if (!d.log || d.log.length === 0) {{
    el.innerHTML = '<span style="color:#3D4A30">No changes yet. Start talking to your AI.</span>';
    return;
  }}
  el.innerHTML = d.log.reverse().map(l =>
    l.action === 'fixed'
      ? `<div class="log-item" style="color:#74B464">✅ Fixed → ${{l.file}}</div>`
      : `<div class="log-item">▶ Ran → ${{l.cmd}}</div>`
  ).join('');
}}
refreshLog();
setInterval(refreshLog, 4000);
</script>
</body></html>"""


# ── Start ───────────────────────────────────────────────────
def start():
    ip = socket.gethostbyname(socket.gethostname())
    srv = HTTPServer(("0.0.0.0", PORT), H)

    print(f"""
╔══════════════════════════════════════════════╗
║     ⚡  CodeBridge by Bunchhh  ⚡            ║
║   democratizing-ai-powered-development       ║
╠══════════════════════════════════════════════╣
║  Project  : {os.path.basename(PROJECT):<30} ║
║  Code     : {CODE:<30} ║
╠══════════════════════════════════════════════╣
║  Dashboard : http://localhost:{PORT}           ║
║  Mobile    : http://{ip}:{PORT}               ║
║  MCP URL   : http://{ip}:{PORT}/mcp           ║
╠══════════════════════════════════════════════╣
║  1. Copy the MCP URL above                   ║
║  2. Paste into Claude / ChatGPT / Gemini     ║
║  3. See ⚡ logo → start talking               ║
╠══════════════════════════════════════════════╣
║  Learn more: https://bunchhh.com             ║
╚══════════════════════════════════════════════╝
Press Ctrl+C to stop.
""")
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n⚡ CodeBridge stopped.")

if __name__ == "__main__":
    start()