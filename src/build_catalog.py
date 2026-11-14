# -*- coding: utf-8 -*-
"""Сборка базы из выгрузки XML-таблиц KCD2 (wiki/KCD2_ITEMS_RESULTS.zip).

Источник — 07_ПРЕДМЕТЫ_ПОЛНЫЕ.json: 5 604 записи со всеми атрибутами
движка. Скрипт:

1. достаёт русское название (если его нет — придумывает понятное);
2. раскладывает предмет по категории и подкатегории;
3. переводит все характеристики на русский;
4. пишет data/reference/items_full.json, cats_full.json, subs_full.json.

Ключевая особенность: часть типов XML — техническая (Armor содержит ещё
и конскую упряжь, MeleeWeapon — щиты, NPCTool — невидимые объекты мира).
Поэтому подкатегория ставится по внутреннему имени меша и полю Class,
а тип XML используется только как подсказка.

Запуск: python3 src/build_catalog.py
"""
import json
import os
import re
import sys
import zipfile
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")
WIKI = os.path.join(ROOT, "wiki")
ZIP_NAME = "KCD2_ITEMS_RESULTS.zip"

sys.path.insert(0, HERE)
from item_fields import (  # noqa: E402
    FIELD_RU, GROUP_ORDER, GROUP_RU, HIDDEN,
    field_group, field_label, field_unit, format_value,
)

ICON_BASE = "https://inara.cz/data/kingdomcometwo/items/icons/"


# ---------------------------------------------------------------- категории
CATS = [
    (0, "Алхимия и травы", "🌿"),
    (1, "Боеприпасы", "🏹"),
    (2, "Доспехи и одежда", "🛡️"),
    (3, "Оружие ближнего боя", "⚔️"),
    (4, "Оружие дальнего боя", "🔫"),
    (5, "Конская упряжь", "🐎"),
    (6, "Еда и напитки", "🍖"),
    (7, "Книги и документы", "📜"),
    (8, "Кости и бляхи", "🎲"),
    (9, "Материалы", "🔨"),
    (10, "Трофеи и ценности", "💎"),
    (11, "Ключи и кошели", "🗝️"),
    (12, "Инструменты и ремонт", "🔧"),
    (13, "Бытовые предметы", "🏠"),
    (14, "Объекты мира", "🗺️"),
    (15, "Прочее", "🎒"),
]

SUBS = {
    0: [("fresh", "Свежие травы"), ("dried", "Сушёные травы"),
        ("poison", "Яды"), ("perfume", "Духи"), ("potion", "Снадобья"),
        ("base", "Алхимические основы")],

    1: [("arrows", "Стрелы"), ("bolts", "Болты"), ("shot", "Дробь и пули"),
        ("other", "Прочее")],

    2: [("helmet", "Шлемы"),
        ("coif", "Койфы и батваты"),
        ("cap", "Шапки и шляпы"),
        ("headwrap", "Чепцы и платки"),
        ("wreath", "Венки и обручи"),
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
        ("other", "Прочее")],

    3: [("sword", "Мечи"), ("sabre", "Сабля"), ("dagger", "Кинжалы и тесаки"),
        ("axe", "Топоры"), ("mace", "Булавы и молоты"),
        ("polearm", "Древковое"),
        ("shield", "Щиты"), ("banner", "Знамёна и факелы"),
        ("other", "Прочее")],

    4: [("bow", "Луки"), ("crossbow", "Арбалеты"), ("gun", "Огнестрел"),
        ("other", "Прочее")],

    5: [("saddle", "Сёдла"), ("caparison", "Попоны"),
        ("bridle", "Уздечки"), ("chanfron", "Шафроны"),
        ("harness", "Упряжь")],

    6: [("drinks", "Напитки"), ("meal", "Готовые блюда"),
        ("cooked", "Варёное и жареное"), ("smoked", "Копчёное"),
        ("dried", "Вяленое и сушёное"), ("fruitveg", "Овощи, фрукты, грибы"),
        ("bread", "Хлеб и выпечка"), ("cheese", "Сыры и молочное"),
        ("meat", "Мясо и рыба"), ("grain", "Крупы и приправы"),
        ("other", "Прочее")],

    7: [("skill", "Книги навыков"), ("lore", "Книги и дневники"),
        ("story", "Повести и стихи"), ("recipe", "Рецепты и чертежи"),
        ("letter", "Письма и записки"), ("ledger", "Договоры и бумаги"),
        ("map", "Карты"), ("other", "Прочее")],

    8: [("die", "Кости"), ("badge", "Бляхи")],

    9: [("guard", "Гарды"), ("pommel", "Навершия"),
        ("ingot", "Металлы и руда"), ("horseshoe", "Подковы"),
        ("skin", "Шкуры и кожа"), ("feather", "Перья и пух"),
        ("organ", "Животные части"), ("herbmat", "Растительное сырьё"),
        ("other", "Прочее")],

    10: [("skin", "Шкуры и меха"), ("trophy", "Трофеи и части тел"),
         ("rosary", "Чётки"), ("relic", "Реликвии и кресты"),
         ("valuable", "Ценности")],

    11: [("key", "Ключи"), ("lockpick", "Отмычки"), ("pouch", "Кошели"),
         ("keyring", "Связки ключей")],

    12: [("tool", "Инструменты"), ("kit", "Наборы для ремонта"),
         ("care", "Мыло и повязки")],

    13: [("household", "Утварь и посуда"), ("container", "Мешки и ёмкости"),
         ("cloth", "Ткани"), ("ingredient", "Приправы и специи")],

    14: [("tool", "Рабочие инструменты мира"), ("prop", "Декор и утварь"),
         ("weapon", "Оружие в мире"), ("other", "Прочее")],

    15: [("money", "Деньги"), ("quest", "Сюжетные предметы"),
         ("junk", "Мусор"), ("other", "Разное")],
}

