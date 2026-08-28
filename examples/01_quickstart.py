"""
01_quickstart.py: Basic biomedical reasoning with Biomni-Plus
"""

import os
from dotenv import load_dotenv
load_dotenv(override=True)

from biomni_plus import create_biomni_plus_agent

def main():
    print("Initializing Biomni-Plus Agent...")
    agent = create_biomni_plus_agent(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        data_path="./data",
        modules=["database", "genomics", "literature"],
    )

    query = "What is the official gene symbol and function of UniProt P04637? Answer in 2 sentences."
    print(f"\nQuery: {query}\n")

    response = agent.go(query)
    print("=== Response ===")
    print(response)

if __name__ == "__main__":
    main()
