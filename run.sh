#!/usr/bin/env bash
cd "$(dirname "$0")"
# sem terminal extra se lançado por atalho
exec python3 main.py
