"""
04_alzheimers_ad1.py: Alzheimer's Disease & Multi-Omics Analysis (Biomni-AD Parity)
"""

import os
from dotenv import load_dotenv
load_dotenv(override=True)

from biomni_plus import create_biomni_plus_agent

def main():
    # Initialize with is_ad_specialized=True
    agent = create_biomni_plus_agent(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        modules=["database", "genomics", "literature"],
        is_ad_specialized=True,
    )

    query = (
        "Explain the genetic and pathophysiological mechanisms of APOE4 in Alzheimer's Disease. "
        "Highlight how APOE4 differs from APOE2/APOE3 in amyloid-beta plaque deposition."
    )
    print(f"Executing AD Multi-Omics Analysis: {query}\n")
    response = agent.go(query)
    print("=== Alzheimer's Research Synthesis ===")
    print(response)

if __name__ == "__main__":
    main()
