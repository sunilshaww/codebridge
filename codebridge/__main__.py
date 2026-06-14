from .server import start
import sys, os

def main():
    """Entry point for CodeBridge CLI."""
    args = sys.argv[1:]

    if not args or args[0] != "start":
        print("\n⚡ CodeBridge from Bunchhh")
        print("Usage:")
        print("  codebridge start              ← uses current folder")
        print("  codebridge start /path/to/project\n")
        return

    # Get project path — default to current directory
    if len(args) > 1:
        path = args[1]
        if not os.path.isdir(path):
            print(f"Error: Folder not found — {path}")
            return
    else:
        path = os.getcwd()  # ← FIX: use current folder by default

    import codebridge.server as s
    s.PROJECT = os.path.abspath(path)
    start()

if __name__ == "__main__":
    main()