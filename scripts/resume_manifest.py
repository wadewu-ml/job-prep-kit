"""Check resume files against recorded hashes; never claim to inspect page layout."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(workspace, version_ids=None):
    root = (Path(workspace) / "resumes").resolve()
    data = json.loads((root / "versions.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("简历版本清单必须是对象")
    if data.get("schema_version") != 1 or not isinstance(data.get("versions"), list):
        raise ValueError("需要 schema_version=1 和 versions 数组")
    if not data["versions"]:
        raise ValueError("还没有登记简历；不能判定简历已完成")
    seen = set()
    checked = 0
    for version in data["versions"]:
        if not isinstance(version, dict):
            raise ValueError("简历版本条目必须是对象")
        if not isinstance(version.get("id"), str) or not version["id"] or version["id"] in seen:
            raise ValueError("版本 id 为空或重复")
        seen.add(version["id"])
        if version_ids is not None and version["id"] not in version_ids:
            continue
        checked += 1
        for kind in ("docx", "pdf"):
            path = (root / version[kind]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("简历路径不得逃出 resumes 目录")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != version.get(kind + "_sha256"):
                raise ValueError(f"{version['id']}: {kind} 哈希不一致，重新检查实际文件")
    if version_ids is not None and version_ids - seen:
        raise ValueError("投递引用了未登记的简历版本：" + ", ".join(sorted(version_ids - seen)))
    return checked


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(f"已核对 {verify(args.workspace)} 个版本的文件哈希；内容和版面需查看实际文件。")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, str(exc) + "\n")
