import os
import asyncio
from typing import Optional

# Ensure configurations are checked and environment variables populated first
import src.config
from src.graph import app
from src.utils import print_stream

async def main():
    groq_key = os.environ.get("GROQ_API_KEY", "")
    core_key = os.environ.get("CORE_API_KEY", "")

    if groq_key == "DUMMY_KEY_PLACEHOLDER" or not groq_key:
        print("\n" + "!" * 50)
        print("ERROR: GROQ_API_KEY is not set!")
        print("Please copy '.env.example' to '.env', and fill in your GROQ_API_KEY.")
        print("!" * 50 + "\n")
        return

    if not core_key:
        print("\n" + "!" * 50)
        print("ERROR: CORE_API_KEY is not set!")
        print("Please copy '.env.example' to '.env', and fill in your CORE_API_KEY.")
        print("!" * 50 + "\n")
        return

    test_inputs = [
        "Download and summarize the findings of this paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC11379842/pdf/11671_2024_Article_4070.pdf",
        "Can you find 8 papers on quantum machine learning?",
        "Find recent papers (2023-2024) about CRISPR applications in treating genetic disorders, focusing on clinical trials and safety protocols",
        "Find and analyze papers from 2023-2024 about the application of transformer architectures in protein folding prediction, specifically looking for novel architectural modifications with experimental validation."
    ]

    outputs = []
    for idx, test_input in enumerate(test_inputs):
        if idx > 0:
            print("\nWaiting 25 seconds to avoid Gemini/Groq free-tier rate limits...")
            await asyncio.sleep(25)
        try:
            final_answer = await print_stream(app, test_input)
            if final_answer:
                outputs.append((test_input, final_answer.content))
        except Exception as e:
            print(f"Error executing query '{test_input}': {e}")

    print("\n" + "="*50)
    print("## TEST RESULTS")
    print("="*50 + "\n")
    for idx, (query, output) in enumerate(outputs, 1):
        print(f"### Test {idx}: Input:\n{query}\n")
        print(f"### Test {idx}: Output:\n{output}\n")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
