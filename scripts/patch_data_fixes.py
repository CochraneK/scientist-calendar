#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性数据修正（已执行，留档备查）。

每一条修正都注明依据，便于回溯：
  1. 阿基米德生卒年 -286–211 -> 前287–前212
     依据：Wikidata Q8739 的 preferred 声明（前 287 年生、前 212 年卒），
           与英文维基百科一致。原值取自 non-preferred 声明，且 "-286" 的写法在页面上显示异常。
  2. 希波克拉底生卒年 "约前460–约前370" -> "前460–前370"
     依据：仅为格式统一（其余条目均不带"约"字），年份本身未变。
  3. 德尼·帕潘卒年 1712 -> 1713
     依据：2016 年在伦敦 St Bride's 教堂登记簿中发现其 1713-08-26 下葬记录，
           英文维基百科与 Wikidata Q106208 均已改为 1713。
  4. 阿尔伯特·克劳德 8月21日 -> 8月24日
     依据：英文维基百科信息框 1899-08-24；Wikidata Q233943 存四个值，
           原用的 08-21 属少数说法。8月21日仍有柯西，不破坏 365 天覆盖。
  5. 诺贝尔奖日 -> 卡尔·古斯塔夫·雅可比（12 月 10 日生）
     依据：全库唯一的非人物条目，field 标为"医学"亦不成立。
           雅可比 1804-12-10 生、1851-02-18 卒（英文维基百科），替换后总数仍为 466。
  6. 萨特延德拉·玻色 5月2日 -> 1月1日（真实生日）；阿基米德 1月1日 -> 5月2日
     依据：Wikidata Q45789 / 英文维基百科均记玻色 1894-01-01 生。
           阿基米德生年不可考，原本也只是占位在 1 月 1 日，与玻色互换后 365 天覆盖不变。
  7. 皮埃尔·德·费马 8月20日 -> 1月12日（逝世纪念日）
     依据：英文维基百科记其"生于 1607 年 10 月 31 日至 12 月 6 日之间"，具体日期不可考；
           原 8 月 20 日实为其同名同父异母兄长 1601 年的洗礼日期，与生年 1607 自相矛盾。
           改用其逝世日 1665-01-12。
  8. 埃德加·科德 8月23日 -> 8月19日
     依据：英文维基百科记 1923-08-19 生（Wikidata Q92596 相同）。

用法：python -X utf8 scripts/patch_data_fixes.py [--dry]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCIENTISTS = ROOT / "app" / "scientists.json"
QUOTES = ROOT / "app" / "quotes.json"
AVATARS = ROOT / "public" / "avatars.json"

JACOBI = {
    "id": "jacobi",
    "name": "卡尔·古斯塔夫·雅可比",
    "latinName": "Carl Gustav Jacob Jacobi",
    "years": "1804–1851",
    "field": "数学",
    "country": "德国",
    "color": "violet",
    "relation": "椭圆函数与雅可比行列式",
    "tagline": "把椭圆积分反过来研究，开出椭圆函数的新领域",
    "story": (
        "雅可比出生于波茨坦，16 岁进入柏林大学，1826 年起任教于柯尼斯堡大学。"
        "1829 年他出版《椭圆函数理论新基础》，系统建立了椭圆函数与 theta 函数的理论；"
        "他引入的雅可比行列式成为多变量微积分的标准工具，偏导数符号 ∂ 也因他的推广而通行。"
    ),
    "contribution": "椭圆函数理论、雅可比行列式与雅可比符号",
    "fact": (
        "雅可比给学生的研究建议是“反过来，永远反过来”（man muss immer umkehren）——"
        "把已知的结论倒过来看，正是他研究椭圆积分的方法。"
    ),
    "month": 12,
    "day": 10,
}

JACOBI_QUOTE = {
    "text": "反过来，永远反过来。",
    "source": "雅可比给学生的研究建议（man muss immer umkehren）",
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry" in sys.argv

    scientists = json.loads(SCIENTISTS.read_text(encoding="utf-8"))
    quotes = json.loads(QUOTES.read_text(encoding="utf-8"))
    avatars = json.loads(AVATARS.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in scientists}

    # 1) 生卒年修正（条件化，保证脚本可重复运行）
    archimedes = by_id["auto-q8739"]
    if archimedes["years"] != "前287–前212":
        print(f"阿基米德: {archimedes['years']} -> 前287–前212")
        archimedes["years"] = "前287–前212"

    hippocrates = by_id["hippocrates"]
    if hippocrates["years"] != "前460–前370":
        print(f"希波克拉底: {hippocrates['years']} -> 前460–前370")
        hippocrates["years"] = "前460–前370"

    papin = by_id["auto-q106208"]
    if papin["years"] != "1647–1713":
        print(f"德尼·帕潘: {papin['years']} -> 1647–1713")
        papin["years"] = "1647–1713"

    # 2) 日期修正
    claude = by_id["auto-q233943"]
    if (claude["month"], claude["day"]) != (8, 24):
        print(f"阿尔伯特·克劳德: {claude['month']}月{claude['day']}日 -> 8月24日")
        claude["month"], claude["day"] = 8, 24

    # 3) 诺贝尔奖日 -> 雅可比
    if "jacobi" not in by_id:
        index = next(i for i, entry in enumerate(scientists) if entry["id"] == "nobel-prize-day")
        print("诺贝尔奖日 -> 卡尔·古斯塔夫·雅可比（12月10日）")
        scientists[index] = JACOBI
        quotes.pop("nobel-prize-day", None)
        avatars.pop("nobel-prize-day", None)
        quotes["jacobi"] = JACOBI_QUOTE
        avatars["jacobi"] = {"photo": False}
        by_id = {entry["id"]: entry for entry in scientists}

    # 4) 日期修正（第二轮）
    if by_id["bose"]["month"] == 5:
        bose = by_id["bose"]
        print(f"萨特延德拉·玻色: {bose['month']}月{bose['day']}日 -> 1月1日")
        bose["month"], bose["day"] = 1, 1
        archimedes = by_id["auto-q8739"]
        print(f"阿基米德: {archimedes['month']}月{archimedes['day']}日 -> 5月2日")
        archimedes["month"], archimedes["day"] = 5, 2

    if by_id["fermat"]["month"] == 8:
        fermat = by_id["fermat"]
        print(f"皮埃尔·德·费马: {fermat['month']}月{fermat['day']}日 -> 1月12日（逝世纪念日）")
        fermat["month"], fermat["day"] = 1, 12

    if by_id["codd"]["month"] == 8:
        codd = by_id["codd"]
        print(f"埃德加·科德: {codd['month']}月{codd['day']}日 -> 8月19日")
        codd["month"], codd["day"] = 8, 19

    if not dry:
        for path, payload in (
            (SCIENTISTS, scientists),
            (QUOTES, quotes),
            (AVATARS, avatars),
        ):
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("\n已写入文件")
    else:
        print("\n预览模式，未写入")

    return 0


if __name__ == "__main__":
    sys.exit(main())
