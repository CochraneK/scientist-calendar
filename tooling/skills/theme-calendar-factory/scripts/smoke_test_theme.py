#!/usr/bin/env python3
"""theme-calendar-factory 换主题冒烟测试脚本（换主题后必做）。

为什么需要它：
  - 换主题后，**只做语法/字符串检查**（如 ast.parse、grep 旧主题名）查不出真正的串味或渲染问题
  - 真实跑一遍模板生成 PDF，再抽取产物文本自检，才能确认：
      1. 中点（名姓分隔）渲染存在（不会像月度版那样把整段丢掉）；
      2. 名言/引语都以句末标点成句（没有补标点则发版后会「不成句」）；
      3. 旧主题名残留为 0（主题串味）。

触发场景：用户要「换主题」「迁移主题日历」「新增主题版」之后，先跑本脚本。
只依赖本 Skill 的模板脚本（generate_monthly_pdf.py / generate_daily_pdf.py），
加 reportlab + PyMuPDF 即可运行。

用法：
  python smoke_test_theme.py

环境：必须在**项目根目录**下运行（模板脚本的 entryFile/quoteFile 是相对当前工作目录解析）。

产物：在系统临时目录生成最小 fixture（entries.json / quotes.json / theme.json）
并真实跑两份模板，产出后做三项自检；结束后清理临时目录。
退出码：0 = 冒烟通过；1 = 存在问题（便于 CI/手动拦截）。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 本 Skill 的脚本目录
SCRIPT_DIR = Path(__file__).resolve().parent

# 模板生成器（本 Skill 的对照模板，不是项目定制版）
MONTHLY_GEN = SCRIPT_DIR / "generate_monthly_pdf.py"
DAILY_GEN = SCRIPT_DIR / "generate_daily_pdf.py"
ICS_GEN = SCRIPT_DIR / "generate_ics.py"
VERIFY_SCRIPT = SCRIPT_DIR / "verify_pdf_layout.py"
NO_START_PUNCT = frozenset("。，、；：！？）》」』”’…")

# 冒烟 fixture 规模：6 条（覆盖月/日/名/·/长名/无标点名言）
N_ENTRIES = 6

# 默认使用带 reportlab 的解释器；若环境缺少 reportlab 则给出迁移提示
DEFAULT_PY = r"C:/Users/cunyi/.workbuddy/binaries/python/envs/default/Scripts/python.exe"


def _has_reportlab(py: str) -> bool:
    """用 subprocess 检查 reportlab 与 PyMuPDF 是否可用（避免 import 时直接崩）。"""
    try:
        subprocess.run(
            [
                py,
                "-c",
                "import reportlab\ntry:\n    import pymupdf\nexcept ImportError:\n    import fitz",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def _make_fixture(root: Path, theme_name: str, unit_label: str) -> tuple[Path, Path]:
    """造最小 fixture：entries.json + quotes.json（含刻意边界：带·、超长名、无标点名言）。"""
    entries = []
    names = [
        ("阿尔伯特·爱因斯坦", "Albert Einstein"),
        ("玛丽·居里", "Marie Curie"),
        ("弗朗索瓦·马让迪", "François Magendie"),
        ("圣地亚哥·拉蒙-卡哈尔", "Santiago Ramón y Cajal"),
        ("约翰·纳什", "John Nash"),
        ("玛丽亚·安德烈耶娃", "Maria Andreyevova"),
    ]
    for i in range(N_ENTRIES):
        month = 1 + (i % 12)
        day = 1 + (i % 28)
        name, latin = names[i]
        entries.append({
            "id": f"smoke-{i}",
            "month": month,
            "day": day,
            "name": name,
            "latinName": latin,
            "years": "1540–1924",
            "field": "物理",
            "country": "瑞士",
            "color": "blue",
            "relation": "先驱",
            "tagline": "每天一位的候选条目",
            "story": "这是一条用于冒烟测试的短故事，包含 DSM-III 罗马数字与中文标点（用于验证卡片、避头点与零压字）。",
            "contribution": "核心贡献样例，用于卡片排版与折行检测。",
            "fact": "你知道吗的补充事实样例（含 DSM-III 罗马数字不误报豆腐块）。",
        })

    quotes = {
        "smoke-0": {"text": "医院最首要的要求，是不要伤害病人。", "source": "冒烟测试来源 0"},
        "smoke-1": {"text": "知识就是力量", "source": "冒烟测试来源 1"},  # 无句末标点，应被补句号
        "smoke-2": {"text": "爱提问、多观察，是科学研究的起点。", "source": "冒烟测试来源 2"},
        "smoke-3": {"text": "持续记录，才能留下可靠的知识。", "source": "冒烟测试来源 3"},
    }
    entries_path = root / "entries.json"
    quotes_path = root / "quotes.json"
    entries_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    quotes_path.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")

    theme = {
        "theme": {"name": theme_name, "nameEn": "Smoke Test Calendar", "unitLabel": unit_label},
        "entryFile": "entries.json",
        "quoteFile": "quotes.json",
        "outputDir": "pdf",
        "fieldMap": {
            "id": "id",
            "month": "month",
            "day": "day",
            "name": "name",
            "subtitle": "latinName",
            "years": "years",
            "field": "field",
            "place": "country",
            "relation": "relation",
            "tagline": "tagline",
            "story": "story",
            "cardA": "contribution",
            "cardB": "fact",
        },
        "labels": {
            "cardA": "核心贡献",
            "cardB": "你知道吗",
        },
    }
    theme_path = root / "theme.json"
    theme_path.write_text(json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries_path, quotes_path


def _extract_pdf_text(pdf_path: Path) -> str:
    """用 PyMuPDF 抽取 PDF 全部文本（用于冒烟自检，with 自动释放文件锁以便 Windows 清理临时目录）。"""
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24 推荐导入名
    except ImportError:
        import fitz  # 兼容旧版 PyMuPDF

    with fitz.open(str(pdf_path)) as doc:
        return "\n".join(page.get_text() for page in doc)


def _run_generator(py: str, gen_path: Path, config_path: Path) -> Path:
    """在临时目录下运行模板生成器，返回产出的 PDF 路径。"""
    out = subprocess.run(
        [py, str(gen_path), "--config", str(config_path)],
        cwd=str(Path.cwd()),  # entryFile/quoteFile 是相对当前工作目录解析
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if out.returncode != 0:
        raise RuntimeError(f"模板生成失败（{gen_path.name}）：\n{out.stdout}\n{out.stderr}")
    # 生成器会打印输出 PDF 路径；未指定 --out 时落在 outputDir
    out_pdf = Path(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else None
    return out_pdf


def _cleanup(path: Path) -> None:
    """清理临时目录。

    Windows 上 PDF 句柄可能尚未释放导致删除失败，此时明确告警并给出路径，
    不要用 ignore_errors 静默吞掉——否则项目里会悄悄堆积临时目录。
    """
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        print(f"⚠ 临时目录未能清理（可能有文件句柄未释放）：{path}", file=sys.stderr)


def _run_smoke(py: str) -> int:
    if not _has_reportlab(py):
        print(
            "缺少 reportlab/PyMuPDF，无法运行模板冒烟测试。\n"
            f"请在装有 reportlab 的解释器下运行，或设置 PY 指向它。默认：{DEFAULT_PY}",
            file=sys.stderr,
        )
        return 1

    # 用系统临时目录：避免在项目根目录留下垃圾（theme.json 里用的是绝对路径，不依赖 cwd）
    tmp = Path(tempfile.mkdtemp(prefix="tcf_smoke_"))
    root = tmp / "theme-smoke"
    root.mkdir(parents=True, exist_ok=True)
    try:
        _make_fixture(root, "冒烟测试历", "位医者")

        # 两份 PDF 模板 + 1 份 ICS 模板共用同一份 theme.json
        monthly_pdf = _run_generator(py, MONTHLY_GEN, root / "theme.json")
        daily_pdf = _run_generator(py, DAILY_GEN, root / "theme.json")
        ics_path = _run_generator(py, ICS_GEN, root / "theme.json")
        if not monthly_pdf or not daily_pdf or not ics_path:
            raise RuntimeError("模板未产出 PDF 或 ICS，请检查生成器输出")

        monthly_text = _extract_pdf_text(monthly_pdf)
        daily_text = _extract_pdf_text(daily_pdf)
        ics_raw = ics_path.read_text(encoding="utf-8")

        all_text = monthly_text + "\n" + daily_text

        # 自检 1：中点（名姓分隔）存在 —— STSong-Light 不含 U+00B7，渲染应保留中点码位
        dot_ok = "\u00b7" in all_text or "\u30fb" in all_text or "·" in all_text
        print(f"[自检 1] 中点（名姓分隔）渲染：{'通过' if dot_ok else '失败'}")

        # 自检 2：名言/引语都以句末标点成句（不缺句号）
        no_punct_ok = ("知识就是力量。") in all_text or ("知识就是力量") not in all_text
        print(f"[自检 2] 名言句末标点补齐：{'通过' if no_punct_ok else '失败'}")

        # 自检 3：旧主题名残留为 0（主题串味）
        residue_ok = (
            ("科学家日历" not in all_text)
            and ("每天认识一位科学家" not in all_text)
            and ("科学家日历" not in ics_raw)
        )
        print(f"[自检 3] 模板硬编码项目文案残留为 0：{'通过' if residue_ok else '失败（残留见产物文本）'}")

        # 自检 4：量词语法 & 每日版页脚主题化（不出现「出生的位医者们」、每日版页脚含「每天认识一位医者」）
        grammar_ok = ("出生的位" not in monthly_text) and ("出生的医者们" in monthly_text) and ("每天认识一位医者" in daily_text)
        print(f"[自检 4] 封面量词与每日版页脚主题化：{'通过' if grammar_ok else '失败'}")

        # 自检 5：ICS 符合 RFC 5545（75 字节折行 + 6 条 VEVENT）
        ics_lines = ics_raw.splitlines()
        ics_ok = (
            ics_raw.startswith("BEGIN:VCALENDAR")
            and ics_raw.count("BEGIN:VEVENT") == N_ENTRIES
            and all(len(ln.encode("utf-8")) <= 75 for ln in ics_lines)
        )
        print(f"[自检 5] RFC 5545 订阅日历 (.ics)：{'通过' if ics_ok else '失败'}")

        # 自检 6：STSong-Light 不静默吞掉欧洲重音字母，且不留全角拼音裂口（François → Francois，Ramón → Ramon）
        diacritic_ok = (
            ("Francois Magendie" in daily_text)
            and ("Franois" not in all_text)
            and ("Santiago Ramon y Cajal" in daily_text)
        )
        print(f"[自检 6] 欧洲重音字母防丢字与裂口（François / Ramón）：{'通过' if diacritic_ok else '失败'}")

        # 自检 7：几何排版体检（零压字 / 零豆腐块含 DSM-III 不误报）+ 零行首避头点标点
        v_daily = subprocess.run([py, "-X", "utf8", str(VERIFY_SCRIPT), str(daily_pdf), "--quiet"], capture_output=True)
        v_monthly = subprocess.run([py, "-X", "utf8", str(VERIFY_SCRIPT), str(monthly_pdf), "--quiet"], capture_output=True)
        bad_starts = [
            ln.strip() for ln in all_text.splitlines()
            if ln.strip() and ln.strip()[0] in NO_START_PUNCT
        ]
        layout_ok = (v_daily.returncode == 0) and (v_monthly.returncode == 0) and (len(bad_starts) == 0)
        print(f"[自检 7] 排版几何体检与行首避头点禁则：{'通过' if layout_ok else '失败'}")

        if dot_ok and no_punct_ok and residue_ok and grammar_ok and ics_ok and diacritic_ok and layout_ok:
            print("\n✓ 换主题冒烟测试通过（7/7）")
            return 0
        print("\n✗ 换主题冒烟测试未通过，请按上方自检修复模板后重跑", file=sys.stderr)
        return 1
    finally:
        _cleanup(tmp)


def main() -> int:
    if len(sys.argv) > 1:
        py = sys.argv[1]
    elif _has_reportlab(sys.executable):
        py = sys.executable
    else:
        py = DEFAULT_PY
    return _run_smoke(py)


if __name__ == "__main__":
    sys.exit(main())
