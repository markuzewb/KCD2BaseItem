# -*- coding: utf-8 -*-
"""Чтение xlsx без сторонних библиотек.

В файле справочника анимаций строки лежат inline (<x:is><x:t>…), общей
таблицы строк нет. Разбираем XML потоково через iterparse, чтобы не
держать в памяти 6 МБ разметки.
"""
import re
import xml.etree.ElementTree as ET
import zipfile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def sheet_names(zpath):
    """Имена листов по порядку."""
    with zipfile.ZipFile(zpath) as z:
        xml = z.read("xl/workbook.xml").decode("utf-8")
    return re.findall(r'<x:sheet name="([^"]+)"', xml)


def sheet_files(zpath):
    """{(номер листа): путь внутри архива}"""
    with zipfile.ZipFile(zpath) as z:
        rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    out = {}
    for m in re.finditer(r'Target="/xl/worksheets/(sheet(\d+)\.xml)"', rels):
        out[int(m.group(2))] = "xl/worksheets/" + m.group(1)
    return out


def cell_ref(ref):
    """A1 -> (строка, колонка)"""
    m = re.match(r"([A-Z]+)(\d+)", ref)
    col = 0
    for ch in m.group(1):
        col = col * 26 + (ord(ch) - 64)
    return int(m.group(2)), col


def read_sheet(zpath, number):
    """Список строк листа; каждая строка — список значений по колонкам."""
    files = sheet_files(zpath)
    path = files[number]
    rows = {}
    with zipfile.ZipFile(zpath) as z:
        with z.open(path) as f:
            for event, el in ET.iterparse(f, events=("end",)):
                if el.tag != NS + "row":
                    continue
                rnum = int(el.get("r") or 0)
                cells = {}
                for c in el:
                    if c.tag != NS + "c":
                        continue
                    ref = c.get("r")
                    if not ref:
                        continue
                    _, col = cell_ref(ref)
                    val = ""
                    isn = c.find(NS + "is")
                    if isn is not None:
                        val = "".join(t.text or "" for t in isn.iter(NS + "t"))
                    else:
                        v = c.find(NS + "v")
                        if v is not None:
                            val = v.text or ""
                    cells[col] = val.strip()
                if cells:
                    width = max(cells)
                    rows[rnum] = [cells.get(i, "") for i in range(1, width + 1)]
                el.clear()
    return [rows[k] for k in sorted(rows)]
