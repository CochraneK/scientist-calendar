# 科学家日历 · Scientist Calendar

一年 365 天，每天认识一位科学家。共 466 位精选人物档案：每一天有一位人物、一项发现、一个改变世界的念头。

- 在线版（GitHub Pages）：<https://cochranek.github.io/scientist-calendar/>
- 打印版：两份 A4 PDF——每日人物版（横版，471 页，一人一页）+ 月度生日版（纵版，13 页，一页一个月），站点导航可直接下载

## 功能

- 今日人物：按当天日期自动展示对应科学家
- 档案浏览：466 张档案卡，按领域筛选、支持搜索
- 头像模式：单字 / 照片切换；肖像来自 Wikimedia Commons，无肖像的人物回落为单字头像
- 打印版（每日人物版）：封面 + 打印说明 + 2 页总览 + 466 页人物页（页码 5–470）
- 打印版（月度生日版）：纵版 A4，一页一个月，每人只显示生日·名字·名言

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `app/` | 主应用（vinext + React 19），`page.tsx` 同时供静态站复用 |
| `app/data/scientists.json` | 466 位科学家档案（日期、领域、生卒年、贡献、轶事） |
| `app/data/quotes.json` | 人物语录，按 id 索引 |
| `app/data/curated_content*.json` | 人工精修稿（与 scientists.json 合并的增量源） |
| `tooling/pages/` | Vite 静态站（base `/scientist-calendar/`），构建输出到 `docs/` |
| `tooling/pages/extras/` | 构建后复制进 `docs/` 的附加文件（如 `backup-candidates.md`） |
| `docs/` | 静态站构建产物，GitHub Pages 直接从这里发布 |
| `public/` | 共享资源：`avatars/` 肖像、`avatars.json` 头像清单、`art/` 插画、`print/` 打印 PDF |
| `tooling/` | 开发工具集合：脚本、测试与迁移 Skill |
| `tooling/scripts/` | 数据、校验与 PDF 脚本（含 `verify_pdf_layout.py` 豆腐块护栏） |
| `tooling/tests/` | `node --test` 测试 |
| `tooling/skills/theme-calendar-factory/` | 可复用的「主题日历工厂」Skill（换主题不改生成器代码） |

## 数据脚本

| 命令 | 作用 |
| --- | --- |
| `npm run audit:data` | 结构体检：字段完整性、365 天覆盖、头像/语录关联、中文标点、年份格式 |
| `python -X utf8 tooling/scripts/fix_punctuation.py --dry` | 预览/修复正文里的半角标点 |
| `python -X utf8 tooling/scripts/verify_dates.py` | 用 Wikidata 交叉核验生卒年与生日（结果写入 `output/wikidata-cache.json` 缓存，gitignored 自动生成） |
| `python -X utf8 tooling/scripts/patch_data_fixes.py` | 历史数据修正留档（可重复执行） |

日期口径：全库统一使用**格里历**（公历）；Wikidata 中标为儒略历的日期已换算后比对。
个别生卒日期不可考的人物（如阿基米德、费马）落在占位日期或逝世纪念日上。

## 开发

```bash
npm install
npm run dev           # 主应用: http://localhost:3000
npm run build         # 构建主应用
npm run build:pages   # 构建静态站到 docs/（自动复制 extras）
npm test              # build + 测试（SSR 渲染与数据集一致性）
npm run lint
```

静态站以 `../public` 为公共资源目录；本地预览需带上 `/scientist-calendar/` 路径前缀。

## 打印版 PDF（两份）

每日人物版（横版 A4、一人一页）与月度生日版（纵版 A4、一页一个月）由两套脚本分别生成：

```bash
# 每日人物版（精选 466 位）
python -X utf8 tooling/scripts/generate_print_calendar.py
#   产物: output/pdf/科学家日历_精选466位_A4打印版.pdf

# 月度生日版（一页一个月，只显示 生日·名字·名言）
python -X utf8 tooling/scripts/generate_monthly_calendar.py
#   产物: output/pdf/科学家日历_月度生日版_A4.pdf
```

依赖 Python 3 + reportlab（内置中文字体 `UnicodeCIDFont`，无需额外安装字体）。生成后两份都覆盖复制到 `public/print/`，再 `npm run build:pages` 同步到 `docs/print/`（GitHub Pages 发布目录）：

```bash
cp "output/pdf/科学家日历_精选466位_A4打印版.pdf" "public/print/"
cp "output/pdf/科学家日历_月度生日版_A4.pdf"      "public/print/"
npm run build:pages
```

> 字体坑：CID 字体 `STSong-Light` 不含 `·`（U+00B7）字形，渲染会丢整段；生成器已在 `face="cn"` 时把 `·` 替换为 `・`（U+30FB）。每次重生成后务必跑 `python -X utf8 tooling/scripts/verify_pdf_layout.py <pdf> --check-tofu`，豆腐块必须为 0 才发版。

## 数据维护

- 一致性测试在 `tooling/tests/rendered-html.test.mjs`：id 唯一、365 天全覆盖、头像清单与语录引用完整
- 扩充候选池：`tooling/pages/extras/backup-candidates.md`（随站点发布）

## 发布

```bash
git push github main   # GitHub Pages 自动从 docs/ 目录发布
```
