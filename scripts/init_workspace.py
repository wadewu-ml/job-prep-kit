"""Create an ignored personal workspace without copying any existing user data."""
import argparse
import json
import shutil
from datetime import datetime, timedelta
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
        f"告诉助手：请按 `{ROOT / 'SKILL.md'}`，用这个个人工作区帮我完成当前任务。\n\n"
        "可以直接提供旧简历、材料所在位置或一条岗位链接，说明想改简历、选岗还是准备面试。"
        "助手按 workflows/00-材料导入.md 读取已有内容，只补问影响结果的缺项，不需要先填完模板。\n\n"
        "经历与出处复用 records/facts.md；长经历再按需拆出详情。投递与日程只记 applications/data.json，"
        "JD、实际附件和面试记录通过 materials 关联。\n\n"
        "工具在原模板项目 scripts/ 中。运行 tracker.py render --workspace 指向本目录后，"
        "双击 applications/dashboard.html 查看本地看板；数据变化后重新生成。手工台账也可以继续使用。\n",
        encoding="utf-8")
    (destination / "README.md").write_text(
        "# 个人求职工作区\n\n先读 [开始使用](START.md) 和 [工作流](workflows/README.md)。\n\n"
        "PROFILE 保存偏好与网申字段；records/facts.md 保存经历证据；"
        "applications/data.json 保存投递与日程，三个 Markdown 视图和本地看板由工具生成。\n\n"
        f"工具项目位置：`{ROOT}`。在该项目目录运行：\n\n"
        f'```powershell\npython scripts/tracker.py render --workspace "{destination}"\n```\n\n'
        "然后双击 applications/dashboard.html。现有文件可直接关联，不需要搬进本目录。\n\n"
        "真实简历和面试资料只放本目录，不上传或整体分享。简历流程见 workflows/01-简历制作.md，"
        "来源规则见 reference/evidence-rules.md。\n", encoding="utf-8")
    if demo:
        data = json.loads((ROOT / "templates/application-example.json").read_text(encoding="utf-8"))
        submission = data["applications"][0]["submission"]
        submission.pop("resume_version")
        submission["resume_unavailable_reason"] = "合成演示不附真实 DOCX/PDF；仅展示历史附件待补流程"
        # Relative dates let the demo show upcoming work whenever it is tried.
        now = datetime.now().astimezone().replace(microsecond=0)
        app = data["applications"][0]
        app["submission"]["at"] = (now - timedelta(days=1)).isoformat()
        app["sources"]["receipt"]["checked_at"] = now.isoformat()
        app["sources"]["interview"] = {
            "kind": "personal_notice", "locator": "applications/synthetic-001/notice.md",
            "excerpt": "合成演示：安排次日的面试，无真实招聘含义。", "checked_at": now.isoformat()}
        app["status"] = "interview"
        app["company"], app["role"] = "示例数据团队", "数据分析助理"
        app["choices"] = [app["role"]]
        app["location"] = "示例城市 A"
        app["next_action"] = "把一次数据核对的过程讲清楚"
        app["events"] = [{"title": "技术面试", "at": (now + timedelta(days=1)).replace(hour=14, minute=0, second=0).isoformat(), "kind": "scheduled", "source": "interview", "done": False}]
        app["materials"] = {"jd": "applications/synthetic-001/jd.md", "experience": "records/experiences/data-project.md", "interview": "interviews/synthetic-001.md"}
        app["brief"] = {"work": "核对数据质量，整理图表并解释结果。", "reason": "课程项目中的数据核对经历，可用于说明岗位要求的分析过程。", "preparation": "练习两分钟回答：先说数据用途，再解释缺失项如何处理。", "question": "新人主要做分析方法改进，还是例行报表？"}
        data["demo"] = True
        data["applications"].append({"id": "synthetic-002", "company": "示例应用团队", "project": "合成招聘项目", "role": "应用支持助理", "location": "工作地待核实", "status": "candidate", "sources": {}, "events": [], "needs_user": "确认是否考虑需要出差的岗位", "next_action": "了解实际出差频率，再判断是否申请", "brief": {"work": "协助产品演示和用户问题整理。", "reason": "有数据解释的相邻经历；客户现场工作仍需了解。", "question": "出差频率、驻场时长和工作城市均待核实。"}})
        for app_id, company, role, state, action, brief in (
            ("synthetic-003", "示例研究团队", "信息研究助理", "assessment", "完成一轮限时阅读练习", {"reason": "资料整理经历与岗位任务相关。", "preparation": "先归纳材料结论，再核对支持结论的依据。", "question": "试题形式以正式通知为准。"}),
            ("synthetic-004", "示例产品团队", "产品分析助理", "waiting", "等待正式反馈", {"reason": "已完成面试，关注问题分析和协作方式。"}),
            ("synthetic-005", "示例内容团队", "内容整理助理", "withdrawn", "", {"reason": "演示已结束记录；保留材料供后续复用。"}),
            ("synthetic-006", "示例运营团队", "运营分析助理", "offer", "核对书面条件，再决定是否接受", {"reason": "已收到合成书面录用，用于演示条件比较。", "question": "固定收入与浮动部分的发放条件仍需确认。"}),
        ):
            record = {"id": app_id, "company": company, "project": "合成招聘项目", "role": role, "location": "地点待核实", "status": state, "sources": {"receipt": dict(app["sources"]["receipt"])}, "submission": dict(submission), "events": [], "next_action": action, "brief": brief}
            if state in {"assessment", "offer"}:
                record["sources"]["notice"] = {"kind": "personal_notice", "locator": f"applications/{app_id}/notice.md", "excerpt": "全部内容为合成示例，无真实招聘含义。", "checked_at": now.isoformat()}
                record["events"] = [{"title": "测评截止" if state == "assessment" else "录用回复截止", "at": (now + timedelta(days=3 if state == "assessment" else 5)).replace(hour=18, minute=0, second=0).isoformat(), "kind": "deadline", "source": "notice", "done": False}]
            if state == "offer":
                record["result"] = {"source": "notice"}
                record["needs_user"] = "核实条件后，决定是否接受这份录用"
                record["materials"] = {"offer": "applications/Offer比较.md"}
            data["applications"].append(record)
        demo_files = {
            "applications/synthetic-001/jd.md": "# 合成岗位说明\n\n仅供演示：整理公开数据、检查数据质量、制作图表和说明。来源 https://example.invalid/jobs/001 是占位链接，不是真实招聘。\n",
            "applications/synthetic-001/notice.md": "# 合成面试通知\n\n仅供演示，无真实招聘含义。时间按创建演示工作区的日期生成，见台账 events。\n",
            "applications/synthetic-003/notice.md": "# 合成测评通知\n\n全部为虚构资料，用于演示测评截止和准备动作。\n",
            "applications/synthetic-006/notice.md": "# 合成书面录用通知\n\n全部为虚构资料，用于演示书面录用、待核实条件和回复截止，不构成真实录用。\n",
            "records/experiences/data-project.md": "# 合成课程项目：公开数据整理\n\n事实ID：F001。来源：本演示虚构材料，不属于任何真实候选人。\n\n## 事实\n整理一份合成数据表，标记缺失项并制作图表；未提供性能或效率提升数字。\n\n## 可复用表达\n简历：整理数据、核对缺失项并制作图表说明。\n面试：先说明数据用于回答什么问题，再解释缺失项如何处理。\n\n## 相关反馈\n见 ../../interviews/synthetic-001.md；下次开场先交代问题和用途。\n",
            "interviews/synthetic-001.md": "# 合成面试准备\n\n岗位 synthetic-001；相关经历见 ../records/experiences/data-project.md。\n\n问题：你如何检查数据质量？\n准备：讲清缺失项核对方法，不编造提升百分比。\n下一次改动：先说明数据用途，再讲处理步骤。\n",
            "records/facts.md": "# 合成经历索引\n\n| ID | 主题 | 来源/详情 | 状态 |\n|---|---|---|---|\n| F001 | 公开数据整理课程项目 | [详情](experiences/data-project.md) | 合成演示，不是真实经历 |\n"}
        for relative, content in demo_files.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
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
