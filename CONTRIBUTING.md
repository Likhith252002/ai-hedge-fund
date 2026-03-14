# 🤝 Contributing to AI Hedge Fund

Thank you for considering a contribution! Here's everything you need to know.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Branch Naming](#branch-naming)
- [Commit Style](#commit-style)
- [Pull Request Process](#pull-request-process)

---

## 📜 Code of Conduct

Be respectful, constructive, and inclusive. We're all here to build something cool.

---

## 🛠️ How to Contribute

### 🐛 Bug Reports
Open an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).
Include: what you expected, what happened, and steps to reproduce.

### ✨ Feature Requests
Open an issue using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

### 🔧 Code Contributions
1. Fork the repo
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Make your changes
4. Test locally (backend + frontend both running)
5. Open a Pull Request

---

## 💻 Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/ai-hedge-fund.git
cd ai-hedge-fund

# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## 🌿 Branch Naming

| Type | Pattern | Example |
|:---|:---|:---|
| Feature | `feat/<name>` | `feat/sentiment-scoring` |
| Bug fix | `fix/<name>` | `fix/websocket-reconnect` |
| Docs | `docs/<name>` | `docs/api-reference` |
| Refactor | `refactor/<name>` | `refactor/agent-base-class` |

---

## 💬 Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add portfolio export to CSV
fix: handle yfinance rate limit on fundamentals
docs: update quick start section
refactor: extract retry logic to shared utility
```

---

## 🔍 Pull Request Process

1. **Target `main` branch**
2. **Fill in the PR template** — describe what changed and why
3. **Keep PRs focused** — one feature or fix per PR
4. **Ensure the app still runs** — test backend and frontend locally
5. **No secrets in commits** — never commit `.env` or API keys

A maintainer will review your PR within a few days. Thank you! 🙏
