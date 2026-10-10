# job-prep-kit

A local workspace for résumés, job applications, and interview preparation.

Keep the job description, the résumé you sent, the latest reply, and your next step in one place. Use the included notes to work on your résumé, compare roles, prepare for interviews, and evaluate offers. You can work through the files yourself or use an AI assistant that can read and edit them.

## Getting started

Download or clone this repository, then point your file-capable AI assistant at [SKILL.md](SKILL.md). Give it a résumé, a folder of project notes or a job description, and say what you want to work on:

> Use SKILL.md. My existing résumé is at `<path>`. Help me tailor it to this job description, using only experience supported by my materials.

The assistant reads what you already have, keeps reusable facts in a private workspace and asks about gaps that affect the task. You do not need to complete every template first. Document generation and website access use the tools available to your assistant.

With Python 3.10 or later, the assistant (or you) can create a workspace with:

```sh
python scripts/init_workspace.py
```

This creates `private/START.md`. Existing documents can stay where they are; record their paths instead of copying everything. The scripts use only the Python standard library. To use the notes without Python, copy the templates you need into a separate folder.

## Working through a job search

| Task | Guide |
| --- | --- |
| Bring in existing materials and reuse experience | [Material intake](workflows/00-材料导入.md) |
| Turn your experience into a clear résumé | [Résumé writing](workflows/01-简历制作.md) |
| Read job descriptions and decide where to apply | [Role selection](workflows/02-岗位筛选.md) |
| Complete applications and follow up on replies | [Applications](workflows/03-投递管理.md) |
| Practise for assessments and learn from interviews | [Interview preparation](workflows/04-面试复盘.md) |
| Compare offers and check the details before accepting | [Offer decisions](workflows/05-Offer决策.md) |

The workflow notes and templates are currently written in Chinese.

Each guide points to the relevant files in your workspace. Keep evidence for résumé claims, save the version sent with each application, and record replies against the right role. An uploaded document is not a submitted application; a difficult interview is not a rejection.

## Tracking applications

Update `private/applications/data.json`, then run:

```sh
python scripts/tracker.py render --workspace private
```

Open `private/applications/dashboard.html` in your browser. The page puts upcoming commitments and concrete next steps first. Below them, a compact opportunity list shows why a role is worth pursuing, what still needs checking, and the next step. Job descriptions, the résumé actually sent, relevant experience and interview notes stay linked to each role. Search the list or switch to completed applications; expand a row for materials and sources.

The dashboard is a local, read-only snapshot: no server, account or network connection is required. Ask the assistant to update the ledger, rerun the command and refresh the page. The same command also generates the application table, timeline and schedule. Completed events leave the schedule; offers awaiting a decision remain active. Waiting for a reply does not create a follow-up task. Optional role summaries can be added as you work; there is no profile-completion score or required intake form.

`records/facts.md` doubles as the experience index. Longer project notes can live in separate files, linked from that index. Applications can link existing materials through optional `materials` fields; there is no second copy of the tracking data.

Prefer a spreadsheet or a handwritten table? Keep your existing record. The JSON tracker and dashboard are optional.

To try the tracker with fictional data:

```sh
python scripts/init_workspace.py --dest private/demo --demo
python scripts/tracker.py render --workspace private/demo
```

Open `private/demo/DEMO.md` for a short walkthrough. See [script documentation](scripts/README.md) for the data format and optional résumé file checks.

## Optional listing watcher

`automation/career_watch.py` reads public, static job listings and reports new or changed entries. It needs settings for the site's page structure. The example configuration is fictional; replace it with a configuration for a site you have checked. See the [setup guide](automation/定时任务搭建指南.md).

The tracker does not send reminders. The watcher does not read your inbox or submit applications. Any scheduling or website interaction requires a separate tool and your instructions.

## Personal files

The repository contains blank templates and fictional examples. Fill them in inside your private workspace, not in the public template files. `private/` is ignored by Git, but that does not encrypt it or prevent manual uploads. Keep application receipts, contact details, and résumé attachments out of public commits.

[Privacy notes](reference/privacy.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)
