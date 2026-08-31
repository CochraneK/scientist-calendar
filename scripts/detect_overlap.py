"""检测今日人物卡片「核心贡献/你知道吗」(feature-meta) 是否浮空或真重叠。
跨宽度 + 跨人物实测 meta 在 feature-copy 内的位置比例，并检测与上方文字块是否重叠。
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:9011/scientist-calendar/"
WIDTHS = [375, 414, 768, 820, 1024, 1280]
# 待测人物：点 archive-grid 前 N 个卡片
N_PERSONS = 14

def measure(page):
    return page.evaluate(
        """() => {
            const card = document.querySelector('.feature-card');
            const copy = document.querySelector('.feature-copy');
            const meta = document.querySelector('.feature-meta');
            const story = document.querySelector('.feature-story');
            const quote = document.querySelector('.quote-block');
            const nameEl = card && card.querySelector('h3');
            if (!card || !copy || !meta) return null;
            const cr = copy.getBoundingClientRect();
            const mr = meta.getBoundingClientRect();
            const sr = story && story.getBoundingClientRect();
            const qr = quote && quote.getBoundingClientRect();
            const name = nameEl ? nameEl.textContent : '?';
            // meta 是否在 copy 底部 35% 内（正常锚底）
            const ratio = (mr.top - cr.top) / cr.height;
            // 真重叠：meta 顶部高于 story/quote 底部（同列）
            let overlap = false; let aboveEl = '';
            if (sr) { if (mr.top < sr.bottom - 1 && mr.left < sr.right && mr.right > sr.left) { overlap=True; aboveEl='story'; } }
            if (qr && !overlap) { if (mr.top < qr.bottom - 1 && mr.left < qr.right && mr.right > qr.left) { overlap=True; aboveEl='quote'; } }
            return {name, ratio: +ratio.toFixed(2), metaTop:+mr.top.toFixed(0), copyH:+cr.height.toFixed(0),
                    metaBottom:+mr.bottom.toFixed(0), cardBottom:+(card.getBoundingClientRect().bottom).toFixed(0),
                    overlap, aboveEl,
                    metaH:+mr.height.toFixed(0)};
        }"""
    )

with sync_playwright() as p:
    browser = p.chromium.launch()
    for w in WIDTHS:
        page = browser.new_page(viewport={"width": w, "height": 900})
        page.goto(BASE, wait_until="load", timeout=20000)
        page.wait_for_selector(".feature-card", timeout=15000)
        time.sleep(0.3)
        # 默认人物
        first = measure(page)
        print(f"[{w}px] 默认 {first['name']}: ratio={first['ratio']} metaTop={first['metaTop']} copyH={first['copyH']} overlap={first['overlap']}{('<-'+first['aboveEl']) if first['overlap'] else ''}")
        # 切换人物
        cards = page.query_selector_all(".archive-card")
        tried = 0
        seen = {first["name"]}
        for c in cards:
            if tried >= N_PERSONS:
                break
            try:
                c.click()
            except Exception:
                continue
            time.sleep(0.25)
            m = measure(page)
            if not m or m["name"] in seen:
                continue
            seen.add(m["name"])
            tried += 1
            flag = ""
            if m["overlap"]:
                flag = f"  >>> 真重叠! 盖住 {m['aboveEl']}"
            elif m["ratio"] < 0.55:
                flag = "  >>> 浮空(位置高)"
            print(f"[{w}px] {m['name']}: ratio={m['ratio']} metaTop={m['metaTop']} copyH={m['copyH']} overlap={m['overlap']}{flag}")
        page.close()
    browser.close()
print("\n检测完成。ratio<0.55=浮空/位置高；overlap=True=真重叠(盖住上方文字)")
