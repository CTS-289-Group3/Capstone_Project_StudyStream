# Git Workflow: Feature Branch + PR

## Step 1 — Create the issue on GitHub

1. Go to your GitHub repo → **Issues** → **New issue**
2. Copy the content from `GITHUB_ISSUE.md` into the issue body
3. Give it the title: `Calendar fixes + UI improvements (calendar hours, week view, task modals, logo)`
4. Add labels: `bug`, `enhancement`, `good first review`
5. **Submit** and note the issue number (e.g., `#7`)

---

## Step 2 — Create the feature branch locally

Open your terminal at the root of your project (`CSC-289/project_v2` or wherever your Django project lives):

```bash
# Make sure you're on main and up to date
git checkout main
git pull origin main

# Create and switch to the feature branch
git checkout -b feature/calendar-ui-improvements
```

---

## Step 3 — Copy in the updated files

Replace these files in your project with the ones from this zip:

| File to replace | Location in your project |
|---|---|
| `home/templates/home/home.html` | `home/templates/home/home.html` |
| `accounts/templates/accounts/home.html` | `accounts/templates/accounts/home.html` |
| `accounts/templates/accounts/base.html` | `accounts/templates/accounts/base.html` |
| `logo_navbar.png` | `accounts/static/accounts/images/logo_navbar.png` |
| `logo_icon.png` | `accounts/static/accounts/images/logo_icon.png` |

---

## Step 4 — Stage and commit

```bash
# Stage all changed files
git add accounts/templates/accounts/home.html
git add accounts/templates/accounts/base.html
git add home/templates/home/home.html
git add accounts/static/accounts/images/logo_navbar.png
git add accounts/static/accounts/images/logo_icon.png

# Commit with a descriptive message
git commit -m "fix: calendar hours, week view, task view modal, logo system

- Extend calendar to show 7am–11pm (was cut off at 8pm)
- Fix addCell missing definition (week view was broken/blank)
- Fix month-view day click offset calculation
- Add clickable day headers in week view → navigate to day view
- Add task view modal (read-only detail panel before edit)
- Calendar events now open task view modal instead of edit form
- Task name click opens view modal; Edit/Delete inside modal
- Fix edit modal overflow on small screens (max-height capped)
- Replace landing page text headline with logo image
- Use logo_navbar.png in nav, logo_icon.png in footer
- Compact landing page section padding

Closes #[INSERT_ISSUE_NUMBER]"
```

---

## Step 5 — Push the branch

```bash
git push origin feature/calendar-ui-improvements
```

---

## Step 6 — Open the Pull Request on GitHub

1. Go to your GitHub repo — you'll see a yellow banner: **"Compare & pull request"** — click it
2. Set:
   - **Base branch:** `main`
   - **Compare branch:** `feature/calendar-ui-improvements`
3. **Title:** `fix: Calendar hours, week view, task view modal, logo system`
4. Copy the content from `GITHUB_PR.md` into the PR description
5. Replace `#[INSERT_ISSUE_NUMBER]` with your actual issue number
6. Assign it to yourself; request a review from your groupmates
7. **Create pull request**

---

## Step 7 — After groupmate review

If they request changes:
```bash
# Make the changes they requested
git add .
git commit -m "fix: address PR review feedback"
git push origin feature/calendar-ui-improvements
```

When approved:
- Merge via **"Squash and merge"** or **"Merge pull request"** on GitHub
- Delete the feature branch after merging

