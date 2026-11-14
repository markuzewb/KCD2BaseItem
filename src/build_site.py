# -*- coding: utf-8 -*-
"""УСТАРЕЛО: собирает страницу по прежней базе из 3 784 предметов.

Актуальная сборка — src/build_full.py (5 604 предмета, все характеристики).
Этот скрипт оставлен для истории и перезапишет полную базу, если запустить.

Сборка index.html из эталонного файла без изменений.

Страница должна полностью совпадать с присланным KCD2_Items.html:
тот же CSS, та же разметка, тот же JavaScript и те же иконки
(внешние ссылки на inara.cz). Единственное, что убирается —
посторонний Cloudflare-скрипт, который сайт-источник вставил в конец
файла при скачивании.

Запуск: python3 src/build_site.py
Вход:   data/reference/KCD2_Items.html
Выход:  index.html
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")
SRC = os.path.join(REF, "KCD2_Items.html")
OUT = os.path.join(ROOT, "index.html")

# Cloudflare-вставка сайта-источника: к базе предметов отношения не имеет
CF_MARK = "<script>(function(){function c()"


def main():
    s = open(SRC, encoding="utf-8").read()

    cut = s.find(CF_MARK)
    if cut > 0:
        s = s[:cut].rstrip() + "\n</body>\n</html>\n"

    # закрывающие теги должны быть в единственном экземпляре
    s = s.replace("</script></body>", "</script>\n</body>")

    # --- улучшенная таксономия ---
    # items_tagged.json получается из src/retag_items.py: исправлены
    # ошибки ручной разметки, категории разбиты подробнее
    tagged_items = os.path.join(REF, "items_tagged.json")
    if os.path.exists(tagged_items):
        items_t = json.load(open(tagged_items, encoding="utf-8"))
        cats_t = json.load(open(os.path.join(REF, "cats_tagged.json"), encoding="utf-8"))
        subs_t = json.load(open(os.path.join(REF, "subs_tagged.json"), encoding="utf-8"))

        sub_names = {str(it["id"]): it["sub"] for it in items_t}
        items_t = [it for it in items_t if it.get("sub")]

        s = re.sub(r"const ITEMS = \[.*?\];\n",
                   lambda m: "const ITEMS = " + json.dumps(
                       items_t, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   s, count=1, flags=re.S)
        s = re.sub(r"const CATEGORIES = \[.*?\];\n",
                   lambda m: "const CATEGORIES = " + json.dumps(
                       cats_t, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   s, count=1, flags=re.S)
        s = re.sub(r"const SUBCATS = \{.*?\};\n",
                   lambda m: "const SUBCATS = " + json.dumps(
                       subs_t, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   s, count=1, flags=re.S)

        # метка «Ж» у женских вещей
        old_name = '<div class="ru-name">${esc(it.ru)||"—"}</div>'
        badge = ("<span class='badge' style='background:rgba(236,72,153,.15);"
                 "color:#f9a8d4;border-color:rgba(236,72,153,.35);padding:1px 6px;"
                 "font-size:10px;vertical-align:middle'>Ж</span>")
        new_name = ('<div class="ru-name">${esc(it.ru)||"—"}'
                    '${it.female?" ' + badge + '":""}</div>')
        s = s.replace(old_name, new_name)

        print(f"таксономия: {len(items_t)} предметов, {len(cats_t)} категорий, "
              f"{sum(len(v) for v in subs_t.values())} подкатегорий")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(s)

    print(f"готово: {OUT} ({os.path.getsize(OUT)//1024} КБ)")
    print(f"внешних иконок inara.cz: {s.count('iconUrl') - s.count(chr(34) + 'iconUrl' + chr(34))}")


if __name__ == "__main__":
    main()
