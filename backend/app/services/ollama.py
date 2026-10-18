import json

import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:8b"


def generate_answer(
    system_prompt: str,
    user_prompt: str,
) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "stream": False,
            "think": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "num_predict": 512,
                "temperature": 0,
            },
        },
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    content = data["message"]["content"]

    # Verify that the model actually returned valid JSON.
    # This gives us an early, consistent failure instead of
    # allowing malformed JSON to travel deeper into Burhān.
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Ollama returned invalid JSON: {content}"
        ) from exc

    return content