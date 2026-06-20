"""
test_models.py
Run this once to see exactly which Gemini models your API key can use.
Usage: python test_models.py
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY not found. Check your .env file.")

genai.configure(api_key=api_key)

print("Models available to your key that support generate_content:\n")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(" -", m.name)