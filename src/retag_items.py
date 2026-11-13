#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пересмотр таксономии базы предметов KCD2.

Задача: подразделить предметы подробнее и убрать технические «свалки»
(«Псевдонимы предметов», «Разные предметы», «Женская одежда», «Тестовые»).

Основа классификации — внутреннее имя меша (оно в датасете стабильно:
shield_kite_*, Cap22_m05_A, HoseSeparate01_*, recipe_*, bsmt_pommel*),
плюс слот «Одежда (база)», тип записи и русская подпись.

Результат: data/reference/{items,cats,subs}_tagged.json
Запуск: python3 src/retag_items.py
"""
import json
import os
import re
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")


# ---------------------------------------------------------------- категории
# (id, русское название, английское имя исходного типа, иконка)
CATS = [
    (0, "Алхимия и травы", "Herb", "🌿"),
    (1, "Боеприпасы", "Ammo", "🏹"),
    (2, "Доспехи и одежда", "Armor", "🛡️"),
    (3, "Оружие ближнего боя", "MeleeWeapon", "⚔️"),
    (4, "Оружие дальнего боя", "MissileWeapon", "🔫"),
    (5, "Еда и напитки", "Food", "🍖"),
    (6, "Книги и документы", "Document", "📜"),
    (7, "Кости и бляхи", "Die", "🎲"),
    (8, "Материалы", "CraftingMaterial", "🔨"),
    (9, "Трофеи и ценности", "Loot", "💎"),
    (10, "Ключи", "Key", "🗝️"),
    (11, "Инструменты и ремонт", "Tool", "🔧"),
    (12, "Прочее", "MiscItem", "🎒"),
]
CAT_RU = {c[0]: c[1] for c in CATS}

# id -> [(ключ, подпись)] — порядок отображения
SUBS = {
    0: [("fresh", "Свежие травы"), ("dried", "Сушёные травы"),
        ("poison", "Яды"), ("perfume", "Духи"), ("potion", "Зелья"),
        ("base", "Алхимические основы")],

    1: [("arrows", "Стрелы"), ("bolts", "Болты"), ("shot", "Дробь и пули"),
        ("other", "Прочее")],

    2: [("helmet", "Шлемы"),
        ("cap", "Шапки и шляпы"),
        ("headwrap", "Чепцы и платки"),
        ("wreath", "Венки и обручи"),
        ("coif", "Койфы и батваты"),
        ("hood", "Капюшоны"),
        ("cuirass", "Кирасы и панцири"),
        ("brigandine", "Бригантины"),
        ("mail", "Кольчуги и хауберки"),
        ("gambeson", "Гамбезоны и пурпуэны"),
        ("waffenrock", "Ваффенроки"),
        ("cotehardie", "Котарди и платья"),
        ("tunic", "Рубахи и туники"),
        ("coat", "Куртки и дублеты"),
        ("caftan", "Кафтаны и жупаны"),
        ("habit", "Рясы"),
        ("legarmor", "Защита ног"),
        ("hose", "Штаны и чулки"),
        ("ankleboots", "Ботинки"),
        ("kneeboots", "Сапоги"),
        ("shoes", "Туфли"),
        ("gloves", "Перчатки"),
        ("mittens", "Рукавицы"),
        ("armplate", "Наручи и налокотники"),
        ("collar", "Бармицы и воротники"),
        ("spurs", "Шпоры"),
        ("spectacles", "Очки"),
        ("jewelry", "Украшения"),
        ("belt", "Пояса"),
        ("pouch", "Сумки и кошели"),
        ("horse", "Конская упряжь"),
        ("other", "Прочее")],

    3: [("sword", "Мечи"), ("sabre", "Сабля"), ("dagger", "Кинжалы и тесаки"),
        ("axe", "Топоры"), ("mace", "Булавы и молоты"),
        ("polearm", "Древковое"),
        ("shield", "Щиты"), ("banner", "Знамёна"), ("other", "Прочее")],

    4: [("bow", "Луки"), ("crossbow", "Арбалеты"), ("gun", "Огнестрел"),
        ("other", "Прочее")],

    5: [("drinks", "Напитки"), ("meal", "Готовые блюда"),
        ("cooked", "Варёное и жареное"), ("smoked", "Копчёное"),
        ("dried", "Вяленое и сушёное"), ("fruitveg", "Овощи, фрукты, грибы"),
        ("bread", "Хлеб и выпечка"),
        ("cheese", "Сыры и молочное"),
        ("meat", "Мясо и рыба"), ("grain", "Крупы и приправы"),
        ("other", "Прочее")],

    6: [("skill", "Книги навыков"), ("lore", "Книги и дневники"),
        ("story", "Повести и стихи"),
        ("recipe", "Рецепты и чертежи"), ("letter", "Письма и записки"),
        ("ledger", "Договоры и бумаги"),
        ("map", "Карты"), ("other", "Прочее")],

    7: [("die", "Кости"), ("badge", "Бляхи")],

    8: [("guard", "Гарды"), ("pommel", "Навершия"),
         ("ingot", "Металлы и руда"),
         ("horseshoe", "Подковы"),
         ("skin", "Шкуры и кожа"),
         ("feather", "Перья и пух"),
         ("organ", "Животные части"),
         ("herbmat", "Растительное сырьё"),
         ("other", "Прочее")],

    9: [("skin", "Шкуры и меха"), ("trophy", "Трофеи и части тел"),
         ("rosary", "Чётки"),
         ("relic", "Реликвии и кресты"), ("valuable", "Ценности"),
         ("sundry", "Бытовые безделушки")],

    10: [("key", "Ключи"), ("lockpick", "Отмычки")],

    11: [("tool", "Инструменты"), ("kit", "Наборы для ремонта"),
         ("care", "Мыло и повязки")],

    12: [("household", "Утварь и посуда"), ("cloth", "Ткани"),
         ("ingredient", "Приправы и специи"), ("junk", "Мусор"),
         ("quest", "Сюжетные предметы"), ("other", "Разное")],
}


# ------------------------------------------------------- слот по базе меша
SLOT_PREFIX = [
    ("Waffenrock", "waffenrock"),
    ("HoseSeparate", "hose"), ("HoseJoined", "hose"), ("HoseLoose", "hose"),
    ("HoseFront", "hose"), ("HoseBack", "hose"),
    ("Coat", "coat"), ("Caftan", "caftan"), ("Habit", "habit"),
    ("Hood", "hood"),
    ("Gambeson", "gambeson"), ("Pourpoint", "gambeson"), ("Aketon", "gambeson"),
    ("CoifMail", "coif"), ("CoifLarge", "coif"), ("CoifSmall", "coif"), ("Coif", "coif"),
    ("Necklace", "jewelry"), ("Ring", "jewelry"), ("Pendant", "jewelry"),
    ("Brooch", "jewelry"), ("Earring", "jewelry"),
    ("TunicShort", "tunic"), ("TunicLong", "tunic"), ("Dress", "tunic"),
    ("Smock", "tunic"), ("Cotehardie", "cotehardie"), ("Surcote", "cotehardie"),
    ("LegsPadded", "legarmor"), ("LegsChain", "legarmor"),
    ("LegsPlate", "legarmor"), ("LegsBrigandine", "legarmor"),
    ("BootsKnee", "kneeboots"), ("BootsAnkle", "ankleboots"),
    ("Boot", "kneeboots"), ("Shoes", "shoes"), ("Shoe", "shoes"),
    ("Glove", "gloves"), ("Gauntlet", "gloves"), ("Mitten", "mittens"),
    ("HandWrap", "gloves"),
    ("Belt", "belt"), ("Pouch", "pouch"),
    ("Brigandine", "brigandine"), ("Cuirass", "cuirass"),
    ("Mail", "mail"), ("Chainmail", "mail"), ("Hauberk", "mail"),
    ("Collar", "collar"), ("Sleeves", "armplate"), ("ArmPlate", "armplate"),
    ("ArmBrigandine", "armplate"), ("Couter", "armplate"),
    ("Spurs", "spurs"), ("Spectacles", "spectacles"),
    ("Saddle", "horse"), ("Bridle", "horse"), ("Caparison", "horse"),
    ("Chanfron", "horse"), ("HorseShoe", "horse"), ("Harness", "horse"),
    ("KettleHat", "helmet"), ("Bascinet", "helmet"), ("SkullCap", "helmet"),
    ("Helmet", "helmet"), ("Sallet", "helmet"), ("Hounskull", "helmet"),
    ("Cap", "cap"), ("Hat", "cap"),
    ("Veil", "headwrap"), ("Wimple", "headwrap"),
    ("Bonnet", "headwrap"), ("CoifCap", "headwrap"),
    ("HairDecor", "wreath"), ("Wreath", "wreath"), ("Bandeau", "wreath"),
]

# подкатегория по внутреннему имени, когда слот не помог
NAME_PATTERNS = [
    (r"^(shield|pavise|heater|kite)", "shield"),
    (r"^(longsword|shortsword|huntingsword|sabre|saber|sword|broadsword"
     r"|falchion|basilard)", "sword"),
    (r"^(axe|waraxe|battleaxe|halberd|polearm|bardiche|glaive|spear"
     r"|voulge|guisarm|pitchfork|poleaxe|morgenstern)", "polearm"),
    (r"^(mace|hammer|flail|club|morningstar)", "mace"),
    (r"^(dagger|baselard)", "dagger"),
    (r"^(bow)", "bow"),
    (r"^(crossbow)", "crossbow"),
    (r"^(gun|rifle|pistol)", "gun"),
    (r"^(arrow)", "arrows"),
    (r"^(bolt)", "bolts"),
    (r"^(shot|ball|pellet)", "shot"),
]

WEAPON_WORDS = [
    (r"меч", "sword"), (r"сабл", "sabre"), (r"кинжал|тесак", "dagger"),
    (r"топор|секир", "axe"), (r"булав|молот|кистен|палиц", "mace"),
    (r"копь|древк|алебард|бердыш|рогатин", "polearm"),
    (r"щит|павез", "shield"), (r"лук\b", "bow"), (r"арбалет", "crossbow"),
    (r"ручниц|пищал", "gun"),
]


# --------------------------------------------------------------- утилиты
def base_of(it):
    return ((it.get("extra") or {}).get("Одежда (база)") or "").strip()


def bare_name(it):
    """Внутреннее имя без префикса женской вещи."""
    nm = it.get("name") or ""
    return nm[2:] if nm.startswith("F_") else nm


def hay(it):
    """Низкорегистровая строка для ключевых слов."""
    return " ".join([
        (it.get("ru") or ""), (it.get("en") or ""),
        bare_name(it), (it.get("icon") or ""),
    ]).lower()


def slot_by_base(base):
    if not base:
        return None
    b = base[2:] if base.startswith("F_") else base
    for pre, slot in SLOT_PREFIX:
        if b.startswith(pre):
            return slot
    return None


def slot_by_name(it):
    nm = bare_name(it)
    for pre, slot in SLOT_PREFIX:
        if nm.startswith(pre):
            return slot
    return None


def match_prefix(it, pairs):
    nm = bare_name(it).lower()
    for pre, sub in pairs:
        if nm.startswith(pre):
            return sub
    return None


# ------------------------------------------------------------------ броня
# ключевые слова по русской/английской подписи (фолбэк, когда слот не найден)
ARMOR_WORDS = [
    (r"шлем|helm|bascinet|бацинет|шапель|цервельер|капалин|kettle", "helmet"),
    (r"капюшон|hood", "hood"),
    (r"койф|батват|coif|aketon", "coif"),
    (r"перчат|glove|gauntlet", "gloves"),
    (r"рукавиц|mitten", "mittens"),
    (r"понож|наколенник|legs|leg armour|leg armor", "legarmor"),
    (r"штан|чулки|hose|бриджи|шоссы|braies", "hose"),
    (r"наруч|налокотник|couter|arm plate|vambrace", "armplate"),
    (r"бармица|воротник|collar", "collar"),
    (r"сапог|boot", "kneeboots"),
    (r"ботинк|ankle", "ankleboots"),
    (r"туфл|башмак|обув|shoe|slipper", "shoes"),
    (r"пояс|ремень|belt", "belt"),
    (r"сумк|кошел|pouch", "pouch"),
    (r"кольц|перстень|ожерел|амулет|ring|necklace|amulet|earring", "jewelry"),
    (r"седло|уздечк|попон|подков|saddle|bridle|caparison|horseshoe", "horse"),
    (r"ваффенрок|waffenrock", "waffenrock"),
    (r"котарди|платье|cotehardie|dress", "cotehardie"),
    (r"сорочк|smock|хитон", "tunic"),
    (r"кафтан|жупан|caftan|zupan", "caftan"),
    (r"ряса|habit", "habit"),
    (r"дублет|камзол|куртк|жакет|doublet|jacket|coat", "coat"),
    (r"рубах|туник|tunic|shirt", "tunic"),
    (r"гамбез|пурпуэн|gambeson|pourpoint", "gambeson"),
    (r"кирас|панцирь|cuirass", "cuirass"),
    (r"бригантин|brigandine", "brigandine"),
    (r"кольчуг|хауберк|mail|hauberk", "mail"),
    (r"шапк|шляп|берет|колпак|cap\b|hat", "cap"),
    (r"платок|чепец|veil|wimple", "headwrap"),
    (r"венок|обруч|wreath|bandeau", "wreath"),
    (r"очки|spectacle", "spectacles"),
    (r"шпор|spurs", "spurs"),
]

# уточнения внутри крупных групп по внутреннему префиксу
REFINE_CAP = [
    ("veil", "headwrap"), ("bonnet", "headwrap"), ("wimple", "headwrap"),
    ("hairdecor", "wreath"), ("wreath", "wreath"), ("bandeau", "wreath"),
]
REFINE_BOOTS = [
    ("bootsknee", "kneeboots"), ("bootsankle", "ankleboots"),
    ("shoes", "shoes"), ("slipper", "shoes"),
]
REFINE_TUNIC = [
    ("cotehardie", "cotehardie"), ("surcote", "cotehardie"),
    ("dress", "cotehardie"), ("tunic", "tunic"),
]
REFINE_BODY = [
    ("cuirass", "cuirass"), ("brigandine", "brigandine"),
    ("mail", "mail"), ("hauberk", "mail"), ("chainmail", "mail"),
]
REFINE_GLOVES = [("mitten", "mittens"), ("handwrap", "gloves")]


def sub_armor(it):
    """Подкатегория внутри «Доспехов и одежды»."""
    nm = bare_name(it).lower()
    ru = (it.get("ru") or "").lower()
    en = (it.get("en") or "").lower()
    txt = ru + " " + en

    # шпоры и очки — не одежда по смыслу, но носимые аксессуары
    if nm.startswith("spurs") or re.search(r"шпор|spur", txt):
        return "spurs"
    if nm.startswith("spectacles") or re.search(r"очки|spectacle", txt):
        return "spectacles"

    s = slot_by_name(it) or slot_by_base(base_of(it))

    # уточнение широких слотов
    if s == "cap":
        r = match_prefix(it, REFINE_CAP)
        if r:
            return r
        return "cap"
    if s in ("kneeboots", "ankleboots", "shoes"):
        return match_prefix(it, REFINE_BOOTS) or s
    if s in ("tunic", "smock"):
        return match_prefix(it, REFINE_TUNIC) or "tunic"
    if s in ("cuirass", "brigandine", "mail"):
        return match_prefix(it, REFINE_BODY) or s
    if s == "gloves":
        return match_prefix(it, REFINE_GLOVES) or "gloves"
    if s == "coat":
        # «Habit» — рясы, «Caftan» — кафтаны; всё прочее — куртки
        return "coat"
    if s:
        return s

    # слот не определился — идём по ключевым словам
    pairs = ARMOR_WORDS
    for pat, slot in pairs:
        if re.search(pat, txt):
            return slot
    if "torso" in nm:
        return "coat"
    return "other"


# ----------------------------------------------------------------- оружие
def sub_weapon(it):
    nm = bare_name(it).lower()
    txt = hay(it)

    # тип оружия важнее состояния: сломанный меч остаётся мечом
    if nm.startswith(("shield", "pavise", "heater", "kite")):
        return "shield"
    if nm.startswith(("longsword", "shortsword", "huntingsword", "sword",
                      "broadsword", "falchion", "basilard", "sabre", "saber")):
        return "sabre" if nm.startswith(("sabre", "saber")) else "sword"
    if nm.startswith(("dagger", "baselard", "knife", "dirk", "huntingknife")):
        return "dagger"
    if nm.startswith(("axe", "waraxe", "battleaxe")):
        return "axe"
    if nm.startswith(("halberd", "polearm", "bardiche", "glaive", "spear",
                      "voulge", "guisarm", "pitchfork", "poleaxe", "morgenstern")):
        return "polearm"
    if nm.startswith(("mace", "warhammer", "hammer", "flail", "club", "morningstar")):
        return "mace"
    # знамёна и факелы — не оружие в узком смысле
    if nm.startswith(("torch", "flag", "svancara", "standard", "banner")):
        return "banner"
    for pat, slot in NAME_PATTERNS:
        if re.match(pat, nm):
            return "sabre" if slot == "sword" and "sabr" in nm else slot
    # тип может стоять не в начале имени (kovaniSymbolSermirny_longSwordGuild_broken)
    for word, slot in (("sword", "sword"), ("sabr", "sabre"), ("dagger", "dagger"),
                       ("club", "mace"), ("mace", "mace"), ("warhammer", "mace"),
                       ("halberd", "polearm"), ("polearm", "polearm"),
                       ("battleaxe", "axe"), ("waraxe", "axe"), ("axe", "axe")):
        if word in nm:
            return slot
    if re.search(r"flag|banner|standard|torch|svancara", nm):
        return "banner"
    if re.search(r"хоругв|знамя|знамён|знамен|факел|banner|standard|torch", txt):
        return "banner"
    if re.search(r"сабл|sabre", txt):
        return "sabre"
    for pat, slot in WEAPON_WORDS:
        if re.search(pat, (it.get("ru") or "").lower()):
            return slot
    return "other"


def sub_bow(it):
    """Подкатегория для дальнобойного оружия (записи старой категории 14)."""
    nm = bare_name(it).lower()
    txt = hay(it)
    if "crossbow" in nm:
        return "crossbow"
    if "bow" in nm:
        return "bow"
    if re.search(r"арбалет", txt):
        return "crossbow"
    if re.search(r"лук\b|bow", txt):
        return "bow"
    if re.search(r"ручниц|пищал|gun|rifle", txt):
        return "gun"
    return "other"


def sub_ammo(it):
    nm = bare_name(it).lower()
    ru = (it.get("ru") or "").lower()
    if "arrow" in nm or "стрела" in ru or "стрел" in ru:
        return "arrows"
    if "bolt" in nm or "болт" in ru:
        return "bolts"
    if "shot" in nm or "ball" in nm or "pellet" in nm or "дроб" in ru or "пуля" in ru:
        return "shot"
    return "other"


# -------------------------------------------------------------------- еда
MEAT = (r"мяс|окорок|колбас|сало|бекон|ветчин|почк|сердц|печен|печён|язык|"
        r"огузок|вырезк|оковал|шкварк|куриц|курятин|курин|птиц|гус[ьи]|утк|"
        r"chicken|goose|duck|crackl|rump|tenderloin|loin|"
        r"желудок|потрох|ребр|стейк|beef|pork|venison|meat|kidney|heart|"
        r"liver|tongue|stomach|sausage|bacon|ham\b|ribs|steak|goulash|"
        r"рыб|сельд|карп|щук|форел|окун|лещ|судак|fish|carp|pike|trout|"
        r"herring|eel|perch|bass|bream|черв|worm")
FRUITVEG = (r"яблок|груш|слив|вишн|капуст|морков|лук\b|чеснок|реп[аы]|свекл|"
            r"огур|гриб|ягод|малин|ежевик|брусник|apple|pear|plum|cherry|"
            r"cabbage|carrot|onion|garlic|turnip|beet|cucumber|mushroom|berr|"
            r"peas|горох|тыкв|pumpkin|grape|виноград|арбуз|watermelon|"
            r"персик|peach|орех|nuts?|петрушк|parsnip|хрен|horseradish")
BREAD = (r"хлеб|булк|багет|бейгл|лепёшк|лепешк|пирог|тесто|крендел|"
         r"bread|bagel|bun\b|cake|dough|pastry|pretzel")
CHEESE = r"сыр|творог|молок|сметан|яйц|cheese|milk|curd|butter|cream|egg\b"
GRAIN = r"мука|мёд|\bмед\b|круп|крупа|овёс|овес|пшено|соль|перец|специ|пряност|flour|grain|salt|pepper|spice"
MEAL = (r"суп|бульон|похлёбк|похлебк|рагу|каш[аи]\b|пир\b|запекан|жаркое|"
        r"stew|soup|porridge|roast|dish|broth")


def sub_food(it):
    ru = (it.get("ru") or "").lower()
    nm = bare_name(it).lower()
    ex = it.get("extra") or {}

    if ru.startswith(("вино", "пиво", "медовух", "сидр", "спиртн", "водк",
                      "ликёр", "ликер", "браг", "напит", "самогон")) or \
            re.search(r"вино|пиво|медовух|спиртн|самогон|wine|beer|mead|"
                      r"alcohol|spirit", ru + " " + nm):
        return "drinks"
    if ex.get("Содержание алкоголя"):
        return "drinks"
    if re.search(r"питьевая вода|^вода\b|\bвода\b|water|бурдюк|waterskin",
                 ru + " " + nm):
        return "drinks"
    if "вачек" in ru or "mash" in nm:
        return "meal"
    if ru.startswith(("сушён", "сушен")):
        return "dried"
    if ru.startswith(("копчён", "копчен")):
        return "smoked"
    if ru.startswith(("вялен", "сушён", "сушен")) or "dried" in nm:
        return "dried"
    if ru.startswith(("варён", "варен", "жарен", "печён", "печен", "приготов",
                      "тушён", "тушен")):
        return "cooked"
    if re.search(MEAL, ru):
        return "meal"
    if re.search(MEAT, ru + " " + nm):
        return "meat"
    if re.search(BREAD, ru + " " + nm):
        return "bread"
    if re.search(CHEESE, ru + " " + nm):
        return "cheese"
    if re.search(FRUITVEG, ru + " " + nm):
        return "fruitveg"
    if re.search(GRAIN, ru + " " + nm):
        return "grain"
    return "other"


# ------------------------------------------------------------------ книги
def sub_book(it):
    ru = (it.get("ru") or "").lower()
    en = (it.get("en") or "").lower()
    nm = bare_name(it).lower()

    if nm.startswith(("skillbook", "stealth_skillbook")):
        return "skill"
    if nm.startswith(("recipe", "sketch")):
        return "recipe"
    if nm.startswith(("lorebook", "kuttenberglorebook")):
        return "lore"
    if nm.startswith("map"):
        return "map"
    if nm.startswith("letter"):
        return "letter"
    if re.search(r"карта|план\b|map", ru + " " + en) or "map" in nm:
        return "map"
    if re.search(r"рецепт|чертёж|чертеж|recipe|sketch|blueprint", ru + " " + en):
        return "recipe"
    if re.search(r"письмо|записк|грамот|послани|letter|note", ru + " " + en):
        return "letter"
    if re.search(r"договор|расписк|долгов|вексел|указ|приказ|грамота|"
                 r"охранная|contract|iou|bond|edict|order|safe conduct",
                 ru + " " + en):
        return "ledger"
    if re.search(r"дневник|записк|журнал|diary|journal|log\b", ru + " " + en):
        return "lore"
    if re.search(r"стих|поэм|песн|вирш|баллад|сказани|повесть|poem|poetry|"
                 r"song|verse|tale|ballad", ru + " " + en):
        return "story"
    if re.search(r"искусств|навык|умени|skill|basics|основы", ru + " " + en):
        return "skill"
    if re.search(r"список|перечень|опись|учет|учёт|счет|счёт|реестр|"
                 r"list|registry|accounts|ledger|inventory|предложени", ru + " " + en):
        return "ledger"
    if re.search(r"книг|манускрипт|трактат|хроник|летопис|жизнеописан|"
                 r"энциклопеди|пергамент|дневник|сочинени|book|manuscript|"
                 r"chronicle|treatise|parchment|diary", ru + " " + en):
        return "lore"
    if re.search(r"^ius |livre|пир мертвец|предложени|offer|hermes|"
                 r"действие|состав|тайна|мудрость|герб|о составе|about",
                 ru + " " + en):
        return "lore"
    return "other"


# -------------------------------------------------------------- материалы
def sub_material(it):
    """Материалы: только записи исходной категории «Материалы»."""
    nm = bare_name(it).lower()
    txt = " ".join([(it.get("ru") or "").lower(), (it.get("en") or "").lower()])

    if nm.startswith("bsmt_"):
        body = nm[5:]
        if body.startswith("pommel"):
            return "pommel"
        if body.startswith("guard"):
            return "guard"
        if re.match(r"steel|iron|copper|tin|bronze|brass|silver|gold", body):
            return "ingot"
        return "other"
    if re.search(r"\bподков|horseshoe", txt):
        return "horseshoe"
    if re.search(r"\bгард|\bguard", txt):
        return "guard"
    if re.search(r"наверши|pommel", txt):
        return "pommel"
    if re.search(r"\bсталь|\bжелезо|\bмедь|\bбронза|\bолово|слиток|\bруда|"
                 r"\bsteel|\biron|\bcopper|ingot|\bore\b|bronze", txt):
        return "ingot"
    if re.search(r"древесин|дерев|\bwood|timber|plank", txt):
        return "other"
    if re.search(r"\bперо|\bперья|\bпух|feather|plume", txt):
        return "feather"
    if re.search(r"шкур|\bкож|\bskin|pelt|\bhide\b|\bмех", txt):
        return "skin"
    if re.search(r"\bклык|рога?\b|коготь|\bзуб|кость|fang|claw|horn|tooth|"
                 r"bone|безоар|bezoar|смалец|потрох|желчь", txt):
        return "organ"
    if re.search(r"гриб|мухомор|трав|цвет|корен|ягод|mushroom|\bherb|"
                 r"flower|root|паутин|cobweb|ладан|olibanum", txt):
        return "herbmat"
    return "other"


# ------------------------------------------------- не-ключи / не-ценности
def sub_misc(it):
    """Предметы из старых «Ключей», «Добычи» и «Разного»: разложить по смыслу."""
    low = (it.get("ru") or "").lower()
    en = (it.get("en") or "").lower()
    nm = bare_name(it).lower()
    txt = low + " " + en
    ex = it.get("extra") or {}

    # заведомо технические записи
    if nm.startswith("test") or ex.get("Пометка") == "тест":
        return 12, "junk"

    # ключи и отмычки
    if re.search(r"ключ|отмычк|\bkey\b|lockpick", txt + " " + nm):
        return 10, ("lockpick" if re.search(r"отмычк|lockpick", txt + nm) else "key")

    # травы
    if nm.startswith("herb") or re.search(r"трав[аыу]|herb", txt):
        return 0, ("dried" if low.startswith(("сушён", "сушен")) else "fresh")
    if re.search(r"яд\b|яд[ыа]|poison", txt):
        return 0, "poison"

    # еда и напитки
    if re.search(r"вино|пиво|water|вода|молок|milk|мёд|мед\b|honey|"
                 r"самогон|hooch|сливовиц", txt):
        return 5, sub_food(it)
    if re.search(r"форел|окун|карп|щук|trout|perch|carp|pike|рыб|fish|"
                 r"мяс|meat|жаркое", txt):
        return 5, sub_food(it)

    # экипировка, попавшая в «псевдонимы»
    g = guess_equipment(it, loose=True)
    if g:
        return g
    a = sub_armor(it)
    if a != "other":
        return 2, a

    # шкуры, трофеи, ценности
    if re.search(r"\bперья\b|\bперо\b|feather", txt):
        return 8, "feather"
    if re.search(r"шкур|кож[аи]\b|hide|pelt|\bskin\b|мех|fur", txt):
        return 9, "skin"
    if re.search(r"трофей|клык|рога?\b|коготь|trophy|fang|horn|claw|"
                 r"кость|bone|череп|skull|волос|палец|зуб|хвост|tail|"
                 r"\bухо\b|\bуши\b|\bear\b|потрох|орган|внутренност|"
                 r"entrails", txt):
        return 9, "trophy"
    if re.search(r"крест|распят|cross|crucifix|реликви|reliquary|мощи|"
                 r"икон|icon", txt):
        return 9, "relic"
    if re.search(r"четки|чётк|rosary", txt):
        return 9, "rosary"
    if re.search(r"кольц|перстень|ожерел|бусы|бусин|брош|заколк|"
                 r"ring|necklace|earring|brooch|bead|pin\b", txt):
        return 9, "valuable"
    if re.search(r"кубок|чаш|монет|медальон|ценност|статуэтк|"
                 r"chalice|coin|medallion|valuable", txt):
        return 9, "valuable"

    # ножи: столовые — утварь, прочие — кинжалы/тесаки
    if re.search(r"нож|knife|тесак", txt):
        if re.search(r"кухонн|столов|eating|kitchen|ложк|вилк", txt):
            return 12, "household"
        return 3, "dagger"
    if re.search(r"вилк|ложк|fork|spoon", txt):
        return 12, "household"

    # инструменты и ремонт
    if re.search(r"набор\b|repairkit", txt + " " + nm):
        return 11, "kit"
    if re.search(r"мыло|повязк|soap|bandage", txt + " " + nm):
        return 11, "care"
    if re.search(r"молот|клещ|наковал|пил[аы]|шило|игл|лопат|кирк|"
                 r"веретено|hammer|tongs|anvil|saw|awl|needle|shovel|"
                 r"pickaxe|spindle|tool", txt):
        return 11, "tool"

    # книги и документы
    if re.search(r"письмо|документ|записк|страница|грамота|приказ|указ|"
                 r"letter|document|note|page|order", txt):
        return 6, ("ledger" if re.search(r"грамота|приказ|указ|order", txt)
                   else "letter")
    if re.search(r"карта|map", txt):
        return 6, "map"

    return sub_misc_extra(it)


# оружие/броня по внутреннему имени внутри «псевдонимов» и «разного»
GUESS_ARMOR = [
    ("kettlehat", "helmet"), ("bascinet", "helmet"), ("skullcap", "helmet"),
    ("helmet", "helmet"), ("mail", "mail"), ("hauberk", "mail"),
    ("brigandine", "brigandine"), ("cuirass", "cuirass"), ("coif", "coif"),
    ("hosejoined", "hose"), ("hoseseparate", "hose"), ("hose", "hose"),
    ("gambeson", "gambeson"), ("pourpoint", "gambeson"), ("aketon", "gambeson"),
    ("waffenrock", "waffenrock"), ("coat", "coat"), ("tunic", "tunic"),
    ("dress", "cotehardie"), ("cotehardie", "cotehardie"),
    ("boot", "kneeboots"), ("shoe", "shoes"),
    ("glove", "gloves"), ("gauntlet", "gloves"), ("sleeve", "armplate"),
    ("legs", "legarmor"), ("hood", "hood"), ("cap", "cap"), ("hat", "cap"),
    ("belt", "belt"), ("pouch", "pouch"), ("spurs", "spurs"),
    ("collar", "collar"), ("chemise", "tunic"), ("shoe", "shoes"),
    ("braies", "hose"), ("purse", "pouch"), ("quilt", "coat"),
    ("spectacle", "spectacles"), ("bridle", "horse"), ("yoke", "horse"),
]
GUESS_WEAPON = [
    ("longsword", "sword"), ("shortsword", "sword"), ("sword", "sword"),
    ("sabre", "sabre"), ("dagger", "dagger"), ("axe", "axe"),
    ("mace", "mace"), ("hammer", "mace"), ("halberd", "polearm"),
    ("shield", "shield"), ("bow", "bow"), ("crossbow", "crossbow"),
]


def guess_equipment(it, loose=False):
    nm = bare_name(it).lower()
    txt = hay(it)
    if not loose and not re.search(r"^(alias|loot|prepadeni|kovani|sesivani|"
                                   r"budovani|stare|poi|zbrane)", nm):
        return None
    if re.search(r"sword|меч|сабл|sabr|кінжал|кинжал|dagger|axe|топор|mace|булав", txt):
        for pre, sub in GUESS_WEAPON:
            if pre in nm or pre in txt:
                return 3, sub
        return 3, "other"
    if re.search(r"shield|щит", txt):
        return 3, "shield"
    if re.search(r"bow|лук\b|crossbow|арбалет", txt):
        return 4, "bow"
    for pre, sub in GUESS_ARMOR:
        if nm.startswith(pre) or pre in nm:
            return 2, sub
    return None


# --------------------------------------------------- «прочее» по смыслу
JUNK = (r"мусор|хлам|объедк|остатки|обрывок|тряпк|порван|сломан|сломанн|ржав|"
        r"использован|пуст(ая|ой)? (склянка|бутыл)|дохл|garbage|trash|"
        r"rubbish|junk|broken|ruined|rotten|scrap")
HOUSEHOLD = (r"кувшин|тарелк|чашк|кружк|горшок|котел|котёл|ложк|вилк|"
             r"светильник|свеч|лампад|поднос|бочк|ведро|корзин|сундук|"
             r"jug|plate|cup|mug|pot|cauldron|spoon|fork|lamp|candle|"
             r"tray|barrel|bucket|basket|chest")
CLOTH_MAT = (r"холст|сатин|парча|шёлк|шелк|сукно|полотно|ткань|ткан|"
             r"cloth|linen|satin|brocade|silk|wool|fabric")
INGREDIENT = (r"соль|перец|специ|пряност|мёд|мед\b|уксус|масло|"
              r"salt|pepper|spice|honey|vinegar|oil")
# явные следы квеста: «для кого-то», «от кого-то», имена NPC в названии
QUEST_STRONG = (r" для | от |письмо|грамот|приказ|приказы|указ|документ|"
                r"доказательств|улики|снаряжение|припасы|подношени|"
                r"возмещени|наследств|печать|знак |оберег|амулет|"
                r"lute|лютн|дудочк|флейт|астроляб|игрушечн|"
                r"family|heirloom|evidence|proof|orders?\b")
# мифические/сюжетные артефакты
MYTHIC = (r"гром-камень|гром камень|thunderstone|яйцо василиска|"
          r"basilisk|волшебн|magic|чудесн")


def sub_misc_extra(it):
    """Остаток «Прочего»: раскидать по смыслу, мусор — отдельно."""
    low = (it.get("ru") or "").lower()
    nm = bare_name(it).lower()
    txt = low + " " + nm

    if re.search(r"мешок|sack|bundle|свёрток|связк|бурдюк|waterskin", txt):
        if re.search(r"мук|соль|круп|flour|salt|grain", txt):
            return 12, "ingredient"
        if re.search(r"гвозд|nail", txt):
            return 8, "other"
        if re.search(r"уголь|charcoal|coal", txt):
            return 8, "other"
        if re.search(r"руд|ore|серебр|silver", txt):
            return 8, "ingot"
        if re.search(r"мусор|хлам|trash|junk|garbage", txt):
            return 12, "junk"
        if re.search(r"ручниц|оружи|weapon|припас|снаряжен|supplies", txt):
            return 12, "quest"
        return 12, "household"
    if re.search(r"бумаг|пергамент|parchment", txt):
        return 6, "other"
    if re.search(r"\bзуб|череп|skull|\bкость|bone|\bволос|\bпалец|\bухо\b|"
                 r"\bear\b|потрох|внутренност|нутро|intestin", txt):
        return 9, "trophy"
    if re.search(r"останки|remains|скелет|skeleton", txt):
        return 9, "trophy"
    if re.search(r"букет|цвет|flower|майск|шест|maypole|рисунок|drawing|"
                 r"помет|dropping|личные вещи|пожитк|belongings|stuff", txt):
        return 12, "quest"
    if re.search(r"мрамор|статуэтк|статуя|statue", txt):
        return 9, "valuable"
    if re.search(r"мазь|ointment|salve|смалец", txt):
        return 11, "care"
    if re.search(JUNK, txt):
        return 12, "junk"
    if re.search(r"\bухо\b|\bуши\b|\bear\b|потрох|внутренност|"
                 r"\bхвост\b|\btail\b|\bволос", txt):
        return 9, "trophy"
    if re.search(r"фарш|pulp", txt):
        return 5, "meat"
    if re.search(r"яйц|egg\b", txt):
        return 5, "cheese"
    f = sub_food(it)
    if f != "other":
        return 5, f
    if re.search(HOUSEHOLD, txt):
        return 12, "household"
    if re.search(r"снадобь|зелье|отвар|potion|remedy", txt):
        return 0, "potion"
    if re.search(r"флакон|flask|склянк|бут��л|bottle", txt):
        return 12, "household"
    if re.search(r"заколк|\bpin\b|булавк|brooch", txt):
        return 9, "jewel"
    if re.search(CLOTH_MAT, txt):
        return 12, "cloth"
    if re.search(INGREDIENT, txt):
        return 12, "ingredient"
    if re.search(r"сломанный (меч|топор)|обломок|broken (sword|axe)|weapon stub",
                 txt):
        return 8, "other"
    if re.search(r"гвозд|nail|скоб|креп|веревк|rope|фитил|wick|порох|"
                 r"gunpowder|уголь|charcoal|кора|bark|деготь|tar\b|квасц|alum|"
                 r"монет|coin", txt):
        return 8, "other"
    if re.search(r"чернил|ink|краск|paint|пигмент|dye", txt):
        return 12, "cloth"
    if re.search(r"сера|sulphur|sulfur|дегот|дёгот|tar\b|смол|resin|"
                 r"воск|wax|квасц|alum|порох|gunpowder|уголь|charcoal|"
                 r"кора|bark|флакон|glass", txt):
        return 8, "other"
    if re.search(r"серебр|золот|руда|ore|слиток|ingot", txt):
        return 8, "ingot"
    if re.search(QUEST_STRONG, low + " " + (it.get("en") or "").lower()):
        return 12, "quest"
    if re.search(MYTHIC, txt):
        return 12, "quest"
    return 12, "other"


# карта старых категорий -> новая
def retag(it):
    c, s = it["cat"], it["sub"]
    nm = bare_name(it).lower()
    low = (it.get("ru") or "").lower()

    # служебные/тестовые записи не должны попадать в игровые разделы
    if it.get("src") == "test" or nm.startswith("test"):
        return 12, "junk"

    if c == 0:                       # алхимические основы
        if re.search(r"спирт|spirit", low + " " + nm):
            return 0, "base"
        if re.search(r"масло|oil", low + " " + nm):
            return 0, "base"
        return 5, sub_food(it)        # вино/вода — в напитки
    if c == 1:
        return 1, sub_ammo(it)
    if c in (2, 8, 10, 18):          # броня, шлемы, капюшоны, пояса
        if c == 18:
            return 2, ("belt" if "belt" in nm else "pouch")
        return 2, sub_armor(it)
    if c == 12:
        return 3, sub_weapon(it)
    if c in (7, 17):                 # еда, яды
        if c == 17:
            return 0, "poison"
        return 5, sub_food(it)
    if c == 15:                      # духи, наборы, мыло
        if s == "perfume" or re.search(r"духи|perfume", low + " " + nm):
            return 0, "perfume"
        if s == "repair" or re.search(r"набор|repairkit", low + " " + nm):
            return 11, "kit"
        return 11, "care"
    if c == 9:
        return 0, ("dried" if low.startswith(("сушён", "сушен")) else "fresh")
    if c == 6:
        return 6, sub_book(it)
    if c in (4, 5):
        return 7, ("badge" if c == 4 else "die")
    if c == 3:
        return 8, sub_material(it)
    if c == 11 or c == 13:
        return sub_misc(it)
    if c == 14:                      # дальнобойное: луки, арбалеты, ручницы
        if nm.startswith(("gun", "rifle", "pistol")):
            return 4, "gun"
        if "bow" in nm and "crossbow" not in nm:
            return 4, "bow"
        if "crossbow" in nm:
            return 4, "crossbow"
        sub = sub_bow(it)
        return 4, sub
    return 12, "other"


# --------------------------------------------------- названия для пустых
RU_FIX = {
    "Mittens": "Рукавицы",
    "Scatter shot": "Дробь разброса",
    "": "Безымянный предмет",
    "Tin badge of goddess Fortuna": "Оловянная бляха богини Фортуны",
    "Silver badge of goddess Fortuna": "Серебряная бляха богини Фортуны",
    "Golden badge of goddess Fortuna": "Золотая бляха богини Фортуны",
    "A strange poem": "Странное стихотворение",
    "Bloody knife": "Окровавленный нож",
    "Weapon stub": "Обломок оружия",
    "St. Anthony's standard": "Хоругвь Святого Антония",
    "Torch": "Факел",
    "Noble's spurs": "Панские шпоры",
    "Knight's spurs": "Шпоры рыцаря",
    "Hungarian spurs": "Венгерские шпоры",
    "Rowel spurs": "Шпоры с колесиками",
    "Spectacles": "Очки",
    "Parler's spectacles": "Очки Парлера",
    "Gnarly's club": "Дубинка",
    "Tyrol brocade cotehardie": "Тирольское парчовое котарди",
    "Cast silver": "Литого серебра слиток",
    "Zikmund's sausage": "Колбаса Сигизмунда",
    "Wallnut cake": "Ореховый пирог",
    "Chef's specialty": "Особое блюдо повара",
    "Homemade blade": "Самодельный клинок",
    "Halved pavise": "Разрубленная павеза",
    "Order cloak": "Плащ ордена",
    "Scatter shot": "Дробь разброса",
}
RU_BY_NAME = {
    "CapPainter_m01": "Шапка живописца",
    "TorsoPainter_m01": "Торс живописца",
    "PourpointDevil01_mNoDagger": "Пурпуэн дьявола",
    "trafficCone": "Подозрительный вачек",
    "zachranaPtacka_die_trojak": "Игральная кость тройки",
    "pocestny_bookPageRhyme": "Страница с рифмой",
    "Poi_indianaJonesPoem": "Странное стихотворение",
    "alias_prepadeniVlasskehoDvora_chefsSpecial": "Особое блюдо повара",
}

# убрать лишние пробелы/битые кавычки в подписях
def clean_ru(s):
    s = (s or "").strip()
    s = s.replace('\\"', '"').replace("  ", " ")
    return s


def fill_names(items):
    fixed = 0
    for it in items:
        ru = clean_ru(it.get("ru"))
        if not ru or ru.startswith("—"):
            cand = None
            if it.get("name") in RU_BY_NAME:
                cand = RU_BY_NAME[it["name"]]
            elif it.get("icon") in RU_BY_NAME:
                cand = RU_BY_NAME[it["icon"]]
            elif it.get("en") in RU_FIX:
                cand = RU_FIX[it["en"]]
            elif (it.get("en") or "").startswith("Podezřelý"):
                cand = "Подозрительный вачек"
            elif (it.get("en") or "").startswith("Mittens"):
                cand = "Рукавицы"
            elif (it.get("en") or "").startswith("Tin badge"):
                cand = "Оловянная бляха"
            elif (it.get("en") or "").startswith("Silver badge"):
                cand = "Серебряная бляха"
            elif (it.get("en") or "").startswith("Golden badge"):
                cand = "Золотая бляха"
            elif not it.get("en"):
                cand = "Безымянный предмет"
            if cand:
                ru = cand
                fixed += 1
        it["ru"] = clean_ru(ru) or "Безымянный предмет"
    return fixed


def main():
    items = json.load(open(os.path.join(REF, "items.json"), encoding="utf-8"))
    fixed_names = fill_names(items)

    for it in items:
        new_c, new_s = retag(it)
        it["cat"] = new_c
        it["sub"] = new_s

    sub_map = {cid: OrderedDict(SUBS[cid]) for cid in SUBS}
    for it in items:
        it["subLabel"] = sub_map.get(it["cat"], {}).get(it["sub"], "Прочее")
        it["female"] = bool((it.get("name") or "").startswith("F_"))

    cnt = Counter(it["cat"] for it in items)
    cats_out = [{"id": cid, "ru": ru, "en": en, "count": cnt[cid], "icon": ic}
                for cid, ru, en, ic in CATS if cnt.get(cid)]

    subs_out = {}
    for cid in sorted({it["cat"] for it in items}):
        cnt2 = Counter(it["sub"] for it in items if it["cat"] == cid)
        subs_out[str(cid)] = [{"key": k, "label": lab, "count": cnt2[k]}
                              for k, lab in SUBS.get(cid, []) if cnt2.get(k)]

    for name, obj in (("items_tagged.json", items), ("cats_tagged.json", cats_out),
                      ("subs_tagged.json", subs_out)):
        json.dump(obj, open(os.path.join(REF, name), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))

    print(f"готово: {len(items)} предметов, {len(cats_out)} категорий, "
          f"{sum(len(v) for v in subs_out.values())} подкатегорий")
    print(f"исправлено пустых названий: {fixed_names}")
    for cid, ru, _, _ in CATS:
        if cnt.get(cid):
            print(f"  {ru:26} {cnt[cid]:5}")
            for r in subs_out[str(cid)]:
                print(f"      {r['label']:30} {r['count']}")


if __name__ == "__main__":
    main()
