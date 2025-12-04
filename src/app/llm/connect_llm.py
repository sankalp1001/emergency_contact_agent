"""
LLM Connection Module
Handles connections to Groq LLM API with tool calling support using gpt-oss with harmony format
"""

from groq import Groq
from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Any, Optional, Generator

load_dotenv()

# Initialize Groq client
client = Groq()

# Model configuration - using gpt-oss with harmony output format
DEFAULT_MODEL = "openai/gpt-oss-120b"


def get_response_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system_prompt: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Get a response with tool calling support using harmony format
    
    Args:
        messages: Conversation message history
        tools: List of tool definitions
        system_prompt: System prompt for the LLM
        model: Model to use
    
    Returns:
        Complete response object with potential tool calls
    """
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    kwargs = {
        "model": model,
        "messages": full_messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    
    # Add tools if provided
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    
    response = client.chat.completions.create(**kwargs)
    
    return response


def get_simple_response(user_message: str, system_prompt: str = None) -> Generator[str, None, None]:
    """
    Get a simple streaming response without tool calling
    
    Args:
        user_message: User's message
        system_prompt: Optional system prompt
    
    Yields:
        Response chunks
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({
            "role": "system", 
            "content": "You are an Emergency Contact Agent built by Sankalp Mallappa. Keep responses short and helpful."
        })
    
    messages.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=0.3,
        stream=True
    )
    
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def get_streaming_response_with_history(
    messages: List[Dict[str, Any]],
    system_prompt: str,
    model: str = DEFAULT_MODEL
) -> Generator[str, None, None]:
    """
    Get a streaming response with conversation history (no tools)
    """
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    response = client.chat.completions.create(
        model=model,
        messages=full_messages,
        temperature=0.3,
        stream=True
    )
    
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def parse_tool_calls(response) -> List[Dict[str, Any]]:
    """Parse tool calls from LLM response"""
    tool_calls = []
    
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            
            tool_calls.append({
                "id": tool_call.id,
                "name": tool_call.function.name,
                "arguments": arguments
            })
    
    return tool_calls


def has_tool_calls(response) -> bool:
    """Check if response contains tool calls"""
    return (response.choices[0].message.tool_calls is not None and 
            len(response.choices[0].message.tool_calls) > 0)


def get_response_content(response) -> str:
    """Extract text content from response"""
    return response.choices[0].message.content or ""


def get_finish_reason(response) -> str:
    """Get the finish reason from response"""
    return response.choices[0].finish_reason


def format_tool_result_message(tool_call_id: str, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Format a tool result for sending back to the LLM"""
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": json.dumps(result)
    }


def format_assistant_message_with_tool_calls(content: str, tool_calls: list) -> Dict[str, Any]:
    """Format an assistant message that includes tool calls"""
    message = {
        "role": "assistant",
        "content": content or ""
    }
    
    if tool_calls:
        message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            }
            for tc in tool_calls
        ]
    
    return message


# Legacy function for backward compatibility
def get_response(user_message: str) -> Generator[str, None, None]:
    """Legacy function for simple responses"""
    return get_simple_response(user_message)


if __name__ == "__main__":
    print("=== Testing LLM Connection ===\n")
    print("Simple response test:")
    for chunk in get_simple_response("Hello, what can you help me with?"):
        print(chunk, end="", flush=True)
    print("\n")
