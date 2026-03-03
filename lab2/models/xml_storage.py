from __future__ import annotations

from pathlib import Path
from datetime import date
from xml.dom import minidom
from xml.sax import ContentHandler, make_parser

from models.vet_record import VetRecord


def write_records_to_xml(records: list[VetRecord], file_path: Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    document = minidom.Document()
    root = document.createElement("vet_records")
    document.appendChild(root)

    for record in records:
        record_node = document.createElement("record")
        root.appendChild(record_node)

        _append_text_node(document, record_node, "pet_name", record.pet_name)
        _append_text_node(document, record_node, "birth_date", record.birth_date.isoformat())
        _append_text_node(document, record_node, "last_visit_date", record.last_visit_date.isoformat())
        _append_text_node(document, record_node, "vet_name", record.vet_name)
        _append_text_node(document, record_node, "diagnosis", record.diagnosis)

    with path.open("w", encoding="utf-8") as xml_file:
        document.writexml(xml_file, addindent="  ", newl="\n", encoding="utf-8")

def read_records_from_xml(file_path: Path) -> list[VetRecord]:
    parser = make_parser()
    handler = _VetRecordsSaxHandler()
    parser.setContentHandler(handler)
    parser.parse(str(file_path))
    return handler.records

def _append_text_node(
    document: minidom.Document,
    parent: minidom.Element,
    tag_name: str,
    text: str,
) -> None:
    node = document.createElement(tag_name)
    node.appendChild(document.createTextNode(text))
    parent.appendChild(node)

class _VetRecordsSaxHandler(ContentHandler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[VetRecord] = []
        self._current_tag = ""
        self._text_buffer: list[str] = []
        self._record: dict[str, str] = {}

    def startElement(self, name: str, attrs):
        self._current_tag = name
        self._text_buffer = []
        if name == "record":
            self._record = {}

    def characters(self, content: str):
        if self._current_tag:
            self._text_buffer.append(content)

    def endElement(self, name: str):
        text = "".join(self._text_buffer).strip()

        if name in {
            "pet_name",
            "birth_date",
            "last_visit_date",
            "vet_name",
            "diagnosis",
        }:
            self._record[name] = text

        if name == "record":
            self.records.append(
                VetRecord(
                    pet_name=self._record.get("pet_name", ""),
                    birth_date=_safe_date(self._record.get("birth_date")),
                    last_visit_date=_safe_date(self._record.get("last_visit_date")),
                    vet_name=self._record.get("vet_name", ""),
                    diagnosis=self._record.get("diagnosis", ""),
                )
            )

        self._current_tag = ""
        self._text_buffer = []


def _safe_date(value: str | None) -> date:
    try:
        return date.fromisoformat(value or "")
    except Exception:
        return date.today()