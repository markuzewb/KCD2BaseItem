# -*- coding: utf-8 -*-
"""Сборка спрайт-листа иконок предметов KCD2.

Берёт отдельные webp-иконки (<iconid>_icon_page1.webp) из распакованного
набора игры, склеивает в несколько спрайтов по 64 px и пишет
data/icons.json с координатами каждой иконки.

Запуск:  python3 src/build_icons.py
Вход:    data/raw/icons/<iconid>_icon_page1.webp
Выход:   assets/icons/sheet-N.webp, data/icons.json
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "data", "raw", "icons")
OUTDIR = os.path.join(ROOT, "assets", "icons")
OUTJSON = os.path.join(ROOT, "data", "icons.json")

CELL = 64
COLS = 16
QUALITY = 82
SHEET_ITEMS = COLS * 16  # 256 иконок на лист


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    files = {}
    if os.path.isdir(SRC):
        for fn in os.listdir(SRC):
            if fn.endswith("_icon_page1.webp"):
                files[fn[: -len("_icon_page1.webp")]] = os.path.join(SRC, fn)
    ids = sorted(files)
    if not ids:
        print("нет иконок в", SRC)
        return

    sheets = []
    for si in range(0, len(ids), SHEET_ITEMS):
        chunk = ids[si: si + SHEET_ITEMS]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("RGBA", (COLS * CELL, rows * CELL), (0, 0, 0, 0))
        for k, icon_id in enumerate(chunk):
            try:
                im = Image.open(files[icon_id]).convert("RGBA")
            except Exception:
                continue
            if im.size != (CELL, CELL):
                im = im.resize((CELL, CELL), Image.LANCZOS)
            sheet.paste(im, ((k % COLS) * CELL, (k // COLS) * CELL), im)
        out = os.path.join(OUTDIR, f"sheet-{len(sheets) + 1}.webp")
        sheet.save(out, "WEBP", quality=QUALITY, method=6)
        sheets.append(os.path.basename(out))
        print(f"{out}: {len(chunk)} иконок, {os.path.getsize(out) // 1024} КБ")

    index = {}
    for i, icon_id in enumerate(ids):
        s = i // SHEET_ITEMS
        k = i % SHEET_ITEMS
        index[icon_id] = [s, (k % COLS) * CELL, (k // COLS) * CELL]

    json.dump({"cell": CELL, "sheets": sheets, "icons": index},
              open(OUTJSON, "w", encoding="utf-8"), ensure_ascii=False,
              separators=(",", ":"))
    print(f"готово: {len(index)} иконок, {len(sheets)} листов -> {OUTJSON}")


if __name__ == "__main__":
    main()
