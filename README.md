# 科学家日历 · Scientist Calendar

一年 365 天，每天认识一位科学家。项目收录 466 位人物，以日期、领域、贡献、故事、语录和肖像组织成可搜索的交互日历，并提供两套 A4 打印版。

- 在线版（GitHub Pages）：<https://cochranek.github.io/scientist-calendar/>
- 打印版：每日人物版（横版，一人一页）+ 月度生日版（纵版，一月一页）

## 功能

- 今日人物：按用户本地日期展示对应人物，跨午夜自动刷新
- 月历：365 天覆盖，同日多人可循环查看
- 档案浏览：按领域筛选并支持姓名、国家、领域和贡献搜索
- 渐进渲染：档案列表分批挂载，避免首屏一次创建全部 466 张卡片
- 按需详情：首包只加载轻量人物索引，长故事、趣闻和语录按月份动态加载
- 头像模式：单字 / 照片切换；无照片人物自动回落为单字头像
- 打印版：每日人物版与月度生日版均可从站点下载

## 数据与目录

`app/data/scientists.json` 与 `app/data/quotes.json` 是 Web 展示数据的**唯一事实源**。`scientists-index.json` 与 `details/*.json` 是自动生成的 Web 优化产物，不应手工编辑。

| 路径 | 说明 |
| --- | --- |
| `app/page.tsx` | 主界面，同时供 vinext 与静态 Pages 入口复用 |
| `app/data/scientists.json` | 466 位科学家完整档案 |
| `app/data/quotes.json` | 人物语录，按 id 索引 |
| `app/data/scientists-index.json` | 自动生成的轻量索引 |
| `app/data/details/` | 自动生成的 12 个月详情分片 |
| `app/data/curated_content*.json` | 人工精修内容及历史增量源 |
| `src/domain/` | 日期、365 天日历等领域规则 |
| `src/hooks/` | 当前日期与跨午夜刷新逻辑 |
| `tooling/pages/` | GitHub Pages 的 Vite 构建入口与配置 |
| `tooling/scripts/` | 数据审计、Wikidata 核验、PDF 生成与版面检查 |
| `tooling/tests/` | Node 渲染与数据一致性测试 |
| `tooling/requirements.txt` | PDF 工具链的 Python 固定依赖 |
| `public/` | 肖像、插画、PDF 等静态资源 |
| `docs/` | 本地 `build:pages` 的构建输出；线上发布使用 Actions artifact |

## 开发

要求 Node.js `>=22.13.0`。

```bash
npm ci
npm run dev
```

完整本地验证：

```bash
npm run typecheck
npm run typecheck:worker
npm run lint
npm run audit:data
npm run check:web-data
npm test
npm run build:pages
```

修改 `scientists.json` 或 `quotes.json` 后，先重新生成 Web 分片：

```bash
npm run build:web-data
npm run check:web-data
```

CI 会执行 `check:web-data`；如果生成文件落后于事实源，Quality 会直接失败。

## 数据校验

| 命令 | 作用 |
| --- | --- |
| `npm run audit:data` | 字段、365 天覆盖、头像/语录关联、中文标点和年份格式体检 |
| `npm run build:web-data` | 从完整数据生成轻量索引与 12 个月详情分片 |
| `npm run check:web-data` | 检查生成分片是否与事实源一致，不改文件 |
| `python -X utf8 tooling/scripts/verify_dates.py` | 使用 Wikidata 交叉核验生日与生卒年 |
| `python -X utf8 tooling/scripts/verify_facts.py` | 抽样核验高关注人物事实字段 |
| `python -X utf8 tooling/scripts/fix_punctuation.py --dry` | 预览正文半角标点修正 |

日期口径统一使用**格里历（公历）**。Wikidata 中明确标为儒略历的日期在核验时转换后比较；史料无法确定生日的人物可能使用纪念日或资料占位日期，相关情况应在数据中明确说明。

## PDF 工具链

建议使用独立虚拟环境；不依赖任何开发者机器上的固定 Python 路径。

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r tooling/requirements.txt
```

生成两套打印版：

```bash
python -X utf8 tooling/scripts/generate_print_calendar.py
python -X utf8 tooling/scripts/generate_monthly_calendar.py
```

默认产物：

- `output/pdf/科学家日历_精选466位_A4打印版.pdf`
- `output/pdf/科学家日历_月度生日版_A4.pdf`

发布前至少运行豆腐块/压字检查：

```bash
python -X utf8 tooling/scripts/verify_pdf_layout.py "output/pdf/科学家日历_精选466位_A4打印版.pdf" --quiet
python -X utf8 tooling/scripts/verify_pdf_layout.py "output/pdf/科学家日历_月度生日版_A4.pdf" --quiet
```

确认通过后再复制到 `public/print/` 并重新构建 Pages：

```bash
cp "output/pdf/科学家日历_精选466位_A4打印版.pdf" "public/print/"
cp "output/pdf/科学家日历_月度生日版_A4.pdf" "public/print/"
npm run build:pages
```

生成器会规避 `STSong-Light` 对部分标点字形支持不足的问题；PDF 校验仍应作为每次重新生成后的发布前步骤。

## 肖像来源

现有照片资源主要来自 Wikimedia Commons；没有照片的人物使用单字头像。新增或替换肖像时必须同时记录原始文件页、作者/来源、许可证和许可证链接。历史图片的完整 provenance / attribution 元数据仍应持续补齐，不能仅以“来自 Wikimedia Commons”替代逐文件许可记录。

## 发布

`main` 的发布链为：

1. `Quality` 对同一提交执行类型检查、lint、数据审计、生成数据一致性检查、Vinext 测试和实际 Pages 构建。
2. 只有 Quality 成功后，`Deploy to GitHub Pages` 才会 checkout 该次通过验证的**精确 commit SHA**。
3. Pages workflow 重新生成 `docs/`，上传 Pages artifact 并部署。

因此正常发布只需把已审查改动合入 `main`；不要手工提交 `docs/` 来绕过 Quality 门禁。

## 数据维护

- `tooling/tests/rendered-html.test.mjs` 检查 SSR 渲染、id 唯一、365 天覆盖、头像与语录引用等契约
- `tooling/pages/extras/backup-candidates.md` 保存后续扩充候选池
- 数据源更新后应同时运行 `audit:data`、`build:web-data`、`check:web-data` 与完整测试
