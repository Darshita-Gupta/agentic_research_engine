import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Check for presence of required keys
groq_key_missing = not os.environ.get("GROQ_API_KEY")
core_key_missing = not os.environ.get("CORE_API_KEY")

if groq_key_missing:
    print("INFO: GROQ_API_KEY environment variable not set. Setting dummy placeholder for compilation.")
    os.environ["GROQ_API_KEY"] = "DUMMY_KEY_PLACEHOLDER"

if core_key_missing:
    print("INFO: CORE_API_KEY environment variable not set. Please set it in your .env file.")
