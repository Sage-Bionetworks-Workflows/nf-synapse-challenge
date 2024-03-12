#!/usr/bin/env python3
"""
This module contains functions for the ``create_folders.nf``
and ``run_docker.nf`` workflows. It provides the following functionality:
- Create a folder in Synapse
- Update a folder in Synapse with File entities
- Modifies a File entity's filehandle name by prefixing it with a given string
"""

from logging import root
import os
import sys

import helpers

import synapseclient
import synapseutils

from typing import List, Union


def create_folder(
    syn: synapseclient.Synapse,
    folder_name: str,
    parent: Union[str, synapseclient.Entity],
) -> synapseclient.Entity:
    """
    Creates a Folder entity under the designated ``parent``.

    Arguments:
        syn: A Synapse Python client instance
        folder_name: The name of the subfolder to be created
        parent: A synapse Id or Entity of the parent folder or project under which the new folder will live

    Returns:
        The created Synapse Folder entity

    """

    # Create Folder object
    subfolder = synapseclient.Folder(name=folder_name, parent=parent)
    # Store in Synapse
    subfolder = syn.store(obj=subfolder)

    return subfolder


def prefix_filename(
    syn: synapseclient.Synapse, prefix_name: str, old_file_entity: synapseclient.File
) -> None:
    """
    Prefixes the name of the old file entity with the desired ``prefix_name`` and updates the file name and metadata in Synapse.

    Arguments:
        syn: The Synapse Python client instance
        prefix_name: The prefix to be added to your Synapse File name
        old_file_entity: The old File entity to be updated

    """
    filename = old_file_entity.name
    prefixed_filename = f"{prefix_name}_{filename}"

    synapseutils.changeFileMetaData(
        syn,
        entity=old_file_entity,
        downloadAs=prefixed_filename,
        forceVersion=False,
        name=prefixed_filename,
    )


def update_subfolders(
    syn: synapseclient.Synapse,
    folder_name: str,
    input_file: str,
    submitter_id: str,
    parent_id: Union[str, synapseclient.Entity],
) -> synapseclient.File:
    """
    Update subfolders based on the given predictions file, submitter ID, and parent ID, and returns the file entity.

    Arguments:
        syn: A Synapse Python client instance
        folder_name: The name of the subfolder that will house the input_file
        input_file: The name of the file to be uploaded into the subfolder
        submitter_id: The ID of the submitter
        parent_id: The ID of the parent folder

    Returns:
        The Synapse File entity that was created

    """

    submitter_folder = syn.findEntityId(submitter_id, parent_id)

    subfolder = syn.findEntityId(folder_name, submitter_folder)

    if not subfolder:
        raise ValueError(
            f"Could not find '{folder_name}' subfolder on Synapse for submitter ID: {submitter_id}"
        )

    file_entity = syn.store(synapseclient.File(input_file, parentId=subfolder))
    return file_entity


def update_permissions(
    syn: synapseclient.Synapse,
    subfolder: Union[str, synapseclient.Entity],
    project_id: str,
    principal_id: str,
    access_type: List[str] = [],
) -> None:
    """
    Updates the permissions (local share settings) of the given Folder/File to change access for the given principalId.
    By default it will always revoke all access types for all challenge participants and the public.

    Arguments:
        syn: A Synapse Python client instance
        subfolder: The Folder whose permissions will be updated
        project_id: The Project Synapse ID
        principal_id: The synapse ID to change permissions for
        access_type: Type of permission to be granted
    """

    # New ACL has all access types revoked for everyone except Project maintainers by default
    all_participants = syn.restGET(f"/entity/{project_id}/challenge").get(
        "participantTeamId"
    )
    registered_users = synapseclient.AUTHENTICATED_USERS
    public = synapseclient.PUBLIC

    for id in [all_participants, registered_users, public]:
        syn.setPermissions(subfolder, principalId=id, accessType=[])

    # Also update the access type for the designated principalId if there is one
    if principal_id:
        syn.setPermissions(subfolder, principalId=principal_id, accessType=access_type)


