# -*- coding: utf-8 -*-
"""Сборка базы предметов KCD2 для сайта «Богемия RP».

Читает выгрузку игровых данных (kcd2004_item.json + text_ui_dict.json),
локализует названия на русский и формирует компактный JSON для сайта.

Запуск:  python3 src/build_items.py
Вход:    data/raw/item.json, data/raw/text_ui_dict.json
Выход:   data/items.json
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from grammar_ru import translate_name, capitalize  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "items.json")

# Категории: тип в игре -> (id, русское название, подкатегории)
CATEGORY_MAP = {
    "MeleeWeapon": ("weapons", "Оружие ближнего боя"),
    "MissileWeapon": ("ranged", "Дальнобойное оружие"),
    "Ammo": ("ammo", "Боеприпасы"),
    "Armor": ("armor", "Доспехи и одежда"),
    "Helmet": ("armor", "Доспехи и одежда"),
    "Hood": ("armor", "Доспехи и одежда"),
    "Food": ("food", "Еда и напитки"),
    "Herb": ("herbs", "Травы"),
    "Poison": ("potions", "Зелья и яды"),
    "Ointment": ("potions", "Зелья и яды"),
    "AlchemyBase": ("potions", "Зелья и яды"),
    "Document": ("books", "Книги и документы"),
    "MiscItem": ("misc", "Разное"),
    "CraftingMaterial": ("materials", "Материалы"),
    "Die": ("dice", "Кости"),
    "DiceBadge": ("dice", "Кости"),
    "QuickSlotContainer": ("armor", "Доспехи и одежда"),
    "ItemAlias": ("misc", "Разное"),
    "PickableItem": ("misc", "Разное"),
    "NPCTool": (None, None),
}

# Подтипы внутри «Доспехи и одежда» по слоту
SLOT_RU = {
    "cap": ("head", "Голова"),
    "coif": ("head", "Голова"),
    "hood": ("head", "Голова"),
    "collar": ("head", "Голова"),
    "ring": ("jewelry", "Украшения"),
    "necklace": ("jewelry", "Украшения"),
    "dagger": ("dagger", "Кинжалы"),
    "belt": ("belt", "Пояса"),
    "plate": ("body", "Корпус"),
    "coat": ("body", "Корпус"),
    "cloth": ("body", "Корпус"),
    "chainmail": ("body", "Корпус"),
    "gloves": ("hands", "Руки"),
    "sleeves": ("hands", "Руки"),
    "trousers": ("legs", "Ноги"),
    "legArmor": ("legs", "Ноги"),
    "boot": ("legs", "Ноги"),
    "spur": ("legs", "Ноги"),
    "pouch": ("pouch", "Сумки"),
    "horseHead": ("horse", "Лошадь"),
    "horseTorso": ("horse", "Лошадь"),
    "horseSaddle": ("horse", "Лошадь"),
    "horseshoe": ("horse", "Лошадь"),
    "weaponMelee": ("melee", "Ближний бой"),
    "weaponRanged": ("range", "Стрелковое"),
    "shield": ("shield", "Щиты"),
}

WEAPON_SKILL_RU = {
    "sword": "Меч", "longsword": "Длинный меч", "sabre": "Сабля",
    "axe": "Топор", "mace": "Булава", "halberd": "Древковое",
    "dagger": "Кинжал", "bow": "Лук", "crossbowLight": "Лёгкий арбалет",
    "crossbowMedium": "Средний арбалет", "crossbowHeavy": "Тяжёлый арбалет",
    "shield": "Щит", "huntingSword": "Охотничий меч", "flail": "Кистень",
    "torch": "Факел", "unarmed": "Кулак", "rifle": "Ручница",
    "shieldBroken": "Щит", "undefined": "—",
}


SLOT_PATTERNS = [
    # (регулярка по Name/Clothing, подкатегория)
    (r"^(Hood|F_Hood|HoodOpen)", "hood"),
    (r"^(SkullCap|KettleHat|Bascinet|Hounskull|Sallet|Cap|F_Cap|F_Hat|Hat|Bonnet|Wimple|Veil|CoifCap)", "cap"),
    (r"^(Coif|CoifSmall|CoifLarge|CoifMail)", "coif"),
    (r"^(Collar)", "collar"),
    (r"^(Ring)", "ring"),
    (r"^(Necklace|Pendant)", "necklace"),
    (r"^(Belt)", "belt"),
    (r"^(Brigandine|Cuirass|Coat|Kastenbrust)", "plate"),
    (r"^(TunicShort|TunicLong|F_SimpleDress|F_Smock|LeatherApron|Dress)", "cloth"),
    (r"^(GambesonShort|GambesonLong|Caftan|Pourpoint|Aketon)", "cloth"),
    (r"^(MailShort|MailLong|Hauberk)", "chainmail"),
    (r"^(Gloves|Mitts)", "gloves"),
    (r"^(ArmBrigandine|ArmPlate|Couter)", "sleeves"),
    (r"^(HoseJoined|HoseLoose|HoseSeparate|LegsPadded|LegsChain)", "trousers"),
    (r"^(LegsBrigandine|LegsPlate|Poleyn)", "legArmor"),
    (r"^(Boot|Shoe|Shoes)", "boot"),
    (r"^(Spurs)", "spur"),
    (r"^(Pouch)", "pouch"),
    (r"^(Bridle|Chanfron|DrivingBit)", "horseHead"),
    (r"^(Caparison|Harness)", "horseTorso"),
    (r"^(Saddle)", "horseSaddle"),
    (r"^(HorseShoe)", "horseshoe"),
]


def _slot_from_name(it):
    """Определить слот экипировки по имени меша / иконке (Fallback)."""
    src = (it.get("Clothing") or it.get("Name") or "")
    icon = it.get("IconId") or ""
    for pat, slot in SLOT_PATTERNS:
        if re.match(pat, src):
            return slot
    for pat, slot in SLOT_PATTERNS:
        if re.match(pat, icon):
            return slot
    n = ((it.get("Name") or "") + " " + icon).lower()
    for kw, slot in (
        ("shield", "shield"), ("pavise", "shield"), ("chanfron", "horseHead"),
        ("bridle", "horseHead"), ("caparison", "horseTorso"),
        ("saddle", "horseSaddle"), ("horseshoe", "horseshoe"),
        ("waffenrock", "cloth"), ("spectacles", "jewelry"),
    ):
        if kw in n:
            return slot
    return ""


def num(v, default=None):
    if v is None or v == "":
        return default
    try:
        f = float(v)
        return int(f) if f == int(f) else round(f, 2)
    except (TypeError, ValueError):
        return default


def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", str(s))
    return re.sub(r"\s+", " ", s).strip()


def main():
    items_raw = json.load(open(os.path.join(RAW, "item.json"), encoding="utf-8"))["items"]
    ui = json.load(open(os.path.join(RAW, "text_ui_dict.json"), encoding="utf-8"))

    out = []
    seen = set()
    for it in items_raw:
        t = it.get("_type")
        cat = CATEGORY_MAP.get(t)
        if not cat or not cat[0]:
            continue
        cat_id, cat_name = cat

        uiname = it.get("UIName") or ""
        en = ui.get(uiname, [None])[0] if uiname in ui else None
        en = clean_text(en) if en else clean_text(it.get("Name", ""))
        if not en:
            continue

        if not en or re.fullmatch(r"[A-Za-z0-9_]+", en) and len(en) > 6 and not en.islower():
            # внутренний идентификатор, локализации нет
            continue
        ru = capitalize(translate_name(en))
        if not ru or re.fullmatch(r"[A-Za-z0-9_]+", ru):
            continue
        # убираем служебные префиксы
        ru = re.sub(r"^(?:ui_nm_|ui_in_)", "", ru)

        uid = it.get("Id") or ""
        name = it.get("Name") or ""
        key = uid or name
        if key in seen:
            continue
        seen.add(key)

        slot = it.get("UISlotName") or _slot_from_name(it)
        if t in ("MeleeWeapon", "MissileWeapon"):
            if slot == "shield":
                sub_id, sub_name = "shield", "Щиты"
            elif t == "MissileWeapon":
                sub_id, sub_name = "range", "Стрелковое"
            else:
                sub_id, sub_name = "melee", "Ближний бой"
        elif t == "Ammo":
            sub_id, sub_name = "ammo", "Боеприпасы"
        else:
            sub_id, sub_name = SLOT_RU.get(slot, ("other", "Прочее"))
            # слоты «Голова/Корпус/Ноги/Руки» есть только у брони и одежды;
            # у книг, разного и материалов они давали ложные подкатегории
            if cat_id != "armor" and sub_id in ("head", "body", "legs", "hands",
                                                "jewelry", "belt", "pouch", "horse"):
                sub_id, sub_name = "other", "Прочее"

        wt = it.get("WeaponTypeName") or ""
        rec = {
            "id": uid,
            "n": ru,                       # название
            "e": en,                       # английское название
            "c": cat_id,                   # категория
            "s": sub_id,                   # подкатегория
            "i": it.get("IconId") or "",   # иконка
            "w": num(it.get("Weight"), 0),
            "p": num(it.get("Price"), 0),
        }
        # характеристики
        st = {}
        for src, dst in (
            ("DefenseStab", "ds"), ("DefenseSlash", "dl"), ("DefenseSmash", "dm"),
            ("Attack", "a"), ("AttackStab", "ast"), ("AttackSlash", "asl"),
            ("AttackSmash", "asm"), ("StrReq", "sr"), ("AgiReq", "ar"),
            ("Charisma", "ch"), ("Noise", "no"), ("Visibility", "vi"),
            ("Conspicuousness", "co"), ("MaxQuality", "q"), ("MaxStatus", "du"),
        ):
            v = num(it.get(src))
            if v not in (None, 0):
                st[dst] = v
        if t in ("MeleeWeapon", "MissileWeapon") and wt:
            st["sk"] = WEAPON_SKILL_RU.get(wt, wt)
        if t in ("Food",):
            for src, dst in (("NutritionBenefit", "nut"), ("HealthBenefit", "hea"),
                             ("RefreshBenefit", "ref"), ("AlcoholContent", "alc")):
                v = num(it.get(src))
                if v not in (None, 0):
                    st[dst] = v
        if t == "Herb" and it.get("LatinName"):
            st["lat"] = clean_text(it["LatinName"])
        if t in ("Die",) and it.get("SideValues"):
            st["sv"] = clean_text(it["SideValues"])
            st["sw"] = clean_text(it.get("SideWeights", ""))
        if st:
            rec["a"] = st
        out.append(rec)

    out.sort(key=lambda r: (r["c"], r["s"], r["n"]))
    meta = {
        "count": len(out),
        "categories": CATEGORY_MAP,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"meta": {"count": len(out)}, "items": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"готово: {len(out)} предметов -> {OUT}")
    import collections
    print(collections.Counter(r["c"] for r in out).most_common())


if __name__ == "__main__":
    main()