CAT_ICON = {cid: ic for cid, _, ic in CATS}
CAT_RU = {cid: ru for cid, ru, _ in CATS}


# ------------------------------------------------------------------ утилиты
def attr(x, key, default=""):
    return ((x.get("attributes") or {}).get(key) or default)


def mesh_name(x):
    return attr(x, "Name")


def bare(x):
    n = mesh_name(x)
    return n[2:] if n.startswith("F_") else n


def txt(x):
    return " ".join([
        (x.get("name_ru") or ""), (x.get("name_en") or ""), bare(x),
    ]).lower()


def female(x):
    return mesh_name(x).startswith("F_")


# ------------------------------------------- конская упряжь (внутри Armor)
HORSE_PREFIX = [
    ("WarSaddle", "saddle"), ("NobleSaddle", "saddle"), ("BasicSaddle", "saddle"),
    ("EastSaddle", "saddle"), ("Saddle", "saddle"),
    ("NobleCaparison", "caparison"), ("PaddedCaparison", "caparison"),
    ("Caparison", "caparison"),
    ("WarChanfron", "chanfron"), ("Chanfron", "chanfron"),
    ("CartBridle", "bridle"), ("NomadBridle", "bridle"),
    ("BasicBridle", "bridle"), ("NobleBridle", "bridle"),
    ("EastBridle", "bridle"), ("Bridle", "bridle"),
    ("BasicHarness", "harness"), ("Harness", "harness"),
]


def horse_slot(x):
    n = bare(x)
    for pre, slot in HORSE_PREFIX:
        if n.startswith(pre):
            return slot
    low = txt(x)
    if re.search(r"\bседл", low):
        return "saddle"
    if re.search(r"попон|попона|полупопон", low):
        return "caparison"
    if re.search(r"уздечк|уздечка", low):
        return "bridle"
    if re.search(r"шафрон|шанфрон", low):
        return "chanfron"
    if re.search(r"упряжь", low):
        return "harness"
    return None


# --------------------------------------------------- броня и одежда (Armor)
ARMOR_PREFIX = [
    ("Waffenrock", "waffenrock"),
    ("HoseSeparate", "hose"), ("HoseJoined", "hose"), ("HoseLoose", "hose"),
    ("HoseFront", "hose"), ("HoseBack", "hose"),
    ("Cotehardie", "cotehardie"), ("Surcote", "cotehardie"),
    ("SimpleDress", "cotehardie"), ("Dress", "cotehardie"),
    ("Caftan", "caftan"),
    ("Habit", "habit"),
    ("Coat", "coat"),
    ("TunicShort", "tunic"), ("TunicLong", "tunic"), ("Tunic", "tunic"),
    ("Smock", "tunic"), ("Shirt", "tunic"),
    ("GambesonLong", "gambeson"), ("GambesonShort", "gambeson"),
    ("Gambeson", "gambeson"), ("Pourpoint", "gambeson"),
    ("BrigandineArm", "armplate"), ("Brigandine", "brigandine"),
    ("Cuirass", "cuirass"),
    ("MailLong", "mail"), ("MailShort", "mail"), ("Mail", "mail"),
    ("Hauberk", "mail"),
    ("CoifMail", "coif"), ("CoifLarge", "coif"), ("CoifSmall", "coif"),
    ("CoifCap", "headwrap"), ("Coif", "coif"),
    ("LegsPadded", "legarmor"), ("LegsChain", "legarmor"),
    ("LegsPlate", "legarmor"), ("LegsBrigandine", "legarmor"),
    ("BootsKnee", "kneeboots"), ("BootsAnkle", "ankleboots"),
    ("Boot", "kneeboots"), ("Shoes", "shoes"), ("Shoe", "shoes"),
    ("Glove", "gloves"), ("Gauntlet", "gloves"),
    ("Mitten", "mittens"), ("HandWrap", "gloves"),
    ("ArmPlate", "armplate"), ("ArmBrigandine", "armplate"),
    ("Sleeves", "armplate"), ("Couter", "armplate"),
    ("CollarChain", "collar"), ("CollarPadded", "collar"), ("Collar", "collar"),
    ("Belt", "belt"), ("Pouch", "pouch"),
    ("Spurs", "spurs"), ("Spectacles", "spectacles"),
    ("KettleHat", "helmet"), ("Bascinet", "helmet"), ("SkullCap", "helmet"),
    ("Helmet", "helmet"), ("Sallet", "helmet"), ("Hounskull", "helmet"),
    ("HairDecor", "wreath"), ("Wreath", "wreath"), ("Bandeau", "wreath"),
    ("Veil", "headwrap"), ("Wimple", "headwrap"), ("Bonnet", "headwrap"),
    ("Cap", "cap"), ("Hat", "cap"),
    ("Necklace", "jewelry"), ("Ring", "jewelry"), ("Pendant", "jewelry"),
    ("Brooch", "jewelry"), ("Earring", "jewelry"),
]

