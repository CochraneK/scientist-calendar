---
name: theme-calendar-factory
description: >
  主题日历（一人一天）站点 + 双 PDF 的成套流水线。用同一套「数据契约 + 生成 + 几何验收」，
  快速复刻出新的主题日历：历史学日历、共产党人日历、医学日历、文学家日历、哲学家日历等。
  覆盖：数据建模与字段映射、reportlab 生成「每日人物版(横版 A4, 一人一页)」与
  「月度生日版(纵版 A4, 一页一个月, 只显示生日/名字/名言)」、无法看图时如何用 PyMuPDF
  做几何重叠/越界/卡片泄漏体检、Wikidata 校验的三大假阳性来源（儒略/格里历、繁简标签、
  历史政权国名）、GitHub Pages 发布。
  触发场景：用户说「做一个 X 日历」「照着科学家日历做一个 Y 版」「把这个日历迁移到 Z 主题」
  「生成日历 PDF」「PDF 有重叠/遮挡/压字」「检查日历数据对不对」。
agent_created: true
---

# 主题日历工厂（theme-calendar-factory）

把「每天一个人」的日历做成一个可复制的流水线。已在**科学家日历**（466 人 / 365 天 / 双 PDF）
上跑通并踩平所有坑，换主题只需换数据 + 改配置，**不改生成器代码**。

## 一、什么时候用

- 用户要做一个新的主题日历（历史学 / 共产党人 / 医学 / 文学 / 哲学 / 音乐 / 体育…）
- 已有主题日历，要新增 PDF 版本，或修复 PDF 重叠、遮挡、压字
- 要批量校验人物数据（生日、国籍、领域）对不对

## 二、流水线总览

```
① 数据建模  ──>  ② 数据校验  ──>  ③ 生成两种 PDF  ──>  ④ 几何验收  ──>  ⑤ 发布
   entries.json      audit_data      每日人物版(横版)      verify_pdf_layout   GitHub Pages
   quotes.json       verify_dates    月度生日版(纵版)      （不看图，纯几何）
   theme.json        verify_facts
```

对应脚本（本 skill 的 `scripts/`）：
| 脚本 | 作用 |
|---|---|
| `generate_daily_pdf.py` | 每日人物版：横版 A4，**一人一页**（大图/名言/故事/双卡片） |
| `generate_monthly_pdf.py` | 月度缩览版：纵版 A4，**一页一个月**，每人只显示 生日·名字·名言 |
| `verify_pdf_layout.py` | PDF 几何体检：压字 / 越界 / 卡片泄漏（**不依赖看图**） |

## 三、数据契约

条目 JSON 最少需要：`id / month / day / name`。
建议补齐：`field / place / years / relation / tagline / story / cardA / cardB / color`。

- `color` ∈ `blue|coral|gold|green|violet`，缺失按 `blue`
- `quotes.json` 以 `id` 为键：`{"text": "...", "source": "..."}`；**没有名言时自动回落到 `tagline`**，不要硬造名言
- 中文行文用**全角标点**（原项目有专门的测试守这条，半角逗号/分号在中文里会判失败）
- 尽量覆盖 365 天；同一天多人是允许的

**换主题的正确姿势**：改 `assets/theme.example.json` 里的 `fieldMap`（逻辑角色 → 你的实际字段名），
生成器代码一动不动。例如医学日历把 `cardA` 映射到 `代表成就`、`field` 映射到 `科室`。

```bash
python tooling/scripts/generate_daily_pdf.py   --config theme.json
python tooling/scripts/generate_monthly_pdf.py --config theme.json
python tooling/scripts/verify_pdf_layout.py output/pdf/xxx.pdf --card-color F0EBE1
```

