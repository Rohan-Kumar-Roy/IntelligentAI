from datetime import datetime
import json
import os
from Utilities.utilities import log
from dotenv import load_dotenv
from openai import OpenAI
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from execute_tool import execute_tool_with_retry, make_tool_error
from tools import TOOLS, FUNCTION_NAME_TO_MAP, validate_tool_args
import time
from concurrent.futures import wait
from execute_tool import execute_tool

load_dotenv()  # by default search for .env file

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

messages = [
    {
        "role": "system",
        "content": (
            "Act as a humble, concise agent. Keep replies within 5-10 words. "
            "Use conversation history for context when relevant, but answer only the current question directly without repeating past responses."
            "Never call payment tools unless the user explicitly specifies an amount to charge."
        )
    }
]

def stream_chat(history):
    
    stream = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=history,
        tools=TOOLS,
        stream=True,
    )
    
    full_response = ""
    calls = {}
    label_printed = False
    
    # Delta streaming part
    try:
        for chunk in stream:
            if not chunk.choices:
                continue
    
            delta = chunk.choices[0].delta
    
            if delta.content:
                if not label_printed:
                    print("\n 🤖 Assistant: ", end="", flush=True)
                    label_printed = True
                print(delta.content, end="", flush=True)
                full_response += delta.content
        
            # Tool call building part
            for tc in (delta.tool_calls or []):
                obj = calls.setdefault(
                    tc.index,
                    SimpleNamespace(id=None, function=SimpleNamespace(name="", arguments="")),
                )
        
                if tc.id:
                    obj.id = tc.id
        
                if tc.function and tc.function.name:
                    obj.function.name = tc.function.name
            
                if tc.function and tc.function.arguments:
                    obj.function.arguments += tc.function.arguments
            
    except (KeyboardInterrupt, EOFError):
        log("\n ⚠️ Interrupted by exit command\n =====EXIT=====")
        calls = {}
               
    if label_printed:
        print()  # Move to new line after assistant's response   
          
    calls_list = []
    for key in sorted(calls):
        calls_list.append(calls[key])
        
    return full_response, calls_list

def build_tool_calls_payload(tool_calls):
    payload = []
    for tool_call in tool_calls:
        tool_call_dict = {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            }
        }
        payload.append(tool_call_dict)
    return payload

# Helper function to handle individual tool execution for the thread pool
# Helper function to handle individual tool execution for the thread pool
while True:
    try:
        user_input = input("\n 👤 You: ")
    except (KeyboardInterrupt, EOFError):
        break

    if user_input.lower() in ["exit", "quit", "bye", "goodbye", "return"]:
        print("\nGoodbye!")
        break
      
    if not user_input.strip():
        continue

    messages.append({
        "role": "user",
        "content": user_input
    })
  
    # 2. Handle tool calls with a safety step limit
    max_calls = 5
    current_call = 0
    
    while True:
        full_response, tool_calls = stream_chat(messages)
        
        # Check if the model actually wants to call a tool
        if not tool_calls:
            messages.append({
                "role": "assistant",
                "content": full_response
            })
                
            break
        
        log(f"\n Current_call = {current_call} : model requested {len(tool_calls)} tool calls.")
            
        current_call += 1
        if current_call > max_calls:
            # Safety breakout if model loops too many times
            log("Maximum tool rounds exceeded.")
            fallback = "I couldn't complete the request within the tool execution limit."
            messages.append({
                "role": "assistant",
                "content": fallback
            })
            print("\n 🤖 Assistant: " + fallback)
            break
        
        messages.append({
            "role": "assistant",
            "content": full_response,
            "tool_calls": build_tool_calls_payload(tool_calls)
        })
            
        # ── Parallel Tool Execution with Retry Wrapper ──────────────────
        deadline = time.monotonic() + 15

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_tool = {
                executor.submit(
                    execute_tool_with_retry,
                    tool_call,
                    deadline
                ): tool_call
                for tool_call in tool_calls
            }

            remaining = max(0, deadline - time.monotonic())

            done, not_done = wait(
                future_to_tool.keys(),
                timeout=remaining
            )

            for future, tool_call in future_to_tool.items():
                if future in done:
                    try:
                        result = future.result()
                    except Exception as e:
                        result = make_tool_error(
                            "internal_error",
                            str(e)
                        )
                else:
                    future.cancel()
                    result = make_tool_error(
                        "timeout",
                        "Batch deadline exceeded."
                    )

                log(f"\n 🔧 {tool_call.function.name}: {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
                #Updated Recently