"""Bangun laporan UAS ZipHive dalam format DOCX (PLAN.md P10-T2).

Berkas ini menulis paket OOXML langsung memakai `zipfile` dan `xml.sax.saxutils`,
sehingga tidak menambah dependensi di luar stdlib (AGENTS.md bagian 2 butir 7).
Isi laporan diambil dari `scripts/report_content.py`; seluruh angka berasal dari
`results/summary.csv`, `results/summary_agg.csv`, dan `docs/ANALYSIS.md`.

Bila sebuah gambar tidak tersedia (misalnya `reports/img` tidak ikut repo karena
masuk `.gitignore`), posisinya diganti kotak placeholder sesuai aturan skill
`laporan-akademik-id`, bukan dikarang.
"""

# ruff: noqa: E501
# Baris XML OOXML di bawah ditulis utuh per elemen agar mudah dibaca dan dicocokkan
# dengan spesifikasi; memecahnya menjadi literal bersambung menurunkan keterbacaan.

from __future__ import annotations

import argparse
import struct
import sys
import tomllib
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_content import BLOCKS  # noqa: E402  (butuh sys.path di atas)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = "reports/laporan/ZipHive-Laporan-UAS.docx"

EMU_PER_INCH = 914400
EMU_PER_CM = 360000
MAX_IMAGE_INCH = 6.0
PIXEL_PER_CM = 378  # 96 dpi

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

MONO_FONT = "Courier New"
TEXT_WIDTH = 8700

STYLES_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
<w:docDefaults>
<w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="id-ID"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:pageBreakBefore/><w:jc w:val="center"/><w:spacing w:before="0" w:after="240" w:line="360" w:lineRule="auto"/><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:jc w:val="left"/><w:spacing w:before="240" w:after="120"/><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:jc w:val="left"/><w:spacing w:before="180" w:after="120"/><w:keepNext/><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="240" w:line="240" w:lineRule="auto"/></w:pPr>
<w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="left"/><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>
<w:rPr><w:rFonts w:ascii="{MONO_FONT}" w:hAnsi="{MONO_FONT}" w:cs="{MONO_FONT}"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="left"/><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>
<w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Cover"><w:name w:val="Cover"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TocTitle"><w:name w:val="Toc Title"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="240" w:line="360" w:lineRule="auto"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Placeholder"><w:name w:val="Placeholder"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/><w:spacing w:before="60" w:after="60" w:line="240" w:lineRule="auto"/></w:pPr>
<w:rPr><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:style>
</w:styles>
"""

NUMBERING_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W_NS}">
<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="709" w:hanging="284"/></w:pPr></w:lvl>
</w:abstractNum>
<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="singleLevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="709" w:hanging="284"/></w:pPr></w:lvl>
</w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>
"""