ARMOR_WORDS = [
    (r"шлем|bascinet|бацинет|шапель|цервельер|капалин|kettle", "helmet"),
    (r"койф|батват|coif", "coif"),
    (r"капюшон|hood", "hood"),
    (r"рукавиц|mitten", "mittens"),
    (r"перчат|glove|gauntlet", "gloves"),
    (r"понож|наколенник|leg armour|leg armor|legs", "legarmor"),
    (r"штан|чулки|hose|бриджи|шоссы|braies", "hose"),
    (r"наруч|налокотник|couter|arm plate|vambrace", "armplate"),
    (r"бармица|воротник|collar", "collar"),
    (r"сапог|boot", "kneeboots"),
    (r"ботинк|ankle", "ankleboots"),
    (r"туфл|башмак|обув|shoe|slipper", "shoes"),
    (r"пояс|ремень|belt", "belt"),
    (r"сумк|кошел|pouch", "pouch"),
    (r"кольц|перстень|ожерел|амулет|ring|necklace|amulet|earring", "jewelry"),
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
    (r"шапк|шляп|берет|колпак|шаперон|cap\b|hat", "cap"),
    (r"платок|чепец|veil|wimple", "headwrap"),
    (r"венок|обруч|wreath|bandeau", "wreath"),
    (r"очки|spectacle", "spectacles"),
    (r"шпор|spurs", "spurs"),
]


def armor_slot(x):
    n = bare(x)
    for pre, slot in ARMOR_PREFIX:
        if n.startswith(pre):
            return slot
    low = txt(x)
    for pat, slot in ARMOR_WORDS:
        if re.search(pat, low):
            return slot
    return None


# ------------------------------------------------------------- оружие (Class)
WEAPON_CLASS = {
    "0": "dagger", "1": "sword", "2": "sabre", "3": "axe", "4": "sword",
    "5": "mace", "7": "polearm", "8": "shield", "9": "bow", "10": "crossbow",
    "11": "banner", "13": "gun", "14": "crossbow", "15": "crossbow",
    "16": "dagger", "17": "shield",
}
WEAPON_WORDS = [
    (r"сабл", "sabre"), (r"кинжал|тесак|dagg", "dagger"),
    (r"топор|секир|axe", "axe"),
    (r"булав|молот|кистен|палиц|mace|hammer", "mace"),
    (r"копь|древк|алебард|бердыш|рогатин|вульж|polearm", "polearm"),
    (r"щит|павез|shield", "shield"),
    (r"лук\b|\bbow", "bow"),
    (r"арбалет|crossbow", "crossbow"),
    (r"ручниц|пищал|gun|rifle", "gun"),
    (r"меч|sword", "sword"),
    (r"знам|хоругв|факел|banner|torch", "banner"),
]


def weapon_slot(x, bow_only=False):
    n = bare(x).lower()
    if n.startswith(("shield", "pavise", "heater", "kite")):
        return "shield"
    if n.startswith(("torch", "flag", "svancara", "standard", "banner")):
        return "banner"
    if n.startswith(("longsword", "shortsword", "huntingsword", "sword",
                     "broadsword", "falchion", "basilard")):
        return "sword"
    if n.startswith(("sabre", "saber")):
        return "sabre"
    if n.startswith(("dagger", "knife", "dirk")):
        return "dagger"
    if n.startswith(("axe", "waraxe", "battleaxe")):
        return "axe"
    if n.startswith(("mace", "warhammer", "hammer", "flail", "club")):
        return "mace"
    if n.startswith(("halberd", "polearm", "bardiche", "glaive", "spear",
                     "voulge", "guisarm", "pitchfork", "poleaxe", "morgenstern")):
        return "polearm"

    cls = attr(x, "Class")
    if cls in WEAPON_CLASS:
        slot = WEAPON_CLASS[cls]
        if bow_only:
            return slot if slot in ("bow", "crossbow", "gun") else "other"
        return slot

    low = txt(x)
    for pat, slot in WEAPON_WORDS:
        if re.search(pat, low):
            if bow_only and slot not in ("bow", "crossbow", "gun"):
                continue
            return slot
    return "other"


