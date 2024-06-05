"""Constants for robot_utilities."""

from pathlib import Path

RAW_DATA_DIR = Path(__file__).parents[2] / "data" / "raw"

# NCBITaxon
NCBITAXON_PREFIX = "NCBITaxon:"

# ROBOT
ROBOT_REMOVED_SUFFIX = "_removed_subset"
EXCLUSION_TERMS_FILE = "exclusion_branches.tsv"

# Uniprot
UNIPROT_BASE_URL = "https://rest.uniprot.org/uniprotkb/"
UNIPROT_FIELDS = [
    "organism_id",
    "id",
    "accession",
    "protein_name",
    "ec",
    "ft_binding",
    "go",
    "xref_proteomes",
    "rhea",
    "cc_pathway",
    "reviewed",
    "cc_function",
    "cc_disease",
    "gene_primary",
]
UNIPROT_KEYWORDS = ["Reference+proteome"]  # Not useful
UNIPROT_DESIRED_FORMAT = "tsv"
UNIPROT_SIZE = 500
ORGANISM_ID_MIXED_CASE = "Organism_ID"
TAXONOMY_ID_UNIPROT_PREFIX = "taxonomy_id:"
UNIPROT_REVIEWED_FLAG = "reviewed:true+"  # Not useful
UNIPROT_REFERENCE_PROTEOMES_URL = "https://rest.uniprot.org/proteomes/"
UNIPROT_REFERENCE_PROTEOMES_FIELDS = ["upid", "organism_id"]
PROTEOMES_FILENAME = "Proteomes"
PROTEOMES_PROTEOME_ID_COLUMNNAME = "Proteome Id"
PROTEOMES_ORGANISM_ID_COLUMNNAME = "Organism Id"
KGMICROBE_PROTEOMES_FILENAME = "Proteomes_KGMicrobe_Subset"

#UNIPROT_S3_DIR = RAW_DATA_DIR / "/s3"
