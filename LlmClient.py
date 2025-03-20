# LlmClient.py
from openai import OpenAI
import keys

def get_openai_client():
  return get_volce_engine()

def getDeepSeek():
  return OpenAI(
      api_key=keys.OPENAI_API_KEY,
      base_url="https://api.deepseek.com"
  )
def get_volce_engine():
  client = OpenAI(
      api_key = keys.VOLCENGINE_API_KEY,
      base_url = "https://ark.cn-beijing.volces.com/api/v3",
  )