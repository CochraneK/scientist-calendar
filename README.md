# 科学家日历 · Scientist Calendar

一年 365 天，每天认识一位科学家。项目收录 466 位人物，以日期、领域、贡献、故事、语录和肖像组织成可搜索的交互日历，并提供两套 A4 打印版。

- 在线版（GitHub Pages）：<https://cochranek.github.io/scientist-calendar/>
- 人物永久链接示例：`/scientist-calendar/scientists/newton/`
- 打印版：每日人物版（横版，一人一页）+ 月度生日版（纵版，一月一页）

## 功能

- 今日人物：按用户本地日期展示对应人物，跨午夜自动刷新
- 人物永久链接：466 位人物均有稳定 `/scientists/<id>/` 地址，可直接打开、复制和分享
- 分享人物：支持 Web Share API；不支持时自动回落到复制永久链接
- 搜索与社交预览：人物页生成独立 title、description、canonical、Open Graph、Twitter Card 与 `Person` JSON-LD，并进入 sitemap
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
| `app/page.tsx` | 主界面，同时供 vinext 与静态 Pages 入口复用；负责人物路由、浏览器历史与分享交互 |
| `app/data/scientists.json` | 466 位科学家完整档案 |
| `app/data/quotes.json` | 人物语录，按 id 索引 |
| `app/data/scientists-index.json` | 自动生成的轻量索引 |
| `app/data/details/` | 自动生成的 12 个月详情分片 |
| `app/data/curated_content*.json` | 人工精修内容及历史增量源 |
| `src/domain/scientistRoutes.ts` | 人物永久链接、Pages base path 与 URL 解析规则 |
| `src/domain/` | 日期、365 天日历等领域规则 |
| `src/hooks/` | 当前日期与跨午夜刷新逻辑 |
| `tooling/pages/` | GitHub Pages 的 Vite 构建入口与配置；构建时生成 466 个人物静态入口页与 sitemap |
| `tooling/scripts/check_pages_output.mjs` | 校验人物静态页、canonical、OG URL、Person JSON-LD 与 sitemap |
| `tooling/scripts/` | 数据审计、Wikidata 核验、PDF 生成与版面检查 |
| `tooling/tests/` | Node 渲染与数据一致性测试 |
| `tooling/requirements.txt` | PDF 工具链的 Python 固定依赖 |
| `tooling/data/legacy-avatars.json` | 历史照片债务基线，仅用于阻止新增无来源照片，不代表许可已核验 |
| `public/avatar-provenance.json` | 已核验肖像的逐文件来源、作者、许可证与 attribution 注册表 |
| `public/` | 肖像、插画、PDF 等静态资源 |
| `docs/` | 本地 `build:pages` 的构建输出；线上发布使用 Actions artifact，不提交到 Git |

## 开发

要求 Node.js `>=22.13.0`。

```bash
npm ci
npm run dev
```

完整本地验证：

```bash
npm run audit:deps
npm run typecheck
npm run typecheck:worker
npm run lint
npm run audit:data
npm run audit:avatars
npm run check:web-data
npm test
npm run build:pages
npm run check:pages
```

修改 `scientists.json` 或 `quotes.json` 后，先重新生成 Web 分片：

```bash
npm run build:web-data
npm run check:web-data
```

CI 会执行 `check:web-data`；如果生成文件落后于事实源，Quality 会直接失败。Pages 构建后还会执行 `check:pages`，逐个验证 466 个人物静态入口及 sitemap，避免永久链接或 SEO 元数据悄悄退化。

## 数据校验

| 命令 | 作用 |
| --- | --- |
| `npm run audit:deps` | npm 依赖安全审计；任何已知漏洞都会使 Quality 失败 |
| `npm run audit:data` | 字段、365 天覆盖、头像/语录关联、中文标点和年份格式体检 |
| `npm run audit:avatars` | 阻止新增或启用缺少 provenance 的照片；允许历史债务逐步补齐 |
| `npm run build:web-data` | 从完整数据生成轻量索引与 12 个月详情分片 |
| `npm run check:web-data` | 检查生成分片是否与事实源一致，不改文件 |
| `npm run check:pages` | 检查 466 个人物永久页、canonical/OG/JSON-LD 与 sitemap 是否完整 |
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

