"""
All the things AI can do with the connected project.
Read, write, search, run, understand.
"""

import os, subprocess, json, fnmatch

IGNORE = {"__pycache__", "node_modules", ".git", "venv", ".env",
          "dist", "build", ".next", ".nuxt", "coverage"}
CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml",
             ".yml", ".env", ".md", ".txt", ".html", ".css", ".go",
             ".rs", ".java", ".cpp", ".c", ".sh", ".toml", ".ini", ".cfg"}

def list_files(project_path: str) -> list:
    """Return full file tree of the project."""
    result = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = sorted([d for d in dirs if d not in IGNORE])
        rel_root = os.path.relpath(root, project_path)
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext in CODE_EXTS:
                rel = os.path.join(rel_root, f) if rel_root != "." else f
                full = os.path.join(root, f)
                size = os.path.getsize(full)
                result.append({
                    "name": f,
                    "path": rel,
                    "full_path": full,
                    "ext": ext,
                    "size_kb": round(size / 1024, 1),
                })
    return result

def read_file(project_path: str, rel_path: str) -> dict:
    """Read a file from the project."""
    full = os.path.join(project_path, rel_path)
    if not os.path.exists(full):
        return {"error": f"File not found: {rel_path}"}
    if os.path.getsize(full) > 500_000:  # 500KB limit
        return {"error": "File too large (>500KB). Try a specific section."}
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    lines = content.splitlines()
    return {
        "path": rel_path,
        "content": content,
        "lines": len(lines),
        "size_kb": round(os.path.getsize(full) / 1024, 1),
    }

def write_file(project_path: str, rel_path: str, content: str) -> dict:
    """Write a fix directly to a file in the project."""
    full = os.path.join(project_path, rel_path)
    # Safety: must be inside project folder
    if not os.path.abspath(full).startswith(os.path.abspath(project_path)):
        return {"error": "Cannot write outside project folder."}
    os.makedirs(os.path.dirname(full), exist_ok=True)
    # Backup original
    backup = full + ".cb_backup"
    if os.path.exists(full):
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()
        with open(backup, "w", encoding="utf-8") as f:
            f.write(original)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return {"success": True, "path": rel_path, "backup": backup}

def search_code(project_path: str, query: str) -> dict:
    """Search for text across all project files."""
    results = []
    files = list_files(project_path)
    for file_info in files:
        try:
            with open(file_info["full_path"], "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if query.lower() in line.lower():
                    results.append({
                        "file": file_info["path"],
                        "line": i,
                        "content": line.strip(),
                    })
                    if len(results) >= 50:
                        break
        except:
            continue
        if len(results) >= 50:
            break
    return {"query": query, "results": results, "count": len(results)}

def run_command(project_path: str, command: str) -> dict:
    """Run a terminal command inside the project folder."""
    ALLOWED = ["python", "pytest", "npm", "node", "pip", "ls", "cat",
               "echo", "git status", "git log", "git diff", "uvicorn",
               "celery", "docker", "curl"]
    safe = any(command.strip().startswith(a) for a in ALLOWED)
    if not safe:
        return {"error": f"Command not allowed for safety: {command}"}
    try:
        result = subprocess.run(
            command, shell=True, cwd=project_path,
            capture_output=True, text=True, timeout=30
        )
        return {
            "command": command,
            "stdout": result.stdout[-3000:],  # last 3000 chars
            "stderr": result.stderr[-1000:],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (30s)"}
    except Exception as e:
        return {"error": str(e)}

def undo_last_fix(project_path: str, rel_path: str) -> dict:
    """Restore a file to before the last AI fix."""
    full = os.path.join(project_path, rel_path)
    backup = full + ".cb_backup"
    if not os.path.exists(backup):
        return {"error": "No backup found for this file."}
    with open(backup, "r") as f:
        original = f.read()
    with open(full, "w") as f:
        f.write(original)
    os.remove(backup)
    return {"success": True, "restored": rel_path}

def get_project_summary(project_path: str) -> dict:
    """Quick summary of the project structure."""
    files = list_files(project_path)
    by_ext = {}
    for f in files:
        ext = f["ext"]
        by_ext[ext] = by_ext.get(ext, 0) + 1
    total_size = sum(f["size_kb"] for f in files)
    return {
        "total_files": len(files),
        "total_size_kb": round(total_size, 1),
        "by_type": by_ext,
        "files": [f["path"] for f in files[:100]],
    }