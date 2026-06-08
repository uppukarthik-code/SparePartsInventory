"""Canonical raw-OOXML readers for the railway platform (Phase A consolidation).

These are the SINGLE SOURCE for reading single-sheet .xlsx workbooks via raw
OOXML (zipfile + ElementTree), avoiding an openpyxl runtime dependency. They
replace two previously-duplicated private readers and remove the cross-layer
"leaky" reuse of ``railway_demand_reconstruction._sheet_rows`` by the planning
modules.

Two contracts are preserved EXACTLY (behavior-preserving — outputs must stay
byte-identical):

* ``read_sheet_rows(path) -> list[dict]``
      Materialised list of ``{col_index: value}`` rows. This is the exact prior
      behaviour of ``railway_demand_reconstruction._sheet_rows`` (sheet1 only;
      sharedStrings iterated as direct children of <sst>).

* ``iter_sheet_rows(path, sheet_xml=...) -> generator[dict]``
      Lazy generator of ``{col_index: value}`` rows; accepts a sheet path. This
      is the exact prior behaviour of
      ``railway_data_preparation._xlsx_rows_via_xml`` (sharedStrings iterated via
      ``.iter('si')``).

The two functions intentionally keep their original (subtly different)
sharedStrings traversal so that no produced value can change. ``_col_idx`` is
shared because it was byte-identical in both originals.
"""
import zipfile
from xml.etree import ElementTree as ET

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col_idx(ref):
    """A1-style cell ref -> 0-based column index. (Identical in both originals.)"""
    letters = "".join(c for c in ref if c.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def read_sheet_rows(path):
    """Return list of ``{col_index: value}`` for sheet1 of an xlsx.

    Exact replacement for ``railway_demand_reconstruction._sheet_rows``.
    """
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
            shared.append("".join(t.text or "" for t in si.iter(_NS + "t")))

    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    sd = sheet.find(_NS + "sheetData")
    out = []
    for row in sd.findall(_NS + "row"):
        cells = {}
        for c in row.findall(_NS + "c"):
            t = c.get("t"); v = c.find(_NS + "v"); isn = c.find(_NS + "is")
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr" and isn is not None:
                val = "".join(x.text or "" for x in isn.iter(_NS + "t"))
            elif v is not None:
                val = v.text
            else:
                val = None
            cells[_col_idx(c.get("r"))] = val
        out.append(cells)
    z.close()
    return out


def iter_sheet_rows(path, sheet_xml="xl/worksheets/sheet1.xml"):
    """Yield ``{col_index: value}`` row dicts from a single-sheet xlsx.

    Exact replacement for ``railway_data_preparation._xlsx_rows_via_xml``.
    """
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in sst.iter(_NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(_NS + "t")))

    sheet = ET.fromstring(z.read(sheet_xml))
    for row in sheet.iter(_NS + "row"):
        cells = {}
        for c in row.findall(_NS + "c"):
            ci = _col_idx(c.get("r"))
            t = c.get("t")
            v = c.find(_NS + "v")
            isn = c.find(_NS + "is")
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr" and isn is not None:
                val = "".join(x.text or "" for x in isn.iter(_NS + "t"))
            elif v is not None:
                val = v.text
            else:
                val = None
            cells[ci] = val
        yield cells
