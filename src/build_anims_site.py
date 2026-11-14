# -*- coding: utf-8 -*-
"""Подключение каталога анимаций к сайту.

Добавляет:
  * переключатель разделов сверху — «Предметы» / «Анимации»;
  * отдельную вкладку анимаций со своими категориями и подкатегориями;
  * копирование имени клипа одним нажатием (в таблице и в карточке);
  * карточку анимации: русский смысл, описание из файла, фаза,
    семейство, Fragment, достоверность.

Запуск: python3 src/build_full.py   (сначала предметы, потом анимации)
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

GROUPS_JS = """const FIELD_GROUPS = {"бой":"⚔️ Боевые характеристики","защита":"🛡️ Защита","требования":"💪 Требования","эффект":"✨ Действие","общее":"📦 Общее","крафт":"🔨 Связанные предметы","тех":"⚙️ Прочие параметры"};
function extraGroups(it){
  const by = {};
  (it.extra||[]).forEach(f=>{ (by[f.g] = by[f.g] || []).push(f); });
  return Object.keys(FIELD_GROUPS).filter(g=>by[g]).map(g=>({g, title:FIELD_GROUPS[g], rows:by[g]}));
}
function extraText(it){
  return (it.extra||[]).map(f=>f.k+": "+f.v+(f.u?" "+f.u:"")).join(" ").toLowerCase();
}"""

BADGE_HTML = ("<span class='badge' style='background:rgba(236,72,153,.15);"
              "color:#f9a8d4;border-color:rgba(236,72,153,.35);padding:1px 6px;"
              "font-size:10px;vertical-align:middle'>Ж</span>")


def load(name):
    return json.load(open(os.path.join(REF, name), encoding="utf-8"))


def js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def unpack_anims(pack):
    """Развернуть сжатый каталог: словари повторов -> обычные объекты."""
    ru, de = pack["ru"], pack["desc"]
    ph, fa = pack["phase"], pack["fam"]
    fr, tr = pack["frag"], pack["trust"]
    pose = pack.get("pose") or []
    out = []
    for row in pack["items"]:
        (num, ru_i, de_i, ph_i, fa_i, fr_i, tr_i, det, clip, cat_id, sub,
         pose_i) = (row + [0])[:12]
        fam, fam_ru = fa[fa_i]
        out.append({
            "num": num, "ru": ru[ru_i], "desc": de[de_i], "phase": ph[ph_i],
            "fam": fam, "famRu": fam_ru, "frag": fr[fr_i], "trust": tr[tr_i],
            "det": det, "clip": clip, "catId": cat_id, "sub": sub,
            "pose": pose[pose_i] if pose_i < len(pose) else "",
            "cat": "", "id": clip,
        })
    return out


def strip_item(it):
    src = ""
    s = it.get("sources") or []
    if s:
        src = os.path.basename(s[0]).replace(".xml", "")
    return {
        "id": it["id"], "ru": it["ru"], "en": it.get("en") or "",
        "name": it["name"], "cat": it["cat"], "sub": it["sub"],
        "subLabel": it.get("subLabel") or "", "price": it.get("price"),
        "weight": it.get("weight"), "icon": it.get("icon") or "",
        "iconUrl": it.get("iconUrl") or "", "female": bool(it.get("female")),
        "xmlType": it.get("xmlType") or "", "src": src,
        "extra": it.get("extra") or [],
    }


# ------------------------------------------------------------------ разметка
MODE_SWITCH = """
  <!-- РАЗДЕЛЫ САЙТА -->
  <div class="modes">
    <button class="mode active" data-mode="items"><span class="ic">📦</span>Предметы <span class="cnt" id="modeCntItems">—</span></button>
    <button class="mode" data-mode="anims"><span class="ic">🎬</span>Анимации <span class="cnt" id="modeCntAnims">—</span></button>
  </div>
