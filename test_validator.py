from tools import validate_tool_args

# Define the 10 test cases based on ChatGPT's checklist
# Format: (tool_name, arguments_dict, expected_to_pass: True/False)
test_cases = [
    # 1. Valid city weather call
    ("get_city_weather", {"city": "Delhi"}, True),
    
    # 2. Missing required argument
    ("get_city_weather", {}, False),
    
    # 3. Wrong data type (int instead of str)
    ("get_city_weather", {"city": 123}, False),
    
    # 4. Unexpected argument
    ("get_city_weather", {"city": "Delhi", "country": "India"}, False),
    
    # 5. Empty string argument
    ("get_city_weather", {"city": ""}, False),
    
    # 6. Valid get_current_time call (no arguments)
    ("get_current_time", {}, True),
    
    # 7. Unexpected argument for get_current_time
    ("get_current_time", {"extra": "value"}, False),
    
    # 8. Valid slow_test_tool call with optional int argument
    ("slow_test_tool", {"seconds": 10}, True),
    
    # 9. Invalid type for slow_test_tool (bool instead of int)
    ("slow_test_tool", {"seconds": True}, False),
    
    # 10. Valid slow_test_tool call with no optional arguments
    ("slow_test_tool", {}, True),
]

def run_tests():
    passed_count = 0
    failed_count = 0

    print("Running Validation Test Checklist...\n")
    for i, (tool_name, args, should_pass) in enumerate(test_cases, 1):
        test_passed = True
        error_message = None
        
        try:
            validate_tool_args(tool_name, args)
        except (ValueError, TypeError) as e:
            test_passed = False
            error_message = str(e)

        # Check if the result matches our expectation
        if test_passed == should_pass:
            print(f"Test {i:2d}: {tool_name}({args}) -> Expected {'Pass' : <5} | Got {'Pass' if test_passed else 'Fail'} ✅")
            passed_count += 1
        else:
            print(f"Test {i:2d}: {tool_name}({args}) -> Expected {'Pass' if should_pass else 'Fail'} | Got {'Pass' if test_passed else 'Fail'} ❌ (Error: {error_message})")
            failed_count += 1

    print(f"\nResult: {passed_count}/10 tests matched expectations successfully!")

if __name__ == "__main__":
    run_tests()