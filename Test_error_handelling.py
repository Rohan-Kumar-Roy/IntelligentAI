from types import SimpleNamespace
from execute_tool import execute_tool

test_call = SimpleNamespace(
    id="call_success",
    function=SimpleNamespace(
        name="get_city_weather",
        arguments='{"city": "Delhi"}'
    )
)
print(execute_tool(test_call))


test_call = SimpleNamespace(
    id="call_validation",
    function=SimpleNamespace(
        name="get_city_weather",
        arguments='{"city": 123}'
    )
)
print(execute_tool(test_call))

test_call = SimpleNamespace(
    id="call_unknown",
    function=SimpleNamespace(
        name="unknown_tool_name",
        arguments='{}'
    )
)
print(execute_tool(test_call))

test_call = SimpleNamespace(
    id="call_json",
    function=SimpleNamespace(
        name="get_city_weather",
        arguments='{"city": "Delhi"'  # Missing closing bracket
    )
)
print(execute_tool(test_call))


