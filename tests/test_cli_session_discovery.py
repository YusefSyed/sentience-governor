"""Session discovery (`_session_start_epoch`, `_list_session_files`).

These back `sentience list`, `open --latest` and `analyze --latest`. A trace
whose first line is unreadable must fall back to mtime ordering, never raise.
"""

import json
import os

import pytest

from sentience_governor.cli import ux as cli_ux


def _event(ts: str) -> str:
    return json.dumps(
        {"session_id": "s1", "event_type": "TOOL_CALL", "timestamp_utc": ts}
    )


class TestSessionStartEpoch:
    def test_reads_first_event_timestamp(self, tmp_path):
        trace = tmp_path / "ok.jsonl"
        trace.write_text(_event("2026-04-14T00:00:00.000Z") + "\n")
        assert cli_ux._session_start_epoch(trace) == pytest.approx(1776124800.0)

    @pytest.mark.parametrize("first_line", ["[]", "null", "123", '"text"'])
    def test_non_object_first_line_returns_none(self, tmp_path, first_line):
        """Valid JSON that is not an object has no timestamp to read."""
        trace = tmp_path / "odd.jsonl"
        trace.write_text(
            first_line + "\n" + _event("2026-04-14T00:00:00.000Z") + "\n"
        )
        assert cli_ux._session_start_epoch(trace) is None


class TestListSessionFiles:
    @pytest.mark.parametrize("first_line", ["[]", "null", "123", '"text"'])
    def test_non_object_first_line_falls_back_to_mtime(
        self, tmp_path, first_line
    ):
        """One odd trace must not break listing for every session."""
        good = tmp_path / "good.jsonl"
        good.write_text(_event("2026-04-14T00:00:00.000Z") + "\n")
        odd = tmp_path / "odd.jsonl"
        odd.write_text(first_line + "\n")
        # The odd file has no readable start time, so it is ordered by mtime.
        # Set it later than the good file's start time: it should sort first.
        os.utime(odd, (1776124900.0, 1776124900.0))

        assert cli_ux._list_session_files(tmp_path) == [odd, good]
