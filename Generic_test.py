import time
from unittest.mock import patch, MagicMock
from execute_tool import execute_tool_with_retry, make_tool_error, make_tool_success

def test_retry_success_after_failures():
    """Test that retry wrapper succeeds after two connection errors."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "get_city_weather"
    mock_tool_call.function.arguments = '{"city": "Delhi"}'

    # Simulate execute_tool failing twice with connection_error, then succeeding
    with patch("execute_tool.execute_tool", side_effect=[
        make_tool_error("connection_error", "Failed 1"),
        make_tool_error("connection_error", "Failed 2"),
        make_tool_success("Delhi: 🌡️+26°C")
    ]) as mock_exec:
        deadline = time.monotonic() + 15
        result = execute_tool_with_retry(mock_tool_call, deadline)

        # Assertions
        assert result["status"] == "success"
        assert "Delhi" in result["result"]
        assert mock_exec.call_count == 3


def test_deadline_expiration_timeout():
    """Test that the retry wrapper stops and returns a timeout if deadline is too tight."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "get_city_weather"
    mock_tool_call.function.arguments = '{"city": "Delhi"}'

    # Force a connection error on attempt 1, but set a deadline that expires immediately
    with patch("execute_tool.execute_tool", return_value=make_tool_error("connection_error", "Failed")):
        # Set deadline in the past or extremely close so backoff delay triggers timeout
        deadline = time.monotonic() + 0.001 
        result = execute_tool_with_retry(mock_tool_call, deadline)

        assert result["status"] == "error"
        assert result["error_type"] == "timeout"