#!/usr/bin/env python3
"""
Download a Synapse Folder and its contents recursively, or a single Synapse File.
"""
import os
import sys

import synapseclient
from synapseclient import Folder, File

# Function to recursively download files from a folder
def download_files_recursively(syn: synapseclient.Synapse, entity_id: str, download_path: str):
    """
    This function retrieves the entity (folder or file) by its ID using the Synapse client object.
    If the entity is a Folder, it retrieves the children of the folder (files and subfolders)
    and recursively calls itself for each child.

    The files are downloaded to the specified download_path using the Synapse client object.

    Arguments:
        syn: A Synapse client object.
        entity_id: The ID of the Synapse entity (folder or file) to download.
        download_path: The path to the local directory where the files will be downloaded.

    Returns:
        None
    """
    # Retrieve the entity (folder or file) by its ID
    entity = syn.get(entity_id, downloadLocation=download_path, downloadFile=True)

    # If the entity is a Folder, iterate over its contents
    if isinstance(entity, Folder):
        # Get the children of the folder (files and subfolders)
        children = syn.getChildren(entity_id)
        for child in children:
            # Recursively download files
            download_files_recursively(syn, child['id'], download_path)


def synapse_stage(entity_id: str, download_path: str):
    """
    Downloads a Synapse entity to a staging directory on S3.

    Arguments:
        entity_id (str): The ID of the Synapse entity to download.
        download_path (str): The path to the local directory where the entity will be downloaded.

    Returns:
        None
    """

    # Connect to Synapse
    syn = synapseclient.Synapse()
    syn.login(silent=True)

    # Retrieve entity
    entity = syn.get(entity_id, downloadLocation=download_path, downloadFile=True)

    # If the entity is a File (e.g. the gold standard file), print the file path
    if isinstance(entity, File):
        print(os.path.join(download_path, entity.name))

    # If it's a folder, print the folder path and begin the recursive download
    elif isinstance(entity, Folder):
        print(download_path)
        download_files_recursively(syn, entity_id, download_path)


if __name__ == '__main__':
    download_path = sys.argv[1]
    entity_id = sys.argv[2]

    synapse_stage(entity_id, download_path)