#!/usr/bin/env python3
"""测试入口:转交给运行时事实硬闸实现。"""

from pathlib import Path
import runpy


runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "check-fact-integrity.py"),
    run_name="__main__",
)
