import json
import os
import time
from typing import List, Optional, Dict, Union, Any

import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

app = FastAPI(title="OpenAI-compatible CoT API")

load_dotenv()
# Get API key and endpoint URL from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY").replace('"', "").replace("'", "")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE").replace('"', "").replace("'", "")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
if not OPENAI_API_BASE:
    raise ValueError("OPENAI_API_BASE environment variable is not set")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "mock-gpt-model"
    messages: List[Message]
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = None
    # max_completion_tokens: Optional[int] = None
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
    service_tier: Optional[str] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    stream_options: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    # parallel_tool_calls: Optional[bool] = True
    user: Optional[str] = None
    max_tokens: Optional[int] = 512  # Added max_tokens for backward compatibility


async def _resp_async_generator(
    text_resp: str, request: ChatCompletionRequest
):  # Pass request object
    # let's pretend every word is a token and return it over time
    tokens = text_resp.split(" ")

    for i, token in enumerate(tokens):
        chunk = {
            "id": i,
            "object": "chat.completion.chunk",
            "created": time.time(),
            "model": request.model,
            "choices": [{"delta": {"content": token + " "}}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def call_actual_openai_endpoint(payload):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    response = requests.post(
        OPENAI_API_BASE + "/chat/completions",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()


@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        data = request.model_dump()

        # Capture last user message
        user_content = data["messages"][-1]["content"]
        # Capture metadata
        model = data.get("model", "gpt-4o")
        temperature = data.get("temperature", 1)
        max_tokens = data.get("max_tokens", 4096)
        top_p = data.get("top_p", 1)
        frequency_penalty = data.get("frequency_penalty", 0.0)
        presence_penalty = data.get("presence_penalty", 0.0)
        logit_bias = data.get("logit_bias", None)
        logprobs = data.get("logprobs", False)
        top_logprobs = data.get("top_logprobs", None)
        # max_completion_tokens = data.get("max_completion_tokens", None)
        n = data.get("n", 1)
        response_format = data.get("response_format", None)
        seed = data.get("seed", None)
        service_tier = data.get("service_tier", None)
        stop = data.get("stop", None)
        stream_options = data.get("stream_options", None)
        tools = data.get("tools", None)
        tool_choice = data.get("tool_choice", None)
        # parallel_tool_calls = data.get("parallel_tool_calls", False)
        user_identifier = data.get("user", None)

        print(f"Incoming message: {user_content}")
        print(f"Proxy for {OPENAI_API_BASE}")

        # Modify initial message
        modified_content_1 = (
            "Help solve the user's request by generating a detailed step-by-step plan.\n"
            "Please ensure that your thought process is clear and detailed, as if you are instructing yourself on how to tailor an answer.\n"
            "Do not return an answer, just return the thought process as if it's between you and yourself.\n"
            "Please provide your response strictly in the following format and respect the <THOUGHT> tags:\n"
            "<THOUGHT> [Your short step-by-step plan] </THOUGHT>. User request: "
            + user_content
        )
        data["messages"][-1]["content"] = modified_content_1

        # New payload for first API call
        new_payload_1 = {
            "messages": data["messages"],
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "logit_bias": logit_bias,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            # "max_completion_tokens": max_completion_tokens,
            "n": n,
            "response_format": response_format,
            "seed": seed,
            "service_tier": service_tier,
            "stop": stop,
            "stream_options": stream_options,
            "tools": tools,
            "tool_choice": tool_choice,
            # "parallel_tool_calls": parallel_tool_calls,
            "user": user_identifier,
        }

        # Send POST request to external API (first call)
        response_1 = await call_actual_openai_endpoint(new_payload_1)

        # Capture thoughtProcess from first response
        thought_process = response_1["choices"][0]["message"]["content"]
        print(f"\nThought process: {thought_process}\n")

        # Modify second message with captured thoughtProcess
        modified_content_2 = (
            f"You are a human reflecting on your own thought process to provide a refined final answer to the user.\n\n"
            f"Here is your thought process:\n{thought_process}\n\nYour task:\n\n"
            f"1. Provide a final answer to the user's request based on your thought process.\n\n"
            "**Important:** Do not include the thought process or mention that you reviewed it in your final answer. Just provide the final answer to the user.\n\n"
            f"The user's original request:\n{user_content}"
        )

        # Edit the response to include the modified content and role
        response_1["choices"][0]["message"]["content"] = modified_content_2
        response_1["choices"][0]["message"]["role"] = "user"
        # Remove the "tool_calls" key from the response
        response_1["choices"][0]["message"].pop("tool_calls", None)

        # Replace the original input message with the modified message
        data["messages"][-1] = [response_1["choices"][0]["message"]][0]

        # New payload for second API call
        new_payload_2 = {
            "messages": data["messages"],
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "logit_bias": logit_bias,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            # "max_completion_tokens": max_completion_tokens,
            "n": n,
            "response_format": response_format,
            "seed": seed,
            "service_tier": service_tier,
            "stop": stop,
            "stream_options": stream_options,
            "tools": tools,
            "tool_choice": tool_choice,
            # "parallel_tool_calls": parallel_tool_calls,
            "user": user_identifier,
        }

        # Send POST request to external API (second call)
        response_2 = await call_actual_openai_endpoint(new_payload_2)

        # Extract relevant information from second response
        response_data = response_2
        response_id = response_data["id"]
        response_object = response_data["object"]
        created_time = response_data["created"]
        model_name = response_data["model"]
        system_fingerprint = response_data.get("system_fingerprint", None)
        role = response_data["choices"][0]["message"]["role"]
        final_answer = response_data["choices"][0]["message"]["content"]
        logprobs = response_data["choices"][0].get("logprobs", None)
        finish_reason = response_data["choices"][0]["finish_reason"]
        usage_data = response_data["usage"]

        print(final_answer)

        if request.stream:
            return StreamingResponse(
                _resp_async_generator(final_answer, request),
                media_type="application/x-ndjson",
            )

        return {
            "id": response_id,
            "object": response_object,
            "created": created_time,
            "model": model_name,
            "system_fingerprint": system_fingerprint,
            "choices": [
                {
                    "message": {"role": role, "content": final_answer},
                    "logprobs": logprobs,
                    "finish_reason": finish_reason,
                }
            ],
            "usage": usage_data,
        }

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument(
        "--port",
        type=str,
        default="5001",
        help="Port to run the server on (default: 5001)",
    )
    args = parser.parse_args()

    uvicorn.run(app, host="0.0.0.0", port=int(args.port))