# ---------------------------------------------------------------------- еда
MEAT = (r"мяс|окорок|колбас|сало|бекон|ветчин|почк|сердц|печен|печён|язык|"
        r"огузок|вырезк|оковал|шкварк|куриц|курятин|птиц|гус|утк|"
        r"chicken|goose|duck|crackl|rump|tenderloin|loin|beef|pork|venison|"
        r"kidney|heart|liver|tongue|stomach|sausage|bacon|ham\b|ribs|steak|"
        r"рыб|сельд|карп|щук|форел|окун|лещ|судак|рак\b|"
        r"fish|carp|pike|trout|herring|eel|perch|crayfish|черв|worm")
FRUITVEG = (r"яблок|груш|слив|вишн|капуст|морков|лук\b|чеснок|реп[аы]|свекл|"
            r"огур|гриб|ягод|малин|ежевик|брусник|apple|pear|plum|cherry|"
            r"cabbage|carrot|onion|garlic|turnip|beet|cucumber|mushroom|berr|"
            r"peas|горох|тыкв|pumpkin|grape|виноград|арбуз|watermelon|"
            r"персик|peach|орех|nut|петрушк|parsnip|хрен|horseradish|порей|leek")
BREAD = (r"хлеб|булк|багет|бейгл|лепёшк|лепешк|пирог|тесто|крендел|"
         r"bread|bagel|bun\b|cake|dough|pastry|pretzel")
CHEESE = r"сыр|творог|молок|сметан|яйц|cheese|milk|curd|butter|cream|egg\b"
GRAIN = r"мука|круп|соль|перец|специ|пряност|горчиц|гвоздик|flour|grain|salt|pepper|spice|mustard"
MEAL = (r"суп|бульон|похлёбк|похлебк|рагу|каш[аи]\b|запекан|жаркое|"
        r"stew|soup|porridge|roast|broth")


def food_slot(x):
    a = x["attributes"] or {}
    low = (x.get("name_ru") or "").lower()
    n = bare(x).lower()
    both = low + " " + n

    if re.search(r"вино|пиво|медовух|сидр|спиртн|водк|ликёр|ликер|браг|напит|"
                 r"самогон|сливовиц|water|вода|wine|beer|mead|alcohol|spirit", both):
        return "drinks"
    if a.get("AlcoholContent"):
        return "drinks"
    if low.startswith(("сушён", "сушен", "вялен")) or "dried" in n:
        return "dried"
    if low.startswith(("копчён", "копчен")) or "smoked" in n:
        return "smoked"
    if low.startswith(("варён", "варен", "жарен", "печён", "печен", "приготов",
                       "тушён", "тушен")):
        return "cooked"
    if re.search(MEAL, low):
        return "meal"
    if re.search(MEAT, both):
        return "meat"
    if re.search(BREAD, both):
        return "bread"
    if re.search(CHEESE, both):
        return "cheese"
    if re.search(FRUITVEG, both):
        return "fruitveg"
    if re.search(GRAIN, both):
        return "grain"

    # поле Type у еды: 0 овощи/фрукты, 2 мясо, 3 напитки, 5 мясо/рыба,
    # 6 овощи, 7 грибы, 8 выпечка, 9 молочное
    t = a.get("Type")
    if t == "0":
        return "fruitveg"
    if t in ("2", "5"):
        return "meat"
    if t == "6":
        return "fruitveg"
    if t == "7":
        return "fruitveg"
    if t == "8":
        return "bread"
    if t == "9":
        return "cheese"
    return "other"


# ------------------------------------------------------------------- книги
def book_slot(x):
    low = (x.get("name_ru") or "").lower()
    en = (x.get("name_en") or "").lower()
    n = bare(x).lower()
    both = low + " " + en

    if n.startswith("skillbook") or "skillbook" in n:
        return "skill"
    if n.startswith(("recipe", "sketch")):
        return "recipe"
    if n.startswith(("lorebook", "kuttenberglorebook")):
        return "lore"
    if n.startswith("map"):
        return "map"
    if n.startswith("letter"):
        return "letter"
    if re.search(r"карта|план\b|\bmap\b", both):
        return "map"
    if re.search(r"рецепт|чертёж|чертеж|recipe|sketch|blueprint", both):
        return "recipe"
    if re.search(r"письмо|записк|грамот|послани|letter|note", both):
        return "letter"
    if re.search(r"договор|расписк|долгов|вексел|указ|приказ|contract|iou|bond|edict|order", both):
        return "ledger"
    if re.search(r"список|перечень|опись|учет|учёт|счет|счёт|реестр|"
                 r"list|registry|accounts|ledger|inventory", both):
        return "ledger"
    if re.search(r"стих|поэм|песн|вирш|баллад|сказани|повесть|poem|poetry|"
                 r"song|verse|tale|ballad", both):
        return "story"
    if re.search(r"дневник|журнал|diary|journal", both):
        return "lore"
    if re.search(r"искусств|навык|умени|skill|basics|основы", both):
        return "skill"
    if re.search(r"книг|манускрипт|трактат|хроник|летопис|жизнеописан|"
                 r"энциклопеди|пергамент|сочинени|book|manuscript|"
                 r"chronicle|treatise|parchment", both):
        return "lore"

    # запасной вариант — поле Type у документов
    t = attr(x, "Type")
    return {"2": "recipe", "3": "skill", "4": "map"}.get(t, "other")


