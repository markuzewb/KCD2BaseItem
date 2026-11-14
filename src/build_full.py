# -*- coding: utf-8 -*-
"""Подключение полной базы (5604 предмета, все характеристики) к сайту.

Берёт эталонную вёрстку и подставляет в неё:
  * ITEMS       — все предметы архива вместе со всеми характеристиками;
  * CATEGORIES  — 16 категорий;
  * SUBCATS     — подкатегории;
  * новый вывод характеристик в карточке предмета (по группам);
  * поиск по характеристикам;
  * поиск по характеристикам и фильтр «только с характеристиками».

Запуск: python3 src/build_full.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")
SRC = os.path.join(REF, "KCD2_Items.html")
OUT = os.path.join(ROOT, "index.html")

CF_MARK = "<script>(function(){function c()"

# группы характеристик: как показать в карточке
GROUPS_JS = """const FIELD_GROUPS = {"бой":"⚔️ Боевые характеристики","защита":"🛡️ Защита","требования":"💪 Требования","эффект":"✨ Действие","общее":"📦 Общее","крафт":"🔨 Связанные предметы","тех":"⚙️ Прочие параметры"};
function extraGroups(it){
  const by = {};
  (it.extra||[]).forEach(f=>{ (by[f.g] = by[f.g] || []).push(f); });
  return Object.keys(FIELD_GROUPS).filter(g=>by[g]).map(g=>({g, title:FIELD_GROUPS[g], rows:by[g]}));
}
function plural(n, one, few, many){
  const a = Math.abs(n) % 100, b = a % 10;
  if(a > 10 && a < 20) return many;
  if(b > 1 && b < 5) return few;
  if(b === 1) return one;
  return many;
}
function fmtField(f){
  if(!f.u) return esc(f.v);
  if(f.u === "гроши") return esc(f.v) + " " + plural(Number(String(f.v).replace(",", ".")), "грош", "гроша", "грошей");
  return esc(f.v) + " " + esc(f.u);
}
function extraText(it){
  return (it.extra||[]).map(f=>f.k+": "+f.v+(f.u?" "+f.u:"")).join(" ").toLowerCase();
}"""


def load(name):
    return json.load(open(os.path.join(REF, name), encoding="utf-8"))


def js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def strip_item(it):
    """Оставляем только то, что реально выводится на странице."""
    src = ""
    s = it.get("sources") or []
    if s:
        # Libs/Tables/item/item__horse.xml -> item__horse
        src = os.path.basename(s[0]).replace(".xml", "")
    return {
        "id": it["id"],
        "ru": it["ru"],
        "en": it.get("en") or "",
        "name": it["name"],
        "cat": it["cat"],
        "sub": it["sub"],
        "subLabel": it.get("subLabel") or "",
        "price": it.get("price"),
        "weight": it.get("weight"),
        "icon": it.get("icon") or "",
        "iconUrl": it.get("iconUrl") or "",
        "female": bool(it.get("female")),
        "xmlType": it.get("xmlType") or "",
        "src": src,
        "extra": it.get("extra") or [],
    }


def main():
    s = open(SRC, encoding="utf-8").read()

    cut = s.find(CF_MARK)
    if cut > 0:
        s = s[:cut].rstrip() + "\n</body>\n</html>\n"
    s = s.replace("</script></body>", "</script>\n</body>")

    items = [strip_item(it) for it in load("items_full.json")]
    cats = load("cats_full.json")
    subs = load("subs_full.json")

    # в старой вёрстке у категории есть английский XML-тип — сохраняем поле
    for c in cats:
        c.setdefault("en", "")
    cats.sort(key=lambda c: c["id"])

    s = re.sub(r"const ITEMS = \[.*?\];\n",
               lambda m: "const ITEMS = " + js(items) + ";\n", s, count=1, flags=re.S)
    s = re.sub(r"const CATEGORIES = \[.*?\];\n",
               lambda m: "const CATEGORIES = " + js(cats) + ";\n", s, count=1, flags=re.S)
    s = re.sub(r"const SUBCATS = \{.*?\};\n",
               lambda m: "const SUBCATS = " + js(subs) + ";\n", s, count=1, flags=re.S)

    # --- вспомогательные функции для групп характеристик ---
    s = s.replace("function fmtPrice(p){", GROUPS_JS + "\nfunction fmtPrice(p){", 1)

    # --- карточка предмета: характеристики по группам ---
    old_extra = '${extraEntries.length ? `<div class="section-title">Характеристики</div><div class="kv">${extraEntries.map(([k,v])=>`<div class="kv-row"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`).join("")}</div>` : `<div class="section-title">Характеристики</div><p style="color:var(--muted);font-size:13px">Дополнительных характеристик нет.</p>`}'
    new_extra = ('${(it.extra&&it.extra.length) ? extraGroups(it).map(gr=>'
                 '`<div class="section-title">${gr.title} <span class="cnt" style="font-size:12px;color:var(--muted);font-weight:600">${gr.rows.length}</span></div>'
                 '<div class="kv">${gr.rows.map(f=>`<div class="kv-row"><span class="k">${esc(f.k)}</span>'
                 '<span class="v">${fmtField(f)}</span></div>`).join("")}</div>`'
                 ').join("") : `<div class="section-title">Характеристики</div><p style="color:var(--muted);font-size:13px">У этого предмета в файлах игры нет характеристик.</p>`}')
    if old_extra not in s:
        raise SystemExit("не найден блок характеристик в карточке")
    s = s.replace(old_extra, new_extra, 1)

    # extraEntries больше не нужен
    s = s.replace("  const extraEntries = Object.entries(it.extra||{});\n", "", 1)

    # --- подзаголовок карточки: EN + внутреннее имя + источник ---
    s = s.replace(
        '  $("modalSub").textContent = (it.en ? it.en+" • " : "") + it.name;',
        '  $("modalSub").textContent = (it.en ? it.en+" • " : "") + it.name'
        ' + (it.src ? " • " + it.src : "");', 1)

    # --- поиск теперь ищет и по характеристикам ---
    s = s.replace(
        '      const hay = (it.ru+" "+it.en+" "+it.name+" "+it.id+" "+(it.icon||"")+" "+(it.subLabel||"")).toLowerCase();',
        '      const hay = (it.ru+" "+it.en+" "+it.name+" "+it.id+" "+(it.icon||"")+" "+(it.subLabel||"")+" "+(it.xmlType||"")+" "+extraText(it)).toLowerCase();', 1)

    # --- строка «всего характеристик» в статистике ---
    s = s.replace('$("statCats").textContent = CATEGORIES.length;',
                  '$("statCats").textContent = CATEGORIES.length;\n'
                  '$("statFields").textContent = ITEMS.reduce((n,it)=>n+(it.extra?it.extra.length:0),0).toLocaleString("ru-RU");', 1)
    s = s.replace('Категорий: <b id="statCats">—</b></div>',
                  'Категорий: <b id="statCats">—</b></div>\n'
                  '      <div class="stat-pill">Характеристик: <b id="statFields">—</b></div>', 1)

    # --- фильтр: только предметы с характеристиками ---
    s = s.replace('  onlyWithIcon: false,', '  onlyWithIcon: false,\n  onlyDetailed: false,', 1)
    s = s.replace('    if(state.onlyWithIcon && !it.iconUrl) return false;',
                  '    if(state.onlyWithIcon && !it.iconUrl) return false;\n'
                  '    if(state.onlyDetailed && !(it.extra && it.extra.length)) return false;', 1)
    s = s.replace('<button class="chip" id="onlyWithIcon">Только с иконкой</button>',
                  '<button class="chip" id="onlyWithIcon">Только с иконкой</button>\n'
                  '      <button class="chip" id="onlyDetailed">Только с характеристиками</button>', 1)
    s = s.replace('$("onlyWithIcon").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyWithIcon=this.classList.contains("active"); state.page=1; render(); });',
                  '$("onlyWithIcon").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyWithIcon=this.classList.contains("active"); state.page=1; render(); });\n'
                  '$("onlyDetailed").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyDetailed=this.classList.contains("active"); state.page=1; render(); });', 1)
    s = s.replace('state.onlyWithIcon=false; state.sort="default";',
                  'state.onlyWithIcon=false; state.onlyDetailed=false; state.sort="default";', 1)
    s = s.replace('$("onlyWithIcon").classList.remove("active");',
                  '$("onlyWithIcon").classList.remove("active"); $("onlyDetailed").classList.remove("active");', 1)

    # --- плейсхолдер поиска ---
    s = s.replace('placeholder="Поиск по русскому, английскому названию, Name или ID…  ( / )"',
                  'placeholder="Поиск по названию, Name, ID и характеристикам…  ( / )"', 1)

    # --- вывод источника и типа в карточке предмета ---
    s = s.replace(
        '<div class="detail-item"><div class="k">Примечание</div><div class="v" style="font-size:12px;font-weight:600;color:var(--muted)">${esc(it.note)||"—"}</div></div>',
        '<div class="detail-item"><div class="k">Тип в файлах игры</div><div class="v"><span class="mono">${esc(it.xmlType)||"—"}</span></div></div>\n'
        '      <div class="detail-item"><div class="k">Файл игры</div><div class="v"><span class="mono">${esc(it.src)||"—"}</span></div></div>', 1)

    # --- CSV: добавить характеристики ---
    s = s.replace('"Категория","Подкатегория","Примечание"]',
                  '"Категория","Подкатегория","Тип","Файл","Характеристики"]', 1)
    s = s.replace('it.weight??"",catName(it.cat),it.subLabel||"",it.note]',
                  'it.weight??"",catName(it.cat),it.subLabel||"",it.xmlType||"",it.src||"",'
                  '(it.extra||[]).map(f=>f.k+": "+f.v+(f.u?" "+f.u:"")).join("; ")]', 1)

    # --- бейдж «Ж» ---
    old_name = '<div class="ru-name">${esc(it.ru)||"—"}</div>'
    badge = ("<span class='badge' style='background:rgba(236,72,153,.15);"
             "color:#f9a8d4;border-color:rgba(236,72,153,.35);padding:1px 6px;"
             "font-size:10px;vertical-align:middle'>Ж</span>")
    s = s.replace(old_name,
                  '<div class="ru-name">${esc(it.ru)||"—"}'
                  '${it.female?" ' + badge + '":""}</div>')

    open(OUT, "w", encoding="utf-8").write(s)
    print(f"готово: {len(items)} предметов, {len(cats)} категорий, "
          f"{sum(len(v) for v in subs.values())} подкатегорий")
    print(f"характеристик: {sum(len(i['extra']) for i in items):,}".replace(",", " "))
    print(f"файл: {OUT} ({os.path.getsize(OUT)//1024} КБ)")


if __name__ == "__main__":
    main()
