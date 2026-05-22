# Back up this project on GitHub

Your code is committed locally. **API keys in `.env` are NOT included** (protected by `.gitignore`).

## Step 1 — Create a GitHub repository

1. Sign in at [https://github.com](https://github.com)
2. Click **+** → **New repository**
3. Name it (example): `smarted-support` or `smarted-lms-copilot`
4. Choose **Private** (recommended — keeps your project visible only to you)
5. Do **not** add README, .gitignore, or license (this repo already has them)
6. Click **Create repository**

## Step 2 — Push from your PC

Open PowerShell in this folder:

```powershell
cd "C:\Users\Sharan\OneDrive\Desktop\smarted support"
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub username and repo name:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

GitHub may ask you to sign in (browser or personal access token).

## Step 3 — Download later

**On any computer:**

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

Then restore secrets locally (never commit these):

```powershell
copy .env.example .env
# Edit .env and add your GROQ_API_KEY, JWT_SECRET, etc.
```

Install and run — see root `README.md`.

## Optional — GitHub Desktop

If you prefer a GUI: install [GitHub Desktop](https://desktop.github.com/), **File → Add local repository**, select this folder, **Publish repository**.

## Security reminder

- `.env` and `backend/.env` stay on your machine only
- If you ever accidentally pushed a key, **rotate it** in Groq/OpenAI and change `JWT_SECRET`
- Use a **private** repo for coursework or client work
