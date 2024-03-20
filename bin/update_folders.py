#!/usr/bin/env python3

import os
import sys
from typing import Union
import synapseclient
import helpers


def store_file(
    syn: synapseclient.Synapse,
    folder_name: str,
    input_file: str,
    submitter_id: str,
    parent_id: Union[str, synapseclient.Entity],
) -> synapseclient.File:
    """
    Store a given input file in its correct location on Synapse, and returns the Synapse file entity.

    Arguments:
        syn: A Synapse Python client instance
        folder_name: The name of the subfolder that will house the input_file
        input_file: The name of the file to be uploaded into the subfolder
        submitter_id: The ID of the submitter
        parent_id: The ID of the parent folder

    Returns:
        The Synapse File entity that was created

    Raises:
        ValueError: If the subfolder does not exist

    """

    submitter_folder = syn.findEntityId(submitter_id, parent_id)

    subfolder = syn.findEntityId(folder_name, submitter_folder)

    if not subfolder:
        raise ValueError(
            f"Could not find '{folder_name}' subfolder on Synapse for submitter ID: {submitter_id}"
        )

    file_entity = syn.store(synapseclient.File(input_file, parentId=subfolder))

    return file_entity


def update_folders(
    project_name: str,
    submission_id: str,
    folder_name: str,
    input_file: str,
    root_folder_name: str = "Logs",
) -> None:
    """
    This function can either create or re-create a root folder and set of subfolders to
    store Challenge output files for Challenge participants and organizers.

    The current Challenge Folder structure is as follows:

    Root-Folder/
    |--Level 1 Subfolder (Submitter-Folder)/
    |  |--Level 2 Subfolder/
    |  |  |-- ...

    Arguments:
        project_name: The name of the Project
        submission_id: The Submission ID of the submission being processed
        folder_name: The name of the subfolder that will house the ``input_file``
        input_file: The name of the file to be uploaded into the subfolder
        root_folder_name: The name of the root folder housing all the subfolders and File entities

    Raises:
        ValueError: If the root folder does not exist, or the file attempted to be uploaded is empty.

    """
    # Log into the client
    syn = synapseclient.login(silent=True)

    # Retrieving Synapse IDs that will be necessary later
    project_id = syn.findEntityId(name=project_name)
    submitter_id = helpers.get_participant_id(syn, submission_id)[0]

    # Get the Synapse ID of the root Folder housing all the subfolders and File entities
    root_folder_id = syn.findEntityId(name=root_folder_name, parent=project_id)
    if not root_folder_id:
        raise ValueError(
            f"Could not find '{root_folder_name}' root folder on Synapse for project ID: {project_id}. Exiting."
        )

    # ``input_file`` must not be None or empty to proceed
    # with the upload to Synapse
    if input_file and os.path.getsize(input_file) > 0:
        store_file(
            syn,
            folder_name=folder_name,
            input_file=input_file,
            submitter_id=submitter_id,
            parent_id=root_folder_id,
        )

    else:
        raise ValueError(
            f"Non-empty prediction and log files must be provided to update folders for submission {submission_id}. Exiting."
        )


if __name__ == "__main__":
    project_name = sys.argv[1]
    submission_id = sys.argv[2]
    folder_name = sys.argv[3]
    file_name = sys.argv[4]

    update_folders(
        project_name=project_name,
        submission_id=submission_id,
        folder_name=folder_name,
        input_file=file_name
    )