# ------------------------------------------------------------------ травы
def herb_slot(x):
    low = (x.get("name_ru") or "").lower()
    if low.startswith(("сушён", "сушен")) or "dried" in bare(x).lower():
        return "dried"
    return "fresh"


# ------------------------------------------------------------------- ключи
def misc_slot(x):
    """MiscItem: ключи, кошели, трофеи, утварь, мешки."""
    a = x["attributes"] or {}
    low = (x.get("name_ru") or "").lower()
    n = bare(x).lower()
    both = low + " " + (x.get("name_en") or "").lower() + " " + n
    t = a.get("Type")

    if t == "4" or re.search(r"ключ|отмычк|\bkey\b|lockpick", both):
        if re.search(r"отмычк|lockpick", both):
            return 11, "lockpick"
        if re.search(r"связк", both):
            return 11, "keyring"
        return 11, "key"
    if t == "1" or re.search(r"шкур|skín|hide|pelt|\bskin\b|перья|feather|мех|fur", both):
        if re.search(r"\bперья\b|\bперо\b|feather", both):
            return 9, "feather"
        return 10, "skin"
    if re.search(r"кошел|pouch|purse", both):
        return 11, "pouch"
    if re.search(r"трофей|клык|рога?\b|коготь|trophy|fang|horn|claw|"
                 r"кость|bone|череп|skull|волос|палец|зуб|хвост|tail|"
                 r"\bухо\b|\bear\b|потрох|внутренност|нутро|intestin", both):
        return 10, "trophy"
    if re.search(r"крест|распят|cross|crucifix|реликви|reliquary|мощи|икон|icon", both):
        return 10, "relic"
    if re.search(r"четки|чётк|rosary", both):
        return 10, "rosary"
    if re.search(r"кольц|перстень|ожерел|бусы|бусин|брош|заколк|"
                 r"ring|necklace|earring|brooch|bead", both):
        return 10, "valuable"
    if re.search(r"кубок|чаш|монет|медальон|ценност|статуэтк|"
                 r"chalice|coin|medallion|valuable", both):
        return 10, "valuable"
    if re.search(r"набор\b|repairkit|kit\b", both + " " + n):
        return 12, "kit"
    if re.search(r"мыло|повязк|soap|bandage", both + " " + n):
        return 12, "care"
    if re.search(r"молот|клещ|наковал|пил[аы]|шило|игл|лопат|кирк|"
                 r"веретено|hammer|tongs|anvil|saw|awl|needle|shovel|"
                 r"pickaxe|spindle|tool", both):
        return 12, "tool"
    if re.search(r"мешок|sack|bundle|свёрток|связк|бурдюк|waterskin|бочк|barrel", both):
        return 13, "container"
    if re.search(r"соль|перец|специ|пряност|мёд|мед\b|уксус|масло|горчиц|гвоздик|"
                 r"salt|pepper|spice|honey|vinegar|oil|mustard", both):
        return 13, "ingredient"
    if re.search(r"холст|сатин|парча|шёлк|шелк|сукно|полотно|ткань|ткан|"
                 r"cloth|linen|satin|brocade|silk|wool|fabric", both):
        return 13, "cloth"
    if re.search(r"кувшин|тарелк|чашк|кружк|горшок|котел|котёл|ложк|вилк|"
                 r"светильник|свеч|лампад|поднос|ведро|корзин|сундук|"
                 r"jug|plate|cup|mug|pot|cauldron|spoon|fork|lamp|candle|"
                 r"tray|bucket|basket|chest", both):
        return 13, "household"

    if t == "5":
        if re.search(r"деньг|монет|грош|money|coin", both):
            return 15, "money"
        return 13, "household"
    if t == "6":
        return 15, "junk"
    if re.search(r"мусор|хлам|объедк|остатки|обрывок|тряпк|порван|сломан|ржав|"
                 r"пуст.*(склянк|бутыл)|garbage|trash|junk|broken|ruined", both):
        return 15, "junk"
    if re.search(r"(для|от)\s+[А-ЯЁA-Z]|письмо|грамот|приказ|указ|документ|"
                 r"доказательств|улик|снаряжен|припас|подношен|возмещен|"
                 r"наследств|печать|оберег|амулет", low):
        return 15, "quest"
    return 15, "other"


def npc_slot(x):
    """NPCTool — невидимые объекты мира, которые держит или использует NPC."""
    n = bare(x).lower()
    if re.search(r"axe|sword|hammer|mace|dagger|club|bow|spear|shield|"
                 r"weapon|lute|torch", n):
        return "weapon"
    if re.search(r"ladder|sieve|stick|bowl|spoon|bucket|jug|pot|shovel|"
                 r"rake|hoe|basket|barrel|tub|rod|needle|kettle|pan\b", n):
        return "tool"
    return "prop"