"""

MODE_CSS = """.modes{display:inline-flex;gap:6px;padding:5px;border:1px solid var(--border);border-radius:16px;background:rgba(255,255,255,.03);margin-bottom:16px;flex:0 0 auto}
.mode{display:flex;align-items:center;gap:8px;padding:12px 22px;border-radius:12px;border:1px solid transparent;background:transparent;color:var(--muted);font-size:15px;font-weight:800;transition:.18s;cursor:pointer}
.mode:hover{color:var(--text);background:rgba(255,255,255,.05)}
.mode.active{background:var(--grad);color:#fff;box-shadow:0 6px 18px rgba(124,58,237,.4)}
.mode .ic{font-size:17px}
.mode .cnt{background:rgba(255,255,255,.16);border-radius:99px;padding:1px 9px;font-size:12px;font-weight:800}
.header-inner{gap:14px}
.header-stats{min-width:0}
.header-stats .stat-pill{flex:0 0 auto}
.logo{flex:0 0 auto}
.modes .mode{white-space:nowrap}
@media (max-width:1180px){
  .header-inner{row-gap:10px}
  .header-stats{order:3;width:100%;margin-left:0;justify-content:flex-start}
}
@media (max-width:640px){
  .modes{width:100%}
  .mode{flex:1 1 0;justify-content:center;padding:10px 8px;font-size:13.5px}
}
.anim-desc{color:var(--muted);font-size:12.5px;line-height:1.45;margin-top:3px;max-width:640px}
.clip{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;color:#c4b5fd;word-break:break-all}
.copy-clip{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,.05);color:var(--text);font-size:12px;font-weight:700;cursor:pointer;transition:.15s;margin-top:6px}
.copy-clip:hover{background:rgba(124,58,237,.25);border-color:rgba(124,58,237,.5)}
.copy-clip:active{transform:scale(.97)}
.copy-clip.done{background:rgba(34,197,94,.25);border-color:rgba(34,197,94,.5)}
"""


def main():
    s = open(SRC, encoding="utf-8").read()
    cut = s.find(CF_MARK)
    if cut > 0:
        s = s[:cut].rstrip() + "\n</body>\n</html>\n"
    s = s.replace("</script></body>", "</script>\n</body>")

    # ---------------------------------------------------------- предметы
    items = [strip_item(it) for it in load("items_full.json")]
    cats = load("cats_full.json")
    subs = load("subs_full.json")
    for c in cats:
        c.setdefault("en", "")
    cats.sort(key=lambda c: c["id"])

    anims_pack = load("anim_items.json")
    anims = unpack_anims(anims_pack)
    acats = load("anim_cats.json")
    asubs = load("anim_subs.json")

    s = re.sub(r"const ITEMS = \[.*?\];\n",
               lambda m: "const ITEMS = " + js(items) + ";\n", s, count=1, flags=re.S)
    s = re.sub(r"const CATEGORIES = \[.*?\];\n",
               lambda m: "const CATEGORIES = " + js(cats) + ";\n", s, count=1, flags=re.S)
    s = re.sub(r"const SUBCATS = \{.*?\};\n",
               lambda m: "const SUBCATS = " + js(subs) + ";\n", s, count=1, flags=re.S)

    # данные анимаций
    unpack_js = (
        "const ANIMS = (()=>{const p=ANIM_PACK,out=[];"
        "for(const r of p.items){const f=p.fam[r[4]];"
        "out.push({num:r[0],ru:p.ru[r[1]],desc:p.desc[r[2]],phase:p.phase[r[3]],"
        "fam:f[0],famRu:f[1],frag:p.frag[r[5]],trust:p.trust[r[6]],det:r[7],"
        'clip:r[8],catId:r[9],sub:r[10],pose:p.pose[r[11]||0],cat:"",id:r[8]});}return out;})();\n')
    anim_js = ("const ANIM_PACK = " + js(anims_pack) + ";\n" + unpack_js
               + "const ACATS = " + js(acats) + ";\n"
               + "const ASUBS = " + js(asubs) + ";\n"
               + "const ACOUNT = " + str(len(anims)) + ";\n")
    s = s.replace("const ITEMS = ", anim_js + "const ITEMS = ", 1)

    # ---------------------------------------------------------- CSS
    s = s.replace("</style>", MODE_CSS + "</style>", 1)

    # счётчик в строке результата должен соответствовать разделу
    s = s.replace('всего в базе: <b>${ITEMS.length.toLocaleString(\"ru-RU\")}</b>',
                  'всего в базе: <b>${dataList().length.toLocaleString(\"ru-RU\")} ${isAnims()?"анимаций":"предметов"}</b>', 1)

    # фильтр «только с характеристиками» (был в сборке предметов)
    if 'id="onlyDetailed"' not in s:
        s = s.replace('<button class="chip" id="onlyWithIcon">Только с иконкой</button>',
                      '<button class="chip" id="onlyWithIcon">Только с иконкой</button>\n'
                      '      <button class="chip" id="onlyDetailed">Только с характеристиками</button>', 1)
    if 'onlyDetailed")' not in s.split("/* SEARCH */")[1]:
        s = s.replace('$("onlyWithIcon").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyWithIcon=this.classList.contains("active"); state.page=1; render(); });',
                      '$("onlyWithIcon").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyWithIcon=this.classList.contains("active"); state.page=1; render(); });\n'
                      '$("onlyDetailed").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyDetailed=this.classList.contains("active"); state.page=1; render(); });', 1)
    s = s.replace('$("onlyWithIcon").classList.remove("active");',
                  '$("onlyWithIcon").classList.remove("active"); $("onlyDetailed").classList.remove("active");', 1)
    s = s.replace('state.onlyWithIcon=false; state.sort="default";',
                  'state.onlyWithIcon=false; state.onlyDetailed=false; state.sort="default";', 1)

    # счётчик характеристик в шапке (только если его ещё нет)
    if 'id="statFields"' not in s:
        s = s.replace('Категорий: <b id="statCats">—</b></div>',
                      'Категорий: <b id="statCats">—</b></div>\n'
                      '      <div class="stat-pill">Характеристик: <b id="statFields">—</b></div>', 1)


    # ---------- правки карточки предмета (перенесены из build_full.py) ----------
    old_extra = ('${extraEntries.length ? `<div class="section-title">Характеристики</div>'
                 '<div class="kv">${extraEntries.map(([k,v])=>`<div class="kv-row">'
                 '<span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`).join("")}'
                 '</div>` : `<div class="section-title">Характеристики</div>'
                 '<p style="color:var(--muted);font-size:13px">Дополнительных характеристик нет.</p>`}')
    new_extra = ('${(it.extra&&it.extra.length) ? extraGroups(it).map(gr=>'
                 '`<div class="section-title">${gr.title} <span class="cnt" style="font-size:12px;'
                 'color:var(--muted);font-weight:600">${gr.rows.length}</span></div>'
                 '<div class="kv">${gr.rows.map(f=>`<div class="kv-row"><span class="k">${esc(f.k)}</span>'
                 '<span class="v">${fmtField(f)}</span></div>`).join("")}</div>`'
                 ').join("") : `<div class="section-title">Характеристики</div>'
                 '<p style="color:var(--muted);font-size:13px">У этого предмета в файлах игры нет характеристик.</p>`}')
    if old_extra in s:
        s = s.replace(old_extra, new_extra, 1)
    else:
        raise SystemExit("не найден блок характеристик в карточке предмета")
    s = s.replace("  const extraEntries = Object.entries(it.extra||{});\n", "", 1)

    # подзаголовок: EN + внутреннее имя + источник
    s = s.replace('  $("modalSub").textContent = (it.en ? it.en+" • " : "") + it.name;',
                  '  $("modalSub").textContent = (it.en ? it.en+" • " : "") + it.name'
                  ' + (it.src ? " • " + it.src : "");', 1)

    # плейсхолдер поиска
    s = s.replace('placeholder="Поиск по русскому, английскому названию, Name или ID…  ( / )"',
                  'placeholder="Поиск по названию, Name, ID и характеристикам…  ( / )"', 1)

    # тип и файл игры вместо «Примечания»
    s = s.replace('<div class="detail-item"><div class="k">Примечание</div><div class="v" style="font-size:12px;font-weight:600;color:var(--muted)">${esc(it.note)||"—"}</div></div>',
                  '<div class="detail-item"><div class="k">Тип в файлах игры</div><div class="v"><span class="mono">${esc(it.xmlType)||"—"}</span></div></div>\n'
                  '      <div class="detail-item"><div class="k">Файл игры</div><div class="v"><span class="mono">${esc(it.src)||"—"}</span></div></div>', 1)

    # CSV: характеристики и источник
    s = s.replace('"Категория","Подкатегория","Примечание"]',
                  '"Категория","Подкатегория","Тип","Файл","Характеристики"]', 1)
    s = s.replace('it.weight??"",catName(it.cat),it.subLabel||"",it.note]',
                  'it.weight??"",catName(it.cat),it.subLabel||"",it.xmlType||"",it.src||"",'
                  '(it.extra||[]).map(f=>f.k+": "+f.v+(f.u?" "+f.u:"")).join("; ")]', 1)

    # пустая английская строка не должна показываться прочерком
    s = s.replace('<div class="en-name">${esc(it.en)||"—"}</div>',
                  '<div class="en-name">${esc(it.en)||""}</div>')

    # бейдж «Ж» отделён пробелом
    if "const FEMALE_BADGE" not in s:
        s = s.replace("const FIELD_GROUPS = ",
                      "const FEMALE_BADGE = " + js(BADGE_HTML) + ";\n"
                      "const FIELD_GROUPS = ", 1)
    if "const FEMALE_BADGE" not in s:
        # FIELD_GROUPS вставляется в самом конце — ставим плашку отдельно
        s = s.replace("function fmtPrice(p){",
                      "const FEMALE_BADGE = " + js(BADGE_HTML) + ";\n"
                      "function fmtPrice(p){", 1)
    s = s.replace('<div class="ru-name">${esc(it.ru)||"—"}</div>',
                  '<div class="ru-name">${esc(it.ru)||"—"}'
                  '${it.female?"&nbsp;"+FEMALE_BADGE:""}</div>')

    # заголовки таблицы зависят от раздела
    s = s.replace("""            <th>#</th>
            <th>Русское название</th>
            <th>Название предмета (Name)</th>
            <th>Цена</th>
            <th>Вес</th>
            <th>Категория</th>""",
                  """            <th>#</th>
            <th id="thName">Русское название</th>
            <th id="thClip">Название предмета (Name)</th>
            <th id="thCol4">Цена</th>
            <th id="thCol5">Вес</th>
            <th>Категория</th>""", 1)

    # ------------------------------------------------- переключатель
    s = s.replace('<div class="header-stats">', MODE_SWITCH +
                  '    <div class="header-stats">', 1)

    # ------------------------------------------- вспомогательные функции
    s = s.replace("function fmtPrice(p){", GROUPS_JS + """

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
function fmtPrice(p){""", 1)

    # ---------------------------------------------- набор данных по режиму
    s = s.replace('''const state = {''', '''const state = {
  mode: "items", // items | anims''', 1)
    s = s.replace('''  cat: -1, // -1 = all''', '''  cat: -1, // -1 = все предметы
  acat: -1, // -1 = все анимации
  aSub: "all",''', 1)
    s = s.replace('''function catName(catId){''', '''function isAnims(){ return state.mode === "anims"; }
function dataList(){ return isAnims() ? ANIMS : ITEMS; }
function catList(){ return isAnims() ? ACATS : CATEGORIES; }
function subMap(){ return isAnims() ? ASUBS : SUBCATS; }
function curCat(){ return isAnims() ? state.acat : state.cat; }
function setCat(v){ if(isAnims()) state.acat = v; else state.cat = v; }
function curSub(){ return isAnims() ? state.aSub : state.sub; }
function setSub(v){ if(isAnims()) state.aSub = v; else state.sub = v; }
function catName(catId){''', 1)
    s = s.replace('function catName(catId){ const c=CATEGORIES[catId]; return c ? c.ru : "—"; }',
                  'function catName(catId){ const c=catList()[catId]; return c ? c.ru : "—"; }')
    s = s.replace('function catIcon(catId){ const c=CATEGORIES[catId]; return c ? c.icon : "📦"; }',
                  'function catIcon(catId){ const c=catList()[catId]; return c ? c.icon : "📦"; }')

    # ---------------------------------------------------------- вкладки
    s = s.replace('''function renderTabs(){
  let html = `<button class="tab ${state.cat===-1?"active":""}" data-cat="-1"><span class="ic">🌐</span>Все предметы <span class="cnt">${ITEMS.length}</span></button>`;
  CATEGORIES.forEach(c=>{
    html += `<button class="tab ${state.cat===c.id?"active":""}" data-cat="${c.id}"><span class="ic">${c.icon}</span>${esc(c.ru)} <span class="cnt">${c.count}</span></button>`;
  });
  tabsEl.innerHTML = html;
  tabsEl.querySelectorAll(".tab").forEach(b=>{
    b.addEventListener("click", ()=>{
      state.cat = parseInt(b.dataset.cat,10);
      state.sub = "all";
      state.page = 1;
      renderTabs(); renderSubcats(); render();
      // scroll active tab into view
      // all tabs visible, no scrolling needed
    });
  });
}''', '''function renderTabs(){
  const anims = isAnims();
  const what = anims ? "Все анимации" : "Все предметы";
  let html = `<button class="tab ${curCat()===-1?"active":""}" data-cat="-1"><span class="ic">🌐</span>${what} <span class="cnt">${dataList().length}</span></button>`;
  catList().forEach(c=>{
    html += `<button class="tab ${curCat()===c.id?"active":""}" data-cat="${c.id}"><span class="ic">${c.icon}</span>${esc(c.ru)} <span class="cnt">${c.count}</span></button>`;
  });
  tabsEl.innerHTML = html;
  tabsEl.querySelectorAll(".tab").forEach(b=>{
    b.addEventListener("click", ()=>{
      setCat(parseInt(b.dataset.cat,10));
      if(anims) state.aSub = "all"; else state.sub = "all";
      state.page = 1;
      renderTabs(); renderSubcats(); render();
    });
  });
}''')

    s = s.replace('''function renderSubcats(){
  const bar = $("subcatsBar");
  const list = SUBCATS[String(state.cat)];
  if(state.cat===-1 || !list || !list.length){ bar.style.display="none"; return; }
  bar.style.display="";
  $("subcatsCatName").textContent = catName(state.cat);
  const total = list.reduce((s,x)=>s+x.count,0);
  let html = `<button class="subcat ${state.sub==="all"?"active":""}" data-sub="all">Все подкатегории <span class="cnt">${total}</span></button>`;
  list.forEach(s=>{
    html += `<button class="subcat ${state.sub===s.key?"active":""}" data-sub="${esc(s.key)}">${esc(s.label)} <span class="cnt">${s.count}</span></button>`;
  });
  $("subcats").innerHTML = html;
  $("subcats").querySelectorAll(".subcat").forEach(b=>{
    b.addEventListener("click", ()=>{ state.sub=b.dataset.sub; state.page=1; renderSubcats(); render(); });
  });''', '''function renderSubcats(){
  const bar = $("subcatsBar");
  const cid = curCat();
  let list = subMap()[String(cid)];
  // если делить не на что — панель подкатегорий не нужна
  if(list && list.length===1 && list[0].key==="all") list = null;
  if(cid===-1 || !list || !list.length){ bar.style.display="none"; return; }
  bar.style.display="";
  $("subcatsCatName").textContent = catName(cid);
  const total = list.reduce((s,x)=>s+x.count,0);
  let html = `<button class="subcat ${curSub()==="all"?"active":""}" data-sub="all">Все подкатегории <span class="cnt">${total}</span></button>`;
  list.forEach(s=>{
    html += `<button class="subcat ${curSub()===s.key?"active":""}" data-sub="${esc(s.key)}">${esc(s.label)} <span class="cnt">${s.count}</span></button>`;
  });
  $("subcats").innerHTML = html;
  $("subcats").querySelectorAll(".subcat").forEach(b=>{
    b.addEventListener("click", ()=>{ setSub(b.dataset.sub); state.page=1; renderSubcats(); render(); });
  });''')

    # ------------------------------------------------------- фильтрация
    s = s.replace('''function getFiltered(){
  const q = state.query.trim().toLowerCase();
  let list = ITEMS.filter(it=>{
    if(state.cat!==-1 && it.cat!==state.cat) return false;
    if(state.sub!=="all" && it.sub!==state.sub) return false;
    if(state.onlyPriced && it.price==null) return false;
    if(state.onlyWeighted && it.weight==null) return false;
    if(state.onlyWithIcon && !it.iconUrl) return false;
    if(q){
      const hay = (it.ru+" "+it.en+" "+it.name+" "+it.id+" "+(it.icon||"")+" "+(it.subLabel||"")).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });''', '''function poseKeyOf(it){
  const st = (it.phase||"").trim()==="Ожидание / поза" || (it.phase||"").trim()==="Цикл";
  return (it.pose || "none") + (st ? "_static" : "_action");
}
function poseStatic(it){
  const p = (it.phase||"").trim();
  return p==="Ожидание / поза" || p==="Цикл";
}
function animHay(it){
  return (it.ru+" "+it.clip+" "+(it.desc||"")+" "+(it.phase||"")+" "+(it.fam||"")+" "+(it.famRu||"")+" "+(it.frag||"")+" "+(it.det||[]).join(" ")).toLowerCase();
}
function getFiltered(){
  const q = state.query.trim().toLowerCase();
  const anims = isAnims();
  const cid = curCat(), sub = curSub();
  const poseTab = anims && cid>=0 && ACATS[cid] && ACATS[cid].pose;
  let list = dataList().filter(it=>{
    if(cid!==-1 && !poseTab && (anims ? it.catId : it.cat)!==cid) return false;
    // во вкладке «Позы» подкатегория — это поза + статично/действие
    if(sub!=="all"){
      if(poseTab){ if(poseKeyOf(it)!==sub) return false; }
      else if(it.sub!==sub) return false;
    }
    if(!anims){
      if(state.onlyPriced && it.price==null) return false;
      if(state.onlyWeighted && it.weight==null) return false;
      if(state.onlyWithIcon && !it.iconUrl) return false;
      if(state.onlyDetailed && !(it.extra && it.extra.length)) return false;
    }
    if(q){
      const hay = anims ? animHay(it)
        : (it.ru+" "+it.en+" "+it.name+" "+it.id+" "+(it.icon||"")+" "+(it.subLabel||"")+" "+(it.xmlType||"")+" "+extraText(it)).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });''')

    # сортировка: у анимаций по номеру
    s = s.replace('''  const s = state.sort;
  if(s==="ru-asc")''', '''  const s = state.sort;
  if(isAnims() && s==="default") list.sort((a,b)=>a.num-b.num);
  else if(s==="ru-asc")''')

    # ------------------------------------------- отрисовка анимаций
    s = s.replace("  if(isTable){\n    tbody.innerHTML = pageItems.map((it,i)=>`",
                  "  if(isAnims()){ renderAnims(pageItems, start); renderPagination(filtered.length, totalPages); return; }\n"
                  "  if(isTable){\n    tbody.innerHTML = pageItems.map((it,i)=>`", 1)

    ANIM_RENDER = r"""
/* ------------------------------------------------------- АНИМАЦИИ */
const POSE_LABEL = {stand:"Стоя", sit:"Сидя", lie:"Лёжа", sleep:"Сон",
                   kneel:"На коленях", crouch:"Присев", horse:"Верхом", lean:"Опираясь"};
function poseLabel(p){ return POSE_LABEL[p] || ""; }
function clipCopyHtml(clip, small){
  return `<button class="copy-clip" data-clip="${esc(clip)}" title="Скопировать имя анимации">⧉ Копировать${small?"":" имя"}</button>`;
}
function animRow(it, n, idx){
  return `
    <tr data-anum="${idx}">
      <td class="num">${n}</td>
      <td>
        <div class="ru-name">${esc(it.ru)||"—"}</div>
        <div class="anim-desc">${esc(it.desc)||""}</div>
      </td>
      <td>
        <div class="clip">${esc(it.clip)}</div>
        ${clipCopyHtml(it.clip)}
      </td>
      <td><span class="badge badge-cat">${esc(it.phase)||"—"}</span></td>
      <td><span class="badge badge-cat">${esc(it.famRu)||"—"}</span></td>
      <td>
        <div class="row-actions">
          <button class="icon-btn" title="Подробнее" data-adetail="${idx}">›</button>
        </div>
      </td>
    </tr>`;
}
function animCard(it, idx){
  return `
    <div class="item-card" data-anum="${idx}">
      <div class="item-card-top">
        <div style="min-width:0">
          <div class="ru-name">${esc(it.ru)||"—"}</div>
          <div class="anim-desc">${esc(it.desc)||""}</div>
        </div>
      </div>
      <div><span class="clip">${esc(it.clip)}</span></div>
      <div class="item-meta">
        <span class="meta-chip">${esc(it.phase)||"—"}</span>
        <span class="meta-chip">${esc(it.famRu)||"—"}</span>
        ${it.pose ? `<span class="meta-chip">${poseLabel(it.pose)}</span>` : ""}
      </div>
      ${clipCopyHtml(it.clip)}
    </div>`;
}
function renderAnims(pageItems, start){
  const isTable = state.view==="table";
  $("tableCard").style.display = isTable ? "" : "none";
  cardsWrap.style.display = isTable ? "none" : "";
  $("emptyTable").style.display = (isTable && pageItems.length===0) ? "" : "none";
  $("emptyCards").style.display = (!isTable && pageItems.length===0) ? "" : "none";
  if(isTable){
    tbody.innerHTML = pageItems.map((it,i)=>animRow(it, start+i+1, it.num)).join("");
    tbody.querySelectorAll("tr").forEach(tr=>{
      tr.addEventListener("click", e=>{
        if(e.target.closest("[data-clip]")||e.target.closest("[data-anim-detail]")) return;
        openAnimModal(parseInt(tr.dataset.anum,10));
      });
    });
    tbody.querySelectorAll("[data-anim-detail]").forEach(b=>{
      b.addEventListener("click", e=>{ e.stopPropagation(); openAnimModal(parseInt(b.dataset.adetail,10)); });
    });
  } else {
    cardsWrap.innerHTML = pageItems.map(it=>animCard(it, it.num)).join("");
    cardsWrap.querySelectorAll(".item-card").forEach(c=>{
      c.addEventListener("click", e=>{
        if(e.target.closest("[data-clip]")) return;
        openAnimModal(parseInt(c.dataset.anum,10));
      });
    });
  }
  bindClipCopy();
}
function bindClipCopy(){
  document.querySelectorAll("[data-clip]").forEach(b=>{
    if(b._bound) return;
    b._bound = true;
    b.addEventListener("click", async e=>{
      e.stopPropagation();
      await copyText(b.dataset.clip, "Имя анимации");
      b.classList.add("done");
      const old = b.textContent;
      b.textContent = "✓ Скопировано";
      setTimeout(()=>{ b.classList.remove("done"); b.textContent = old; }, 1200);
    });
  });
}
function animByNum(num){ return ANIMS.find(a=>a.num===num); }
function openAnimModal(num){
  const it = animByNum(num);
  if(!it) return;
  $("modalIcon").innerHTML = "🎬";
  $("modalTitle").textContent = it.ru || it.clip;
  $("modalSub").textContent = it.clip;
  const det = (it.det&&it.det.length)
    ? `<div class="section-title">Детали исполнения</div><div class="chips">${it.det.map(d=>`<span class="meta-chip">${esc(d)}</span>`).join("")}</div>`
    : "";
  $("modalBody").innerHTML = `
    <div class="detail-grid">
      <div class="detail-item"><div class="k">Что это</div><div class="v">${esc(it.ru)||"—"}</div></div>
      <div class="detail-item"><div class="k">Смысл по имени</div><div class="v" style="font-size:13px">${esc(it.desc)||"—"}</div></div>
      <div class="detail-item"><div class="k">Категория</div><div class="v">${esc(it.cat)||"—"}</div></div>
      <div class="detail-item"><div class="k">Поза</div><div class="v">${it.pose ? poseLabel(it.pose) + (poseStatic(it) ? " (статично)" : " (действие)") : "По имени не определить"}</div></div>
      <div class="detail-item"><div class="k">Фаза</div><div class="v">${esc(it.phase)||"—"}</div></div>
      <div class="detail-item"><div class="k">Семейство</div><div class="v">${esc(it.famRu)||"—"}${it.fam&&it.fam!==it.famRu?` <span style="color:var(--muted);font-size:12px">(${esc(it.fam)})</span>`:""}</div></div>
      <div class="detail-item"><div class="k">Fragment</div><div class="v"><span class="mono">${esc(it.frag)||"—"}</span></div></div>
      <div class="detail-item"><div class="k">Достоверность описания</div><div class="v" style="font-size:12.5px">${esc(it.trust)||"—"}</div></div>
      <div class="detail-item"><div class="k">Номер в справочнике</div><div class="v">${it.num}</div></div>
    </div>
    <div class="section-title">Имя анимации для вызова</div>
    <div class="kv"><div class="kv-row"><span class="k">Clip</span><span class="v"><span class="clip">${esc(it.clip)}</span></span></div></div>
    <div style="margin-top:12px">${clipCopyHtml(it.clip)}</div>
    ${det}
    <div class="modal-actions">
      <button class="btn btn-primary" id="mCopyClip2">⧉ Копировать имя анимации</button>
      <button class="btn" id="mCopyRu2">⧉ Копировать русское название</button>
    </div>`;
  $("modalOverlay").classList.add("open");
  $("mCopyClip2").onclick = ()=>copyText(it.clip,"Имя анимации");
  $("mCopyRu2").onclick = ()=>copyText(it.ru,"Название");
  bindClipCopy();
}
"""

    s = s.replace("/* SEARCH */", ANIM_RENDER + "\n/* SEARCH */", 1)

    # счётчик в строке результата должен соответствовать разделу
    s = s.replace('всего в базе: <b>${ITEMS.length.toLocaleString(\"ru-RU\")}</b>',
                  'всего в базе: <b>${dataList().length.toLocaleString(\"ru-RU\")} ${isAnims()?"анимаций":"предметов"}</b>', 1)

    # фильтр «только с характеристиками» (был в сборке предметов)
    if 'id="onlyDetailed"' not in s:
        s = s.replace('<button class="chip" id="onlyWithIcon">Только с иконкой</button>',
                      '<button class="chip" id="onlyWithIcon">Только с иконкой</button>\n'
                      '      <button class="chip" id="onlyDetailed">Только с характеристиками</button>', 1)
    if 'onlyDetailed")' not in s.split("/* SEARCH */")[1]:
        s = s.replace('$("onlyWithIcon").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyWithIcon=this.classList.contains("active"); state.page=1; render(); });',
                      '$("onlyWithIcon").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyWithIcon=this.classList.contains("active"); state.page=1; render(); });\n'
                      '$("onlyDetailed").addEventListener("click", function(){ this.classList.toggle("active"); state.onlyDetailed=this.classList.contains("active"); state.page=1; render(); });', 1)
    s = s.replace('$("onlyWithIcon").classList.remove("active");',
                  '$("onlyWithIcon").classList.remove("active"); $("onlyDetailed").classList.remove("active");', 1)
    s = s.replace('state.onlyWithIcon=false; state.sort="default";',
                  'state.onlyWithIcon=false; state.onlyDetailed=false; state.sort="default";', 1)

    # счётчик характеристик в шапке (только если его ещё нет)
    if 'id="statFields"' not in s:
        s = s.replace('Категорий: <b id="statCats">—</b></div>',
                      'Категорий: <b id="statCats">—</b></div>\n'
                      '      <div class="stat-pill">Характеристик: <b id="statFields">—</b></div>', 1)

    # заголовки таблицы зависят от раздела
    s = s.replace("""            <th>#</th>
            <th>Русское название</th>
            <th>Название предмета (Name)</th>
            <th>Цена</th>
            <th>Вес</th>
            <th>Категория</th>""",
                  """            <th>#</th>
            <th id="thName">Русское название</th>
            <th id="thClip">Название предмета (Name)</th>
            <th id="thCol4">Цена</th>
            <th id="thCol5">Вес</th>
            <th>Категория</th>""", 1)

    # ------------------------------------------------- переключатель
    MODE_JS = r"""
/* ------------------------------------------------ РАЗДЕЛЫ САЙТА */
function applyMode(){
  const anims = isAnims();
  document.querySelectorAll(".mode").forEach(b=>b.classList.toggle("active", b.dataset.mode===state.mode));
  // у анимаций нет цены/веса/иконок — эти фильтры не нужны
  ["onlyPriced","onlyWeighted","onlyWithIcon","onlyDetailed"].forEach(id=>{
    const el = $(id);
    if(!el) return;
    el.style.display = anims ? "none" : "";
    if(anims) el.classList.remove("active");
  });
  const sort = $("sortSelect");
  if(sort){
    [...sort.options].forEach(o=>{
      if(["price-desc","price-asc","weight-desc","weight-asc"].includes(o.value)) o.hidden = anims;
    });
    if(anims && ["price-desc","price-asc","weight-desc","weight-asc"].includes(sort.value)){
      sort.value = "default"; state.sort = "default";
    }
  }
  // заголовки столбцов: у анимаций нет цены и веса
  const th = (id, v)=>{ const e = $(id); if(e) e.textContent = v; };
  th("thName", anims ? "Русское название" : "Русское название");
  th("thClip", anims ? "Имя анимации (Clip)" : "Название предмета (Name)");
  th("thCol4", anims ? "Фаза" : "Цена");
  th("thCol5", anims ? "Семейство" : "Вес");
  $("modeCntItems").textContent = ITEMS.length.toLocaleString("ru-RU");
  $("modeCntAnims").textContent = ACOUNT.toLocaleString("ru-RU");
  const lbl = document.querySelector(".tabs-label span");
  if(lbl) lbl.textContent = anims ? "🎬 Категории анимаций" : "📂 Категории предметов";
  document.querySelectorAll(".stat-pill").forEach(p=>{
    if(/Характеристик/.test(p.textContent)) p.style.display = anims ? "none" : "";
  });
  document.title = anims ? "KCD2 Animations — Каталог анимаций" : "KCD2 Items Database — База предметов";
  const logo = document.querySelector(".logo-title");
  if(logo) logo.innerHTML = anims ? "KCD2 <span>ANIMATIONS</span>" : "KCD2 <span>ITEMS</span>";
  const sub = document.querySelector(".logo-sub");
  if(sub) sub.textContent = anims ? "Каталог анимаций • Богемия RP" : "База предметов • Богемия RP";
}
document.querySelectorAll(".mode").forEach(b=>{
  b.addEventListener("click", ()=>{
    if(state.mode===b.dataset.mode) return;
    state.mode = b.dataset.mode;
    state.page = 1;
    state.query = "";
    searchInput.value = "";
    searchClear.classList.remove("show");
    applyMode(); renderTabs(); renderSubcats(); render(); renderStats();
  });
});
function renderStats(){
  const anims = isAnims();
  $("statTotal").textContent = (anims ? ACOUNT : ITEMS.length).toLocaleString("ru-RU");
  // подпись меняем целиком, не трогая точку-индикатор
  const pill = $("statTotal").parentNode;
  pill.innerHTML = '<span class="dot"></span>' + (anims ? "Всего анимаций: " : "Всего предметов: ")
                 + '<b id="statTotal">' + (anims ? ACOUNT : ITEMS.length).toLocaleString("ru-RU") + '</b>';
  $("statCats").textContent = catList().length;
  const sf = $("statFields");
  if(sf) sf.textContent = ITEMS.reduce((n,it)=>n+(it.extra?it.extra.length:0),0).toLocaleString("ru-RU");
}
"""
    s = s.replace("/* INIT */", MODE_JS + "\n/* INIT */", 1)

    # инициализация: счётчики режимов и статистика
    s = s.replace('$("statTotal").textContent = ITEMS.length.toLocaleString("ru-RU");\n$("statCats").textContent = CATEGORIES.length;',
                  'applyMode(); renderStats();', 1)
    s = s.replace('$("statFields").textContent = ITEMS.reduce((n,it)=>n+(it.extra?it.extra.length:0),0).toLocaleString("ru-RU");',
                  '', 1)
    # resetAll должен уважать режим
    s = s.replace('state.cat=-1; state.sub="all"; state.query="";',
                  'state.cat=-1; state.acat=-1; state.aSub="all"; state.sub="all"; state.query="";', 1)
    open(OUT, "w", encoding="utf-8").write(s)
    print("каркас записан")


if __name__ == "__main__":
    main()
