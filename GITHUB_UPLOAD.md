# GitHub Upload Instructions

Your project is ready to upload to GitHub! Follow these steps:

## 1. Create GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** icon (top right) → **"New repository"**
3. Repository settings:
   - **Name**: `sinlive` (or your preferred name)
   - **Description**: `TV Playout Automation System with HLS streaming`
   - **Visibility**: Public or Private (your choice)
   - **DO NOT** initialize with README (we already have one)
4. Click **"Create repository"**

## 2. Upload to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/sinlive.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

## 3. Alternative: Use GitHub Desktop

If you prefer a GUI:

1. Download [GitHub Desktop](https://desktop.github.com/)
2. Open GitHub Desktop
3. File → Add Local Repository → Select `C:\Users\unall\sinlive`
4. Click "Publish repository"
5. Choose name and visibility
6. Click "Publish"

## What's Included

✅ All source code (`app.py`, `templates/index.html`)
✅ Dependencies (`requirements.txt`)
✅ Documentation (`README.md`, `IDLE_INSTRUCTIONS.md`)
✅ Configuration (`.gitignore`)
✅ Sample videos (`videos/` directory)
✅ Idle screen (`idle.mp4`)

## What's Excluded (via .gitignore)

❌ Virtual environment (`.venv/`)
❌ Generated HLS segments (`static/hls/*.ts`, `*.m3u8`)
❌ Python cache (`__pycache__/`)
❌ IDE files (`.vscode/`, `.idea/`)
❌ Backup files (`*.backup`, `*.bak`)

## After Upload

Your repository will be available at:
`https://github.com/YOUR_USERNAME/sinlive`

You can then:
- Share the link with others
- Clone it on other machines
- Collaborate with team members
- Set up GitHub Actions for CI/CD (optional)

## Quick Commands Reference

```bash
# Check status
git status

# Add new files
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push

# Pull latest changes
git pull
```

---

**Need help?** Check the [GitHub Docs](https://docs.github.com/en/get-started)
