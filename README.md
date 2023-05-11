# iatlas-workflow-scripts
A home for experimental scripts used for launching Nextflow Tower workflows for iAtlas Data Processing

## Setup

These instructions assume that you already have Python, a Python version manager (`pyenv`), and `pipenv` installed.

### Python Environment

Set up your Python environment for using these scripts by ruinning
```
pipenv install
pipenv shell
```

### Environment Variables

In order for the scripts leveraging `py-orca` to connect to Nextflow Tower, you must configure a `NEXTFLOWTOWER_CONNECTION_URI` in your local environment. To do so, you will need a Nextflow Tower token with access to the workspace that you wish to use (`Sage-Bionetworks/iatlas-project` in this case). You can then copy `.env.example` into a local `.env` file, replace `<tower-access-token>`, and run `source .env` in your terminal.

## Immune Subtype Clustering

Steps to run the workflow for Immune Subtype Clustering:
1. Upload all sample files to a folder on Synapse. Make sure that the only `.tsv` files in the folder are the ones that you want to be processed.
2. Prepare the master data sheet by executing `immune_subtype_clustering/prepare_data_sheet.py` with three arguments:
    - `parent`: Synapse ID of the folder where your data files are
    - `export_name`: Name that you want the master data file to be exported to
    - `upload_location`: Synapse ID of the folder that you want to upload the master data file to
```
python immune_subtype_clustering/prepare_data_sheet.py <parent> <export_name> <upload_location>
```
3. Create and store your CWL `.json` configuration file in the same location in Synapse as the data file produced by the previous step.
Example `.json` file:
``` immune_subtype_clustering_input.json
{
    "input_file": {
        "path": <export_name>,
        "class": "File"
    },
    "input_gene_column": "gene"
}
```
4. Create and store your `nf-synstage` input `.csv` file in an S3 bucket accessible to the Nextflow Tower workspace (`s3://iatlas-project-tower-bucket` or `s3://iatlas-project-tower-scratch`).
Example `.csv` file:
``` input.csv
data_file,input_file
<synapse_id_for_master_data_sheet>,<synapse_id_for_json_input_file>
```
5. Stage the master data sheet and your CWL `.json` configuration file to S3 buckets by executing `immune_subtype_clustering/nf_stage.py` with three arguments:
    - `run_name`: What you want the workflow on Nextflow Tower to be named
    - `input`: S3 URI for your `nf-synstage`-friendly input `.csv` file 
    - `outdir`: S3 URI for where you want the output of `nf-synstage` to be stored
```
python immune_subtype_clustering/nf_stage.py <run_name> <input> <outdir>
```
6. Execute the Immune Subtypes Clustering workflow on Nextflow Tower by executing `immune_subtype_clustering/nf_launch.py` with three arguments:
    - `run_name`: What you want the workflow on Nextflow Tower to be named
    - `s3_file`: S3 URI the output from `nf-synstage`
    - `cwl_file`: File path to your CWL workflow file
```
python immune_subtype_clustering/nf_launch.py <run_name> <s3_file> <cwl_file>
```
