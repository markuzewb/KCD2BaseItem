# -*- coding: utf-8 -*-
"""Русские названия игровых полей KCD2.

Внутри игры и в XML предметы хранят характеристики техническими именами
(AttackModSlash, StrReq, Conspicuousness...). Здесь каждое поле получает
понятную русскую подпись и группу, чтобы карточка предмета читалась
человеком, а не мододелом.
"""

# поле -> (русская подпись, единица, группа)
# группы: бой, защита, требования, общее, эффект, крафт, тех
FIELD_RU = {
    # --- общее
    "Weight": ("Вес", "кг", "общее"),
    "Price": ("Цена", "гроши", "общее"),
    "MaxQuality": ("Макс. качество", "", "общее"),
    "MaxStatus": ("Прочность", "", "общее"),
    "IsBreakable": ("Ломается", "", "общее"),
    "IsDivisible": ("Делится", "", "общее"),
    "IsQuestItem": ("Квестовый предмет", "", "общее"),
    "Rarity": ("Редкость", "", "общее"),
    "SocialClassId": ("Соц. класс", "", "общее"),
    "WealthLevel": ("Уровень богатства", "", "общее"),
    "Charisma": ("Харизма", "", "общее"),
    "Visibility": ("Видимость", "", "общее"),
    "Conspicuousness": ("Заметность", "", "общее"),
    "Noise": ("Шум", "", "общее"),
    "FadeCoef": ("Коэф. затухания", "", "тех"),
    "VisibilityCoef": ("Коэф. видимости", "", "тех"),
    "DecayTime": ("Время порчи", "ч", "общее"),
    "LengthInGameHours": ("Длительность", "игровых ч", "эффект"),
    "DisplayInShop": ("Показывать в магазине", "", "общее"),
    "PickpocketInPouch": ("Можно украсть из сумки", "", "общее"),

    # --- бой
    "Attack": ("Урон", "", "бой"),
    "AttackStab": ("Урон колющий", "", "бой"),
    "AttackSlash": ("Урон рубящий", "", "бой"),
    "AttackSmash": ("Урон дробящий", "", "бой"),
    "AttackModStab": ("Мод. урона колющего", "", "бой"),
    "AttackModSlash": ("Мод. урона рубящего", "", "бой"),
    "AttackModSmash": ("Мод. урона дробящего", "", "бой"),
    "Power": ("Мощность", "", "бой"),
    "PowerMod": ("Мод. мощности", "", "бой"),
    "WeaponChargeCount": ("Зарядов оружия", "", "бой"),
    "AmmoApplyCount": ("Расход боеприпасов", "", "бой"),
    "Efficiency": ("Эффективность", "", "эффект"),

    # --- защита
    "Defense": ("Защита", "", "защита"),
    "DefenseStab": ("Защита от укола", "", "защита"),
    "DefenseSlash": ("Защита от рубки", "", "защита"),
    "DefenseSmash": ("Защита от дробления", "", "защита"),
    "LimbResistance": ("Сопротивление конечностям", "", "защита"),

    # --- требования
    "StrReq": ("Требуется сила", "", "требования"),
    "AgiReq": ("Требуется ловкость", "", "требования"),

    # --- еда и снадобья
    "HealthBenefit": ("Польза для здоровья", "", "эффект"),
    "NutritionBenefit": ("Питательность", "", "эффект"),
    "AlcoholContent": ("Содержание алкоголя", "%", "эффект"),
    "RefreshBenefit": ("Освежает", "", "эффект"),
    "ShortTermNutritionBenefitRatio": ("Краткоср. питательность", "", "эффект"),

    # --- травы
    "LatinName": ("Латинское название", "", "эффект"),
    "Poisonous": ("Ядовито", "", "эффект"),
    "InHerbarium": ("В гербарии", "", "эффект"),

    # --- крафт
    "Material": ("Материал", "", "тех"),
    "VisualCategory": ("Визуальная категория", "", "тех"),
    "DriedItemId": ("ID сушёного варианта", "", "крафт"),
    "CookedItemId": ("ID приготовленного варианта", "", "крафт"),
    "SmokedItemId": ("ID копчёного варианта", "", "крафт"),
    "BlacksmithRecipeId": ("ID кузнечного рецепта", "", "крафт"),
    "RecipeId": ("ID рецепта", "", "крафт"),
    "BrokenItemId": ("ID сломанного варианта", "", "крафт"),
    "SourceItemId": ("ID исходного предмета", "", "крафт"),
    "BuffDefinitionId": ("ID эффекта", "", "эффект"),
    "WeaponBuffDefinitionId": ("ID эффекта оружия", "", "эффект"),
    "RPGBuffWeight": ("Вес эффекта", "", "эффект"),
    "RpgWeight": ("Вес эффекта", "", "эффект"),
    "Efficiency": ("Эффективность", "", "эффект"),

    # --- прочее служебное, но иногда информативное
    "Class": ("Класс предмета", "", "тех"),
    "SubClass": ("Подкласс", "", "тех"),
    "SubType": ("Подтип", "", "тех"),
    "Type": ("Тип", "", "тех"),
    "VisorTypeId": ("Тип забрала", "", "тех"),
    "NumberOfQuickSlots": ("Быстрых слотов", "", "общее"),
    "LightSourcePriority": ("Приоритет света", "", "тех"),
    "ProjectileCollisionWhenCarried": ("Сталкивается в руках", "", "тех"),
    "IsSuspicious": ("Вызывает подозрение", "", "общее"),
}

