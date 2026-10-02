"""Package committed source only; never zip a personal working directory."""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package(output):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args])

    if git("status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("先检查并提交源码修改；打包只读取已提交的 HEAD")
    names = git("ls-tree", "-r", "--name-only", "-z", "HEAD").decode("utf-8").split("\0")
    if any(name.startswith("private/") for name in names):
        raise ValueError("private/ 已被跟踪，拒绝打包；先处理隐私资料")
    payload = git("archive", "--format=zip", "--prefix=job-prep-kit/", "HEAD")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as f:
        f.write(payload)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/job-prep-kit-source.zip")
    args = parser.parse_args()
    try:
        print(package(args.output))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + "\n")
