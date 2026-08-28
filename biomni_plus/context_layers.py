"""
Biomedical Context Layers for Biomni-Plus (ClawAgents Engine)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

# Ensure biomni can be imported from parent or installed env
_pkg_root = Path(__file__).resolve().parent.parent
for _candidate in [_pkg_root / "biomni", _pkg_root.parent / "biomni"]:
    if _candidate.exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))


class BiomniDataLakeLayer:
    """Injects Biomni curated datalake dataset index and lazy S3 paths."""

    name = "biomni_datalake"

    def __init__(self, data_path: str = "./data", commercial_mode: bool = False):
        self.data_path = data_path
        self.commercial_mode = commercial_mode

    def inject(self, run_context: Any) -> str | None:
        try:
            if self.commercial_mode:
                from biomni.env_desc_cm import data_lake_dict
            else:
                from biomni.env_desc import data_lake_dict

            items = [f"- {k}: {desc}" for k, desc in list(data_lake_dict.items())[:25]]
            catalog_text = "\n".join(items)
        except Exception:
            catalog_text = (
                "- BindingDB: Drug-target binding affinities\n"
                "- STRING: Protein-protein interaction network\n"
                "- GWAS_Catalog: Genome-wide association study variants\n"
                "- ClinVar: Clinical genomic variant classifications\n"
                "- AlphaFoldDB: Predicted 3D protein structures"
            )

        return (
            "### BIOMEDICAL DATA LAKE RESOURCES\n"
            f"Data Root Directory: {self.data_path}\n"
            "You have access to pre-indexed biological datasets (S3 lazy-loaded & local):\n"
            f"{catalog_text}\n"
            "(Use available domain tools or execute Python/Bash scripts to process these datasets)\n"
        )


class BiomniKnowHowLayer:
    """Injects standard biomedical operating procedures (SOPs) and protocol guides."""

    name = "biomni_knowhow"

    def __init__(self, commercial_mode: bool = False):
        self.commercial_mode = commercial_mode

    def inject(self, run_context: Any) -> str | None:
        try:
            from biomni.know_how import KnowHowLoader
            loader = KnowHowLoader()
            docs = loader.documents
            doc_titles = [d.get("title", d.get("id", "Protocol")) for d in docs[:10]]
            doc_list = "\n".join(f"- {title}" for title in doc_titles)
        except Exception:
            doc_list = (
                "- CRISPR guide RNA (sgRNA) design and off-target screening\n"
                "- Single-cell RNA-seq clustering and cell type annotation\n"
                "- GWAS causal variant mapping and fine-mapping\n"
                "- Molecular docking and pharmacokinetics screening"
            )

        return (
            "### BIOMEDICAL PROTOCOL & KNOW-HOW GUIDELINES\n"
            "Available Standard Operating Protocols:\n"
            f"{doc_list}\n"
        )


class BiomniADLayer:
    """Injects Alzheimer's Disease (AD) data priorities and NIAGADS/ADRD catalogs (Biomni-AD parity)."""

    name = "biomni_ad_catalog"

    def __init__(self, ad_data_path: Optional[str] = None):
        self.ad_data_path = ad_data_path or "./data/biomniAD"

    def inject(self, run_context: Any) -> str | None:
        return (
            "### ALZHEIMER'S DISEASE (AD) DATA PRIORITY POLICY\n"
            "When answering AD/neurodegeneration tasks:\n"
            "1. LOCAL FILES FIRST: Check local BiomniAD directories before triggering external queries.\n"
            "2. CATALOG SOURCES: Query NIAGADS, ADRD OpenGenomics, and BiomniAD Discovery catalogs.\n"
            "3. Ground truth integrity: Never fabricate genomic variants, OMIM IDs, or clinical phenotypes.\n"
        )