def create_folders(
    project_name: str,
    submission_id: str,
    create_or_update: str,
    predictions_file: Union[None, str],
    log_file: Union[None, str],
    syn: Union[None, synapseclient.Synapse] = None,
    subfolders: List[str] = ["docker_logs", "predictions"],
    only_admins: str = "predictions",
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
        create_or_update: Determines whether the Folder structure will be built
                         from scratch, or updated with new output files. Value
                         can either be ''create'' or ''update''.
        predictions_file: The name of the predictions file that the predictions folder
                          should be updated with.
        log_file: The name of the log file that the docker_logs folder should be
                  updated with.
        subfolders: The subfolders to be created under the parent folder.
        only_admins: The name of the subfolder that will have local share settings
                     differing from the other subfolders.
        root_folder_name: The name of the root folder under the Project. Default is ''Logs''.

    """
    # Establish access to the Synapse API
    if not syn:
        syn = synapseclient.login()

    # Retrieving Synapse IDs that will be necessary later
    project_id = syn.findEntityId(name=project_name)
    submitter_id = helpers.get_participant_id(syn, submission_id)[0]

    if create_or_update == "create":
        # Create the Root-Folder/ directly under Project
        root_folder = create_folder(
            syn, folder_name=root_folder_name, parent=project_id
        )

        # Creating the level 1 (directly under Root-Folder/) subfolder,
        # which is named after the submitters' team/userIds.
        level1_subfolder = create_folder(
            syn, folder_name=submitter_id, parent=root_folder
        )
        update_permissions(
            syn,
            subfolder=level1_subfolder,
            project_id=project_id,
            principal_id=submitter_id,
            access_type=["READ", "DOWNLOAD"],
        )
        # Creating the level 2 subfolders that live directly under submitter subfolder.
        for level2_subfolder in subfolders:
            level2_subfolder = create_folder(
                syn, folder_name=level2_subfolder, parent=level1_subfolder
            )
            # The level 2 subfolders will inherit the permissions set on the level 1 subfolder above.
            # The subfolder denoted under ``only_admins`` will have its own ACL, and will be only accessed by
            # Project maintainers:
            if level2_subfolder.name == only_admins:
                update_permissions(
                    syn,
                    subfolder=level2_subfolder,
                    project_id=project_id,
                    principal_id=submitter_id,
                    access_type=[],
                )

    elif create_or_update == "update":
        # Get the Synapse ID of the root Folder housing all the subfolders and File entities
        root_folder_id = syn.findEntityId(name=root_folder_name, parent=project_id)
        if not root_folder_id:
            raise ValueError(
                f"Could not find '{root_folder_name}' root folder on Synapse for project ID: {project_id}"
            )
        # Dictionary to store file entities and their corresponding folder names
        file_entities = {}
        for input_file, folder_name in (
            (predictions_file, "predictions"),
            (log_file, "docker_logs"),
        ):
            # ``input_file`` must not be None or empty to proceed
            # with the upload to Synapse
            if input_file and os.path.getsize(input_file) > 0:
                file_entities[folder_name] = update_subfolders(
                    syn,
                    folder_name=folder_name,
                    input_file=input_file,
                    submitter_id=submitter_id,
                    parent_id=root_folder_id,
                )
                # Prefix the filename with the submission ID
                # after storing it in Synapse
                if file_entities[folder_name]:
                    prefix_filename(
                        syn,
                        prefix_name=submission_id,
                        old_file_entity=file_entities[folder_name],
                    )
        if not any(file_entities.values()):
            raise ValueError(
                f"Non-empty prediction and/or log file(s) must be provided to update folders for submission {submission_id}. Exiting."
            )

    else:
        raise ValueError(
            "``create_or_update`` must be either 'create' or 'update'. Exiting."
        )


if __name__ == "__main__":

    # Defining arguments
    project_name = sys.argv[1]
    submission_id = sys.argv[2]
    create_or_update = sys.argv[3]
    # TODO: https://sagebionetworks.jira.com/browse/ORCA-311
    predictions_file = sys.argv[4] if len(sys.argv) >= 5 else None
    log_file = sys.argv[5] if len(sys.argv) == 6 else None

    # Create or update folders
    create_folders(
        project_name=project_name,
        submission_id=submission_id,
        create_or_update=create_or_update,
        predictions_file=predictions_file,
        log_file=log_file,
    )