# поля, которые в карточку не выводим: это пути к моделям, звуки, ID-ссылки
# и прочая служебная обвязка движка — человеку они ничего не дают
HIDDEN = {
    "Id", "Name", "UIName", "UIInfo", "IconId", "UiSound", "Clothing",
    "Model", "ContainerModel", "ShortModel", "LongModel", "HolsterModel",
    "InquiverModel", "InquiverMaterial", "AttachmentName", "AllowUnstream",
    "HandContentSerializationMode", "SoundSwitch", "OldFormula",
    "BrokenItemClassId", "GlassType", "PhaseResetOnSlotReturn",
    "HomeSlotAutoReturn", "ProjectileCollisionWhenCarried1",
    "ProjectileCollisionWhenCarried11", "SourceItemId", "DriedItemId",
    "CookedItemId", "SmokedItemId", "BlacksmithRecipeId", "RecipeId",
    "BuffDefinitionId", "WeaponBuffDefinitionId", "SharpeningAnimSuffix",
    "SideWeights", "SideValues", "EntityScript", "ManipulationType",
    "DecayTime", "SocialClassId", "WealthLevel", "FadeCoef",
    "VisibilityCoef", "ShortTermNutritionBenefitRatio", "RPGBuffWeight",
    "RpgWeight", "FireSoundMultiplicator", "PowerMod", "AmmoApplyCount",
    # ключи строк локализации: сами тексты лежат в другом файле игры
    "Desc", "Effect", "Occur", "Description", "Text",
    # числовые коды подтипа: это внутренняя классификация движка,
    # расшифровки в данных нет, игроку она ничего не говорит
    "SubType",
    # теги — служебные метки движка (имена мешей, флаги спавна)
    "Tags",
    # визуальная категория — код фона иконки в инвентаре,
    # к настоящему типу предмета отношения не имеет
    "VisualCategory",
    # тип забрала — номер варианта модели, расшифровки в данных нет
    "VisorTypeId",
}

# порядок групп в карточке
GROUP_ORDER = ["бой", "защита", "требования", "эффект", "общее", "крафт", "тех"]
GROUP_RU = {
    "бой": "⚔️ Боевые характеристики",
    "защита": "🛡️ Защита",
    "требования": "💪 Требования",
    "эффект": "✨ Действие",
    "общее": "📦 Общее",
    "крафт": "🔨 Связанные предметы",
    "тех": "⚙️ Прочие параметры",
}

# значения-переключатели
BOOLEANS = {
    "true": "да", "false": "нет",
    "1": "да", "0": "нет",
}

RARITY = {
    "Legendary": "Легендарная",
    "Rare": "Редкая",
    "Uncommon": "Необычная",
    "Common": "Обычная",
    "None": "—",
}

# Class у оружия — это тип клинка/рукояти, а не абстракция
WEAPON_CLASS = {
    "0": "кинжал",
    "1": "короткий меч",
    "2": "сабля",
    "3": "топор",
    "4": "длинный меч",
    "5": "булава / молот",
    "7": "древковое",
    "8": "щит",
    "9": "лук",
    "10": "лёгкий арбалет",
    "11": "факел",
    "13": "ручница",
    "14": "средний арбалет",
    "15": "тяжёлый арбалет",
    "16": "охотничий тесак",
    "17": "сломанный щит",
}

# Herb.Type: в игре трава бывает свежей и сушёной
HERB_TYPE = {"0": "свежая трава", "1": "сушёная трава"}

# Document.Type: книги, рецепты, карты, письма...
DOCUMENT_TYPE = {
    "1": "книга",
    "2": "рецепт или чертёж",
    "3": "книга навыка",
    "4": "карта",
    "5": "письмо и записка",
    "6": "чертёж снаряжения",
}

# Ammo.Type
AMMO_TYPE = {"1": "стрела", "2": "болт", "3": "пуля", "4": "картечь"}

# CraftingMaterial.Type
CRAFT_TYPE = {"2": "природный материал", "3": "деталь снаряжения"}

# CraftingMaterial.SubType
CRAFT_SUBTYPE = {
    "1": "клык", "2": "рога", "6": "безоар", "7": "шкура",
}

# Ointment.Type
OINTMENT_TYPE = {
    "0": "повязка", "1": "набор для ремонта", "2": "духи", "3": "мыло",
}

# DiceBadge.Type — материал бляхи
DICE_TYPE = {"0": "оловянная", "1": "серебряная", "2": "золотая"}

