# -*- coding: utf-8 -*-
"""Движок локализации названий предметов KCD2 на русский язык."""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexicon_ru import NOUNS, SPECIAL  # noqa: E402

# Прилагательные, которые должны стоять в правильной форме после перевода
# (мужской род по умолчанию). Для женского/среднего рода — отдельные формы.
PLURAL_TAIL = {
    "sleeves", "gloves", "gauntlets", "boots", "shoes", "spurs", "hands",
    "legs", "hose", "chausses", "trousers", "horseshoes", "feathers", "fangs",
    "antlers", "notes", "ledgers", "spectacles", "keys", "stones", "pearls",
}

# Слова, после которых идёт родительный падеж владельца — оставляем как есть.
DROP = {"a", "an", "the", "of", "o'", "á"}


def _norm(w: str) -> str:
    return w.strip().lower().replace("’", "'").replace(" ", " ")


def translate(name: str) -> str:
    """Перевести английское название предмета на русский."""
    if not name:
        return ""
    raw = name.strip()
    low = _norm(raw)

    # 1) Точное совпадение в словаре готовых названий
    if low in SPECIAL:
        return SPECIAL[low]

    # 2) Снимаем ведущий артикль
    low2 = re.sub(r"^(a|an|the)\s+", "", low)

    # 3) Прямой перевод по словарю NOUNS построчно, если есть точное совпадение
    words = raw.split()
    out = []
    for i, w in enumerate(words):
        k = _norm(w)
        if k in DROP:
            out.append(None)
            continue
        if k in SPECIAL:
            out.append(SPECIAL[k])
        elif k in NOUNS:
            out.append(NOUNS[k])
        else:
            out.append(("?", k))
    return out


def probe_coverage(names):
    from lexicon_ru import NOUNS, SPECIAL
    total = 0
    exact = 0
    wordok = 0
    unknown = {}
    for n in names:
        total += 1
        low = n.strip().lower()
        if low in SPECIAL:
            exact += 1
            continue
        ok = True
        for w in re.findall(r"[A-Za-zÀ-ž'’\-]+", n):
            k = w.lower().replace("’", "'")
            if k in ("a", "an", "the", "of", "o'", "á"):
                continue
            if k in NOUNS or k in SPECIAL:
                continue
            ok = False
            unknown[k] = unknown.get(k, 0) + 1
        if ok:
            wordok += 1
    return total, exact, wordok, unknown


if __name__ == "__main__":
    names = [l for l in open("/tmp/kcd/names_all.txt", encoding="utf-8").read().split("\n") if l.strip()]
    total, exact, wordok, unknown = probe_coverage(names)
    print(f"всего {total}: точных {exact}, пословно {wordok} ({100*(exact+wordok)/total:.1f}%)")
    print("неизвестных слов:", len(unknown))
    top = sorted(unknown.items(), key=lambda kv: -kv[1])[:120]
    print(", ".join(f"{w}({c})" for w, c in top))