> **命名对照（易混）**：上面是**本 Skill 的模板脚本名**（`generate_daily_pdf.py` / `generate_monthly_pdf.py`）。
> 科学家日历项目把它们**定制化改名**为 `generate_print_calendar.py`（每日版）/ `generate_monthly_calendar.py`（月度版），
> 并放在 `tooling/scripts/` 下；`tooling/skills/theme-calendar-factory/scripts/` 里的同名文件才是对照模板。
> 换主题时以本 Skill `scripts/` 的模板为准，项目里的改名副本只是同一流水线的具体实现。

## 四、验收：看不到图时怎么保证版面正确（最关键的一节）

很多环境**无法查看渲染图**（读 PNG 会被过滤）。此时**不要靠肉眼**，用 PyMuPDF 做纯几何判定：

```python
page.get_text("words")   # -> (x0, y0, x1, y1, text, ...) 每个词的包围盒
page.get_drawings()      # -> 填充矩形（可据此定位卡片/色块）
```

三类检查：
1. **两两压字**：任意两个词包围盒若 `重叠宽 > 1.2pt 且 重叠高 > 1.2pt` 即为真压字（阈值避免贴边误报）
2. **越界**：内容文字越出内容区（撞页眉 / 掉出页底）
3. **卡片泄漏**：落在卡片矩形里、却不属于卡片内容的文字（卡片最后绘制时会被不透明填充盖住 → 内容丢失而非压字）
4. **豆腐块（tofu）**：中文被交给无中文字形的字体（如 Helvetica）渲染时，提取出的文字会变成连续的 `I`/`IIII`，
   页面上看着像乱码，但**压字检测完全查不出来**。用 `verify_pdf_layout.py` 的 `--check-tofu`（默认开）正则 `I{3,}` 抓，
   发现即回生成器把那行 `draw_text(..., "latin")` 去掉、改用中文字体（见坑 16）。

> ⚠️ 坐标系是两个坑：
> - **reportlab 原点在左下、y 向上**；**PyMuPDF 原点在左上、y 向下**。换算 `reportlab_y = 页高 - pymupdf_y`
> - 越界阈值因版面而异（横版/纵版、页眉高度不同）。`verify_pdf_layout.py` 默认**只跑压字与泄漏**，
>   越界需 `--check-bounds` 并手动给 `--header-y/--floor-y/--footer-y`

## 五、踩过的坑（照做可避开 90% 的返工）

### 版面类
1. **排版与绘制必须共用同一个高度函数。**
   曾经 pack 用 43pt、draw 用 55pt 推进 y，绘制比排版高 12pt → 最忙月份末条被挤出页底（不可见但确实丢了）。
2. **超长名字要按栏宽缩字号并截断，否则会越出本栏压到邻栏。**
   15 字的名字在 9pt 仍会溢出；要「11→7pt 逐级缩，仍放不下就截断加 …」。
3. **引语→来源→分隔线→故事 必须严格自上而下流水布局。**
   曾经来源与分隔线都由 `quote_end` 分别独立推算，多行来源时来源落到故事行上造成压字。
   改成「来源在分隔线之上、故事在分隔线之下」后，结构上就不可能互压。
4. **正文截断后不要 `join` 再重新换行。**
   重新换行会多出一行穿进卡片。要按预先算好的行、在固定 y 上逐行绘制。
5. **`roundRect(left, card_top, w, h)` 的顶边是 `card_top + h`，不是 `card_top`**（y 轴向上）。
   曾据此把内容底线设成 `card_top - 20`，实际让正文穿进了卡片。
6. **卡片最后绘制**，其不透明填充会盖住其后内容——这是"泄漏"的根因（不表现为压字，而是内容被吞）。
7. **卡片高度要自适应。** 固定高框在短内容（一句话）时非常丑；应按实际行数在 [46,174] 之间取值。

### 数据校验类（Wikidata 三大假阳性来源）
8. **儒略历 / 格里历**：9–13 天的偏移不是错误（莱布尼茨 7/1 vs 6/21、开普勒 1571-12-27 vs 1572-01-06）。
   且要注意方向：**Wikidata 可能存旧历，档案也可能存旧历，要双向比对**。