# --------------------------------------------------------------- resolvers
def resolve(x):
    """Вернуть (категория, подкатегория) для записи."""
    t = x["xml_type"]
    n = bare(x).lower()

    # --- технические записи
    if n.startswith("test") or "combattest" in n or "autotest" in n:
        return 15, "junk"

    if t == "Armor":
        hs = horse_slot(x)
        if hs:
            return 5, hs
        slot = armor_slot(x)
        if slot:
            return 2, slot
        if n.startswith(("prop",)):
            return 14, "prop"
        return 2, "other"

    if t == "Helmet":
        return 2, "helmet"
    if t == "Hood":
        return 2, "hood"

    if t == "MeleeWeapon":
        return 3, weapon_slot(x)
    if t == "MissileWeapon":
        return 4, weapon_slot(x, bow_only=True) or "other"
    if t == "Ammo":
        if "bolt" in n:
            return 1, "bolts"
        if "arrow" in n:
            return 1, "arrows"
        if re.search(r"shot|ball|pellet", n):
            return 1, "shot"
        low = (x.get("name_ru") or "").lower()
        if "болт" in low:
            return 1, "bolts"
        if "стрел" in low:
            return 1, "arrows"
        if re.search(r"дроб|пуля", low):
            return 1, "shot"
        return 1, "other"

    if t == "Food":
        slot = food_slot(x)
        if slot == "drinks" and attr(x, "Type") == "1":
            return 0, "potion"
        return 6, slot

    if t == "Poison":
        return 0, "poison"
    if t == "Herb":
        return 0, herb_slot(x)
    if t == "AlchemyBase":
        return 0, "base"
    if t == "Ointment":
        ot = attr(x, "Type")
        if ot == "2" or re.search(r"духи|perfume", txt(x)):
            return 0, "perfume"
        if ot == "1":
            return 12, "kit"
        if re.search(r"мыло|повязк|soap|bandage", txt(x)):
            return 12, "care"
        return 0, "potion"

    if t == "Document":
        return 7, book_slot(x)
    if t == "Die":
        return 8, "die"
    if t == "DiceBadge":
        return 8, "badge"
    if t == "CraftingMaterial":
        return 9, material_slot(x)
    if t == "MiscItem":
        return misc_slot(x)
    if t == "Key":
        return 11, "key"
    if t == "KeyRing":
        return 11, "keyring"
    if t == "Money":
        return 15, "money"
    if t == "QuickSlotContainer":
        return 11, "pouch"
    if t == "ItemAlias":
        return 15, "quest"
    if t == "NPCTool":
        return 14, npc_slot(x)
    if t == "PickableItem":
        return 1 if re.search(r"pellet|ball", n) else 14, "other"
    if t == "Container":
        return 13, "container"

    return 15, "other"


def material_slot(x):
    n = bare(x).lower()
    both = (x.get("name_ru") or "").lower() + " " + (x.get("name_en") or "").lower()

    if n.startswith("bsmt_"):
        body = n[5:]
        if body.startswith("pommel"):
            return "pommel"
        if body.startswith("guard"):
            return "guard"
        if re.match(r"steel|iron|copper|tin|bronze|brass|silver|gold", body):
            return "ingot"
        return "other"
    if re.search(r"подков|horseshoe", both):
        return "horseshoe"
    if re.search(r"\bгард|\bguard", both):
        return "guard"
    if re.search(r"наверши|pommel", both):
        return "pommel"
    if re.search(r"\bсталь|\bжелезо|\bмедь|\bбронза|\bолово|слиток|\bруда|"
                 r"\bsteel|\biron|\bcopper|ingot|\bore\b|bronze", both):
        return "ingot"
    if re.search(r"\bперо|\bперья|\bпух|feather|plume", both):
        return "feather"
    if re.search(r"шкур|\bкож|\bskin|pelt|\bhide\b|\bмех", both):
        return "skin"
    if re.search(r"\bклык|рога?\b|коготь|\bзуб|кость|fang|claw|horn|tooth|"
                 r"bone|безоар|bezoar|смалец|потрох|желчь", both):
        return "organ"
    if re.search(r"гриб|трав|цвет|корен|ягод|mushroom|\bherb|flower|root|"
                 r"паутин|cobweb|ладан|olibanum", both):
        return "herbmat"
    return "other"


# ------------------------------------------------------------ название
NAME_BY_MESH = {
    "alchemyOil": "Масло",
    "alchemySpiritus": "Спирт",
    "alchemyWater": "Вода",
    "alchemyWine": "Вино",
    "money": "Гроши",
    "keyring": "Связка ключей",
    "loot_sackOfNails": "Мешок гвоздей",
    "crossbow_lever": "Рычаг арбалета",
    "crossbow_goat_foot": "Арбалетный ворот",
    "rifle_ramrod": "Шомпол",
    "rifle_ignition": "Запал ручницы",
    "powder_flask": "Пороховница",
    "pellet_broken": "Сломанная дробь",
    "ball_broken": "Сломанная пуля",
    "combattest_brokenshield": "Сломанный щит (тест)",
}

