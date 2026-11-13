# -*- coding: utf-8 -*-
"""Сборка index.html из эталонного файла без изменений.

Страница должна полностью совпадать с присланным KCD2_Items.html:
тот же CSS, та же разметка, тот же JavaScript и те же иконки
(внешние ссылки на inara.cz). Единственное, что убирается —
посторонний Cloudflare-скрипт, который сайт-источник вставил в конец
файла при скачивании.

Запуск: python3 src/build_site.py
Вход:   data/reference/KCD2_Items.html
Выход:  index.html
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "data", "reference", "KCD2_Items.html")
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

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(s)

    print(f"готово: {OUT} ({os.path.getsize(OUT)//1024} КБ)")
    print(f"внешних иконок inara.cz: {s.count('iconUrl') - s.count(chr(34) + 'iconUrl' + chr(34))}")


if __name__ == "__main__":
    main()