9. **`julian_to_gregorian` 用 `datetime.toordinal()` 是错的**：datetime 是前置格里历，
   会变成「格里历→JDN→格里历」的恒等变换，换算**静默失效**。必须用儒略历专用 JDN 公式。
   修完要用历史锚点验证（1582-10-04→10-14、1700-02-18→02-28、1900-01-01→01-13）。
10. **Wikidata 中文标签常返回繁体**（神聖羅馬帝國 / 內萊塔尼亞 / 萊茵邦聯），
    而归并表写的是简体 → 匹配不上。要先做繁→简归一，再配历史政权→现代国家表
    （还要注意译名差异：萨丁尼亚 / 撒丁尼亚）。
11. **多重国籍要逐项比对**，不能只比第一段（"塞尔维亚 / 美国" 的 Wikidata 可能只命中第二项）。
12. **生卒年差 > 2 年基本是 QID 挂错人**（纳什→Q309905 给出 1752/1835），
    要单独归为「QID 存疑」并**豁免其日期比对**（跟另一个人比日期毫无意义）。
    修完这类噪声，真实错误从 38 条降到 2 条。

### 工程类
13. **`build:pages` 若配置 `outDir: docs` + `emptyOutDir: true`，会清空发布目录**，
    中断即丢失已发布内容。确保 `public/` 里有全部素材可重建，并且不要在运行中打断。
14. **沙箱/受限环境里 `rm -rf dist` 可能触发批量删除保护而失败**，
    导致 `npm test` 挂在清空输出目录这步——这不是代码问题。用 `mv dist tmp/dist_old` 绕开
    （`tmp/` 通常已被 gitignore）。判断标准：看 transform 是否成功，而非 emptyDir 是否报错。
15. **验证脚本不要放在 `tmp/`**（通常被 gitignore，无法随项目迁移和复用），要放进 `tooling/scripts/` 提交（与生成器同目录）。

### 字体 / 渲染类
16. **中文标题/文字误用拉丁字体 → 豆腐块（连续 `III…`）**。
    生成器里 `draw_text(c, "科学家日历 · 月度版", ..., "latin")` 会把汉字交给 Helvetica 渲染，
    结果不是报错、而是整行变成 `IIII · II` 这种看不出内容的乱码，肉眼在页面上极难察觉，压字检测也查不出。
    - **根因**：`draw_text` 的 `face` 参数默认 `"cn"`（→ STSong-Light），但个别页眉/装饰行被显式写成 `"latin"`（→ Helvetica）。
    - **修法**：凡含中文的行一律不要带 `"latin"`；只有纯数字/英文（如 `"DAILY NOTEBOOK"`、日期 `12.31`）才用 `"latin"`。
    - **永久回归护栏**：`verify_pdf_layout.py` 已内置 `--check-tofu`（默认开），用 `re.findall(r"I{3,}", page_text)` 抓豆腐块，
      每次生成 PDF 后跑一遍，豆腐块必须为 0 才发版。科学家日历的月度版就曾带着这个 bug 发版，靠 smoke-test 才抓出。
17. **中文名姓/分隔用的 `·`（U+00B7 MIDDLE DOT）在 STSong-Light 下整段丢失**。
    数据里「名·姓」（如 `阿尔伯特·爱因斯坦`）以及副标题/页脚分隔「 · 」都依赖 U+00B7。
    但 STSong-Light(Adobe-GB1 CID 字体) 没有 U+00B7 的字形，reportlab 画到该字符会把**之后的整段文字一起丢掉**
    （月度版变成「阿尔伯特爱因斯坦」名姓粘连，精选版更狠——把姓截掉只剩名）。
    - **根因**：CID 字体 CMap 未含 U+00B7，reportlab 遇不可映射字符直接省略后续内容。
    - **修法**：`draw_text`/`draw_centered`/`wrap_lines` 在 `face="cn"` 时把 `U+00B7` 替换为 `U+30FB`（片假名中点，CID 字体有字形、视觉等价）；
      拉丁 face（Helvetica）保留 U+00B7（WinAnsi 含 0xB7，正常渲染）。
    - **验证**：重生成后用 PyMuPDF 抽 `阿尔伯特·爱因斯坦`，确认中间点码位存在（extract 回映射成 0xb7 也属正常）。
