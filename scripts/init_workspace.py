"""Create an ignored personal workspace without copying any existing user data."""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def initialize(destination, demo=False):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("目标已存在；为保护已有资料，不覆盖。请选择空的新目录。")
    destination.mkdir(parents=True)
    for name in ("README.md", "AGENTS.md", "MISSION.md", "PROFILE.md", "company-info.md", "学校行政流程.md"):
        shutil.copy2(ROOT / name, destination / name)
    for name in ("applications", "reference", "lessons", "workflows", "resumes", "scans"):
        # Only the versioned template allowlist is copied, never arbitrary attachments.
        for relative in json.loads((ROOT / "templates/workspace-files.json").read_text(encoding="utf-8"))[name]:
            source = ROOT / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name in ("records", "records/evidence", "resumes/source", "resumes/current", "resumes/archive", "interviews", "automation"):
        (destination / name).mkdir(parents=True, exist_ok=True)
    for source, target in (("templates/facts.md", "records/facts.md"), ("templates/resume-master.md", "resumes/source/master.md"), ("templates/resume-versions.json", "resumes/versions.json"), ("templates/applications.json", "applications/data.json"), ("templates/interview.md", "interviews/TEMPLATE.md"), ("templates/offer-comparison.md", "applications/Offer比较.md")):
        shutil.copy2(ROOT / source, destination / target)
    shutil.copy2(ROOT / "automation/config.template.json", destination / "automation/config.json")
    (destination / ".gitignore").write_text("*\n", encoding="utf-8")
    (destination / "START.md").write_text(
        "# 个人求职工作区\n\n此目录仅供本人使用，不要上传或整体分享。根项目是空白模板。\n\n"
        "1. 填 PROFILE.md 的方向和底线；无需一开始填完所有敏感字段。\n"
        "2. 按 workflows/01-简历制作.md 建 records/facts.md 和简历母版。\n"
        "3. 用 applications/data.json 记录岗位、凭证和日程；不要同时手改生成的视图。\n"
        "4. 将本目录交给助手，要求先读 AGENTS.md；按 workflows/README.md 选择任务。\n"
        "5. 工具在原模板项目 scripts/ 中，用 --workspace 指向本目录。\n",
        encoding="utf-8")
    (destination / "README.md").write_text(
        "# 个人求职工作区\n\n先读 [开始使用](START.md) 和 [工作流](workflows/README.md)。\n\n"
        "PROFILE 保存偏好与网申字段；records/facts.md 保存经历证据；"
        "applications/data.json 保存投递与日程，三个 Markdown 视图由工具生成。\n\n"
        f"工具项目位置：`{ROOT}`。在该项目目录运行：\n\n"
        f'```powershell\npython scripts/tracker.py render --workspace "{destination}"\n```\n\n'
        "真实简历和面试资料只放本目录，不上传或整体分享。简历流程见 workflows/01-简历制作.md，"
        "来源规则见 reference/evidence-rules.md。\n", encoding="utf-8")
    if demo:
        data = json.loads((ROOT / "templates/application-example.json").read_text(encoding="utf-8"))
        submission = data["applications"][0]["submission"]
        submission.pop("resume_version")
        submission["resume_unavailable_reason"] = "合成演示不附真实 DOCX/PDF；仅展示历史附件待补流程"
        (destination / "applications/data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(ROOT / "templates/demo.md", destination / "DEMO.md")
        with (destination / "START.md").open("a", encoding="utf-8") as f:
            f.write("\n本目录是合成演示，先读 DEMO.md；不要将演示记录用于真实申请。\n")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=ROOT / "private")
    parser.add_argument("--demo", action="store_true", help="填入合成台账及简短使用演示，不包含真实附件")
    args = parser.parse_args()
    try:
        print("已创建：", initialize(args.dest, demo=args.demo))
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
