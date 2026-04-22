from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path


UPDATE_ONLY = {
    "MVideoBidder.exe",
    "_internal",
}


def wait_process_exit(pid: int, timeout: int = 90) -> None:
    if sys.platform != "win32":
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        output = (result.stdout or "").lower()
        if str(pid) not in output:
            return

        time.sleep(1)

    raise TimeoutError("Основной процесс не завершился вовремя")


def remove_path(path: Path) -> None:
    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def find_payload_root(extracted_dir: Path) -> Path:
    names = {p.name for p in extracted_dir.iterdir()}

    if "MVideoBidder.exe" in names or "_internal" in names:
        return extracted_dir

    child_dirs = [p for p in extracted_dir.iterdir() if p.is_dir()]
    if len(child_dirs) == 1:
        child = child_dirs[0]
        child_names = {p.name for p in child.iterdir()}
        if "MVideoBidder.exe" in child_names or "_internal" in child_names:
            return child

    return extracted_dir


def apply_update(extracted_dir: Path, app_dir: Path) -> None:
    payload_root = find_payload_root(extracted_dir)

    for item in payload_root.iterdir():
        if item.name not in UPDATE_ONLY:
            continue

        target = app_dir / item.name
        remove_path(target)

        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--app-dir", required=True)
    parser.add_argument("--exe-name", required=True)
    parser.add_argument("--pid", required=True, type=int)
    args = parser.parse_args()

    zip_path = Path(args.zip).resolve()
    app_dir = Path(args.app_dir).resolve()
    exe_path = app_dir / args.exe_name

    temp_extract_dir = zip_path.parent / "update_extracted"
    remove_path(temp_extract_dir)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    wait_process_exit(args.pid)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(temp_extract_dir)

    apply_update(temp_extract_dir, app_dir)

    subprocess.Popen([str(exe_path)], cwd=str(app_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())