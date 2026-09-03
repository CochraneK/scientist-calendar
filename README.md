# 科学家日历 · Scientist Calendar

一年 365 天，每天认识一位科学家。共 466 位精选人物档案：每一天有一位人物、一项发现、一个改变世界的念头。

- 在线版（GitHub Pages）：<https://cochranek.github.io/scientist-calendar/>
- 打印版：A4 横版 PDF，471 页（站点导航中可直接下载）

## 功能

- 今日人物：按当天日期自动展示对应科学家
- 档案浏览：466 张档案卡，按领域筛选、支持搜索
- 头像模式：单字 / 照片切换；肖像来自 Wikimedia Commons，无肖像的人物回落为单字头像
- 打印版：封面 + 打印说明 + 2 页总览 + 466 页人物页（页码 5–470）

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `app/` | 主应用（vinext + React 19），`page.tsx` 同时供静态站复用 |
| `app/scientists.json` | 466 位科学家档案（日期、领域、生卒年、贡献、轶事） |
| `app/quotes.json` | 人物语录，按 id 索引 |
| `static/` | Vite 静态站（base `/scientist-calendar/`），构建输出到 `docs/` |
| `static/extras/` | 构建后复制进 `docs/` 的附加文件（如 `backup-candidates.md`） |
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

## 打印版 PDF

```bash
python -X utf8 tooling/scripts/generate_print_calendar.py
# 产物: output/pdf/科学家日历_精选466位_A4打印版.pdf（版次年号自动取当前年份）
```

依赖 Python 3 + reportlab，使用其内置中文字体（`UnicodeCIDFont`），无需额外安装字体。生成后覆盖复制到 `public/print/`，再运行 `npm run build:pages` 同步到 `docs/print/`。

```bash
cp "output/pdf/科学家日历_精选466位_A4打印版.pdf" "public/print/" && npm run build:pages
```

## 数据维护

- 一致性测试在 `tooling/tests/rendered-html.test.mjs`：id 唯一、365 天全覆盖、头像清单与语录引用完整
- 扩充候选池：`static/extras/backup-candidates.md`（随站点发布）

## 发布

```bash
git push github main   # GitHub Pages 自动从 docs/ 目录发布
```
