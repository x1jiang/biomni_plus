"""
02_genomics_query.py: Genomics & Target Discovery with Biomni-Plus
"""

import os
from dotenv import load_dotenv
load_dotenv(override=True)

from biomni_plus import create_biomni_plus_agent

def main():
    agent = create_biomni_plus_agent(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        modules=["database", "genomics", "literature"],
    )

    query = (
        "Retrieve the chromosomal coordinates and known disease-associated mutations "
        "for the human BRCA1 gene using Ensembl and ClinVar."
    )
    print(f"Executing Genomics Workflow: {query}\n")
    response = agent.go(query)
    print("=== Analysis Result ===")
    print(response)

if __name__ == "__main__":
    main()
