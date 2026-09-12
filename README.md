# CodeGuardian AI

AI code review bot for GitHub. Install once, get automatic reviews on every pull request.

---

## Install

**[Add CodeGuardian to your repositories →](https://github.com/apps/codeguardian-ai)**

Select the repos you want reviewed. That's it.

---

## How It Works

| Trigger | What Happens |
|---------|--------------|
| **Open a PR** | Automatic review starts |
| **Push new commits** | Re-review on sync |
| **Comment `/review`** | On-demand re-review |
| **Reopen PR** | Automatic review |

---

## What You Get

### On Every PR

**Inline comments** — Findings pinned to exact lines in your diff

**Summary review** — Consolidated verdict at the top:

```
## CodeGuardian Review — REQUEST_CHANGES

### Summary
This PR adds user authentication but misses input validation on the login endpoint.

### Suggested Commit Message
feat(auth): add login endpoint with JWT tokens

### Findings by Severity

#### ⚠️ Warning (2)
- **style** — `auth/login.py:42` — Function missing type hints on parameters
- **static** — `auth/login.py:55` — Unused import `json` (F401)

#### ℹ️ Info (1)
- **style** — `auth/utils.py:12` — Variable `usr` should be descriptive (`user`)

---

**OVERALL VERDICT: REQUEST_CHANGES**
```

**Check Run badge** — Shows on the PR's Checks tab and commit status

---

## Verdicts

| Verdict | Meaning | When |
|---------|---------|------|
| ✅ **APPROVE** | Clean — merge with confidence | No issues found |
| ⚠️ **REQUEST_CHANGES** | Fix needed | Style warnings or code quality issues |
| 🚨 **ESCALATE** | Security risk — do not merge | High-severity security finding (SQLi, XSS, secrets, etc.) |

---

## What Gets Reviewed

### Code Quality (Python)
- Unused imports, undefined variables, type mismatches
- Runs **only on lines you changed** — no noise from existing code

### Style (Python)
- **Baseline**: Type hints, docstrings, descriptive names, max 3 nesting levels
- **Your conventions**: Learns from your existing codebase (naming patterns, error handling, etc.)

### Security (30+ languages)
- SQL injection, XSS, hardcoded secrets, weak crypto, path traversal, command injection
- Python, JavaScript/TypeScript, Java, Go, Rust, and more

---

## Using It

### Automatic (Default)
Just open a PR. Review appears within ~30 seconds.

### Manual Trigger
Comment on any PR:
```
/review
```
Bot re-runs the full pipeline.

### Skip a Review
Add `[skip review]` to your PR title or description.

---

## What You'll See

### In the PR Conversation
- Bot posts a review with inline comments
- Each comment shows: **source** (static/style/security), **severity**, **message**

### In the Checks Tab
- "CodeGuardian Review" check with verdict
- Click for full details

### On Commits
- Green check (APPROVE), yellow (REQUEST_CHANGES), red (ESCALATE)

---

## FAQ

**Does it see my private code?**
Only the PR diff is analyzed. Your full codebase is never sent anywhere.

**What languages?**
- Code quality & style: Python
- Security: 30+ languages (JS/TS, Java, Go, Rust, etc.)

**Can I customize rules?**
Not on the hosted version. For custom rules, [self-host](SELF_HOSTING.md).

**False positive?**
Dismiss the inline comment or reply with context — the bot doesn't argue.

**How much?**
Free for public and private repos.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/codegaurdian/issues)
- **Email**: support@codeguardian.ai

---

*Self-hosting? See [SELF_HOSTING.md](SELF_HOSTING.md) for deployment guide.*