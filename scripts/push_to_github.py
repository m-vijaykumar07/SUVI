"""
SUVI GitHub Deployment Script
Initializes Git, commits all project files, links remote repository, and pushes.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_git(cmd, check=True):
    print(f"[*] Running: git {cmd}")
    res = subprocess.run(f"git {cmd}", cwd=BASE_DIR, shell=True, capture_output=True, text=True)
    if res.stdout.strip():
        print(res.stdout.strip())
    if res.returncode != 0 and check:
        print(f"[!] Git error: {res.stderr.strip()}")
    return res

def main():
    print("=" * 65)
    print("       SUVI - Push Source Code to GitHub")
    print("=" * 65)

    # 1. Check Git installed
    try:
        subprocess.run("git --version", shell=True, check=True, capture_output=True)
    except Exception:
        print("[!] Error: Git is not installed or not found in system PATH.")
        sys.exit(1)

    # 2. Check or Init Git Repo
    if not (BASE_DIR / ".git").exists():
        print("[+] Initializing local Git repository...")
        run_git("init")
        run_git("branch -M main")

    # 3. Add and Commit
    print("[+] Staging project files...")
    run_git("add .")

    commit_msg = "feat: initial release of SUVI (Smart Unified Voice Intelligence)"
    print(f"[+] Committing with message: '{commit_msg}'...")
    run_git(f'commit -m "{commit_msg}"', check=False)

    # 4. Prompt for Remote URL
    print("\n--- GitHub Remote Repository Setup ---")
    print("To push to GitHub:")
    print("1. Go to https://github.com/new and create a new repository (e.g., named 'SUVI').")
    print("2. Copy the HTTPS or SSH clone URL (e.g., https://github.com/yourusername/SUVI.git).")
    
    remote_url = input("\nEnter your GitHub repository URL: ").strip()

    if not remote_url:
        print("[!] No repository URL provided. Committed locally. You can push manually anytime using:")
        print("    git remote add origin <URL>")
        print("    git push -u origin main")
        return

    # Check existing remote
    remotes = run_git("remote -v", check=False).stdout
    if "origin" in remotes:
        run_git(f"remote set-url origin {remote_url}")
    else:
        run_git(f"remote add origin {remote_url}")

    print(f"[+] Pushing to remote branch 'main'...")
    push_res = run_git("push -u origin main", check=False)

    if push_res.returncode == 0:
        print("\n" + "=" * 65)
        print("SUCCESS! SUVI source code has been successfully pushed to GitHub!")
        print("=" * 65)
    else:
        print("\n[!] Push completed with warnings or authentication prompt required.")
        print("If GitHub asked for authentication, please sign in or use a GitHub Personal Access Token (PAT).")
        print("Command to retry push manually:")
        print(f"    cd {BASE_DIR}")
        print("    git push -u origin main")

if __name__ == "__main__":
    main()
