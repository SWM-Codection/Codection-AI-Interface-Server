import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_PRIVATE_KEY = os.getenv("OPENAI_PRIVATE_KEY")

ASSISTANT_ID = os.getenv("ASSISTANT_ID")