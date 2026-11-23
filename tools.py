from datetime import datetime
import requests
from Utilities.utilities import log
import threading
import time

TOOL_SCHEMAS = {
    "get_current_time": {
        "required": {}, 
        "optional": {}
    },
    "get_city_weather": {
        "required": {"city": str}, 
        "optional": {}
    },
    "get_user_city": {
        "required": {}, 
        "optional": {}
    },
    "slow_test_tool": {
        "required": {},
        "optional": {"seconds": int}
    },
    "process_payment": {
        "required": {"amount": int, "idempotency_key": str},
        "optional": {}
    }
}

# 🆕 ADD THIS MISSING VALIDATOR FUNCTION
def validate_tool_args(func_name, args):
    schema = TOOL_SCHEMAS.get(func_name)
    if schema is None:
        raise ValueError(f"No schema found for tool: {func_name}")

    required = schema["required"]
    optional = schema["optional"]

    # Check required arguments
    for arg_name in required:
        if arg_name not in args:
            raise ValueError(f"Missing required argument: {arg_name}")

    # Check unexpected arguments
    allowed_args = set(required) | set(optional)
    supplied_args = set(args)
    unexpected = supplied_args - allowed_args
    if unexpected:
        raise ValueError(f"Unexpected arguments: {unexpected}")

    # Validate argument types
    all_args = {**required, **optional}
    for arg_name, value in args.items():
        expected_type = all_args[arg_name]
        
        # Prevent bool from being accepted as int
        if expected_type is int:
            valid_type = type(value) is int
        else:
            valid_type = isinstance(value, expected_type)

        if not valid_type:
            raise TypeError(f"Argument '{arg_name}' must be {expected_type.__name__}")

        # Reject empty or whitespace-only strings
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"Argument '{arg_name}' cannot be empty")

    return True

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %I:%M %p")

def get_city_weather(city):
    url = f"https://wttr.in/{city}?format=4"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text

def get_user_city():
    return "Patna"

def slow_test_tool(seconds: int = 20):
    log("Slow tool started, sleeping for 20s...")
    time.sleep(seconds)
    log("Slow tool FINISHED!")
    return "Slow tool completed successfully."

IDEMPOTENCY_STORE = {}
IDEMPOTENCY_LOCK = threading.Lock()
PAYMENT_CALL_COUNT = 0

def process_payment(amount, idempotency_key):
    global PAYMENT_CALL_COUNT
    with IDEMPOTENCY_LOCK:
        # Check if this logical payment has already been processed
        if idempotency_key in IDEMPOTENCY_STORE:
            return IDEMPOTENCY_STORE[idempotency_key]
        
        result = {
            "payment_status": "success",
            "amount": amount,
            "transaction_id": "txn_001"
        }
        
        # Store the outcome against this key
        IDEMPOTENCY_STORE[idempotency_key] = result
        PAYMENT_CALL_COUNT += 1

        # Simulate lost response AFTER successful payment on the first attempt
        if PAYMENT_CALL_COUNT == 1:
            raise requests.exceptions.ConnectionError(
                "Simulated connection failure after payment"
            )
            
        return result


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns current date and time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_weather",
            "description": "Returns weather for a given city name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The exact name of the city.",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_city",
            "description": "Call this FIRST to get the user's home city name.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slow_test_tool",
            "description": "Simulates a slow tool execution for testing deadlines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "integer", "description": "Number of seconds to sleep."}
                },
                "required": []
            },
        },
    },
  {
        "type": "function",
        "function": {
            "name": "process_payment",
            "description": "Processes a payment transaction securely with idempotency support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer", 
                        "description": "The amount to charge."
                    },
                    "idempotency_key": {
                        "type": "string", 
                        "description": "Unique key to prevent duplicate charges."
                    }
                },
                "required": ["amount", "idempotency_key"]
            },
        },
    },
]  

FUNCTION_NAME_TO_MAP = {
    "get_current_time" : get_current_time,
    "get_city_weather" : get_city_weather,
    "get_user_city"    : get_user_city,
    "slow_test_tool": slow_test_tool,
    "process_payment": process_payment,
}