# слова для «безымянных» объектов мира — их нет в локализации,
# потому что игрок их никогда не видит в инвентаре
NPC_WORDS = [
    (r"ladder", "Лестница"), (r"sieve", "Сито"), (r"stick", "Палка"),
    (r"bowl", "Миска"), (r"bucket", "Ведро"), (r"shovel", "Лопата"),
    (r"rake", "Грабли"), (r"sarcophagus", "Саркофаг"),
    (r"skull", "Гора черепов"), (r"pestle", "Пестик"),
    (r"mortar", "Ступа"), (r"tongs", "Клещи"), (r"spindle", "Веретено"),
    (r"comb\b", "Гребень"), (r"lute", "Лютня"), (r"jug", "Кувшин"),
    (r"needle", "Игла"), (r"knife", "Нож"), (r"axe", "Топор"),
    (r"hammer", "Молот"), (r"hatchet", "Топорик"), (r"scoop", "Совок"),
    (r"basket", "Корзина"), (r"barrel", "Бочка"), (r"tub\b", "Кадка"),
    (r"board", "Доска"), (r"plank", "Доска"), (r"rope", "Верёвка"),
    (r"gate", "Створка ворот"), (r"latch", "Щеколда"), (r"ram\b", "Таран"),
    (r"frame", "Пяльцы"), (r"laundry", "Стирка"),
    (r"hen", "Курица"), (r"coal", "Уголь"), (r"hay", "Сено"),
    (r"pile", "Куча"), (r"stone", "Камень"), (r"bowl", "Миска"),
    (r"potion", "Снадобье"), (r"bread", "Хлеб"), (r"meat", "Мясо"),
    (r"bag", "Сумка"), (r"yoke", "Хомут"), (r"harness", "Упряжь"),
    (r"bridle", "Уздечка"), (r"saddle", "Се��ло"), (r"chanfron", "Шафрон"),
    (r"caparison", "Попона"), (r"scabbard", "Ножны"),
]

# заглушки локализации: в игре так называется «пустышка»
STUB_NAMES = {
    "a suspicious bag", "подозрительная сумка", "suspicious bag",
    "a suspicious sack", "подозрительный мешок",
}


# словарь «внутреннее слово -> русское», чтобы не показывать
# пользователю машинные имена вроде BascinetVisor02_m01_B3_closed
MESH_WORDS = [
    ("bascinetvisior", "Забрало бацинета"), ("bascinet_visior", "Забрало бацинета"),
    ("bascinetviso", "Забрало бацинета"), ("bascinet", "Бацинет"),
    ("kettlehat", "Шапель"), ("skullcap", "Тюбетейка"), ("helmet", "Шлем"),
    ("coif", "Койф"), ("brigandine", "Бригантина"), ("cuirass", "Кираса"),
    ("gambeson", "Гамбезон"), ("waffenrock", "Ваффенрок"),
    ("caparison", "Попона"), ("chanfron", "Шафрон"), ("saddle", "Седло"),
    ("bridle", "Уздечка"), ("harness", "Упряжь"), ("horseshoe", "Подкова"),
    ("gauntlet", "Латная рукавица"), ("glove", "Перчатка"),
    ("armbrigandine", "Бригантинный наруч"), ("armplate", "Наруч"),
    ("collar", "Воротник"), ("hood", "Капюшон"), ("veil", "Платок"),
    ("hose", "Штаны"), ("legs", "Поножи"), ("shoes", "Туфли"),
    ("boots", "Сапоги"), ("boot", "Сапог"), ("coat", "Куртка"),
    ("tunic", "Туника"), ("dress", "Платье"), ("cotehardie", "Котарди"),
    ("habit", "Ряса"), ("caftan", "Кафтан"), ("pourpoint", "Пурпуэн"),
    ("belt", "Пояс"), ("pouch", "Кошель"), ("spurs", "Шпоры"),
    ("spectacles", "Очки"), ("necklace", "Ожерелье"), ("ring", "Кольцо"),
    ("brooch", "Брошь"), ("wreath", "Венок"), ("hairdecor", "Обруч"),
    ("shield", "Щит"), ("pavise", "Павеза"), ("sword", "Меч"),
    ("dagger", "Кинжал"), ("sabre", "Сабля"), ("axe", "Топор"),
    ("mace", "Булава"), ("hammer", "Молот"), ("polearm", "Древковое"),
    ("crossbow", "Арбалет"), ("bow", "Лук"), ("arrow", "Стрела"),
    ("bolt", "Болт"), ("quiver", "Колчан"), ("tankard", "Кружка"),
    ("letter", "Письмо"), ("shackles", "Кандалы"), ("rod", "Удочка"),
    ("chisel", "Зубило"), ("piece", "Заготовка"),
    ("embroidery", "Вышивка"), ("helmet", "Шлем"),
]

STUB_ICONS = {"trafficcone", "replaceme"}


def mesh_label(n):
    """Внутреннее имя -> русская подпись по словарю корней."""
    low = n.lower()
    for root, ru in MESH_WORDS:
        if root in low:
            return ru
    return None


def pretty_mesh(n):
    """Внутреннее имя -> читаемая подпись: Cap01_mApprentice03 -> Cap 01 apprentice 03."""
    s2 = re.sub(r"^[a-z]+?_", "", n)          # отрезаем префикс-источник
    s2 = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s2)
    s2 = s2.replace("_", " ").strip()
    return s2[:1].upper() + s2[1:] if s2 else ""


