all: exclusion-branches uniprot-download

exclusion-branches:

	wget "https://raw.githubusercontent.com/Knowledge-Graph-Hub/kg-microbe/master/data/raw/exclusion_branches.tsv" -O data/raw/exclusion_branches.tsv

ncbi_removed_subset:

	#Will download from s3 bucket which will be put there by jenkins while running kg-microbe pipeline. Need to ask Harry for assistance.


uniprot-download:

	uniprot2s3 run
