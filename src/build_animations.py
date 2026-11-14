# -*- coding: utf-8 -*-
"""Сборка каталога анимаций из справочника wiki/*.xlsx.

Из имени клипа строится русское название:
    combat_clinch1_sz1_az2_attacksync_backoff_blunt_master
    -> «Захват 1: отход» + детали «ведущая роль, синхронизация, дробящее…»

Технические коды (стороны, зоны удара, синхронизация) в название не лезут —
они уходят в «детали», чтобы строка оставалась читаемой.

Запуск: python3 src/build_animations.py
Выход:  data/reference/anim_items.json, anim_cats.json, anim_subs.json
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anim_words import ACC, DETAIL_ONLY, RU, TECH, VERB, is_code  # noqa: E402
from xlsx_read import read_sheet  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")
WIKI = os.path.join(ROOT, "wiki")

XLSX = "KCD2_animations_full_reference_9006 (1).xlsx"
SHEET_ALL = 2      # «Все 9006»
SHEET_FAM = 5      # «Семейства»

# ------------------------------------------------------------- категории
# порядок вкладок и иконки; содержимое берётся из файла, поэтому здесь
# только оформление — если в архиве появится новая категория, она
# встанет в «Прочее» с иконкой 📦
CAT_ICON = {
    "Бой / турнир": "⚔️",
    "Диалоги / жесты": "💬",
    "Сюжетные сцены": "🎬",
    "Передвижение": "🏃",
    "Город / быт": "🏘️",
    "Конюх / лошади": "🐎",
    "Алхимия / лечение": "🌿",
    "Трактир / отдых": "🍺",
    "Стража / охрана": "🛡️",
    "Повседневные действия": "🧹",
    "Сон / отдых": "😴",
    "Монах / служба": "⛪",
    "Кузнец / оружейник": "🔨",
    "Предметы / взаимодействие": "📦",
    "Писарь / книжник": "📜",
    "Пекарь": "🥖",
    "Транспорт": "🛒",
    "Кухня / повар": "🍲",
    "Лесоруб": "🪓",
    "Каменщик": "🧱",
    "Крестьянин / фермер": "🌾",
    "Ремесло / мастерская": "🛠️",
    "Торговля / лавка": "🪙",
    "Портной": "🧵",
    "Лагерь / ремонт": "⛺",
    "Жесты / общение": "👋",
    "Стояние / переходы": "🧍",
    "Углежог": "🔥",
    "Верховая езда": "🏇",
    "Домашняя работа": "🧺",
    "Охота / разделка": "🦌",
    "Плотник": "🪚",
    "Лагерь": "⛺",
    "Охота / рыбалка": "🎣",
    "Лагерь / костёр": "🔥",
    "Животные / уход": "🐕",
    "Прочее": "📦",
}

# категории, которые слишком большие и делятся на подкатегории
# (остальные подкатегорий не получают — так проще искать)
BIG = {"Бой / турнир", "Диалоги / жесты", "Прочее", "Сюжетные сцены",
       "Передвижение", "Город / быт", "Повседневные действия",
       "Стояние / переходы", "Верховая езда"}

# смысловые подкатегории для крупных групп: ключ -> (подпись, [токены])
SUB_GROUPS = {
    # бой
    "combat": ("Боевые приёмы", ["combat", "battle"]),
    "tournament": ("Турнир", ["tournament"]),
    "rifle": ("Ручница и огнестрел", ["rifle", "handcannon", "cannon"]),
    "stealth": ("Скрытность и добивание", ["stealth", "takedown", "stealthgrab"]),
    "hitreaction": ("Реакции на удар", ["hitreaction", "hit", "scarereaction", "stun"]),
    "weapon": ("Оружие: достаёт и меняет", ["weapon", "holster", "swap", "draw"]),
    "crossbow": ("Арбалет", ["crossbow", "crosbow"]),
    "bow": ("Лук", ["bow"]),
    "crowd": ("Толпа и зрители", ["crowd", "audience", "cheer"]),
    "kill": ("Убийство", ["kill", "killed", "death", "dead", "dying"]),
    "surrender": ("Сдача в плен", ["surrender"]),
    "clinch": ("Захват и борьба", ["clinch", "clinch1", "clinch2", "fistfight"]),
    "block": ("Блок и защита", ["block", "blk", "guard", "blockperfect", "blockbroken"]),
    "dodge": ("Уклонения", ["dodge", "juke", "riposte"]),
    # диалоги
    "dlg": ("Диалоговые жесты", ["dlg", "adlg"]),
    "fa": ("Жесты боя в диалоге", ["fa"]),
    "quest": ("Сюжетные реплики", ["quest"]),
    "relaxed": ("Спокойные позы", ["relaxed"]),
    "sit": ("Сидя", ["sitting", "sit"]),
    "table": ("За столом", ["table"]),
    # прочее
    "crime": ("Преступления", ["crime", "steal", "robber", "pickpocket", "locked"]),
    "minigame": ("Мини-игры", ["minigame"]),
    "lockpicking": ("Взлом замков", ["lockpicking"]),
    "sharpening": ("Заточка", ["swordsharping", "sharpening"]),
    "corpse": ("Трупы и переноска", ["corpse", "corpse1", "corpse2", "deathbody"]),
    "cast": ("Литьё и ковка", ["cast", "casting", "mold"]),
    "cover": ("Укрытия", ["cover"]),
    "crouched": ("Присев", ["crouched", "crouch"]),
    "ladder": ("Лазание", ["ladder", "climb", "stairs"]),
    "siege": ("Осада", ["siege", "palisade", "barricade", "trebuchet"]),
    "camp": ("Лагерь", ["camp", "firewood", "campfire"]),
    "getup": ("Встаёт и садится", ["getup", "standup", "sitdown", "laydown", "wakeup"]),
    "corpse_": ("Мёртвые позы", ["dead", "laydown"]),
    # передвижение
    "walk": ("Ходьба", ["walk"]),
    "run": ("Бег", ["run", "sprint"]),
    "jump": ("Прыжки", ["jump"]),
    "idle": ("Ожидание", ["idle", "idle01", "idle02", "idle03"]),
    "horse": ("Верхом", ["horse", "horserider", "rider"]),
    "turn": ("Повороты", ["turn", "turns", "bigturns"]),
    # быт
    "sitting": ("Сидя", ["sitting", "sit"]),
    "door": ("Двери", ["door"]),
    "waiting": ("Ожидание", ["waiting"]),
    "leaning": ("Опирается", ["leaning", "lean", "leans01", "leans02"]),
    "gate": ("Ворота", ["gate"]),
    "beggar": ("Нищие", ["beggar"]),
    # повседневные
    "behavior": ("Бытовые действия", ["behavior"]),
    "dead": ("Мёртвые", ["dead", "corpse"]),
    "reading": ("Чтение", ["reading", "read", "book"]),
}

# ------------------------------------------------------------------ утилиты
PART_WORDS = {
    "in": "начало", "out": "завершение", "loop": "цикл", "var": "вариант",
    "idle": "ожидание", "stand": "стоя", "sitting": "сидя", "sit": "сидя",
    "walk": "ходьба", "run": "бег", "left": "слева", "right": "справа",
    "male": "мужская", "female": "женская", "over": "поверх",
}


def tokens(clip):
    return [t for t in re.split(r"[_\s]+", clip.lower()) if t]


def phrase(word):
    """«ходьба» -> «Ходьба» (первое слово названия)"""
    return word[:1].upper() + word[1:] if word else word


# слова, которые в названии звучат канцелярски: уводим в детали
SOFT = {"боевая", "диалоговая", "сюжетная", "обычная", "общая", "простая",
        "нейтральная", "расслабленная", "базовая", "одиночная"}

# если название начинается с профессии — дальше идёт глагол
VERB_HEAD = {"лесоруб", "пекарь", "каменщик", "плотник", "кузнец", "бронник",
             "конюх", "трактирщик", "аптекарь", "писарь", "портной",
             "кожевник", "сапожник", "возчик", "фермер", "углежог",
             "стражник", "солдат", "нищий", "монах", "священник",
             "покупатель", "торговец", "рыбак", "охотник", "палач",
             "мельник", "староста", "судья", "писец", "лекарь"}


def build_title(clip):
    """Русское название из имени клипа.

    Возвращает (заголовок, детали) — второе уходит в карточку.
    """
    ts = tokens(clip)
    ru, det = [], []
    for i, t in enumerate(ts):
        if t in TECH:
            kind, label = TECH[t]
            if t in DETAIL_ONLY or kind in ("tech", "side", "sex", "hand",
                                            "zone", "stance", "dir",
                                            "wclass", "weapon", "mode"):
                if label:
                    det.append(label)
                continue
            if label:
                ru.append(label)
            continue
        if t in RU:
            word = RU[t]
            if t in DETAIL_ONLY:
                det.append(word)
            else:
                ru.append(word)
            continue
        if is_code(t) or re.fullmatch(r"\d+", t):
            continue
        det.append(t)

    # убираем повторы, сохраняя порядок
    seen, uniq = set(), []
    for w in ru:
        if w not in seen:
            seen.add(w)
            uniq.append(w)

    # служебные слова вроде «боевая» / «диалоговая» не должны занимать
    # первое место: название и так лежит в разделе «Бой» или «Диалоги»
    soft = [w for w in uniq if w in SOFT]
    main = [w for w in uniq if w not in SOFT]
    det = soft + det
    if not main:
        main = uniq[:1]
    main = main[:3]

    title = ", ".join(main)
    # «Лесоруб, собирает ветка» -> «Лесоруб собирает ветку»
    if main and main[0].lower() in VERB_HEAD and len(main) > 1:
        rest = [VERB.get(w, w) for w in main[1:]]
        rest = [ACC.get(w, w) for w in rest]
        title = main[0] + " " + " ".join(rest)
    return title, det


def category_key(row):
    return (row[3] or "Прочее").strip()


def sub_key(cat, clip):
    """Подкатегория внутри большой группы."""
    ts = set(tokens(clip))
    best = None
    best_len = 0
    for key, (label, toks) in SUB_GROUPS.items():
        for tk in toks:
            if tk in ts and len(tk) > best_len:
                best, best_len = key, len(tk)
    return best or "other"


def main():
    rows = read_sheet(os.path.join(WIKI, XLSX), SHEET_ALL)
    head, data = rows[0], rows[1:]
    print("анимаций в файле:", len(data))

    fam = {}
    for r in read_sheet(os.path.join(WIKI, XLSX), SHEET_FAM)[1:]:
        if len(r) >= 3:
            fam[r[0]] = r[2]

    items, cats, subs = [], {}, {}
    cat_names = {}
    for r in data:
        if len(r) < 9:
            continue
        num, clip, desc, cat, phase, family, fragment, trust, src = r[:9]
        cat = category_key(r)
        cat_names[cat] = cat_names.get(cat, 0) + 1

        title, details = build_title(clip)
        if not title:
            title = desc.split(";")[0].split(":")[0].strip() or "Анимация"

        it = {
            "id": clip,
            "num": int(num) if num.isdigit() else 0,
            "ru": title,
            "clip": clip,
            "desc": desc,
            "cat": cat,
            "phase": phase,
            "fam": family,
            "famRu": fam.get(family, family),
            "frag": fragment,
            "trust": trust,
            "det": details[:14],
        }
        items.append(it)

        if cat in BIG:
            sk = sub_key(cat, clip)
        else:
            sk = "all"
        it["sub"] = sk
        subs.setdefault(cat, {})
        s = subs[cat].setdefault(sk, {"key": sk, "label": "", "count": 0})
        s["count"] += 1

    # подписи подкатегорий
    for cat, d in subs.items():
        for sk, s in d.items():
            if sk == "all":
                s["label"] = "Все анимации"
            elif sk in SUB_GROUPS:
                s["label"] = SUB_GROUPS[sk][0]
            else:
                s["label"] = "Прочие"

    # категории: порядок — по количеству, крупные вперёд
    order = sorted(cat_names, key=lambda c: (c == "Прочее", -cat_names[c]))
    cat_list = []
    for i, name in enumerate(order):
        cat_list.append({
            "id": i, "ru": name, "count": cat_names[name],
            "icon": CAT_ICON.get(name, "📦"),
        })
        for it in items:
            if it["cat"] == name:
                it["catId"] = i

    # из подкатегорий убираем «all» для больших, оставляем как «Все»
    out_subs = {}
    for name, cid in [(c["ru"], c["id"]) for c in cat_list]:
        lst = sorted(subs.get(name, {}).values(), key=lambda s: -s["count"])
        lst = [s for s in lst if s["key"] != "all"] or lst
        out_subs[str(cid)] = lst

    os.makedirs(REF, exist_ok=True)
    for fname, obj in (("anim_items.json", items), ("anim_cats.json", cat_list),
                       ("anim_subs.json", out_subs)):
        with open(os.path.join(REF, fname), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(os.path.join(REF, "anim_items.json")) / 1024 / 1024
    print(f"готово: {len(items)} анимаций, {len(cat_list)} категорий, "
          f"{sum(len(v) for v in out_subs.values())} подкатегорий, {size:.2f} МБ")


if __name__ == "__main__":
    main()
