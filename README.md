# uniprot2s3

This repository performs the API calls necessary to download Uniprot data to s3. 

## Microbial subset from kg-microbe

The first step will download the `exclusion_branches.tsv` and `ncbitaxon_removed_subset.json` to the `data/raw` directory. The `ncbitaxon_removed_subset.json` file is used to query only the set of microbes from the kg-microbe repository in UniProt. 

To run, execute the `make all` command.

## Human only subset

Switch to the `human_query` branch, and execute the `make uniprot-download` command. 

# Acknowledgements

This [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) project was developed from the [monarch-project-template](https://github.com/monarch-initiative/monarch-project-template) template and will be kept up-to-date using [cruft](https://cruft.github.io/cruft/).
