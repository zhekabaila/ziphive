#!/bin/sh
# ZipHive - siapkan laptop ini sebagai node (macOS). Klik dua kali dari Finder.
set -u
cd "$(dirname "$0")" || exit 1

# Pakai venv proyek bila sudah dibuat oleh setup-node agar Python sistem tidak tersentuh.
if [ -x ".venv/bin/python" ]; then
    PYTHON=.venv/bin/python
elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
else
    PYTHON=python
fi

"$PYTHON" scripts/bootstrap_node.py "$@"
STATUS=$?
printf '\nSelesai dengan kode %s. Tekan Enter untuk menutup jendela ini.\n' "$STATUS"
read -r _
exit "$STATUS"
