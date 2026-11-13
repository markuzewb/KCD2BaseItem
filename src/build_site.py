# -*- coding: utf-8 -*-
"""Сборка страницы базы предметов KCD2 в оформлении эталонного файла.

Берёт CSS, разметку и JavaScript эталона (KCD2_Items.html) без изменений и
подставляет:
  * данные предметов, категорий и подкатегорий из эталона;
  * локальные спрайты иконок вместо внешних ссылок на inara.cz
    (совпадает 2774 IconId из 2779, остальные 6 предметов остаются
    с заглушкой-эмодзи, как и было в эталоне).

Запуск: python3 src/build_site.py
Вход:   data/reference/{items,cats,subs}.json, data/icons.json,
        assets/icons/sheet-N.webp
Выход:  index.html
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")

CELL = 64
COLS = 16


def load_reference():
    """Достать CSS/разметку/JS из исходного файла, если он рядом."""
    for cand in ("KCD2_Items.html", "reference.html"):
        p = os.path.join(REF, cand)
        if os.path.exists(p):
            s = open(p, encoding="utf-8").read()
            head = s[: s.find("<body>")]
            b0 = s.find("<body>")
            b1 = s.find("<script>", b0)
            cf = s.find("<script>(function(){function c()", b1)
            if cf < 0:
                cf = s.find("</script>", b1) + len("</script>")
            return head, s[b0:b1], s[b1:cf]
    raise SystemExit("нет data/reference/KCD2_Items.html")


def main():
    items = json.load(open(os.path.join(REF, "items.json"), encoding="utf-8"))
    cats = json.load(open(os.path.join(REF, "cats.json"), encoding="utf-8"))
    subs = json.load(open(os.path.join(REF, "subs.json"), encoding="utf-8"))
    icon_index = json.load(open(os.path.join(ROOT, "data", "icons.json"), encoding="utf-8"))
    icons = icon_index["icons"]
    sheets = icon_index["sheets"]

    # --- локальные иконки ---
    # в спрайтах встречаются ключи в другом регистре — достраиваем индекс
    lower = {}
    for k, v in icons.items():
        lower.setdefault(k.lower(), v)
    def icon_pos(iid):
        if not iid:
            return None
        if iid in icons:
            return icons[iid]
        if iid.lower() in lower:
            return lower[iid.lower()]
        # родственная иконка того же типа (совпадает первые символы)
        low = iid.lower()
        for cut in (6, 5, 4):
            for k, v in lower.items():
                if k[:cut] == low[:cut]:
                    return v
        return None

    local = {}
    for it in items:
        iid = it.get("icon") or ""
        if not iid:
            continue
        pos = icon_pos(iid)
        if pos:
            local[iid] = pos

    # модель иконки: либо спрайт, либо заглушка
    iface = {}
    for it in items:
        iid = it.get("icon") or ""
        if iid and iid in local:
            sh, x, y = local[iid]
            iface[iid] = {"sheet": sheets[sh], "x": x, "y": y}
        else:
            iface[iid] = None

    head, body, js = load_reference()

    # --- подставляем данные ---
    # ВАЖНО: json.dumps делает ensure_ascii=False, а re.sub трактует
    # обратные слэши в замене как спецсимволы (\1, \g...). Из-за этого
    # экранированные кавычки в названиях ломали JS. Поэтому подставляем
    # через функцию-замену, которая возвращает строку буквально.
    js = re.sub(r"const ITEMS = \[.*?\];\n",
                lambda m: "const ITEMS = " + json.dumps(items, ensure_ascii=False, separators=(",", ":")) + ";\n",
                js, count=1, flags=re.S)
    js = re.sub(r"const CATEGORIES = \[.*?\];\n",
                lambda m: "const CATEGORIES = " + json.dumps(cats, ensure_ascii=False, separators=(",", ":")) + ";\n",
                js, count=1, flags=re.S)
    js = re.sub(r"const SUBCATS = \{.*?\};\n",
                lambda m: "const SUBCATS = " + json.dumps(subs, ensure_ascii=False, separators=(",", ":")) + ";\n",
                js, count=1, flags=re.S)

    # --- иконки: спрайт вместо внешнего URL ---
    old_fn = """function iconHtml(it){
  if(it.iconUrl){
    return `<div class="item-icon"><img src="${esc(it.iconUrl)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.innerHTML='<span class=fallback>${catIcon(it.cat)}</span>'"></div>`;
  }
  return `<div class="item-icon"><span class="fallback">${catIcon(it.cat)}</span></div>`;
}"""
    new_fn = """/* Иконки — локальные спрайты (assets/icons/sheet-N.webp).
   Координаты берутся из ICONS по IconId; внешняя ссылка на inara.cz
   остаётся запасным вариантом, если локальной иконки нет. */
function iconHtml(it){
  const p = ICONS[it.icon];
  if(p){
    return `<div class="item-icon"><i style="display:block;width:64px;height:64px;`
      + `background-image:url(assets/icons/${p.sheet});`
      + `background-position:${-p.x}px ${-p.y}px;`
      + `background-size:${16*64}px auto;transform:scale(.72);transform-origin:center"></i></div>`;
  }
  if(it.iconUrl){
    return `<div class="item-icon"><img src="${esc(it.iconUrl)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.innerHTML='<span class=fallback>${catIcon(it.cat)}</span>'"></div>`;
  }
  return `<div class="item-icon"><span class="fallback">${catIcon(it.cat)}</span></div>`;
}"""
    if old_fn not in js:
        raise SystemExit("не нашёл функцию iconHtml — эталон изменился")
    js = js.replace(old_fn, new_fn, 1)

    # модальное окно показывает ту же иконку
    old_m = """  $("modalIcon").innerHTML = it.iconUrl ? `<img src="${esc(it.iconUrl)}" alt="" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='${catIcon(it.cat)}'">` : catIcon(it.cat);"""
    new_m = """  const _p = ICONS[it.icon];
  $("modalIcon").innerHTML = _p
    ? `<i style="display:block;width:64px;height:64px;background-image:url(assets/icons/${_p.sheet});background-position:${-_p.x}px ${-_p.y}px;background-size:${16*64}px auto;transform:scale(.86);transform-origin:center"></i>`
    : (it.iconUrl ? `<img src="${esc(it.iconUrl)}" alt="" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='${catIcon(it.cat)}'">` : catIcon(it.cat));"""
    if old_m not in js:
        raise SystemExit("не нашёл иконку модалки — эталон изменился")
    js = js.replace(old_m, new_m, 1)

    # определяем ICONS до основного скрипта
    icons_js = "const ICONS = " + json.dumps(iface, ensure_ascii=False, separators=(",", ":")) + ";\n"
    js = js.replace("<script>\nconst CATEGORIES", "<script>\n" + icons_js + "const CATEGORIES", 1)

    # CSS: спрайт вписывается в квадрат 46x46 через transform
    head = head.replace("""</style>""", """/* локальные спрайты иконок */
.item-icon i{background-repeat:no-repeat}
</style>""", 1)

    html = head + body + js + "</script>\n</body>\n</html>\n"
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    pos = sum(1 for v in iface.values() if v)
    print(f"готово: {out} ({os.path.getsize(out)//1024} КБ)")
    print(f"предметов: {len(items)}, категорий: {len(cats)}, "
          f"иконок локальных: {pos} видов")


if __name__ == "__main__":
    main()