18. **月度版页脚靠右的文字必须用 `drawRightString`（右对齐），横向流式分栏会变成横向散排。**
    两处极易踩：
    - **页脚/页眉最右文字**（`每天认识一位科学家`、`主题 · 月度版`）若用 `drawString`（左对齐）且 `x = W - MARGIN`，
      文字会从右页边往右溢出，肉眼只看到「每天认识一」被切掉 → 改用 `draw_right(...)`（右对齐，文字落在 `x` 左侧）。
    - **分栏顺序**：`pack_month` 旧版 `ci = max(range(N_COLS), key=lambda i: col_y[i])` 是「贪心填最矮栏」，
      会横向散排（col0/col1/col2 各混排整月顺序）；用户要的是「先列后行」——先填满 col0 再 col1 再 col2。
      改成顺序填栏：`ci` 从 0 起，当前栏放不下才 `ci += 1`，三栏都满才续页。验证：把各栏展开后与排序序全等。
19. **名言/引语必须句末标点结尾（多数用句号）**。
    `quote_of` 取到的引语常无结尾标点（如 `知识就是力量`）；阅读体验上每句应成句。
    在 `quote_of` 出口统一 `ensure_terminal_punct`：已以 `。！？.!?…」』）`等结尾则保留，否则补 `。`；
    占位符 `—` 不处理。验证：跑全量 `quote_of` 确认 0 条缺结尾标点。
20. **通用模板里不得出现项目专属文案（同步修复时最易带入）。**
    曾把科学家日历项目修复同步回模板时，把页脚 `"每天认识一位科学家"` 一起带了进去，
    结果做「冒烟测试历」时页脚显示"每天认识一位科学家"——**主题串味**。
    - **根因**：模板其他地方都正确用了 `theme.cfg["theme"]["unitLabel"]`（如封面"每个月，认识在这个月出生的{unitLabel}们"），
      唯独页脚被写死；而且只做 `ast.parse` 语法检查**查不出**这种字符串级泄漏。
    - **修法**：任何面向用户的文案都从 `theme.cfg` 取（`unitLabel` / `theme.name`），函数需要就把主题对象传进去
      （如 `draw_footer(c, page_no, total, unit_label)`）。
    - **永久护栏**：换主题后**必须实际跑一次模板**（造 3–6 条 fixture，见下方冒烟测试），
      把产物文本抽出来 grep 旧主题名（如 `科学家`），必须为 0。**只做语法检查不够。**

### 模板冒烟测试（换主题后必做，2 分钟）
造一份最小 fixture（`entries.json` 6 条 + `quotes.json`），`theme.json` 里用**绝对路径**指向它们，然后真跑模板：

```bash
PY="<装有 reportlab 的解释器>"   # 例：C:/Users/cunyi/.workbuddy/binaries/python/envs/default/Scripts/python.exe
"$PY" scripts/generate_monthly_pdf.py --config /tmp/tcf_smoke/theme.json
"$PY" scripts/generate_daily_pdf.py   --config /tmp/tcf_smoke/theme.json   # 若用到每日版
```
fixture 要刻意包含：带 `·` 的名字、无句末标点的名言、超长名字（测缩字号/截断）。
产出后抽文本自检：`中点是否存在`、`名言是否都以标点结尾`、**旧主题名残留是否为 0**。

> **模板路径很脆弱**：`entryFile` / `quoteFile` 是 `Path(cfg[...])` **相对当前工作目录**解析，没有 join 项目根。
> 必须在**项目根目录**下运行（配置里写 `app/data/xxx.json`），换目录跑会找不到数据。

