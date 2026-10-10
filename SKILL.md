---
name: job-prep-kit
description: Help with a job search using existing résumés, experience notes and job descriptions. Use to prepare or tailor a résumé, assess roles, track applications and replies, prepare for interviews, or compare offers in a local workspace.
---

# Job preparation

Work from the user's materials and finish the task they asked for. Do not require them to fill out a workspace before helping.

## Start with what exists

Locate the user's workspace and read its `PROFILE.md` and `records/facts.md` if present. Use the material paths they supplied; do not search unrelated personal folders. Reuse confirmed answers and authorization.

For a new workspace, run `python scripts/init_workspace.py` from this skill's directory, or pass `--dest` with the user's chosen location. If it already exists, use it without reinitializing. Personal content belongs there, not in the public templates. Scripts live alongside this skill; `--workspace` always points to the personal directory.

If the user provided an old résumé, project notes or a folder of materials, follow [material intake](workflows/00-材料导入.md). Start producing the requested result; ask only for missing information that changes it. When working without file tools, provide the draft in chat and say what has not been saved.

## Choose the relevant workflow

| Request | Read |
| --- | --- |
| Import materials or reuse experience | [Material intake](workflows/00-材料导入.md) |
| Write or tailor a résumé | [Résumé writing](workflows/01-简历制作.md) |
| Assess a role or find suitable openings | [Role selection](workflows/02-岗位筛选.md) |
| Apply, record a reply or follow up | [Applications](workflows/03-投递管理.md) |
| Prepare for an assessment or review an interview | [Interview preparation](workflows/04-面试复盘.md) |
| Compare offers | [Offer decisions](workflows/05-Offer决策.md) |

Read only the relevant experience entries and job materials. Keep `records/facts.md` as the index; longer experience files are optional. A résumé, an application answer and an interview explanation may emphasize different details but must use the same facts.

For the JSON tracker, update `applications/data.json`, then run `python scripts/tracker.py render --workspace <workspace>`. This generates the tables and `applications/dashboard.html`; it does not submit applications. Link existing JD, sent résumé and interview files through optional `materials` fields. See [tool usage](scripts/README.md) only when those fields or commands are needed. Preserve an existing manual tracker if the user prefers it.

When assessing or preparing for a role, retain a short, evidence-based reason to pursue it, the question that could change the decision, and the next preparation focus in its optional `brief`. Link the relevant experience through `materials.experience`. Reuse the source notes; do not require these summaries before starting work or turn waiting for a reply into an invented task.

## Evidence and output

Use employer websites and official university employment sites first, retaining the source and check date. Unknown terms remain unknown. Personal claims come from the user's evidence; never expand them to match a JD. See [source guidance](reference/evidence-rules.md) when sources conflict or need qualification.

External submissions, messages and decisions follow the user's authorization and available tools. Save actual submission evidence and the résumé version sent. Report the result, material gaps and next action briefly; do not turn routine work into another checklist for the user.
