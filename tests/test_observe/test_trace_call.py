"""observe.trace-call tests."""
import json
import time
from pathlib import Path

import pytest

from agent_tools.observe.trace_call import trace_call, _active_traces


class TestTraceCall:
    """Tests for trace_call."""

    @pytest.fixture(autouse=True)
    def clear_traces(self):
        """Clear active traces between tests."""
        _active_traces.clear()

    def test_start_returns_trace_id(self, tmp_path: Path):
        """Start phase returns a trace_id."""
        log_file = tmp_path / "trace.jsonl"
        result = json.loads(trace_call(str(log_file), "test.tool", "start"))

        assert "trace_id" in result
        assert result["phase"] == "start"

    def test_end_requires_trace_id(self, tmp_path: Path):
        """End phase requires trace_id."""
        log_file = tmp_path / "trace.jsonl"
        result = json.loads(trace_call(str(log_file), "test.tool", "end"))

        assert "error" in result

    def test_end_returns_duration(self, tmp_path: Path):
        """End phase returns duration in milliseconds."""
        log_file = tmp_path / "trace.jsonl"

        start_result = json.loads(trace_call(str(log_file), "test.tool", "start"))
        trace_id = start_result["trace_id"]

        time.sleep(0.01)

        end_result = json.loads(trace_call(str(log_file), "test.tool", "end", trace_id=trace_id))

        assert end_result["phase"] == "end"
        assert end_result["duration_ms"] >= 10

    def test_logs_both_phases(self, tmp_path: Path):
        """Both start and end are logged to file."""
        log_file = tmp_path / "trace.jsonl"

        start_result = json.loads(trace_call(str(log_file), "test.tool", "start"))
        trace_id = start_result["trace_id"]
        trace_call(str(log_file), "test.tool", "end", trace_id=trace_id)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

        start_entry = json.loads(lines[0])
        end_entry = json.loads(lines[1])

        assert start_entry["phase"] == "start"
        assert end_entry["phase"] == "end"
        assert start_entry["trace_id"] == end_entry["trace_id"]

    def test_start_includes_params(self, tmp_path: Path):
        """Start can include parameters data."""
        log_file = tmp_path / "trace.jsonl"
        params = json.dumps({"arg1": "value1"})

        trace_call(str(log_file), "test.tool", "start", data=params)

        entry = json.loads(log_file.read_text().strip())
        assert entry["params"]["arg1"] == "value1"

    def test_end_includes_result(self, tmp_path: Path):
        """End can include result data."""
        log_file = tmp_path / "trace.jsonl"

        start_result = json.loads(trace_call(str(log_file), "test.tool", "start"))
        trace_id = start_result["trace_id"]

        result_data = json.dumps({"status": "success"})
        trace_call(str(log_file), "test.tool", "end", data=result_data, trace_id=trace_id)

        lines = log_file.read_text().strip().split("\n")
        end_entry = json.loads(lines[1])
        assert end_entry["result"]["status"] == "success"

    def test_invalid_phase(self, tmp_path: Path):
        """Invalid phase returns error."""
        log_file = tmp_path / "trace.jsonl"
        result = json.loads(trace_call(str(log_file), "test.tool", "invalid"))

        assert "error" in result
