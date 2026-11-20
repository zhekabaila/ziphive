"""UT-CMP-01..03: round-trip algoritma kompresi."""

from __future__ import annotations

import pytest

from pcomp import compressor


@pytest.mark.parametrize("algo", ["gzip", "bz2", "lzma"])
def test_roundtrip(algo: str) -> None:
    """UT-CMP-01..03: setiap algoritma mengembalikan data identik."""
    data = (b"ZipHive " * 1000) + bytes(range(256))
    packed = compressor.compress(algo, 6, data)
    assert packed != data
    assert compressor.decompress(algo, 6, packed) == data


@pytest.mark.parametrize("algo", ["gzip", "bz2", "lzma"])
def test_empty_payload(algo: str) -> None:
    packed = compressor.compress(algo, 6, b"")
    assert compressor.decompress(algo, 6, packed) == b""


def test_compression_ratio_for_repetitive_data() -> None:
    data = b"abc" * 10000
    packed = compressor.compress("lzma", 6, data)
    assert len(packed) < len(data) // 10


def test_unknown_algorithm_rejected() -> None:
    with pytest.raises(ValueError):
        compressor.compress("zip", 6, b"data")
    with pytest.raises(ValueError):
        compressor.decompress("zip", 6, b"data")


def test_invalid_level_rejected() -> None:
    with pytest.raises(ValueError):
        compressor.compress("gzip", 10, b"data")
    with pytest.raises(ValueError):
        compressor.compress("bz2", 0, b"data")


def test_sim_returns_data_unchanged() -> None:
    """Algoritma sim hanya untuk test: data dikembalikan apa adanya."""
    data = b"simulasi" * 10
    assert compressor.compress("sim", 6, data) == data
    assert compressor.decompress("sim", 6, data) == data


def test_sim_delay_scales_with_size() -> None:
    assert compressor.sim_delay_seconds(0) == 0.0
    small = compressor.sim_delay_seconds(1024 * 1024)
    large = compressor.sim_delay_seconds(4 * 1024 * 1024)
    assert large == pytest.approx(small * 4)


def test_algorithms_registry() -> None:
    assert set(compressor.ALGORITHMS) == {"gzip", "bz2", "lzma", "sim"}
    assert compressor.file_extension("gzip") == "gz"
    assert compressor.file_extension("bz2") == "bz2"
    assert compressor.file_extension("lzma") == "xz"
    assert compressor.file_extension("sim") == "sim"
