# AGENTS.md — 科学家日历

科学家日历：466 位科学家、365 天「每天认识一位」。产物是双 A4 PDF（每日人物版 471 页 / 月度生日版 13 页）+ GitHub Pages 站点。本文件是下次会话恢复上下文的入口，不是第二份 README。

## 怎么跑
- 站点：`npm run dev`（主站，vinext）、`npm run build:pages`（构建静态站到 `docs/`，**纯构建产物、已 gitignore，不提交；由 GitHub Actions 部署**）。
- **PDF 生成必须用托管 venv**：裸 `python` 与系统 `C:/Python313/python.exe` **都没有 reportlab**，会 `ModuleNotFoundError`。
  正确解释器：`C:/Users/cunyi/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（reportlab 5.x + PyMuPDF）。
  - `npm run pdf:daily` / `pdf:monthly` 本质是调 `tooling/scripts/` 下的生成器。
  - `npm run verify:pdf` 跑 `verify_pdf_layout.py --check-tofu`，豆腐块必须为 0 才发版。
- 发布（Pages 由 GitHub Actions 部署）：`git push origin main`（先用 `git remote -v` 核对远程名，当前为 `origin`）；push 前如遇到代理干扰 SSH 可用 `env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy -u ALL_PROXY -u all_proxy` 清代理。push 即触发 `.github/workflows/quality.yml` → 通过后触发 `pages.yml` → `build:pages` → 部署；`docs/` 不提交（已 gitignore），仓库 Pages 设置 Source 须为 `GitHub Actions`（非 `/docs`）。

## 技术栈
Next.js(vinext)/React19 主站 + Vite 独立静态站 + Cloudflare Worker；PDF 用 reportlab（`STSong-Light` CID 字体，无需装字体）。

## 目录与约定（别重新发明）
- 数据：`app/data/`（scientists.json / quotes.json / curated_content*.json）。
- 脚本：`tooling/scripts/`（Python 数据/校验/PDF）、`tooling/tests/`、`tooling/pages/`（Vite 站）、`tooling/skills/theme-calendar-factory/`（本项目复制的通用 skill；**权威源在用户级 `~/.workbuddy/skills/`**，改完 `cp` 同步两边）。
- 生成器里 `ROOT = Path(__file__).resolve().parents[2]`（脚本在 `tooling/scripts/` 下两层才是项目根；写 `parents[1]` 会让脚本找不到 `app/data`）。
- 根目录约 17 项硬下限（框架锁死项：next/vite/ts/worker 配置 + README + 子目录），勿删。

## 关键坑（不看会重踩）
- **CID 字体 `STSong-Light` 不含 `·`/U+00B7** → 渲染丢整段；凡 `face=="cn"` 一律用 `・`(U+30FB) 代替（已在生成器内 `_fix_dot` 处理）。
- 月度版三处护栏：页脚/页眉最右文字用 `draw_right` 右对齐防切、`pack_month` 顺序填栏（先列后行）、`quote_of` 句末补标点——改月度生成器别动掉。
- skill 通用模板**不得出现项目专属文案**（曾把「每天认识一位科学家」写死进页脚导致主题串味）；换主题后必须真跑一次模板冒烟测试，grep 旧主题名必须为 0。

## 当前状态 / 下一步
- 已发布可用：月度版排版修复 + 中点修复已验证；skill 模板页脚主题化回归已修（坑 #20 + 冒烟测试流程）。
- 已完成（**尚未验证/提交**）：
  - ① 每日人物版句末标点：`ensure_terminal_punct()` 已接入 `generate_print_calendar.py`（项目版）与 skill 的 `generate_daily_pdf.py`。注意数据里 466 条语录本就带标点，此为兜底防御。
  - ② `smoke_test_theme.py` 已落地到 `tooling/skills/theme-calendar-factory/scripts/`，造 fixture 真跑双生成器并自检三项（中点 / 句末标点 / 旧主题名残留为 0）。已跑通。
  - ③ 空态 `.empty-state` 样式补齐；领域筛选加 `aria-pressed`；空态加「返回全部人物」CTA。
- 下一步：`npm ci`（依赖缺失）→ `typecheck` / `lint` / `audit:data` → 提交推送。详见 `.workbuddy/memory/2026-11-23.md`。
- 记忆：`.workbuddy/memory/MEMORY.md` 存长期约定与常用命令；`.workbuddy/memory/YYYY-MM-DD.md` 存每日工作日志。注意 `.workbuddy/` 已被 gitignore，**重克隆会丢失**，重要状态请同步写入本文件。
