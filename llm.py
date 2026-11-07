import os
import time

from openai import OpenAI

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

VOIDAI_BASE_URL = os.getenv("VOIDAI_BASE_URL", "https://api.voidai.app/v1")
MODEL_FAST = os.getenv("VOIDAI_MODEL_FAST", "gpt-4o-mini")
MODEL_LARGE = os.getenv("VOIDAI_MODEL_LARGE", "gpt-5.6-luna")

client = OpenAI(
    api_key=os.getenv("VOIDAI_API_KEY", ""),
    base_url=VOIDAI_BASE_URL,
)


def chat(messages, model=None, temperature=None, retries=5):
    kwargs = {"model": model or MODEL_FAST, "messages": messages}
    if temperature is not None:
        kwargs["temperature"] = temperature

    for _ in range(retries):
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                time.sleep(5)
            elif "503" in err_str or "502" in err_str:
                time.sleep(3)
            else:
                print("Ошибка API:", e)
                return None
    return None