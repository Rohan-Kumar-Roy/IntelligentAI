from execute_tool  import execute_tool
from types import SimpleNamespace
# --- TEMPORARY TEST BLOCK FOR LESSON 1.3 ---

if __name__ == "__main__":
    print("\n=== RUNNING LESSON 1.3 TEST SCENARIOS ===")
    
    scenarios = [
        SimpleNamespace(id="1", function=SimpleNamespace(name="get_city_weather", arguments='{"city": "Delhi"}')),
        SimpleNamespace(id="2", function=SimpleNamespace(name="get_city_weather", arguments='{"city": 123}')),
        SimpleNamespace(id="3", function=SimpleNamespace(name="get_city_weather", arguments='{}')),
        SimpleNamespace(id="4", function=SimpleNamespace(name="get_city_weather", arguments='{"city": "Delhi", "country": "India"}')),
        SimpleNamespace(id="5", function=SimpleNamespace(name="unknown_tool_name", arguments='{}')),
        SimpleNamespace(id="6", function=SimpleNamespace(name="get_city_weather", arguments='{"city": "Delhi" (broken json'))
    ]
    
    for call in scenarios:
        print(f"\nTesting tool: {call.function.name} with args: {call.function.arguments}")
        res = execute_tool(call)
        print(f"Output: {res}")
    print("\n==========================================") 


