import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from security.redaction import redact
from integration.log_watch import parse_input_line


def test_redact_password():
    s = 'SteamPassword": "secret123"'
    assert "secret123" not in redact(s)


def test_parse_getuserinput():
    line = "2026-08-14 10:12:07|ArchiSteamFarm-1|WARN|ASF|GetUserInput() <f4rm> Aprove no app"
    req = parse_input_line(line)
    assert req is not None
    assert req.bot_name == "f4rm"


def test_skip_entrada_echo():
    line = "INFO|ASF|GetUserInput() Entrada: y"
    assert parse_input_line(line) is None


if __name__ == "__main__":
    test_redact_password()
    test_parse_getuserinput()
    test_skip_entrada_echo()
    print("tests_ok")
