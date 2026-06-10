from .server import start
import sys, os

def main():
    """Entry point for CodeBridge CLI."""
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        if len(sys.argv) > 2:
            path = sys.argv[2]
            if os.path.isdir(path):
                import codebridge.server as s
                s.PROJECT = os.path.abspath(path)
        start()
    else:
        print("\n⚡ CodeBridge")
        print("Usage: python -m codebridge start")
        print("       python -m codebridge start /path/to/project\n")

if __name__ == "__main__":
    main()