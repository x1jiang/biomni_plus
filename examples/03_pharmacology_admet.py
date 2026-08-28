"""
03_pharmacology_admet.py: Drug discovery & chemoinformatics with Biomni-Plus
"""

import os
from dotenv import load_dotenv
load_dotenv(override=True)

from biomni_plus import create_biomni_plus_agent

def main():
    agent = create_biomni_plus_agent(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        modules=["database", "pharmacology", "biochemistry"],
    )

    query = (
        "Analyze the oncology drug Imatinib (SMILES: Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(C)CC5). "
        "Calculate its molecular weight, target kinase, and primary clinical indication."
    )
    print(f"Executing Pharmacology Query: {query}\n")
    response = agent.go(query)
    print("=== Drug Discovery Report ===")
    print(response)

if __name__ == "__main__":
    main()
