"""S3 Utilities, including uploading and downloading data from S3."""

import csv
import json
import multiprocessing
import os
from functools import partial
from pathlib import Path
from typing import List, Union
from urllib import parse

import pandas as pd
import requests
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

from .constants import (
    CHUNK_SIZE_PER_WORKER,
    KGMICROBE_PROTEOMES_FILENAME,
    NCBITAXON_PREFIX,
    ORGANISM_ID_MIXED_CASE,
    PROTEOMES_FILENAME,
    PROTEOMES_ORGANISM_ID_COLUMNNAME,
    PROTEOMES_PROTEOME_ID_COLUMNNAME,
    RAW_DATA_DIR,
    TAXONOMY_ID_UNIPROT_PREFIX,
    UNIPROT_BASE_URL,
    UNIPROT_DESIRED_FORMAT,
    UNIPROT_FIELDS,
    UNIPROT_KEYWORDS,
    UNIPROT_REFERENCE_PROTEOMES_FIELDS,
    UNIPROT_REFERENCE_PROTEOMES_URL,
    UNIPROT_SIZE,
)
from .dummy_tqdm import DummyTqdm

ORGANISM_RESOURCE = "ncbitaxon_removed_subset.json"
EMPTY_ORGANISM_OUTFILE = RAW_DATA_DIR / "uniprot_empty_organism.tsv"

# Define UNIPROT_S3_DIR globally
UNIPROT_S3_DIR = Path(RAW_DATA_DIR).joinpath("s3")
UNIPROT_S3_DIR.mkdir(parents=True, exist_ok=True)

