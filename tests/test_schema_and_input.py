"""Testes unitários leves — sem ASF rodando."""
from __future__ import annotations

from integration.input_types import detect_input_type, types_to_try
from integration.schema import _kind_from_type_name, _fields_from_structure
from security.redaction import redact


def test_detect_2fa():
    assert detect_input_type("Enter Steam Guard code") == "SteamGuard"
    assert detect_input_type("Two-factor authentication") == "TwoFactorAuthentication"
    assert "TwoFactorAuthentication" in types_to_try("unknown prompt")


def test_schema_kind():
    assert _kind_from_type_name("System.Boolean") == "bool"
    assert _kind_from_type_name("System.Int32") == "int"


def test_structure_parse():
    fields = _fields_from_structure({"Result": {"Enabled": "System.Boolean", "SteamLogin": "System.String"}})
    names = {f.name for f in fields}
    assert "Enabled" in names and "SteamLogin" in names


def test_redact():
    s = redact('password: "secret123" Authentication: tokendata')
    assert "***" in s


if __name__ == "__main__":
    test_detect_2fa()
    test_schema_kind()
    test_structure_parse()
    test_redact()
    print("OK")
