"""Banner identitas kelompok yang dibaca dari config/group.toml."""

from __future__ import annotations

import sys
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLACEHOLDER_MARK = "BELUM DIISI"
PLACEHOLDER_HINT = "Lengkapi config/group.toml sebelum mengambil hasil eksperimen."


@dataclass(frozen=True)
class Member:
    """Satu anggota kelompok."""

    nama: str
    npm: str


@dataclass(frozen=True)
class GroupInfo:
    """Identitas kelompok untuk banner CLI."""

    project_name: str
    tema: str
    mata_kuliah: str
    institusi: str
    nama_kelompok: str
    anggota: tuple[Member, ...]

    @property
    def has_placeholder(self) -> bool:
        """True bila masih ada nilai placeholder yang harus diisi user."""
        values = [self.project_name, self.tema, self.mata_kuliah, self.institusi]
        values.append(self.nama_kelompok)
        for member in self.anggota:
            values.extend([member.nama, member.npm])
        return any(is_placeholder(value) for value in values)


def is_placeholder(value: str) -> bool:
    """Deteksi nilai placeholder seperti '<ISI NAMA>' atau string kosong."""
    text = value.strip()
    if not text:
        return True
    return text.startswith("<") and text.endswith(">")


def _require_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"field '{key}' wajib berupa string di group.toml")
    return value


def load_group_info(path: Path) -> GroupInfo:
    """Muat group.toml dan validasi field wajibnya."""
    if not path.is_file():
        raise FileNotFoundError(f"file group.toml tidak ditemukan: {path}")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"group.toml tidak valid: {exc}") from exc

    kelompok = raw.get("kelompok")
    if not isinstance(kelompok, Mapping):
        raise ValueError("bagian [kelompok] wajib ada di group.toml")

    anggota_raw = raw.get("anggota")
    if not isinstance(anggota_raw, list) or not anggota_raw:
        raise ValueError("minimal satu [[anggota]] wajib ada di group.toml")

    anggota: list[Member] = []
    for entry in anggota_raw:
        if not isinstance(entry, Mapping):
            raise ValueError("setiap [[anggota]] wajib berupa tabel")
        anggota.append(Member(nama=_require_str(entry, "nama"), npm=_require_str(entry, "npm")))

    return GroupInfo(
        project_name=_require_str(raw, "project_name"),
        tema=_require_str(raw, "tema"),
        mata_kuliah=_require_str(raw, "mata_kuliah"),
        institusi=_require_str(raw, "institusi"),
        nama_kelompok=_require_str(kelompok, "nama"),
        anggota=tuple(anggota),
    )


def render_banner(info: GroupInfo) -> str:
    """Susun teks banner dari identitas kelompok."""
    lines = [
        "=" * 60,
        f" {info.project_name} - Distributed Data Compression",
        f" {info.mata_kuliah}",
        f" {info.institusi}",
        f" Tema: {info.tema}",
        f" Kelompok: {info.nama_kelompok}",
        " Anggota:",
    ]
    for member in info.anggota:
        lines.append(f"   - {member.nama} ({member.npm})")
    lines.append("=" * 60)
    if info.has_placeholder:
        lines.extend(
            [
                f" PERINGATAN: identitas kelompok {PLACEHOLDER_MARK}.",
                f" {PLACEHOLDER_HINT}",
            ]
        )
    return "\n".join(lines)


def print_banner(info: GroupInfo) -> None:
    """Cetak banner ke stdout (satu-satunya print yang diizinkan)."""
    print(render_banner(info))


def try_print_banner(path: Path) -> bool:
    """Cetak banner bila group.toml dapat dibaca; selain itu beri peringatan dan lanjut."""
    try:
        info = load_group_info(path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"peringatan: banner dilewati ({exc})", file=sys.stderr)
        return False
    print_banner(info)
    return True
