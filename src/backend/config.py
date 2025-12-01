# src/backend/config.py

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")

if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set in .env")
