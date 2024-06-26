all: exclusion-branches ncbi_removed_subset uniprot-download

exclusion-branches:

	wget "https://kg-hub.berkeleybop.io/kg-microbe/current/raw/exclusion_branches.tsv" -O data/raw/exclusion_branches.tsv

ncbi_removed_subset:

	wget "https://kg-hub.berkeleybop.io/kg-microbe/current/raw/ncbitaxon_removed_subset.json" -O data/raw/ncbitaxon_removed_subset.json

uniprot-download:
	PWD=$(pwd)
	uniprot2s3 run --show-status --input-dir $(PWD)/data/raw
