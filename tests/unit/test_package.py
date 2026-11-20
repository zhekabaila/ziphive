"""UT-BOOT-01: paket pcomp dapat diimpor dan versinya konsisten."""

from __future__ import annotations

import re

import pcomp
import pcomp.bench
import pcomp.master
import pcomp.metrics
import pcomp.tools
import pcomp.worker
from pcomp import constants


def test_package_importable() -> None:
    assert pcomp.__version__ == constants.__version__


def test_version_format() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", pcomp.__version__)


def test_project_constants() -> None:
    assert constants.PROJECT_NAME == "ZipHive"
    assert constants.PACKAGE_NAME == "pcomp"


def test_protocol_version_matches_protocol_doc() -> None:
    assert constants.PROTOCOL_VERSION == 1