一条命令生成并校验两套打印版：

```bash
npm run pdf:build
```

也可以分步运行：

```bash
npm run pdf:daily
npm run pdf:monthly
npm run verify:pdf
```

默认产物：

- `output/pdf/科学家日历_精选466位_A4打印版.pdf`
- `output/pdf/科学家日历_月度生日版_A4.pdf`

`verify:pdf` 会对两份生成结果执行豆腐块/压字检查。确认通过后再复制到 `public/print/` 并重新构建 Pages：

```bash
cp "output/pdf/科学家日历_精选466位_A4打印版.pdf" "public/print/"
cp "output/pdf/科学家日历_月度生日版_A4.pdf" "public/print/"
npm run build:pages
npm run check:pages
```

生成器会规避 `STSong-Light` 对部分标点字形支持不足的问题；PDF 校验仍应作为每次重新生成后的发布前步骤。相关生成器、数据或 Python 依赖发生变化时，`PDF Quality` workflow 会在干净的 Python 3.13 环境重新生成并验证两份 PDF。

## 肖像来源

现有照片资源主要来自 Wikimedia Commons；没有照片的人物使用单字头像。历史照片早于逐文件 provenance 制度，完整 attribution 仍需逐项追溯，不能仅以“来自 Wikimedia Commons”替代具体许可记录。

为了不继续扩大这笔历史债务，`tooling/data/legacy-avatars.json` 固定了治理规则启用时已有的照片集合。今后新增照片，或把历史人物从 `photo: false` 改为 `photo: true`，必须在 `public/avatar-provenance.json` 同时添加完整记录，否则 `npm run audit:avatars` 与 CI 会失败。记录至少包含：

```json
{
  "scientist-id": {
    "sourceUrl": "https://commons.wikimedia.org/wiki/File:...",
    "author": "作者或来源机构",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
    "attribution": "按原始文件页要求填写的署名"
  }
}
```

历史条目补齐来源后，应把对应记录加入 `avatar-provenance.json`；基线文件只用于识别既有债务，不是许可证或来源证明。

## 发布

`main` 的发布链为：

1. `Quality` 对同一提交执行依赖安全审计、类型检查、lint、数据审计、头像 provenance 审计、生成数据一致性检查、Vinext 测试，并构建和逐项校验 Pages 人物永久页与 sitemap。
2. 只有 Quality 成功后，`Deploy to GitHub Pages` 才会 checkout 该次通过验证的**精确 commit SHA**。
3. Pages workflow 对同一 SHA 再次生成并校验静态站，然后上传 Pages artifact 并部署。

因此正常发布只需把已审查改动合入 `main`；不要手工提交 `docs/` 来绕过 Quality 门禁。

## 许可状态

当前仓库尚未声明顶层软件许可证。仓库公开可见不等同于自动授予代码复用许可；肖像、引语等第三方素材也分别受其原始来源和许可证约束。若计划把项目作为可复用开源软件发布，应在明确期望的授权范围后再添加合适的顶层 `LICENSE`，不要把第三方素材一并错误覆盖到软件许可证中。

## 数据维护

- `tooling/tests/rendered-html.test.mjs` 检查 SSR 渲染、id 唯一、365 天覆盖、头像与语录引用等契约
- `tooling/scripts/check_pages_output.mjs` 检查 Pages 人物永久页与 sitemap 的生成契约
- `tooling/pages/extras/backup-candidates.md` 保存后续扩充候选池
- 数据源更新后应同时运行 `audit:data`、`audit:avatars`、`build:web-data`、`check:web-data` 与完整测试
