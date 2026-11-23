import json
import requests
from Utilities.utilities import log
from tools import TOOLS, FUNCTION_NAME_TO_MAP, validate_tool_args
import time
import uuid

MAX_RETRIES = 2
BASE_DELAY = 1

def retry_delay(retry_number):
    return BASE_DELAY * (2 ** (retry_number - 1))


def make_tool_error(error_type, message):
    return {
        "status": "error",
        "error_type": error_type,
        "message": message
    }

def make_tool_success(result):
    return {
        "status": "success",
        "result": result
    }
    
    
def execute_tool_with_retry(tool_call, deadline):
    # 1. Generate an idempotency key once for this logical payment operation
    operation_context = {}
    if tool_call.function.name == "process_payment":
        operation_context["idempotency_key"] = str(uuid.uuid4())

    for attempt in range(MAX_RETRIES + 1):

        # Stop if the overall batch deadline has expired
        remaining = deadline - time.monotonic()

        if remaining <= 0:
            return make_tool_error(
                "timeout",
                "Batch deadline exceeded."
            )

        # Pass operation_context down to execute_tool
        result = execute_tool(tool_call, operation_context)

        # Successful execution: return immediately
        if result["status"] == "success":
            return result

        # Only connection errors are retryable for now
        if result["error_type"] != "connection_error":
            return result

        # All attempts have been exhausted
        if attempt == MAX_RETRIES:
            return result

        # Calculate exponential backoff
        delay = retry_delay(attempt + 1)

        # Do not begin another retry if its delay
        # would consume the remaining batch budget
        remaining = deadline - time.monotonic()

        if delay >= remaining:
            return make_tool_error(
                "timeout",
                "Insufficient time remaining for another retry."
            )

        log(
            f"\n Retry {attempt + 1}/{MAX_RETRIES} "
            f"for {tool_call.function.name} "
            f"after {delay} seconds..."
        )

        time.sleep(delay)

    return make_tool_error(
        "internal_error",
        "Unexpected retry loop termination."
    )
    
    
def execute_tool(tool_call, operation_context=None):
    func_name = tool_call.function.name

    # Step 1: Check allowlist
    function = FUNCTION_NAME_TO_MAP.get(func_name)

    if function is None:
        return make_tool_error(
            "unknown_tool",
            f"Unknown tool: {func_name}"
        )

    try:
        # Step 2: Parse JSON
        args = json.loads(
            tool_call.function.arguments or "{}"
        )

        # Step 3: Check dictionary
        if not isinstance(args, dict):
            return make_tool_error(
                "invalid_arguments",
                "Tool arguments must be a JSON object."
            )

        # Step 4: Validate arguments
        validate_tool_args(func_name, args)

        # Step 5: Inject idempotency key for payment tool
        if func_name == "process_payment" and operation_context:
            args["idempotency_key"] = operation_context.get("idempotency_key")

        # Step 6: Execute function
        result = function(**args)

        return make_tool_success(str(result))

    except json.JSONDecodeError:
        return make_tool_error(
            "invalid_json",
            "Invalid JSON arguments."
        )

    except (ValueError, TypeError) as e:
        return make_tool_error(
            "validation_error",
            str(e)
        )

    except requests.exceptions.ConnectionError:
        return make_tool_error(
            "connection_error",
            "Unable to connect to the external service."
        )

    except requests.exceptions.Timeout:
        return make_tool_error(
            "timeout",
            "The external service timed out."
        )

    except Exception as e:
        return make_tool_error(
            "internal_error",
            str(e)
        )