all: exclusion-branches ncbi_removed_subset uniprot-download

exclusion-branches:

	wget "https://kg-hub.berkeleybop.io/kg-microbe/current/raw/exclusion_branches.tsv" -O data/raw/exclusion_branches.tsv

ncbi_removed_subset:

	wget "https://kg-hub.berkeleybop.io/kg-microbe/current/raw/ncbitaxon_removed_subset.json" -O data/raw/ncbitaxon_removed_subset.json
	pwd
	ls -l data/raw

uniprot-download:

	uniprot2s3 run --no-show-status --input-dir data/raw/
