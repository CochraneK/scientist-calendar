# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("C:/Users/cunyi/Documents/科学家日历/output/shots")
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8899/scientist-calendar/"

# 选几位文本长度不同的人物，点击后截图（点击会触发 scrollIntoView 到 #today）
targets = [
    ("hippocrates", 1280),
    ("vaughan", 1280),
    ("holmes-old", 1024),
    ("einstein", 820),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for target, w in targets:
        page = browser.new_page(viewport={"width": w, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(600)
        # 找目标 archive-card 并点击
        clicked = page.evaluate("""(name) => {
            const btns = document.querySelectorAll('.archive-card');
            for (const b of btns) {
                if (b.textContent.includes(name)) { b.click(); return true; }
            }
            return false;
        }""", target)
        page.wait_for_timeout(1200)  # 等滚动+渲染
        # 截 today 区块（滚动后）
        try:
            page.locator("#today").screenshot(path=str(OUT / f"click_{target}_{w}.png"))
        except Exception as e:
            print("fail", target, e)
        # 同时整页
        page.screenshot(path=str(OUT / f"click_full_{target}_{w}.png"), full_page=True)
        # 测量 feature-meta 的位置与卡片高度
        info = page.evaluate("""() => {
            const card = document.querySelector('.feature-card');
            const meta = document.querySelector('.feature-meta');
            const copy = document.querySelector('.feature-copy');
            const r = (el) => { const b = el.getBoundingClientRect(); return { top: b.top, bottom: b.bottom, h: b.height, w: b.width }; };
            return { card: r(card), meta: r(meta), copy: r(copy), vh: innerHeight, scrollY };
        }""")
        print(f"{target}@{w}: cardH={info['card']['h']:.0f} meta.top={info['meta']['top']:.0f} meta.bottom={info['meta']['bottom']:.0f} copyH={info['copy']['h']:.0f} vh={info['vh']} scrollY={info['scrollY']:.0f}")
        page.close()
    browser.close()
print("DONE")