SETTINGS_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W_NS}"><w:updateFields w:val="true"/>
<w:defaultTabStop w:val="709"/>
<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>
</w:settings>
"""

PAGE_FIELD = (
    '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    "<w:r><w:t>1</w:t></w:r>"
    '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
)

FOOTER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">'
    '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
    f"{PAGE_FIELD}</w:p></w:ftr>"
)

SECT_BASE = (
    '<w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1440" w:right="1418" w:bottom="1440" w:left="1701" '
    'w:header="720" w:footer="720" w:gutter="0"/>'
)


def _run(text: str, bold: bool = False, size: int | None = None, mono: bool = False) -> str:
    """Bentuk satu run `w:r` dengan properti opsional."""
    if not text:
        return ""
    properties = ""
    if mono or bold or size:
        properties = "<w:rPr>"
        if mono:
            properties += (
                f'<w:rFonts w:ascii="{MONO_FONT}" w:hAnsi="{MONO_FONT}" w:cs="{MONO_FONT}"/>'
            )
        if bold:
            properties += "<w:b/>"
        if size:
            properties += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        properties += "</w:rPr>"
    return f'<w:r>{properties}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def _runs(text: str, bold: bool = False, size: int | None = None) -> str:
    """Ubah teks berpenanda **tebal** dan `mono` menjadi deretan run Word."""
    parts: list[str] = []
    buffer: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("**", index):
            end = text.find("**", index + 2)
            if end != -1:
                parts.append(_run("".join(buffer), bold, size))
                buffer = []
                parts.append(_run(text[index + 2 : end], True, size))
                index = end + 2
                continue
        if text[index] == "`":
            end = text.find("`", index + 1)
            if end != -1:
                parts.append(_run("".join(buffer), bold, size))
                buffer = []
                parts.append(_run(text[index + 1 : end], bold, size, mono=True))
                index = end + 1
                continue
        buffer.append(text[index])
        index += 1
    parts.append(_run("".join(buffer), bold, size))
    return "".join(part for part in parts if part)


def paragraph(
    text: str = "",
    style: str = "Normal",
    align: str | None = None,
    indent: bool = False,
    num_id: int | None = None,
    bold: bool = False,
    size: int | None = None,
) -> str:
    """Bentuk satu paragraf `w:p`."""
    properties = f'<w:pStyle w:val="{style}"/>'
    if num_id is not None:
        properties += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num_id}"/></w:numPr>'
    if indent:
        properties += '<w:ind w:firstLine="709"/>'
    if align:
        properties += f'<w:jc w:val="{align}"/>'
    return f"<w:p><w:pPr>{properties}</w:pPr>{_runs(text, bold, size)}</w:p>"


def chapter(label: str, title: str) -> str:
    """Judul bab dua baris: label "BAB I" lalu nama bab, satu paragraf Heading 1."""
    body = f'<w:t xml:space="preserve">{escape(label)}</w:t>'
    if label:
        body += "<w:br/>"
    body += f'<w:t xml:space="preserve">{escape(title)}</w:t>'
    return (
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>{body}</w:r></w:p>'
    )


def section_paragraph(sect_xml: str) -> str:
    """Paragraf kosong pembawa `sectPr` sebagai batas antarbagian."""
    return f"<w:p><w:pPr><w:sectPr>{sect_xml}</w:sectPr></w:pPr></w:p>"


def png_size(path: Path) -> tuple[int, int]:
    """Baca lebar dan tinggi piksel dari header PNG."""
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"bukan berkas PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


class Builder:
    """Kumpulan blok dokumen beserta pengelola relasi gambar."""

    def __init__(self, repo_root: Path) -> None:
        """Siapkan pembangun dokumen untuk `repo_root`."""
        self.repo_root = repo_root
        self.media: list[tuple[str, str, bytes]] = []
        self.drawing_id = 0
        self.missing_images: list[str] = []

    def _image_rel(self, path: Path) -> tuple[str, int, int]:
        """Daftarkan gambar dan kembalikan (rId, lebar EMU, tinggi EMU)."""
        self.drawing_id += 1
        name = f"image{self.drawing_id}{path.suffix.lower()}"
        rel_id = f"rIdImg{self.drawing_id}"
        self.media.append((rel_id, name, path.read_bytes()))
        width_px, height_px = png_size(path)
        width_emu = width_px * EMU_PER_CM // PIXEL_PER_CM
        height_emu = height_px * EMU_PER_CM // PIXEL_PER_CM
        limit = int(MAX_IMAGE_INCH * EMU_PER_INCH)
        if width_emu > limit:
            height_emu = height_emu * limit // width_emu
            width_emu = limit
        return rel_id, width_emu, height_emu

    def image_block(self, spec: dict[str, Any]) -> list[str]:
        """Paragraf gambar beserta keterangan, atau placeholder bila berkas hilang."""
        path = self.repo_root / spec["path"]
        if not path.is_file():
            self.missing_images.append(spec["path"])
            return self.placeholder_block(
                spec["number"], spec["isi"], spec["cara"], spec["caption"]
            )
        rel_id, width_emu, height_emu = self._image_rel(path)
        drawing = (
            '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="0" '
            'w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:drawing>'
            '<wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
            f'<wp:docPr id="{self.drawing_id}" name="Gambar {self.drawing_id}"/>'
            f'<a:graphic xmlns:a="{A_NS}">'
            f'<a:graphicData uri="{PIC_NS}"><pic:pic xmlns:pic="{PIC_NS}">'
            f'<pic:nvPicPr><pic:cNvPr id="{self.drawing_id}" name="{escape(path.name)}"/>'
            "<pic:cNvPicPr/></pic:nvPicPr>"
            f'<pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch>'
            "</pic:blipFill>"
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{width_emu}" cy="{height_emu}"/>'
            '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
        )
        return [drawing, paragraph(spec["caption"], style="Caption")]

    def placeholder_block(
        self, number: str, isi: str, cara: str, caption: str, height_cm: int = 5
    ) -> list[str]:
        """Kotak placeholder tiga baris beserta keterangan gambar."""
        height = height_cm * 567
        dashed = (
            "<w:tcBorders>"
            '<w:top w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            '<w:left w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            '<w:bottom w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            '<w:right w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            "</w:tcBorders>"
        )
        cell = (
            f'<w:tc><w:tcPr><w:tcW w:w="{TEXT_WIDTH}" w:type="dxa"/>{dashed}'
            '<w:shd w:val="clear" w:color="auto" w:fill="EDEDED"/>'
            '<w:vAlign w:val="center"/></w:tcPr>'
            f"{paragraph(f'PLACEHOLDER GAMBAR {number}', style='Placeholder', bold=True)}"
            f"{paragraph(f'Isi yang harus ditampilkan: {isi}', style='Placeholder')}"
            f"{paragraph(f'Cara memperoleh: {cara}', style='Placeholder')}"
            "</w:tc>"
        )
        table = (
            f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/>'
            '<w:jc w:val="center"/><w:tblLayout w:type="fixed"/></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{TEXT_WIDTH}"/></w:tblGrid>'
            f'<w:tr><w:trPr><w:trHeight w:val="{height}" w:hRule="atLeast"/></w:trPr>'
            f"{cell}</w:tr></w:tbl>"
        )
        return [table, paragraph(caption, style="Caption")]

    def table_block(self, spec: dict[str, Any]) -> list[str]:
        """Bangun tabel berbingkai beserta keterangan di bawahnya."""
        widths = [int(width) for width in spec["widths"]]
        borders = "".join(
            f'<w:{edge} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
        head_cells = "".join(
            self._cell(label, width, bold=True)
            for label, width in zip(spec["header"], widths, strict=False)
        )
        rows = [f"<w:tr><w:trPr><w:tblHeader/></w:trPr>{head_cells}</w:tr>"]
        mono_columns = set(spec.get("mono", []))
        for row in spec["rows"]:
            cells = "".join(
                self._cell(value, width, mono=index in mono_columns)
                for index, (value, width) in enumerate(zip(row, widths, strict=False))
            )
            rows.append(f"<w:tr>{cells}</w:tr>")
        table = (
            '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
            f"<w:tblBorders>{borders}</w:tblBorders>"
            '<w:tblLayout w:type="fixed"/>'
            '<w:tblCellMar><w:left w:w="85" w:type="dxa"/><w:right w:w="85" w:type="dxa"/>'
            "</w:tblCellMar></w:tblPr>"
            f"<w:tblGrid>{grid}</w:tblGrid>{''.join(rows)}</w:tbl>"
        )
        return [table, paragraph(spec["caption"], style="Caption")]

    @staticmethod
    def _cell(value: str, width: int, bold: bool = False, mono: bool = False) -> str:
        """Bentuk satu sel tabel."""
        text = value
        if mono and value and "`" not in value and "**" not in value:
            text = f"`{value}`"
        return (
            f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
            f"{paragraph(text, style='TableText', bold=bold)}</w:tc>"
        )

    def code_block(self, lines: list[str]) -> list[str]:
        """Kotak satu sel berbingkai tipis berisi perintah monospasi."""
        content = "".join(paragraph(line, style="Code") for line in lines)
        table = (
            f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/>'
            "<w:tblBorders>"
            '<w:top w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
            '<w:left w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
            '<w:right w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
            "</w:tblBorders>"
            '<w:tblLayout w:type="fixed"/>'
            '<w:tblCellMar><w:left w:w="113" w:type="dxa"/><w:right w:w="113" w:type="dxa"/>'
            '<w:top w:w="57" w:type="dxa"/><w:bottom w:w="57" w:type="dxa"/></w:tblCellMar>'
            f'</w:tblPr><w:tblGrid><w:gridCol w:w="{TEXT_WIDTH}"/></w:tblGrid>'
            f'<w:tr><w:tc><w:tcPr><w:tcW w:w="{TEXT_WIDTH}" w:type="dxa"/></w:tcPr>'
            f"{content}</w:tc></w:tr></w:tbl>"
        )
        return [table, paragraph("")]

    def render(self, blocks: list[tuple[str, Any]]) -> str:
        """Ubah daftar blok isi menjadi `word/document.xml`."""
        body: list[str] = [self.cover(), section_paragraph(SECT_BASE)]
        body.append(paragraph("DAFTAR ISI", style="TocTitle", bold=True, size=28))
        body.append(self.toc())
        body.append(
            section_paragraph(
                SECT_BASE + '<w:pgNumType w:fmt="lowerRoman" w:start="2"/>'
                '<w:footerReference w:type="default" r:id="rIdFooter"/>'
            )
        )
        for kind, payload in blocks:
            if kind == "h1":
                body.append(chapter(payload[0], payload[1]))
            elif kind == "h2":
                body.append(paragraph(payload, style="Heading2", bold=True))
            elif kind == "h3":
                body.append(paragraph(payload, style="Heading3", bold=True))
            elif kind == "p":
                body.append(paragraph(payload, indent=True))
            elif kind == "plain":
                body.append(paragraph(payload))
            elif kind == "bullets":
                body.extend(paragraph(item, num_id=1) for item in payload)
            elif kind == "numbers":
                body.extend(paragraph(item, num_id=2) for item in payload)
            elif kind == "table":
                body.extend(self.table_block(payload))
            elif kind == "image":
                body.extend(self.image_block(payload))
            elif kind == "placeholder":
                body.extend(
                    self.placeholder_block(
                        payload["number"],
                        payload["isi"],
                        payload["cara"],
                        payload["caption"],
                        payload.get("height_cm", 5),
                    )
                )
            elif kind == "code":
                body.extend(self.code_block(payload))
            else:
                raise ValueError(f"jenis blok tidak dikenal: {kind}")
        body.append(
            f"<w:sectPr>{SECT_BASE}"
            '<w:pgNumType w:fmt="decimal" w:start="1"/>'
            '<w:footerReference w:type="default" r:id="rIdFooter"/>'
            "</w:sectPr>"
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" '
            f'xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}"><w:body>{"".join(body)}</w:body>'
            "</w:document>"
        )

    def cover(self) -> str:
        """Halaman sampul sesuai identitas pada `config/group.toml`."""
        identity = read_identity(self.repo_root)
        lines = [
            paragraph("LAPORAN UJIAN AKHIR SEMESTER (UAS)", style="Cover", size=28),
            paragraph("KOMPUTASI PARALEL DAN SISTEM TERDISTRIBUSI", style="Cover", size=28),
            paragraph("", style="Cover", size=20),
            paragraph(
                "Perancangan dan Implementasi Kompresi Data Terdistribusi "
                "dengan Arsitektur Master-Worker",
                style="Cover",
                size=32,
            ),
            paragraph("(Studi Kasus Tema 16 Distributed Data Compression)", style="Cover", size=24),
            paragraph("", style="Cover", size=20),
            self.logo_box(),
            paragraph("", style="Cover", size=20),
            paragraph("Disusun oleh", style="Cover", size=24),
            self.identity_table(identity),
            paragraph("", style="Cover", size=20),
            paragraph("PROGRAM STUDI INFORMATIKA", style="Cover", size=24),
            paragraph("FAKULTAS TEKNIK", style="Cover", size=24),
            paragraph("UNIVERSITAS SILIWANGI", style="Cover", size=24),
            paragraph("2026", style="Cover", size=24),
        ]
        return "".join(lines)

    @staticmethod
    def logo_box() -> str:
        """Kotak placeholder logo universitas pada sampul."""
        dashed = (
            "<w:tcBorders>"
            '<w:top w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            '<w:left w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            '<w:bottom w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            '<w:right w:val="dashed" w:sz="8" w:space="0" w:color="808080"/>'
            "</w:tcBorders>"
        )
        return (
            '<w:tbl><w:tblPr><w:tblW w:w="2835" w:type="dxa"/><w:jc w:val="center"/>'
            '<w:tblLayout w:type="fixed"/></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="2835"/></w:tblGrid>'
            '<w:tr><w:trPr><w:trHeight w:val="2835" w:hRule="atLeast"/></w:trPr>'
            f'<w:tc><w:tcPr><w:tcW w:w="2835" w:type="dxa"/>{dashed}'
            '<w:vAlign w:val="center"/></w:tcPr>'
            f"{paragraph('PLACEHOLDER LOGO', style='Placeholder', bold=True)}"
            f"{paragraph('Logo Universitas Siliwangi', style='Placeholder')}"
            "</w:tc></w:tr></w:tbl>"
        )

    @staticmethod
    def identity_table(identity: dict[str, Any]) -> str:
        """Tabel tanpa bingkai berisi nama, NPM, dan kelas anggota."""

        def row(label: str, value: str, align: str) -> str:
            return (
                "<w:tr>"
                f'<w:tc><w:tcPr><w:tcW w:w="3400" w:type="dxa"/></w:tcPr>'
                f"{paragraph(label, style='TableText', align='right')}</w:tc>"
                f'<w:tc><w:tcPr><w:tcW w:w="250" w:type="dxa"/></w:tcPr>'
                f"{paragraph(':', style='TableText', align='center')}</w:tc>"
                f'<w:tc><w:tcPr><w:tcW w:w="2100" w:type="dxa"/></w:tcPr>'
                f"{paragraph(value, style='TableText', align=align)}</w:tc>"
                "</w:tr>"
            )

        rows = [row(member["nama"], member["npm"], "left") for member in identity["anggota"]]
        rows.append(row("Kelas", identity.get("kelas") or "PERLU DIISI USER", "left"))
        return (
            '<w:tbl><w:tblPr><w:tblW w:w="5750" w:type="dxa"/><w:jc w:val="center"/>'
            "<w:tblBorders>"
            '<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            '<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            '<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            '<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            '</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="3400"/><w:gridCol w:w="250"/>'
            '<w:gridCol w:w="2100"/></w:tblGrid>'
            f"{''.join(rows)}</w:tbl>"
        )

    @staticmethod
    def toc() -> str:
        """Field daftar isi otomatis dari gaya Heading."""
        return (
            '<w:p><w:pPr><w:jc w:val="left"/></w:pPr>'
            '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            "<w:r><w:t>Daftar isi dibuat otomatis. Tekan F9 di Word untuk memperbarui.</w:t></w:r>"
            '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        )


def read_identity(repo_root: Path) -> dict[str, Any]:
    """Baca identitas kelompok dari `config/group.toml`."""
    with (repo_root / "config" / "group.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return {"anggota": data.get("anggota", []), "kelas": data.get("kelas")}


def content_types() -> str:
    """Bentuk `[Content_Types].xml`."""
    overrides = [
        ("/word/document.xml", "document.main"),
        ("/word/styles.xml", "styles"),
        ("/word/numbering.xml", "numbering"),
        ("/word/settings.xml", "settings"),
        ("/word/footer1.xml", "footer"),
    ]
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
    ]
    for name, kind in overrides:
        parts.append(
            f'<Override PartName="{name}" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.'
            f'{kind}+xml"/>'
        )
    parts.append("</Types>")
    return "".join(parts)


def package_rels() -> str:
    """Bentuk `_rels/.rels`."""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG_REL_NS}">'
        '<Relationship Id="rIdMain" '
        f'Type="{DOC_REL}/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )


def document_rels(media: list[tuple[str, str, bytes]]) -> str:
    """Bentuk `word/_rels/document.xml.rels` termasuk relasi gambar."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        f'<Relationships xmlns="{PKG_REL_NS}">',
        f'<Relationship Id="rIdStyles" Type="{DOC_REL}/styles" Target="styles.xml"/>',
        f'<Relationship Id="rIdNumbering" Type="{DOC_REL}/numbering" Target="numbering.xml"/>',
        f'<Relationship Id="rIdSettings" Type="{DOC_REL}/settings" Target="settings.xml"/>',
        f'<Relationship Id="rIdFooter" Type="{DOC_REL}/footer" Target="footer1.xml"/>',
    ]
    for rel_id, name, _ in media:
        parts.append(f'<Relationship Id="{rel_id}" Type="{DOC_REL}/image" Target="media/{name}"/>')
    parts.append("</Relationships>")
    return "".join(parts)


