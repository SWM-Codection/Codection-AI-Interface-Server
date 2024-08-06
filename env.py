import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_PRIVATE_KEY = os.getenv("OPENAI_PRIVATE_KEY")

PR_STATIC_ANALYSIS_ID = os.getenv("ASSISTANT_ID")
SAMPLECODE_GENERATOR_ID = os.getenv("SAMPLECODE_GENERATOR_ID")