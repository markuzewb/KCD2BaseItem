# -*- coding: utf-8 -*-
"""Сборка одностраничного сайта «База предметов KCD2 — Богемия RP».

Вход:  data/items.json, data/icons.json, assets/icons/sheet-N.webp
Выход: index.html (всё встроено, кроме спрайтов иконок)

Запуск: python3 src/build_site.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CATS = [
    ("all", "Все предметы"),
    ("weapons", "Оружие"),
    ("armor", "Броня и одежда"),
    ("ranged", "Дальнобойное"),
    ("ammo", "Боеприпасы"),
    ("food", "Еда"),
    ("potions", "Зелья"),
    ("herbs", "Травы"),
    ("materials", "Материалы"),
    ("books", "Книги"),
    ("dice", "Кости"),
    ("misc", "Разное"),
]

SUBS = {
    "weapons": [("melee", "Ближний бой"), ("shield", "Щиты")],
    "armor": [("head", "Голова"), ("body", "Корпус"), ("legs", "Ноги"),
              ("hands", "Руки"), ("jewelry", "Украшения"), ("belt", "Пояса"),
              ("pouch", "Сумки"), ("horse", "Лошадь"), ("other", "Прочее")],
    "food": [("other", "Еда")],
    "potions": [("other", "Зелья")],
    "misc": [("other", "Разное")],
    "books": [("other", "Книги")],
    "materials": [("other", "Материалы")],
    "dice": [("other", "Кости")],
    "herbs": [("other", "Травы")],
    "ranged": [("range", "Стрелковое")],
    "ammo": [("ammo", "Боеприпасы")],
}

STAT_LABELS = {
    "ds": "Защита от колющего", "dl": "Защита от рубящего",
    "dm": "Защита от дробящего", "a": "Атака",
    "ast": "Атака колющая", "asl": "Атака рубящая", "asm": "Атака дробящая",
    "sr": "Сила", "ar": "Ловкость", "ch": "Харизма",
    "no": "Шум", "vi": "Заметность", "co": "Привлекательность",
    "q": "Макс. качество", "du": "Прочность",
    "nut": "Питательность", "hea": "Здоровье", "ref": "Освежение",
    "alc": "Алкоголь", "lat": "Латынь", "sk": "Навык",
    "sv": "Стороны", "sw": "Веса",
}


def build():
    items = json.load(open(os.path.join(ROOT, "data", "items.json"), encoding="utf-8"))["items"]
    icon_index = json.load(open(os.path.join(ROOT, "data", "icons.json"), encoding="utf-8"))
    icons = icon_index["icons"]

    # оставляем только используемые иконки, пересобираем компактный индекс
    used = sorted({it["i"] for it in items if it["i"] in icons})
    pos = {name: i for i, name in enumerate(used)}
    icon_map = [icons[n] for n in used]
    icon_name_idx = pos

    # --- склейка одинаковых записей в варианты ---
    # В item.json у одного и того же предмета бывает десятки копий
    # (разные расцветки/геральдика с идентичными характеристиками).
    # Показываем одну строку, сохраняя все игровые ID.
    groups = {}
    order = []
    for it in items:
        a = it.get("a") or {}
        key = (it["n"], it["e"], it.get("w"), it.get("p"), a.get("du"))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(it)

    out_items = []
    for key in order:
        grp = groups[key]
        it = grp[0]
        icon_idx = icon_name_idx.get(it["i"], -1) if it["i"] in icon_name_idx else -1
        # если у основной записи нет иконки — берём её у любого варианта
        if icon_idx < 0:
            for alt in grp[1:]:
                if alt["i"] in icon_name_idx:
                    icon_idx = icon_name_idx[alt["i"]]
                    break
        rec = [it["n"], it["e"], it["c"], it["s"], it.get("w"), it.get("p"),
               icon_idx, it.get("a"), it["id"]]
        if len(grp) > 1:
            rec.append(len(grp))
            rec.append([x["id"] for x in grp[1:]])
        out_items.append(rec)

    data_js = json.dumps({
        "items": out_items,
        "rawCount": len(items),
        "iconMap": icon_map,
        "iconNames": used,
        "cats": CATS,
        "subs": SUBS,
        "statLabels": STAT_LABELS,
        "sheets": icon_index["sheets"],
        "cell": icon_index["cell"],
    }, ensure_ascii=False, separators=(",", ":"))

    html = TEMPLATE.replace("__DATA__", data_js)
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(out)
    print(f"готово: {out} ({size // 1024} КБ, предметов: {len(out_items)}, иконок: {len(used)})")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>База предметов KCD2 — Богемия RP</title>
<meta name="description" content="Полная база предметов Kingdom Come: Deliverance II на русском: оружие, броня, еда, зелья, травы, книги и кости с характеристиками и ID для консоли.">
<style>
:root{
  --bg:#14100c; --bg2:#1c1712; --panel:#221b15; --panel2:#2a2119;
  --line:#3a2e23; --line2:#4a3a2b;
  --gold:#d4a94a; --gold2:#f0c96a; --gold-dim:#8a6f33;
  --text:#ece3d4; --muted:#a89884; --dim:#7d6f5e;
  --red:#c25b4a; --green:#6f9c5a; --blue:#5b7fa8;
  --r:10px;
  --shadow:0 4px 20px rgba(0,0,0,.45);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:
    radial-gradient(1200px 600px at 50% -100px, #2b2118 0%, transparent 70%),
    var(--bg);
  color:var(--text);
  font:15px/1.5 "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  min-height:100vh;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--gold);text-decoration:none}
a:hover{color:var(--gold2)}

/* ---------- шапка ---------- */
header{
  border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,#1e1811,#171310);
  padding:18px 0 0;
  position:sticky;top:0;z-index:40;
  backdrop-filter:blur(8px);
}
.wrap{max-width:1500px;margin:0 auto;padding:0 18px}
.brand{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.crest{
  width:42px;height:42px;flex:0 0 auto;
  background:linear-gradient(160deg,var(--gold2),var(--gold-dim));
  clip-path:polygon(50% 0,100% 20%,100% 70%,50% 100%,0 70%,0 20%);
  display:grid;place-items:center;
  font:700 19px/1 Georgia,serif;color:#221b12;
}
h1{margin:0;font:600 21px/1.2 Georgia,"Times New Roman",serif;letter-spacing:.2px}
h1 small{display:block;font:400 12px/1.4 "Segoe UI",sans-serif;color:var(--muted);letter-spacing:.4px;margin-top:2px}
.spacer{flex:1}
.count{font-size:13px;color:var(--muted);white-space:nowrap}
.count b{color:var(--gold2)}

/* ---------- поиск ---------- */
.searchbar{display:flex;gap:10px;padding:14px 0;flex-wrap:wrap}
.field{position:relative;flex:1;min-width:240px}
.field input{
  width:100%;padding:11px 38px 11px 38px;
  background:var(--panel);border:1px solid var(--line2);border-radius:var(--r);
  color:var(--text);font-size:15px;outline:none;transition:.15s;
}
.field input:focus{border-color:var(--gold-dim);box-shadow:0 0 0 3px rgba(212,169,74,.12)}
.field .mag{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--dim);font-size:16px}
.field .clr{
  position:absolute;right:8px;top:50%;transform:translateY(-50%);
  border:0;background:transparent;color:var(--dim);font-size:19px;cursor:pointer;
  padding:2px 7px;border-radius:6px;display:none;
}
.field .clr:hover{color:var(--gold);background:var(--panel2)}
.btn{
  padding:10px 16px;background:var(--panel);border:1px solid var(--line2);
  color:var(--text);border-radius:var(--r);cursor:pointer;font-size:14px;
  transition:.15s;white-space:nowrap;
}
.btn:hover{border-color:var(--gold-dim);color:var(--gold2)}
.btn.on{background:rgba(212,169,74,.14);border-color:var(--gold-dim);color:var(--gold2)}

/* ---------- фильтры ---------- */
.filters{display:flex;gap:8px;padding:0 0 12px;flex-wrap:wrap;align-items:center}
.chip{
  padding:6px 13px;background:var(--panel);border:1px solid var(--line);
  border-radius:999px;font-size:13px;cursor:pointer;color:var(--muted);transition:.15s;
  white-space:nowrap;user-select:none;
}
.chip:hover{color:var(--text);border-color:var(--line2)}
.chip.on{background:rgba(212,169,74,.16);border-color:var(--gold-dim);color:var(--gold2);font-weight:600}
.chip .n{opacity:.55;font-size:11px;margin-left:5px}
.subrow{display:none;gap:7px;padding:0 0 12px;flex-wrap:wrap;align-items:center}
.subrow.show{display:flex}
.subrow .lbl{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.7px;margin-right:2px}

/* ---------- панель инструментов ---------- */
.toolbar{
  display:flex;gap:10px;align-items:center;flex-wrap:wrap;
  padding:12px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  margin-bottom:16px;
}
select{
  padding:9px 12px;background:var(--panel);border:1px solid var(--line2);
  border-radius:8px;color:var(--text);font-size:14px;cursor:pointer;outline:none;
}
select:focus{border-color:var(--gold-dim)}
.toolbar .spacer{flex:1}
.viewtoggle{display:flex;gap:0;border:1px solid var(--line2);border-radius:8px;overflow:hidden}
.viewtoggle button{
  background:var(--panel);border:0;color:var(--muted);padding:9px 14px;cursor:pointer;font-size:14px;
}
.viewtoggle button.on{background:rgba(212,169,74,.16);color:var(--gold2)}

/* ---------- сетка карточек ---------- */
.grid{
  display:grid;gap:12px;
  grid-template-columns:repeat(auto-fill,minmax(228px,1fr));
  padding-bottom:60px;
}
.card{
  background:linear-gradient(170deg,var(--panel),var(--bg2));
  border:1px solid var(--line);border-radius:var(--r);
  padding:12px;cursor:pointer;transition:.16s;
  display:flex;gap:12px;align-items:flex-start;position:relative;overflow:hidden;
}
.card:hover{border-color:var(--gold-dim);transform:translateY(-2px);box-shadow:var(--shadow)}
.card::after{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(120deg,transparent 60%,rgba(212,169,74,.05));
}
.ico{
  width:52px;height:52px;flex:0 0 auto;border-radius:8px;
  background:radial-gradient(circle at 40% 30%,#33291e,#1b1611);
  border:1px solid var(--line);position:relative;overflow:hidden;
}
.ico{--sc:.78}
.ico i{
  position:absolute;display:block;width:64px;height:64px;
  background-repeat:no-repeat;transform-origin:0 0;transform:scale(var(--sc));
  background-position:calc(var(--x) * var(--sc)) calc(var(--y) * var(--sc));
  background-size:calc(1024px * var(--sc)) auto;
  left:3px;top:3px;
}
.ico.empty::before{
  content:"?";position:absolute;inset:0;display:grid;place-items:center;
  color:var(--dim);font-size:20px;
}
.card .meta{min-width:0;flex:1}
.card h3{
  margin:0 0 3px;font:600 14px/1.3 "Segoe UI",sans-serif;
  overflow:hidden;text-overflow:ellipsis;display:-webkit-box;
  -webkit-line-clamp:2;-webkit-box-orient:vertical;
}
.card .en{
  font-size:11px;color:var(--dim);margin-bottom:6px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.card .tags{display:flex;gap:5px;flex-wrap:wrap}
.tag{
  font-size:10.5px;padding:2px 7px;border-radius:5px;
  background:rgba(255,255,255,.045);color:var(--muted);border:1px solid rgba(255,255,255,.05);
}
.tag.g{color:var(--gold);border-color:rgba(212,169,74,.25);background:rgba(212,169,74,.09)}
.tag.v{color:var(--blue);border-color:rgba(91,127,168,.3);background:rgba(91,127,168,.1)}

/* ---------- таблица ---------- */
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r);margin-bottom:60px}
table{width:100%;border-collapse:collapse;font-size:13.5px;min-width:760px}
thead th{
  background:var(--panel2);color:var(--muted);font-weight:600;text-align:left;
  padding:11px 12px;border-bottom:1px solid var(--line2);
  cursor:pointer;user-select:none;white-space:nowrap;position:sticky;top:0;
}
thead th:hover{color:var(--gold2)}
thead th .arr{opacity:.35;font-size:10px;margin-left:4px}
thead th.sorted .arr{opacity:1;color:var(--gold)}
tbody tr{border-bottom:1px solid rgba(255,255,255,.04);cursor:pointer}
tbody tr:hover{background:rgba(212,169,74,.055)}
tbody td{padding:8px 12px;vertical-align:middle}
td.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--muted)}
td .tin{display:inline-block;width:26px;height:26px;border-radius:5px;
  background:#1b1611;border:1px solid var(--line);vertical-align:middle;margin-right:8px;
  position:relative;overflow:hidden}
td .tin{--sc:.4}
td .tin i{position:absolute;width:64px;height:64px;transform-origin:0 0;transform:scale(var(--sc));
  background-position:calc(var(--x) * var(--sc)) calc(var(--y) * var(--sc));
  background-size:calc(1024px * var(--sc)) auto;
  left:-1px;top:-1px;background-repeat:no-repeat}
td.name{font-weight:500}

/* ---------- пустой результат ---------- */
.empty{
  text-align:center;padding:70px 20px;color:var(--dim);
}
.empty .big{font-size:44px;opacity:.4;margin-bottom:10px}

/* ---------- модалка ---------- */
.modal{
  position:fixed;inset:0;z-index:100;display:none;
  background:rgba(8,6,4,.82);backdrop-filter:blur(4px);
  padding:24px;overflow-y:auto;
}
.modal.show{display:flex;align-items:flex-start;justify-content:center}
.sheet{
  background:linear-gradient(170deg,#241d16,#181310);
  border:1px solid var(--line2);border-radius:14px;
  max-width:760px;width:100%;box-shadow:0 24px 70px rgba(0,0,0,.7);
  animation:pop .18s ease;
  margin:auto;
}
@keyframes pop{from{opacity:0;transform:translateY(12px) scale(.99)}to{opacity:1;transform:none}}
.sheet .top{display:flex;gap:18px;padding:22px 22px 16px;border-bottom:1px solid var(--line)}
.sheet .bigico{
  width:96px;height:96px;flex:0 0 auto;border-radius:12px;
  background:radial-gradient(circle at 40% 30%,#372c1f,#161008);
  border:1px solid var(--line2);position:relative;overflow:hidden;
}
.sheet .bigico{--sc:1.32}
.sheet .bigico i{
  position:absolute;width:64px;height:64px;transform-origin:0 0;
  transform:scale(var(--sc));left:11px;top:11px;background-repeat:no-repeat;
  background-position:calc(var(--x) * var(--sc)) calc(var(--y) * var(--sc));
  background-size:calc(1024px * var(--sc)) auto;
}
.sheet h2{margin:0 0 4px;font:600 21px/1.25 Georgia,serif;color:var(--gold2)}
.sheet .en2{color:var(--dim);font-size:13px;margin-bottom:9px}
.sheet .cat{display:flex;gap:6px;flex-wrap:wrap}
.sheet .body{padding:18px 22px 22px}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:9px;margin-bottom:18px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:9px 12px}
.stat .k{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}
.stat .v{font-size:16px;font-weight:600;color:var(--text);font-variant-numeric:tabular-nums}
.stat .v.bad{color:var(--red)} .stat .v.good{color:var(--green)}
.idrow{
  display:flex;gap:9px;align-items:center;background:#100c09;
  border:1px solid var(--line);border-radius:8px;padding:11px 13px;margin-top:4px;
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;color:var(--muted);
  word-break:break-all;
}
.idrow b{color:var(--gold);font-weight:400;flex:0 0 auto;font-family:"Segoe UI",sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.copy{
  flex:0 0 auto;background:var(--panel2);border:1px solid var(--line2);color:var(--muted);
  border-radius:6px;padding:5px 10px;cursor:pointer;font-size:12px;transition:.15s;
}
.copy:hover{color:var(--gold2);border-color:var(--gold-dim)}
.copy.ok{color:var(--green);border-color:var(--green)}
.vcap{font-size:13px;color:var(--muted);margin-bottom:9px}
.vcap b{color:var(--gold2)}
.vidlist{max-height:230px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;padding-right:4px}
.vidlist .idrow{margin:0}
.close{
  position:absolute;top:14px;right:16px;background:transparent;border:0;color:var(--dim);
  font-size:26px;cursor:pointer;line-height:1;padding:2px 8px;border-radius:7px;
}
.close:hover{color:var(--gold);background:var(--panel2)}
.sheet .top{position:relative}

/* ---------- подгрузка ---------- */
.sentinel{height:40px}
.end{text-align:center;color:var(--dim);font-size:13px;padding:24px 0 70px}
footer{
  border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;
  padding:22px 0 40px;text-align:center;
}
footer a{color:var(--muted)}

@media(max-width:640px){
  .grid{grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:9px}
  .card{padding:9px;gap:9px}
  .ico{width:42px;height:42px;--sc:.63}
  .ico i{left:2px;top:2px}
  .card h3{font-size:12.5px}
  .card .en{display:none}
  h1{font-size:17px}
  .crest{width:34px;height:34px;font-size:15px}
  .sheet .top{flex-direction:column;gap:12px}
  .stats{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>

<header>
  <div class="wrap">
    <div class="brand">
      <div class="crest">B</div>
      <h1>База предметов Kingdom Come: Deliverance II
        <small>Богемия RP · оружие, броня, еда, зелья и прочее</small>
      </h1>
      <div class="spacer"></div>
      <div class="count" id="count"></div>
    </div>
    <div class="searchbar">
      <div class="field">
        <span class="mag">⌕</span>
        <input id="q" type="search" placeholder="Поиск по названию, ID или описанию…" autocomplete="off" spellcheck="false">
        <button class="clr" id="clr" title="Очистить">×</button>
      </div>
      <button class="btn" id="csv" title="Скачать CSV с текущей выборкой">⭳ CSV</button>
    </div>
    <div class="filters" id="cats"></div>
    <div class="subrow" id="subs"></div>
    <div class="toolbar">
      <select id="sort">
        <option value="n">По названию (А–Я)</option>
        <option value="n-">По названию (Я–А)</option>
        <option value="p-">Сначала дорогие</option>
        <option value="p">Сначала дешёвые</option>
        <option value="w-">Сначала тяжёлые</option>
        <option value="w">Сначала лёгкие</option>
        <option value="d-">Сначала прочные</option>
        <option value="d">Сначала хрупкие</option>
      </select>
      <select id="per">
        <option value="60">60 на странице</option>
        <option value="120">120 на странице</option>
        <option value="240">240 на странице</option>
        <option value="0">Показать все</option>
      </select>
      <div class="spacer"></div>
      <div class="viewtoggle">
        <button id="vGrid" class="on" title="Карточки">▦ Карточки</button>
        <button id="vTable" title="Таблица">☰ Таблица</button>
      </div>
    </div>
  </div>
</header>

<main class="wrap">
  <div id="grid" class="grid"></div>
  <div id="tablewrap" class="tablewrap" style="display:none">
    <table>
      <thead><tr id="thead"></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <div id="nores" class="empty" style="display:none">
    <div class="big">⚔</div>
    <div>Ничего не найдено. Попробуйте изменить запрос или фильтры.</div>
  </div>
  <div class="sentinel" id="sentinel"></div>
  <div class="end" id="end" style="display:none">Показаны все предметы</div>
</main>

<footer>
  <div class="wrap">
    Неофициальная база предметов для проекта <b>Богемия RP</b>.
    Данные и иконки — Kingdom Come: Deliverance II © Warhorse Studios.
    Названия приведены на русском языке.
  </div>
</footer>

<div class="modal" id="modal">
  <div class="sheet" id="sheet">
    <button class="close" id="mclose">×</button>
    <div class="top" id="mtop"></div>
    <div class="body" id="mbody"></div>
  </div>
</div>

<script>
const D = __DATA__;
const ITEMS = D.items;          // [name, en, cat, sub, weight, price, iconIdx, stats, id, nVar, extraIds]
const ICONS = D.iconMap;        // [sheet, x, y]
const SHEETS = D.sheets;
const CELL = D.cell;
const CATS = D.cats;
const SUBS = D.subs;
const SL = D.statLabels;

const N=0,E=1,C=2,S=3,W=4,P=5,I=6,A=7,UID=8,VAR=9,VIDS=10;
const RAW = D.rawCount;

// ---------------- иконки ----------------
// Спрайт: 16 колонок по 64 px = 1024 px шириной.
// Позиция задаётся CSS-переменными --x/--y, масштаб — --sc у контейнера,
// поэтому адаптивные переопределения --sc не ломают выравнивание.
function makeIcon(idx, cls){
  const holder=document.createElement('div');
  holder.className=cls;
  const inner=document.createElement('i');
  if(idx>=0 && ICONS[idx]){
    const [sh,x,y]=ICONS[idx];
    inner.style.backgroundImage='url(assets/icons/'+SHEETS[sh]+')';
    inner.style.setProperty('--x', (-x)+'px');
    inner.style.setProperty('--y', (-y)+'px');
  } else {
    holder.classList.add('empty');
  }
  holder.appendChild(inner);
  return holder;
}

// ---------------- состояние ----------------
const st = { q:'', cat:'all', sub:'all', sort:'n', view:'grid', per:60, shown:0, list:[] };

const $ = s=>document.querySelector(s);
const qEl=$('#q'), gridEl=$('#grid'), tableEl=$('#tablewrap'),
      tbody=$('#tbody'), thead=$('#thead'), nores=$('#nores'),
      endEl=$('#end'), countEl=$('#count');

// ---------------- фильтры ----------------
function catCount(id){
  if(id==='all') return ITEMS.length;
  let n=0; for(const it of ITEMS) if(it[C]===id) n++;
  return n;
}
function buildCats(){
  const box=$('#cats'); box.innerHTML='';
  for(const [id,label] of CATS){
    const n=catCount(id);
    if(!n) continue;
    const b=document.createElement('div');
    b.className='chip'+(st.cat===id?' on':'');
    b.innerHTML=label+'<span class="n">'+n+'</span>';
    b.onclick=()=>{ st.cat=id; st.sub='all'; buildCats(); buildSubs(); apply(); };
    box.appendChild(b);
  }
}
function buildSubs(){
  const box=$('#subs'); box.innerHTML='';
  const subs=SUBS[st.cat];
  // показываем строку подразделов только если вариантов реально больше одного
  const counts0={};
  if(subs) for(const it of ITEMS) if(it[C]===st.cat) counts0[it[S]]=1;
  if(!subs || Object.keys(counts0).length<2){ box.classList.remove('show'); return; }
  box.classList.add('show');
  const lbl=document.createElement('span'); lbl.className='lbl'; lbl.textContent='Раздел:';
  box.appendChild(lbl);
  const all=document.createElement('div');
  all.className='chip'+(st.sub==='all'?' on':'');
  all.textContent='Все';
  all.onclick=()=>{ st.sub='all'; buildSubs(); apply(); };
  box.appendChild(all);
  const counts={};
  for(const it of ITEMS) if(it[C]===st.cat) counts[it[S]]=(counts[it[S]]||0)+1;
  for(const [id,label] of subs){
    if(!counts[id]) continue;
    const b=document.createElement('div');
    b.className='chip'+(st.sub===id?' on':'');
    b.innerHTML=label+'<span class="n">'+counts[id]+'</span>';
    b.onclick=()=>{ st.sub=id; buildSubs(); apply(); };
    box.appendChild(b);
  }
}

// ---------------- поиск ------------
const norm = s=>s.toLowerCase().replace(/ё/g,'е');
let searchIndex=null;
function getIndex(){
  if(searchIndex) return searchIndex;
  searchIndex = ITEMS.map(it=>(norm(it[N])+' '+norm(it[E])+' '+it[UID]));
  return searchIndex;
}

function filtered(){
  const q = norm(st.q.trim());
  const idx = getIndex();
  let list;
  if(!q){
    list = ITEMS.filter(it => (st.cat==='all'||it[C]===st.cat) && (st.sub==='all'||it[S]===st.sub));
  } else {
    const words=q.split(/\s+/).filter(Boolean);
    list=[];
    for(let i=0;i<ITEMS.length;i++){
      const it=ITEMS[i];
      if(st.cat!=='all' && it[C]!==st.cat) continue;
      if(st.sub!=='all' && it[S]!==st.sub) continue;
      const hay=idx[i];
      let ok=true;
      for(const w of words){ if(hay.indexOf(w)<0){ok=false;break;} }
      if(ok) list.push(it);
    }
  }
  sortList(list);
  return list;
}

function sortList(list){
  const s=st.sort;
  const k=s[0], dir = s.endsWith('-')?-1:1;
  if(k==='n'){
    list.sort((a,b)=> a[N].localeCompare(b[N],'ru') * dir);
  } else if(k==='p'){
    list.sort((a,b)=> ((a[P]||0)-(b[P]||0)) * dir);
  } else if(k==='w'){
    list.sort((a,b)=> ((a[W]||0)-(b[W]||0)) * dir);
  } else if(k==='d'){
    list.sort((a,b)=> (((a[A]&&a[A].du)||0)-((b[A]&&b[A].du)||0)) * dir);
  } else if(k==='v'){
    list.sort((a,b)=> ((a[VAR]||0)-(b[VAR]||0)) * dir);
  }
}

// ---------------- рендер карточек ------------
function catLabel(id){ const c=CATS.find(x=>x[0]===id); return c?c[1]:id; }

function renderCards(list, from, to){
  const frag=document.createDocumentFragment();
  for(let i=from;i<to;i++){
    const it=list[i];
    const card=document.createElement('div');
    card.className='card';
    card.onclick=()=>openModal(it);
    card.appendChild(makeIcon(it[I],'ico'));
    const meta=document.createElement('div'); meta.className='meta';
    const h=document.createElement('h3'); h.textContent=it[N]; meta.appendChild(h);
    const en=document.createElement('div'); en.className='en'; en.textContent=it[E]; meta.appendChild(en);
    const tags=document.createElement('div'); tags.className='tags';
    if(it[P]){ const t=document.createElement('span'); t.className='tag g'; t.textContent=it[P]+' G'; tags.appendChild(t); }
    if(it[W]){ const t=document.createElement('span'); t.className='tag'; t.textContent=it[W]+' кг'; tags.appendChild(t); }
    if(it[VAR]){ const t=document.createElement('span'); t.className='tag v'; t.textContent='×'+it[VAR]; t.title='Вариантов: '+it[VAR]; tags.appendChild(t); }
    meta.appendChild(tags);
    card.appendChild(meta);
    frag.appendChild(card);
  }
  gridEl.appendChild(frag);
}

// ---------------- рендер таблицы ----------------
const COLS=[['n','Название'],['c','Категория'],['w','Вес'],['p','Цена'],['d','Прочность'],['v','Варианты']];
function buildHead(){
  thead.innerHTML='';
  for(const [k,label] of COLS){
    const th=document.createElement('th');
    th.dataset.k=k;
    th.innerHTML=label+'<span class="arr">▲▼</span>';
    if(st.sort[0]===k){
      th.classList.add('sorted');
      th.querySelector('.arr').textContent = st.sort.endsWith('-')?'▼':'▲';
    }
    if(k==='v'){ th.style.cursor='pointer'; }
    th.onclick=()=>{
      const desc = st.sort===k;          // повторный клик -> по убыванию
      st.sort = desc? k+'-' : k;
      $('#sort').value = st.sort;
      apply();
    };
    thead.appendChild(th);
  }
}
function renderRows(list, from, to){
  const frag=document.createDocumentFragment();
  for(let i=from;i<to;i++){
    const it=list[i];
    const tr=document.createElement('tr');
    tr.onclick=()=>openModal(it);
    const tdN=document.createElement('td'); tdN.className='name';
    const tin=makeIcon(it[I],'tin'); tdN.appendChild(tin);
    tdN.appendChild(document.createTextNode(it[N]));
    tr.appendChild(tdN);
    const tdC=document.createElement('td'); tdC.textContent=catLabel(it[C]); tr.appendChild(tdC);
    const tdW=document.createElement('td'); tdW.className='num'; tdW.textContent=it[W]||'—'; tr.appendChild(tdW);
    const tdP=document.createElement('td'); tdP.className='num'; tdP.textContent=it[P]||'—'; tr.appendChild(tdP);
    const tdD=document.createElement('td'); tdD.className='num';
    tdD.textContent=(it[A]&&it[A].du)?it[A].du:'—'; tr.appendChild(tdD);
    if(it[VAR]){
      const t=document.createElement('td');
      const sp=document.createElement('span'); sp.className='tag v'; sp.textContent='×'+it[VAR];
      t.appendChild(sp); tr.appendChild(t);
    }
    frag.appendChild(tr);
  }
  tbody.appendChild(frag);
}

// ---------------- применение ----------------
function apply(){
  st.list = filtered();
  st.shown = 0;
  gridEl.innerHTML=''; tbody.innerHTML='';
  const total=st.list.length;
  nores.style.display = total? 'none':'block';
  endEl.style.display='none';
  countEl.innerHTML = 'Найдено: <b>'+total.toLocaleString('ru')+'</b> из '+ITEMS.length.toLocaleString('ru')+
    ' <span style="opacity:.6">(записей: '+RAW.toLocaleString('ru')+')</span>';
  const per = st.per===0? total : st.per;
  const to = Math.min(per, total);
  if(st.view==='grid'){ gridEl.style.display=''; tableEl.style.display='none'; renderCards(st.list,0,to); }
  else { gridEl.style.display='none'; tableEl.style.display=''; buildHead(); renderRows(st.list,0,to); }
  st.shown = to;
  if(st.shown>=total && total>0) endEl.style.display='';
  $('#clr').style.display = st.q? 'block':'none';
}

function loadMore(){
  const total=st.list.length;
  if(st.shown>=total) return;
  const per = st.per===0? total : st.per;
  const to=Math.min(st.shown+per, total);
  if(st.view==='grid') renderCards(st.list, st.shown, to);
  else renderRows(st.list, st.shown, to);
  st.shown=to;
  if(st.shown>=total) endEl.style.display='';
}

// ---------------- модалка ----------------
const STAT_ORDER=['sk','a','ast','asl','asm','ds','dl','dm','sr','ar','ch','q','du','no','vi','co','nut','hea','ref','alc','lat','sv','sw'];
const NEG_STATS=new Set(['no','vi','co']);

function openModal(it){
  const top=$('#mtop'); top.innerHTML='';
  top.appendChild(makeIcon(it[I],'bigico'));
  const info=document.createElement('div'); info.style.minWidth='0'; info.style.flex='1';
  const h=document.createElement('h2'); h.textContent=it[N]; info.appendChild(h);
  const en=document.createElement('div'); en.className='en2'; en.textContent=it[E]; info.appendChild(en);
  const cats=document.createElement('div'); cats.className='cat';
  const c1=document.createElement('span'); c1.className='tag g'; c1.textContent=catLabel(it[C]); cats.appendChild(c1);
  const subs=SUBS[it[C]];
  if(subs){ const found=subs.find(s=>s[0]===it[S]);
    if(found){ const c2=document.createElement('span'); c2.className='tag'; c2.textContent=found[1]; cats.appendChild(c2);} }
  info.appendChild(cats);
  top.appendChild(info);

  const body=$('#mbody'); body.innerHTML='';
  const stats=document.createElement('div'); stats.className='stats';
  const a=it[A]||{};
  let any=false;
  for(const k of STAT_ORDER){
    if(a[k]===undefined) continue;
    any=true;
    const box=document.createElement('div'); box.className='stat';
    const kk=document.createElement('div'); kk.className='k'; kk.textContent=SL[k]||k;
    const vv=document.createElement('div'); vv.className='v';
    vv.textContent=typeof a[k]==='number'? a[k] : a[k];
    if(NEG_STATS.has(k) && typeof a[k]==='number') vv.classList.add('bad');
    box.appendChild(kk); box.appendChild(vv); stats.appendChild(box);
  }
  // вес и цена всегда
  for(const [k,v] of [['Вес',it[W]],['Цена',it[P]]]){
    if(v===undefined||v===null) continue;
    any=true;
    const box=document.createElement('div'); box.className='stat';
    const kk=document.createElement('div'); kk.className='k'; kk.textContent=k;
    const vv=document.createElement('div'); vv.className='v'; vv.textContent=v;
    box.appendChild(kk); box.appendChild(vv); stats.appendChild(box);
  }
  if(any) body.appendChild(stats);

  const allIds = [it[UID]].concat(it[VIDS]||[]);

  const mkRow = (id, idx)=>{
    const row=document.createElement('div'); row.className='idrow';
    if(allIds.length>1){
      const n=document.createElement('b'); n.textContent='#'+(idx+1); n.style.minWidth='30px';
      row.appendChild(n);
    }
    const lbl=document.createElement('b'); lbl.textContent='ID';
    row.appendChild(lbl);
    const code=document.createElement('span'); code.style.flex='1'; code.textContent=id; row.appendChild(code);
    const cp=document.createElement('button'); cp.className='copy'; cp.textContent='Копировать';
    cp.onclick=async()=>{
      try{ await navigator.clipboard.writeText(id); }
      catch(e){
        const t=document.createElement('textarea'); t.value=id;
        document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove();
      }
      cp.textContent='✓ Скопировано'; cp.classList.add('ok');
      setTimeout(()=>{ cp.textContent='Копировать'; cp.classList.remove('ok'); },1400);
    };
    row.appendChild(cp);
    return row;
  };

  if(allIds.length>1){
    const cap=document.createElement('div');
    cap.className='vcap';
    cap.innerHTML='Вариантов в игре: <b>'+allIds.length+'</b> — у всех одинаковые характеристики, отличается только исполнение.';
    body.appendChild(cap);
    const box=document.createElement('div'); box.className='vidlist';
    allIds.forEach((id,i)=>box.appendChild(mkRow(id,i)));
    body.appendChild(box);
  } else {
    body.appendChild(mkRow(allIds[0],0));
  }

  const hint=document.createElement('div');
  hint.style.cssText='margin-top:10px;font-size:12px;color:var(--dim)';
  hint.textContent='Выдача в игре: wh_cheat_addItem ' + it[UID];
  body.appendChild(hint);

  $('#modal').classList.add('show');
  document.body.style.overflow='hidden';
}
function closeModal(){ $('#modal').classList.remove('show'); document.body.style.overflow=''; }
$('#mclose').onclick=closeModal;
$('#modal').onclick=e=>{ if(e.target===$('#modal')) closeModal(); };
document.addEventListener('keydown',e=>{ if(e.key==='Escape') closeModal(); });

// ---------------- CSV ----------------
$('#csv').onclick=()=>{
  const rows=[['Название','Английское название','Категория','Раздел','Вес','Цена','Прочность','ID']];
  for(const it of st.list){
    const base=[it[N],it[E],catLabel(it[C]),it[S],it[W]||'',it[P]||'',(it[A]&&it[A].du)||''];
    rows.push(base.concat([it[UID]]));
    for(const extra of (it[VIDS]||[])) rows.push(base.concat([extra]));
  }
  const csv=rows.map(r=>r.map(v=>{
    const s=String(v==null?'':v);
    return /[";\n]/.test(s)? '"'+s.replace(/"/g,'""')+'"' : s;
  }).join(';')).join('\r\n');
  const blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download='kcd2-items-'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
};

// ---------------- события ----------------
let tmr=null;
qEl.addEventListener('input',()=>{
  clearTimeout(tmr);
  tmr=setTimeout(()=>{ st.q=qEl.value; apply(); },110);
});
$('#clr').onclick=()=>{ qEl.value=''; st.q=''; apply(); qEl.focus(); };
$('#sort').onchange=e=>{ st.sort=e.target.value; apply(); };
$('#per').onchange=e=>{ st.per=parseInt(e.target.value,10); apply(); };
$('#vGrid').onclick=()=>{ st.view='grid'; $('#vGrid').classList.add('on'); $('#vTable').classList.remove('on'); apply(); };
$('#vTable').onclick=()=>{ st.view='table'; $('#vTable').classList.add('on'); $('#vGrid').classList.remove('on'); apply(); };
// подгрузка при прокрутке (с запасным вариантом, если IO нет)
if('IntersectionObserver' in window){
  new IntersectionObserver(es=>{
    if(es[0].isIntersecting) loadMore();
  },{rootMargin:'600px'}).observe($('#sentinel'));
}else{
  window.addEventListener('scroll',()=>{
    if(window.innerHeight+window.scrollY >= document.body.offsetHeight-800) loadMore();
  },{passive:true});
}

buildCats(); buildSubs(); apply();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