# Function to read organisms from a CSV file and return a set
def _read_organisms_from_csv(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return {str(row[ORGANISM_ID_MIXED_CASE]) for row in reader}


def _write_file(file_path, response, organism_id, mode="w"):
    # Write response to file if it contains data
    if len(response.text.strip().split("\n")) > 1:
        with open(file_path, mode) as file:
            file.write(response.text)
    else:
        # Append organism ID to the empty organisms file
        with open(EMPTY_ORGANISM_OUTFILE, mode) as tsv_file:
            tsv_file.write(f"{organism_id}\n")


def get_organism_list(input_dir: Union[Path, str] = RAW_DATA_DIR) -> List[str]:
    """
    Update organism list based on existing empty request files.

    :param organism_list: List of organism IDs.
    """
    # Read organism resource file and extract organism IDs
    with open(Path(input_dir) / ORGANISM_RESOURCE, "r") as f:
        contents = json.load(f)
        ncbi_prefix = NCBITAXON_PREFIX.replace(":", "_")

    # Create a list of organism IDs after filtering and cleaning
    organism_list = [
        i["id"].split(ncbi_prefix)[1]
        for i in contents["graphs"][0]["nodes"]
        if ncbi_prefix in i["id"] and i["id"].split(ncbi_prefix)[1].isdigit()
    ]
    # Update organism list based on existing empty request files
    for file_path in [EMPTY_ORGANISM_OUTFILE]:
        if file_path.is_file():
            no_info_organism_set = _read_organisms_from_csv(file_path)
            organism_list = list(set(organism_list) - no_info_organism_set)
        else:
            # Create file and write header if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as tsv_file:
                tsv_file.write(f"{ORGANISM_ID_MIXED_CASE}\n")
    return organism_list


def run_api(show_status: bool, input_dir=RAW_DATA_DIR) -> None:
    """
    Upload data to S3.

    :param api: A string pointing to the API to upload data to.
    :return: None
    """
    proteome_organism_list = run_proteome_api(show_status)
    UNIPROT_S3_DIR = Path(input_dir).joinpath("s3")
    UNIPROT_S3_DIR.mkdir(parents=True, exist_ok=True)
    # run_uniprot_api(proteome_organism_list, show_status) # ! Single worker.
    run_uniprot_api_parallel(
        taxa_id_from_proteomes_list=proteome_organism_list, show_status=show_status, input_dir=input_dir
    )  # ! Multiple workers.


def run_proteome_api(show_status: bool) -> list:
    """
    Download proteomes and organism_ids from Uniprot in series.

    :param show_status: Boolean flag to show progress status.
    :return: None
    """
    # ! Cannot be used during multiprocessing
    # Cache HTTP requests to avoid repeated calls
    # requests_cache.install_cache("uniprot_cache")

    # Ensure the directory for storing Uniprot files exists
    Path(RAW_DATA_DIR).mkdir(parents=True, exist_ok=True)

    organism_ids_list = fetch_uniprot_reference_proteome_data()

    return organism_ids_list


def construct_query_url(base_url, desired_format, query_terms, fields, query_size, keywords=None):
    """
    Single URL construction for Uniprot data.

    :param base_url: Base url for query.
    :param desired_format: Desired format of API response.
    :param query_terms: Query terms.
    :param fields: List of desired fields from API response.
    :param query_size: Size of API return.
    :param keywords: List of desired keywords from API response, default None.
    :param organism_id: Just if the ID of the NCBITaxon entity.
    """
    # Construct the query URL
    keywords_param = "&keywords=" + "+".join(keywords) if keywords else ""
    fields_param = "&fields=" + ",".join(map(parse.quote, fields))

    url = (
        f"{base_url}/search?query={query_terms}&format={desired_format}"
        f"&size={query_size}{keywords_param}{fields_param}"
    )

    return url


def fetch_uniprot_data(organism_id):
    """
    Single URL request for Uniprot data.

    :param organism_id: Just if the ID of the NCBITaxon entity.
    """
    file_path = UNIPROT_S3_DIR / f"{organism_id}.{UNIPROT_DESIRED_FORMAT}"
    organism_query = TAXONOMY_ID_UNIPROT_PREFIX + organism_id

    url = construct_query_url(
        UNIPROT_BASE_URL, UNIPROT_DESIRED_FORMAT, organism_query, UNIPROT_FIELDS, UNIPROT_SIZE, UNIPROT_KEYWORDS
    )

    try:
        # Make the HTTP request to Uniprot
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        _write_file(file_path, response, organism_id, "w")

        while "next" in response.links:
            next_url = response.links["next"]["url"]
            response = requests.get(next_url, timeout=30)
            response.raise_for_status()
            _write_file(file_path, response, organism_id, "a")

    except requests.exceptions.HTTPError:
        print(f"Bad request for organism {organism_id} - {response.status_code}")
    except requests.exceptions.Timeout:
        print("The request timed out")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def fetch_uniprot_reference_proteome_data() -> list:
    """Single URL request for Uniprot proteome data."""
    file_path = Path(RAW_DATA_DIR) / f"{PROTEOMES_FILENAME}.{UNIPROT_DESIRED_FORMAT}"
    all_proteomes_query = "%28*%29"
    # filtered_proteomes_query = (
    #     "((superkingdom:Bacteria)+OR+(superkingdom:Archaea))+AND+((proteome_type:1)+OR+(proteome_type:2))"
    # )

    url = construct_query_url(
        UNIPROT_REFERENCE_PROTEOMES_URL,
        UNIPROT_DESIRED_FORMAT,
        all_proteomes_query,
        UNIPROT_REFERENCE_PROTEOMES_FIELDS,
        UNIPROT_SIZE,
    )

    try:
        # Make the HTTP request to Uniprot
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Write response to file if it contains data
        if len(response.text.strip().split("\n")) > 1:
            with open(file_path, "w") as file:
                file.write(response.text)

        while "next" in response.links:
            next_url = response.links["next"]["url"]
            response = requests.get(next_url, timeout=30)
            response.raise_for_status()
            # Write response to file if it contains data
            if len(response.text.strip().split("\n")) > 1:
                with open(file_path, "a") as file:
                    file.write(response.text) if PROTEOMES_ORGANISM_ID_COLUMNNAME not in response.text else None

        # Read file to df for sorting
        df = pd.read_csv(file_path, sep="\t", low_memory=False)
        df = df.drop_duplicates()
        df = df.sort_values(
            by=[PROTEOMES_ORGANISM_ID_COLUMNNAME, PROTEOMES_PROTEOME_ID_COLUMNNAME],
            axis=0,
            ascending=True,
        )
        df.to_csv(file_path, sep="\t", index=False)

        organism_ids = df[PROTEOMES_ORGANISM_ID_COLUMNNAME].unique().tolist()

        return organism_ids

    except requests.exceptions.HTTPError:
        print(f"Bad request for {PROTEOMES_FILENAME} - {response.status_code}")
    except requests.exceptions.Timeout:
        print("The request timed out")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def run_uniprot_api(taxa_id_from_proteomes_set, show_status: bool) -> None:
    """
    Download data from Uniprot in series.

    :param taxa_id_from_proteomes_set: Set of organism ids with proteomes from Uniprot.
    :param show_status: Boolean flag to show progress status.
    :return: None
    """
    # ! Cannot be used during multiprocessing
    # Cache HTTP requests to avoid repeated calls
    # requests_cache.install_cache("uniprot_cache")

    organism_list = get_organism_list()

    taxa_id_common_with_proteomes_list = list(set(organism_list).intersection(taxa_id_from_proteomes_set))

    # Process uniprot files
    total_organisms = len(taxa_id_common_with_proteomes_list)
    progress_class = tqdm if show_status else DummyTqdm

    # Iterate over organism IDs and fetch data from Uniprot
    with progress_class(total=total_organisms, desc="Processing uniprot files") as progress:
        for organism_id in taxa_id_common_with_proteomes_list:
            file_path = Path(UNIPROT_S3_DIR) / f"{organism_id}.{UNIPROT_DESIRED_FORMAT}"
            if not file_path.exists():
                fetch_uniprot_data(organism_id)

            # Update progress bar
            progress.update(1)
        # Set final description for the progress bar
        progress.set_description(f"Downloading organism data from Uniprot, final file of batch: {organism_id}")


def run_uniprot_api_parallel(
    taxa_id_from_proteomes_list,
    show_status: bool,
    input_dir: Union[Path, str] = RAW_DATA_DIR,
    workers: int = os.cpu_count(),
) -> None:
    """
    Download data from Uniprot in parallel.

    :param taxa_id_from_proteomes_list: Set of organism ids with proteomes from Uniprot.
    :param show_status: Boolean flag to show progress status.
    :param input_dir: Directory where the data is stored.
    :param workers: Number of workers to use.
    :return: None
    """
    # ! Cannot be used during multiprocessing
    # Cache HTTP requests to avoid repeated calls
    # requests_cache.install_cache("uniprot_cache")

    organism_list = get_organism_list(input_dir=input_dir)

    # Sort list
    taxa_id_common_with_proteomes_list = list(set(organism_list).intersection(taxa_id_from_proteomes_list))
    taxa_id_common_with_proteomes_list.sort()

    # Write used IDs to file
    file_path = Path(RAW_DATA_DIR) / f"{KGMICROBE_PROTEOMES_FILENAME}.{UNIPROT_DESIRED_FORMAT}"
    with open(file_path, "w") as f:
        for line in taxa_id_common_with_proteomes_list:
            f.write(f"{line}\n")

    #!For testing
    # taxa_id_common_with_proteomes_list = taxa_id_common_with_proteomes_list[0:5]

    # Set up a pool of worker processes
    with multiprocessing.Pool(processes=workers) as pool:
        # Use partial to create a new function that has some parameters pre-filled
        fetch_func = partial(fetch_uniprot_data)
        # If show_status is True, use process_map to display a progress bar
        if show_status:
            process_map(
                fetch_func, taxa_id_common_with_proteomes_list, max_workers=workers, chunksize=CHUNK_SIZE_PER_WORKER
            )
        else:
            # Set up a pool of worker processes without a progress bar
            with multiprocessing.Pool(processes=workers) as pool:
                pool.map(fetch_func, taxa_id_common_with_proteomes_list)