# NPCTool.Type — чем занят объект в мире
NPCTOOL_TYPE = {
    "0": "декор мира",
    "1": "рабочий инструмент",
    "2": "ёмкость",
    "3": "скребок",
    "6": "мешок",
    "7": "молот",
    "10": "поднос",
    "12": "лопата",
    "13": "кувшин и кружка",
    "14": "кружка",
    "15": "вилы",
    "16": "рашпиль",
    "17": "оружие",
    "19": "мотыга",
    "21": "тесак",
    "22": "бритва",
    "23": "нож",
    "24": "туша и заготовка",
    "25": "поднос",
    "26": "прочая утварь",
}

# Key.SubType
KEY_SUBTYPE = {"1": "ключ от двери или сундука"}

# MiscItem.Type
MISC_TYPE = {
    "1": "шкуры и кожа",
    "3": "мешки",
    "4": "ключи",
    "5": "прочее",
    "6": "обломки",
}

# Food.Type
FOOD_TYPE = {
    "0": "фрукты и бахча",
    "1": "снадобья",
    "2": "мясо и рыба",
    "3": "напитки",
    "5": "мясо, рыба и потроха",
    "6": "овощи",
    "7": "грибы",
    "8": "выпечка",
    "9": "молочное",
}

VISUAL_CATEGORY = {
    "1": "Одежда",
    "2": "Доспехи",
    "3": "Оружие",
    "4": "Еда",
    "5": "Зелья",
    "6": "Книги",
    "7": "Прочее",
}

def material_ru(v):
    """Путь к ассету материала -> человеческая категория."""
    low = v.lower()
    if "book" in low:
        return "книжный переплёт"
    if "potion_flask" in low or "ceramics" in low:
        return "керамическая склянка"
    if "bandage" in low or "cloth" in low:
        return "ткань"
    if "leather" in low:
        return "кожа"
    if "wood" in low:
        return "дерево"
    if "metal" in low or "steel" in low or "iron" in low:
        return "металл"
    if "glass" in low:
        return "стекло"
    if "paper" in low or "parchment" in low:
        return "пергамент"
    if "food" in low or "meat" in low:
        return "съестное"
    if "stone" in low:
        return "камень"
    return "прочее сырьё"


def field_label(key):
    """Русская подпись для внутреннего имени поля."""
    if key in FIELD_RU:
        return FIELD_RU[key][0]
    return key


def field_unit(key):
    if key in FIELD_RU:
        return FIELD_RU[key][1]
    return ""


def field_group(key):
    if key in FIELD_RU:
        return FIELD_RU[key][2]
    return "тех"


def format_value(key, value, xml_type=""):
    """Привести значение к человеческому виду."""
    if value is None:
        return ""
    v = str(value).strip()
    if v == "":
        return ""
    low = v.lower()

    if key == "Rarity":
        return RARITY.get(v, v)
    if key in ("IsBreakable", "IsDivisible", "IsQuestItem", "Poisonous",
               "InHerbarium", "DisplayInShop", "PickpocketInPouch",
               "AllowUnstream"):
        return BOOLEANS.get(low, v)
    if key == "VisualCategory":
        return VISUAL_CATEGORY.get(v, v)
    if key == "Class":
        return WEAPON_CLASS.get(v, v)
    if key == "Type" and xml_type == "Herb":
        return HERB_TYPE.get(v, v)
    if key == "Type" and xml_type == "MiscItem":
        return MISC_TYPE.get(v, v)
    if key == "Type" and xml_type == "Food":
        return FOOD_TYPE.get(v, v)
    if key == "Type" and xml_type == "Document":
        return DOCUMENT_TYPE.get(v, v)
    if key == "Type" and xml_type == "Ammo":
        return AMMO_TYPE.get(v, v)
    if key == "Type" and xml_type == "CraftingMaterial":
        return CRAFT_TYPE.get(v, v)
    if key == "SubType" and xml_type == "CraftingMaterial":
        return CRAFT_SUBTYPE.get(v, v)
    if key == "Type" and xml_type == "Ointment":
        return OINTMENT_TYPE.get(v, v)
    if key == "Type" and xml_type == "DiceBadge":
        return DICE_TYPE.get(v, v)
    if key == "Type" and xml_type == "NPCTool":
        return NPCTOOL_TYPE.get(v, v)
    if key == "SubType" and xml_type == "Key":
        return KEY_SUBTYPE.get(v, v)
    if key == "SubType" and xml_type == "DiceBadge":
        return ""  # узор бляхи — чистая графика, игроку не нужен
    if key == "Material":
        return material_ru(v)
    if key == "ProjectileCollisionWhenCarried":
        return BOOLEANS.get(low, v)

    # числа: убираем хвосты вида 2.345208000 -> 2,35
    try:
        if "." in v or "e" in low:
            f = float(v)
            if f == int(f):
                return str(int(f))
            return f"{f:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    except ValueError:
        pass
    return v
