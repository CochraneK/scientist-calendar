"""精准截图今日人物卡片，肉眼复核「核心贡献/你知道吗」是否异常。"""
import sys, time, pathlib
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:9011/scientist-calendar/"
OUT = pathlib.Path("output/shots")
OUT.mkdir(parents=True, exist_ok=True)

def shot(page, name, w, h=1000):
    page.set_viewport_size({"width": w, "height": h})
    page.wait_for_timeout(300)
    card = page.query_selector(".feature-card")
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    card.screenshot(path=str(OUT / f"{name}_{w}.png"))
    print("saved", f"{name}_{w}.png")

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 1000})
    page.goto(BASE, wait_until="load", timeout=20000)
    page.wait_for_selector(".feature-card", timeout=15000)
    # 默认（有引语）
    shot(page, "default", 1280)
    shot(page, "default", 390)
    # 找几位极端人物：点 archive 卡片切换
    targets = ["阿基米德", "萨特延德拉·玻色", "卡尔·古斯塔夫·雅可比", "阿尔伯特·克劳德"]
    cards = page.query_selector_all(".archive-card")
    for c in cards:
        try:
            c.click()
        except Exception:
            continue
        page.wait_for_timeout(250)
        nm = page.evaluate("() => document.querySelector('.feature-card h3')?.textContent")
        if nm in targets:
            shot(page, f"p_{nm}", 390)
            shot(page, f"p_{nm}", 1280)
            targets = [t for t in targets if t != nm]
            if not targets:
                break
    b.close()
print("done")
