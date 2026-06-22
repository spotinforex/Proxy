import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("DASHSCOPE_API_KEY")

client = OpenAI(
  api_key=key,
  base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
  model="qwen3.7-plus",
  messages=[
    {"role": "user", "content": "Hello! Tell me a fun fact about AI."}
  ]
)

print(completion.choices[0].message.content)