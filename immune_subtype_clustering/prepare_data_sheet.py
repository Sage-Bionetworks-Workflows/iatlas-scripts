import os
from typing import List

import pandas as pd
import synapseclient
from synapseclient import File


def syn_login():
    syn = synapseclient.Synapse()
    syn.login()
    return syn


def download_data_files(parent: str, syn: synapseclient.Synapse):
    """downloads all TSV files in parent synapse folder from synapse id provided"""
    children = syn.getChildren(parent=parent)
    file_entity_list = []
    for child in children:
        if child["name"].endswith(".tsv"):
            file = syn.get(child["id"])
            file_entity_list.append(file)
    return file_entity_list


def load_data_files(file_entity_list: List[synapseclient.File]) -> List[pd.DataFrame]:
    """loads all files in data_diectory into dataframes, creates Hugo column,
    grabs Hugo and tpm columns, renames tppm column to patient id, appends each df to gene_df_list
    """
    gene_df_list = []
    for file in file_entity_list:
        patient_id = file.name.split("_")[0]
        df = pd.read_csv(file.path, sep="\t")
        df.insert(0, "Hugo", df["target_id"].str.split("|", expand=True)[5])
        gene_df = df[["Hugo", "tpm"]]
        gene_df = gene_df.rename(columns={"tpm": patient_id})
        gene_df_list.append(gene_df)
        print(f"Data from {file.name} loaded")
    return gene_df_list


def merge_dfs(gene_df_list: List[pd.DataFrame]) -> pd.DataFrame:
    """Joins all dfs in gene_df_list by index, renames all Hugo columns after first by index, returns final_df"""
    final_df = gene_df_list[0]
    gene_df_list.pop(0)
    for i, gene_df in enumerate(gene_df_list):
        # Create unique columns so that we can merge on index
        # Cannot merge on "Hugo" because of duplicate values in that column
        gene_df = gene_df.rename(columns={"Hugo": f"Hugo_{i}"})
        final_df = pd.merge(final_df, gene_df, left_index=True, right_index=True)
    print("dfs all joined into final_df")
    return final_df


def verify_export(final_df: pd.DataFrame, export_name: str):
    """Confirms that the contents of all Hugo columns are identical and thus that the index join was OK,
    Drops all renamed Hugo columns, exports final_df to tsv
    """
    check_cols = [col for col in list(final_df.columns) if col.startswith("Hugo")]
    if all(final_df[check_cols].iloc[:, 0].equals(final_df[col]) for col in check_cols):
        print("All columns have identical values")
        check_cols.pop(0)
        final_df = final_df.drop(check_cols, axis=1)
        final_df.to_csv(export_name, index=False, sep="\t")
        print("Export complete")
        return export_name
    else:
        raise ValueError("Not all columns have identical values")


def syn_upload(
    export_name: str,
    file_entity_list: list,
    syn_location: str,
    syn: synapseclient.Synapse,
):
    """Uploads exported data file to Synapse in provided location"""
    file = File(
        export_name,
        parent=syn_location,
    )
    file = syn.store(
        file,
        used=[f.id for f in file_entity_list],
        executed=[
            "https://raw.githubusercontent.com/Sage-Bionetworks-Workflows/iatlas-scripts/immune_subtype_clustering/prepare_data_sheet.py"
        ],
        forceVersion=False,
    )
    print(f"{export_name} uploaded to Synapse in {syn_location}")


if __name__ == "__main__":
    syn = syn_login()
    file_entity_list = download_data_files(parent="syn26535390", syn=syn)
    gene_df_list = load_data_files(file_entity_list=file_entity_list)
    final_df = merge_dfs(gene_df_list=gene_df_list)
    export_name = verify_export(
        final_df=final_df, export_name="immune_subtype_sample_sheet.tsv"
    )
    syn_upload(
        export_name=export_name,
        file_entity_list=file_entity_list,
        syn_location="syn51471781",
        syn=syn,
    )