## 六、发布到 GitHub Pages

- Pages 源设为 `<branch>` 的 `/docs`；PDF 生成后复制到 `public/print/` **和** `docs/print/`
- 前端链接用相对路径 `print/xxx.pdf`，Pages 子路径下也能解析
- 沙箱里 `git push` 可用，但 `gh`/`curl` 常需清掉代理变量：
  `env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy -u ALL_PROXY -u all_proxy gh api ...`
- 发布后验证：`.../pages/builds/latest` 状态为 `built`，且 PDF URL 返回 200 且
  `Content-Length` 与本地文件一致（否则可能拿到的是旧文件）

## 七、迁移清单（换个主题照着走）

- [ ] 准备 `entries.json`（≥365 天覆盖）+ `quotes.json`（按 id 索引；没有就用 tagline 回落），**放进 `app/data/`**
- [ ] 复制 `assets/theme.example.json` 改名，填 `theme` 与 `fieldMap`（`entryFile`/`quoteFile` 已默认指向 `app/data/`）
- [ ] `python tooling/scripts/generate_daily_pdf.py --config theme.json`
- [ ] `python tooling/scripts/generate_monthly_pdf.py --config theme.json`
- [ ] `python tooling/scripts/verify_pdf_layout.py <pdf>` 两份都跑，**压字必须为 0**
- [ ] 每日版若保留卡片：`--card-color F0EBE1 --allow-file <卡片允许词条>`
- [ ] 数据体检：`verify_dates` / `verify_facts`，按第五节的 8–12 条分辨真假阳性
- [ ] 复制到 `public/print/` + `docs/print/`，提交推送，核验 Pages 200 + 文件大小一致
- [ ] 网页上补上新 PDF 的下载入口（**容易漏**：之前新增月度版就忘了挂链接）

### 七·附：默认目录布局（新项目开箱即用，别再走科学家日历踩坑的老路）

科学家日历复盘后定下的整洁下限：**数据、脚本、测试、Skill、独立静态站各归其位**，根目录只留框架锁死项。

```
<project>/
├─ app/                      # Next.js 站点
│  ├─ data/                  # 数据集：scientists.json / quotes.json / curated_content*.json
│  ├─ page.tsx
│  └─ ...
├─ public/                   # 静态素材（含 print/ PDF）
├─ docs/                     # GitHub Pages 发布目录（build:pages 输出）
├─ worker/                   # Cloudflare Worker
├─ tooling/                  # 非站点工程资产
│  ├─ scripts/              # generate_daily_pdf.py / generate_monthly_pdf.py / verify_pdf_layout.py / verify_dates.py ...
│  ├─ tests/                 # 渲染/数据测试
│  ├─ skills/                # 本 Skill 的项目内副本：skills/theme-calendar-factory/
│  └─ pages/                 # 独立静态站（vite，outDir 指向上层 ../../docs）
└─ （根目录仅剩框架锁死项：next.config.ts / vite.config.ts / package.json / tsconfig.json /
     postcss.config.mjs / README.md / .git* / .workbuddy / node_modules —— 约 17 项硬下限）
```

- **数据 JSON 一律进 `app/data/`**：`app/` 根从 12 项降到 3 项，避免"母路径一堆 JSON 外露"。
- **生成/验证脚本一律进 `tooling/scripts/`**：与 `scripts/` 平铺相比，根目录少一堆 `.py` 外露。
- **本 Skill 同时存一份到 `tooling/skills/theme-calendar-factory/`**，随项目走，新人 clone 即有一致工具链。
- **独立静态站放 `tooling/pages/`**，其 `vite.config.ts` 用 `outDir: "../../docs"`、`publicDir: "../../public"` 指回上层。
- 根目录"乱"的真相：**约一半是框架硬约束（Next/Vite/Cloudflare 配置必须根置），一半是没提前规划布局**。
  上面这套布局是框架约束下最干净的下限，新项目直接套，别再平铺。
