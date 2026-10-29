import csv
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}


def extract_pdf_text(pdf_path: str):

    reader = PdfReader(pdf_path)

    pages = []

    for page_num, page in enumerate(reader.pages):

        text = page.extract_text()

        if text:

            pages.append(
                {
                    "page": page_num + 1,
                    "text": text
                }
            )

    return pages


def _extract_docx(path):
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))

    body = root.find("w:body", ns)
    lines = []
    if body is None:
        return []

    for element in body:
        if element.tag.endswith("}p"):
            text = "".join(node.text or "" for node in element.findall(".//w:t", ns))
            if text.strip():
                lines.append(text)
        elif element.tag.endswith("}tbl"):
            for row in element.findall("w:tr", ns):
                cells = []
                for cell in row.findall("w:tc", ns):
                    cell_text = " ".join(
                        "".join(node.text or "" for node in paragraph.findall(".//w:t", ns))
                        for paragraph in cell.findall("w:p", ns)
                    ).strip()
                    cells.append(cell_text)
                if any(cells):
                    lines.append(" | ".join(cells))

    text = "\n".join(lines)
    return [{"page": 1, "text": text}] if text.strip() else []


def _xlsx_shared_strings(archive):
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(node.text or "" for node in item.iter() if node.tag.endswith("}t"))
        for item in root
    ]


def _extract_xlsx(path):
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"

    with zipfile.ZipFile(path) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relationships.findall(f"{{{package_rel_ns}}}Relationship")
        }
        pages = []

        for index, sheet in enumerate(workbook.findall(f".//{{{main_ns}}}sheet"), start=1):
            relation_id = sheet.attrib.get(f"{{{rel_ns}}}id")
            target = targets.get(relation_id)
            if not target:
                continue
            sheet_path = target.lstrip("/")
            if not sheet_path.startswith("xl/"):
                sheet_path = posixpath.normpath(posixpath.join("xl", sheet_path))

            sheet_root = ElementTree.fromstring(archive.read(sheet_path))
            rows = []
            for row in sheet_root.findall(f".//{{{main_ns}}}sheetData/{{{main_ns}}}row"):
                values = []
                for cell in row.findall(f"{{{main_ns}}}c"):
                    value_node = cell.find(f"{{{main_ns}}}v")
                    cell_type = cell.attrib.get("t")
                    if cell_type == "inlineStr":
                        value = "".join(
                            node.text or "" for node in cell.iter()
                            if node.tag.endswith("}t")
                        )
                    elif value_node is None:
                        value = ""
                    elif cell_type == "s":
                        value = shared_strings[int(value_node.text)]
                    else:
                        value = value_node.text or ""
                    values.append(value)
                if any(value.strip() for value in values):
                    rows.append(" | ".join(values))

            sheet_text = f"Worksheet: {sheet.attrib.get('name', f'Sheet {index}')}\n" + "\n".join(rows)
            if rows:
                pages.append({"page": index, "text": sheet_text})

    return pages


def _extract_csv(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as source:
        sample = source.read(4096)
        source.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        except csv.Error:
            dialect = csv.excel
        rows = [" | ".join(cell.strip() for cell in row) for row in csv.reader(source, dialect)]
    text = "\n".join(row for row in rows if row.strip(" |"))
    return [{"page": 1, "text": text}] if text.strip() else []


def _extract_txt(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    return [{"page": 1, "text": text}] if text.strip() else []


def extract_document_text(path):
    extension = Path(path).suffix.lower()
    if extension == ".pdf":
        return extract_pdf_text(str(path))
    if extension == ".docx":
        return _extract_docx(path)
    if extension == ".xlsx":
        return _extract_xlsx(path)
    if extension == ".csv":
        return _extract_csv(path)
    if extension == ".txt":
        return _extract_txt(path)
    raise ValueError(f"Unsupported document type: {extension or 'unknown'}")