def build(repo_root: Path, out_path: Path) -> tuple[int, list[str]]:
    """Bangun berkas DOCX dan kembalikan (jumlah gambar tersemat, gambar hilang)."""
    builder = Builder(repo_root)
    document = builder.render(BLOCKS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types())
        archive.writestr("_rels/.rels", package_rels())
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", document_rels(builder.media))
        archive.writestr("word/styles.xml", STYLES_XML)
        archive.writestr("word/numbering.xml", NUMBERING_XML)
        archive.writestr("word/settings.xml", SETTINGS_XML)
        archive.writestr("word/footer1.xml", FOOTER_XML)
        for _, name, data in builder.media:
            archive.writestr(f"word/media/{name}", data)
    return len(builder.media), builder.missing_images


def main(argv: list[str] | None = None) -> int:
    """Titik masuk `build_report.py`."""
    parser = argparse.ArgumentParser(
        prog="build_report.py", description="Bangun laporan UAS ZipHive sebagai DOCX"
    )
    parser.add_argument("--repo", default=str(REPO_ROOT), help="folder repo")
    parser.add_argument("--out", default=None, help=f"path DOCX (bawaan: {DEFAULT_OUT})")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo)
    out_path = Path(args.out) if args.out else repo_root / DEFAULT_OUT
    images, missing = build(repo_root, out_path)
    print(f"laporan : {out_path}")
    print(f"ukuran  : {out_path.stat().st_size / 1024:.1f} KiB")
    print(f"gambar  : {images} disematkan")
    if missing:
        print(f"placeholder: {len(missing)} gambar belum tersedia")
        for path in missing:
            print(f"  - {path}")
    print("REPORT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
