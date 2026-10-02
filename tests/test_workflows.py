import copy
import sys
import importlib.util
import json
import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def module(relative):
    spec = importlib.util.spec_from_file_location(Path(relative).stem, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


watch = module("automation/career_watch.py")
tracker = module("scripts/tracker.py")
initializer = module("scripts/init_workspace.py")
resume = module("scripts/resume_manifest.py")


def sample():
    return {"schema_version": 1, "applications": [{
        "id": "synthetic-001", "company": "示例企业", "project": "合成校招项目", "role": "示例岗位", "status": "submitted",
        "sources": {"receipt": {"kind": "employer", "locator": "https://example.invalid/receipt", "excerpt": "合成测试：已提交", "checked_at": "2030-09-01T10:00:00+08:00"}},
        "submission": {"at": "2030-09-01T10:00:00+08:00", "source": "receipt", "resume_version": "general-v1"},
        "next_action": "准备面试", "choices": ["示例岗位"],
        "events": [{"title": "合成测评截止", "at": "2030-09-02T18:00:00+08:00", "kind": "deadline", "source": "receipt", "done": False}]
    }]}


class TrackerTests(unittest.TestCase):
    def test_malformed_nested_fields_are_actionable(self):
        for field, value in (("sources", {"receipt": None}), ("submission", []),
                             ("events", [None]), ("result", None), ("status", [])):
            with self.subTest(field=field):
                data = sample()
                data["applications"][0][field] = value
                with self.assertRaisesRegex(ValueError, r"applications\[0\]"):
                    tracker.validate(data)

    def test_missing_receipt_is_not_submitted(self):
        data = sample()
        del data["applications"][0]["submission"]
        with self.assertRaises(ValueError):
            tracker.validate(data)

    def test_third_party_is_not_deadline_proof(self):
        data = sample()
        data["applications"][0]["sources"]["receipt"]["kind"] = "community"
        with self.assertRaises(ValueError):
            tracker.validate(data)

    def test_timezone_required(self):
        data = sample()
        data["applications"][0]["events"][0]["at"] = "2030-09-02T18:00:00"
        with self.assertRaises(ValueError):
            tracker.validate(data)

    def test_unique_ids(self):
        data = sample()
        data["applications"].append(copy.deepcopy(data["applications"][0]))
        with self.assertRaises(ValueError):
            tracker.validate(data)

    def test_feeling_is_not_rejection(self):
        data = sample()
        data["applications"][0]["status"] = "rejected"
        with self.assertRaises(ValueError):
            tracker.validate(data)

    def test_done_string_is_rejected(self):
        data = sample()
        data["applications"][0]["events"][0]["done"] = "false"
        with self.assertRaises(ValueError):
            tracker.validate(data)

    def test_company_count_and_completed_events(self):
        data = sample()
        other = copy.deepcopy(data["applications"][0])
        other["id"] = "synthetic-002"
        other["events"][0]["done"] = True
        data["applications"].append(other)
        views = tracker.render(data, datetime(2030, 9, 2, 9, tzinfo=timezone.utc))
        self.assertIn("已投企业/统一项目 1；已投记录 2", "\n".join(views["投递总表.md"]))
        self.assertEqual(sum("合成测评截止" in s for s in views["投递日程.md"]), 1)

    def test_manual_notes_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "applications"
            p.mkdir()
            (p / "时间轴.md").write_text("手写记录", encoding="utf-8")
            with self.assertRaises(ValueError):
                tracker.write_views(folder, tracker.render(sample()))
            self.assertFalse((p / "投递总表.md").exists())
            self.assertEqual((p / "时间轴.md").read_text(encoding="utf-8"), "手写记录")


class WorkspaceTests(unittest.TestCase):
    def test_changed_resume_and_path_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "resumes"
            root.mkdir()
            for name in ("sample.docx", "sample.pdf"):
                (root / name).write_bytes(b"synthetic bytes, not a real resume")
            digest = hashlib.sha256(b"synthetic bytes, not a real resume").hexdigest()
            version = {"id": "v1", "docx": "sample.docx", "pdf": "sample.pdf", "docx_sha256": digest, "pdf_sha256": digest,
                       "checks": dict.fromkeys(("content", "visual", "reading_order", "accessibility"), "passed")}
            data = {"schema_version": 1, "versions": [version]}
            (root / "versions.json").write_text(json.dumps(data))
            self.assertEqual(resume.verify(folder), 1)
            (root / "sample.pdf").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                resume.verify(folder)
            version["docx"] = "../outside.docx"
            (root / "versions.json").write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                resume.verify(folder)

    def test_init_and_render_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = initializer.initialize(Path(folder) / "personal")
            self.assertEqual((dest / ".gitignore").read_text().strip(), "*")
            self.assertTrue((dest / "workflows/01-简历制作.md").exists())
            data = json.loads((dest / "applications/data.json").read_text(encoding="utf-8"))
            tracker.write_views(dest, tracker.render(data))
            self.assertTrue((dest / "applications/投递总表.md").read_text(encoding="utf-8").startswith(tracker.MARKER))
            with self.assertRaises(ValueError):
                initializer.initialize(dest)
            with self.assertRaises(ValueError):
                resume.verify(dest)


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"base_url": "https://example.invalid", "days": 3, "future_days": 7, "request_interval": 0}
        self.page = {"name": "合成列表", "key": "sample", "path": "/list", "block_pattern": r"<ul>.*?</ul>", "link_pattern": r"/view/(\d+)", "date_mode": "event", "max_pages": 3, "empty_pattern": "END"}

    def block(self, number, days):
        date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        return f'<ul><a href="/view/{number}" title="sample">sample</a>{date}</ul>'

    def test_overlapping_page_does_not_hide_later_items(self):
        page = dict(self.page, max_pages=4)
        pages = [self.block(1, 1) + self.block(2, 1), self.block(2, 1) + self.block(1, 1), self.block(3, 1), "END"]
        with patch.object(watch, "http_get", side_effect=pages):
            items, err = watch.fetch_list(page, self.cfg)
        self.assertIsNone(err)
        self.assertEqual([it["id"] for it in items], ["1", "2", "3"])

    def test_old_pinned_does_not_hide_next_page(self):
        pages = [self.block(1, -30) + self.block(2, 1), self.block(3, 2), "END"]
        with patch.object(watch, "http_get", side_effect=pages):
            items, err = watch.fetch_list(self.page, self.cfg)
        self.assertIsNone(err)
        self.assertEqual([it["id"] for it in items], ["2", "3"])

    def test_changed_markup_is_error(self):
        with patch.object(watch, "http_get", return_value="<html>login or changed page</html>"):
            items, err = watch.fetch_list(self.page, self.cfg)
        self.assertEqual(items, [])
        self.assertTrue(err)

    def test_network_failure_keeps_partial_items(self):
        with patch.object(watch, "http_get", side_effect=[self.block(1, 1), OSError("offline")]):
            items, err = watch.fetch_list(self.page, self.cfg)
        self.assertEqual(len(items), 1)
        self.assertIn("失败", err)

    def test_repeated_page_is_incomplete(self):
        with patch.object(watch, "http_get", return_value=self.block(1, 1)):
            items, err = watch.fetch_list(self.page, self.cfg)
        self.assertIn("分页可能失效", err)

    def test_invalid_date_is_error_not_crash(self):
        with patch.object(watch, "http_get", return_value='<ul><a href="/view/1" title="sample">x</a>2030-99-40</ul>'):
            items, err = watch.fetch_list(self.page, self.cfg)
        self.assertTrue(err)

    def test_render_partial_items_and_delta(self):
        cfg = dict(self.cfg, list_pages=[self.page], output_md="result.md", capture_dir="captures")
        with tempfile.TemporaryDirectory() as folder:
            config_path = str(Path(folder) / "config.json")
            with patch.object(watch, "http_get", side_effect=[self.block(1, 1), OSError("offline")]):
                self.assertFalse(watch.run(cfg, config_path))
            output = (Path(folder) / "result.md").read_text(encoding="utf-8")
            self.assertIn("sample", output)
            self.assertIn("失败", output)
            with patch.object(watch, "http_get", side_effect=[self.block(1, 1), "END"]):
                self.assertTrue(watch.run(cfg, config_path))
            capture = json.loads((Path(folder) / "captures/career_watch_latest.json").read_text(encoding="utf-8"))
            self.assertEqual(capture["pages"]["sample"]["new_urls"], [])

    def test_check_does_not_write(self):
        cfg = dict(self.cfg, list_pages=[self.page])
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(watch, "http_get", return_value="END"), patch("builtins.print"):
                self.assertTrue(watch.run(cfg, str(Path(folder) / "config.json"), check_only=True))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_max_items_reports_truncation(self):
        page = dict(self.page, max_items=1)
        with patch.object(watch, "http_get", side_effect=[self.block(1, 1) + self.block(2, 2), "END"]):
            items, err = watch.fetch_list(page, self.cfg)
        self.assertEqual(len(items), 1)
        self.assertIn("截断", err)

    def test_failure_does_not_reset_new_item_history(self):
        cfg = dict(self.cfg, list_pages=[self.page], output_md="result.md")
        with tempfile.TemporaryDirectory() as folder, patch("builtins.print"):
            path = str(Path(folder) / "config.json")
            for pages in ([self.block(1, 1), "END"], [OSError("offline")], [self.block(1, 1), "END"]):
                with patch.object(watch, "http_get", side_effect=pages):
                    watch.run(cfg, path)
            capture = json.loads((Path(folder) / "captures/career_watch_latest.json").read_text(encoding="utf-8"))
            self.assertEqual(capture["pages"]["sample"]["new_urls"], [])


if __name__ == "__main__":
    unittest.main()
