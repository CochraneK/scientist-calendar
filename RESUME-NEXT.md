# 任务恢复手册 · 头像三模式（单字/照片/线稿）

> 生成时间: 2026-08 会话暂停时。下次启动后按此文档继续。

## 一、任务目标

为科学家日历实现三种头像模式：**单字（默认）/ 真实照片 / 简笔画线稿**，网页 + PDF 均支持，线稿用于打印省墨（约 80%）。

## 二、当前进度（暂停时快照）

| 步骤 | 状态 | 说明 |
|---|---|---|
| 1. Wikidata 头像文件名映射 | ✅ 完成 | `tmp/avatar_map_all.json`（427/466 人有 P18 头像文件名） |
| 2. 下载头像到 public/avatars/ | ⏳ **196/427** | 重试脚本 `tmp/download_avatars_retry.py` 可续跑（只下载缺失的） |
| 3. 线稿生成 public/avatars/lineart/ | ⏳ 0/427 | 脚本 `tmp/make_lineart.py` 就绪，待下载完成后运行 |
| 4. 头像清单 public/avatars.json | ⏳ 未生成 | 脚本 `tmp/make_manifest.py` 就绪 |
| 5. 前端 page.tsx 三种模式切换 | ✅ 代码已改 | 含 `avatarFor()` 逻辑 + 模式切换按钮（单字/照片/线稿） |
| 6. 前端 globals.css 样式 | ✅ 已加 | `.portrait-image` / `.portrait-switch` / `.archive-photo` |
| 7. PDF 脚本线稿支持 | ✅ 已改 | `draw_entry` 圆形内嵌 lineart（有则用，无则单字） |
| 8. PDF 布局修复 | ✅ 已提交 | 总览页两页网格 + contribution 换行 + 姓名动态字号（commit `01bd6cb`） |
| 9. 构建 + 静态站 + 推送 | ⏳ 待做 | 头像相关改动尚未构建/提交 |

**已提交**: `01bd6cb`（PDF 布局修复）。头像前端代码 + 脚本在 `app/page.tsx`、`app/globals.css`、`scripts/generate_print_calendar.py`（未提交部分）。

## 三、暂停时的后台任务

- 头像下载任务 `pwsh-37`（`download_avatars_retry.py`）——关机会终止，重启后重跑即可（脚本幂等，只处理缺失的）。

## 四、下次启动后的执行步骤（按顺序）

```bash
# 1. 继续下载缺失头像（幂等，约需 10-20 分钟，串行+限速防 429）
python -X utf8 tmp/download_avatars_retry.py
#    完成后检查: (Get-ChildItem public\avatars -Filter *.jpg).Count 应接近 426（einstein 用现有 webp 跳过）

# 2. 生成全部线稿
python -X utf8 tmp/make_lineart.py
#    检查: public\avatars\lineart\*.png 数量

# 3. 生成头像清单 manifest（前端依赖它判断哪些人有照片/线稿）
python -X utf8 tmp/make_manifest.py
#    检查: public\avatars.json 存在，photo/line 计数

# 4. 重新生成 PDF（含线稿头像）+ 复制到 public/docs
python -X utf8 scripts/generate_print_calendar.py
Copy-Item "output\pdf\科学家日历_精选466位_A4打印版.pdf" "public\print\" -Force
Copy-Item "output\pdf\科学家日历_精选466位_A4打印版.pdf" "docs\print\" -Force

# 5. 构建验证
npm run build          # 主应用
npm run build:pages    # 静态站（注意: emptyOutDir 会清 docs，需恢复 backup-candidates.md）

# 6. 提交 + 推送
git add -A
# 若 docs/backup-candidates.md 被 emptyOutDir 删除, 先恢复:
#   git checkout 1355a5b -- docs/backup-candidates.md && git add docs/backup-candidates.md
git commit -m "Add avatar modes: photo + lineart with mode switcher"
git push github main
```

## 五、验证要点

1. 网页 http://localhost:3000/：今日人物点"照片/线稿"按钮，能看到真实头像/线稿；无头像的人物自动回落单字
2. 档案卡片在照片/线稿模式下显示小头像
3. PDF 每页圆形内应嵌入线稿头像（省墨），无头像的保持单字
4. 全页无文字重叠（`python -X utf8 tmp/pdf_full_check.py` 应输出 ✅）

## 六、已知注意事项

- **429 限流**：Wikimedia 对高频请求限流，下载脚本已内置退避；若失败多，加大 `time.sleep` 间隔
- **版权**：头像均来自 Wikidata P18（Wikimedia Commons 公共领域/CC），发布时建议在页面注明来源
- **einstein**：沿用现有 `public/art/einstein-archive.webp` 插画，不下载新图
- **诺贝尔奖日**（nobel-prize-day）：非个人，无头像，回落单字
- **manifest 依赖顺序**：必须先跑 make_lineart.py 再跑 make_manifest.py，否则 line 计数为 0

## 七、相关文件

| 文件 | 作用 |
|---|---|
| `tmp/avatar_map_all.json` | 427 个 id → Commons 文件名 |
| `tmp/download_avatars_retry.py` | 下载缺失头像（幂等可续跑） |
| `tmp/make_lineart.py` | 生成线稿（Sobel 边缘检测） |
| `tmp/make_manifest.py` | 生成 public/avatars.json 清单 |
| `tmp/pdf_check_overlap.py` / `pdf_full_check.py` | PDF 重叠检测 |
| `app/page.tsx` | 前端三种模式切换（已改） |
| `app/globals.css` | 头像样式（已加） |
| `scripts/generate_print_calendar.py` | PDF 线稿支持（已改，部分已提交） |