def make_name(x):
    ru = (x.get("name_ru") or "").strip()
    en = (x.get("name_en") or "").strip()
    n = mesh_name(x)
    low = n.lower()

    # 1. нормальный перевод есть — берём его
    if ru and ru.lower() not in STUB_NAMES:
        return ru

    # 2. известные по внутреннему имени
    if n in NAME_BY_MESH:
        return NAME_BY_MESH[n]

    # 3. английское название, если оно осмысленное
    if en and en.lower() not in STUB_NAMES and not en.startswith("WWW"):
        return en

    # 4. объекты мира: тип по ключевому слову
    for pat, label in NPC_WORDS:
        if re.search(pat, low):
            return f"{label} (объект мира)"

    # 5. технический мусор
    if low.startswith(("test", "combattest")) or "viceslotovy" in low:
        return f"Тестовый предмет ({pretty_mesh(n) or n})"

    # 6. тип предмета по корню внутреннего имени
    label = mesh_label(n)
    if label:
        if "placeholder" in low:
            return f"{label} (заглушка)"
        return f"{label} (без названия в игре)"

    # 7. последний шанс — читаемое внутреннее имя
    pretty = pretty_mesh(n)
    if pretty:
        return f"{pretty} (в игре не назван)"
    return "Безымянный предмет"


# ----------------------------------------------------------- характеристики
HIDE_EXTRA = {"Id", "Name", "Class", "SubClass"}  # уже показаны отдельно


def build_extra(x):
    """Все характеристики предмета с русскими подписями и группами."""
    a = x["attributes"] or {}
    xt = (x.get("xml_type") or "").strip()
    out = []
    for key, raw in a.items():
        if key in HIDDEN or key in HIDE_EXTRA:
            continue
        val = format_value(key, raw, xt)
        if val == "":
            continue
        out.append({
            "k": field_label(key),
            "v": val,
            "u": field_unit(key),
            "g": field_group(key),
        })
    # стабильный порядок: по группам, внутри — как объявлено в FIELD_RU
    order = {g: i for i, g in enumerate(GROUP_ORDER)}
    out.sort(key=lambda r: (order.get(r["g"], 99), r["k"]))
    return out


def main():
    zpath = os.path.join(WIKI, ZIP_NAME)
    if not os.path.exists(zpath):
        raise SystemExit(f"нет архива: {zpath}")

    with zipfile.ZipFile(zpath) as z:
        raw = None
        for info in z.infolist():
            try:
                name = info.filename.encode("cp437").decode("cp1251")
            except Exception:
                name = info.filename
            if name.startswith("07_") and name.endswith(".json"):
                raw = z.read(info)
                break
        if raw is None:
            raise SystemExit("в архиве нет файла 07_ПРЕДМЕТЫ_ПОЛНЫЕ.json")

    src = json.loads(raw.decode("utf-8"))
    print(f"исходных записей: {len(src)}")

    items = []
    for x in src:
        cat, sub = resolve(x)
        a = x["attributes"] or {}
        icon = a.get("IconId") or ""
        items.append({
            "id": x["guid"],
            "ru": make_name(x),
            "en": (x.get("name_en") or "").strip(),
            "name": a.get("Name") or "",
            "cat": cat,
            "sub": sub,
            "icon": icon,
            "iconUrl": (ICON_BASE + icon.lower() + ".png") if icon else "",
            "price": _num(a.get("Price")),
            "weight": _num(a.get("Weight")),
            "female": female(x),
            "xmlType": x["xml_type"],
            "extra": build_extra(x),
            "sources": x.get("sources") or [],
        })

    # подписи
    sub_map = {cid: OrderedDict(SUBS[cid]) for cid in SUBS}
    for it in items:
        it["subLabel"] = sub_map.get(it["cat"], {}).get(it["sub"], "Прочее")

    cnt = Counter(it["cat"] for it in items)
    cats_out = [{"id": cid, "ru": ru, "icon": ic, "count": cnt[cid]}
                for cid, ru, ic in CATS if cnt.get(cid)]

    subs_out = {}
    for cid in sorted(cnt):
        c2 = Counter(it["sub"] for it in items if it["cat"] == cid)
        subs_out[str(cid)] = [{"key": k, "label": lab, "count": c2[k]}
                              for k, lab in SUBS.get(cid, []) if c2.get(k)]

    for name, obj in (("items_full.json", items), ("cats_full.json", cats_out),
                      ("subs_full.json", subs_out)):
        with open(os.path.join(REF, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(os.path.join(REF, "items_full.json")) / 1e6
    print(f"готово: {len(items)} предметов, {len(cats_out)} категорий, "
          f"{sum(len(v) for v in subs_out.values())} подкатегорий, {size:.2f} МБ")
    for cid, ru, _ in CATS:
        if cnt.get(cid):
            print(f"  {ru:24} {cnt[cid]:5}")
            for r in subs_out[str(cid)]:
                print(f"      {r['label']:30} {r['count']}")


def _num(v):
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else f


if __name__ == "__main__":
    main()
