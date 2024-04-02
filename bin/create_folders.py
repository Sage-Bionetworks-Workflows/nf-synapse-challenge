#!/usr/bin/env python3
"""
This module contains functions for the ``create_folders.nf``
and ``run_docker.nf`` workflows. It provides the following functionality:
- Create a folder in Synapse
- Update a folder in Synapse with File entities
- Modifies a File entity's filehandle name by prefixing it with a given string
"""

import sys
from typing import List, Union

import synapseclient

import helpers


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
    syn: Union[None, synapseclient.Synapse] = None,
    subfolders: List[str] = ["docker_logs", "predictions"],
    private_folders: List[str] = ["predictions"],
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
        private_folders: The name of the subfolder that will have local share settings
                     differing from the other subfolders.
        root_folder_name: The name of the root folder under the Project. Default is ''Logs''.

    """
    # Establish access to the Synapse API
    if not syn:
        syn = synapseclient.login()

    # Retrieving Synapse IDs that will be necessary later
    project_id = syn.findEntityId(name=project_name)
    submitter_id = helpers.get_participant_id(syn, submission_id)[0]

    # Create the Root-Folder/ directly under Project
    root_folder = create_folder(syn, folder_name=root_folder_name, parent=project_id)

    # Creating the level 1 (directly under Root-Folder/) subfolder,
    # which is named after the submitters' team/userIds.
    level1_subfolder = create_folder(syn, folder_name=submitter_id, parent=root_folder)
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
        # The subfolder denoted under ``private_folders`` will have its own ACL, and will be only accessed by
        # Project maintainers:
        if level2_subfolder.name in private_folders:
            update_permissions(
                syn,
                subfolder=level2_subfolder,
                project_id=project_id,
                principal_id=submitter_id,
                access_type=[],
            )


if __name__ == "__main__":
    # Assigning variables to the command line args
    project_name = sys.argv[1]
    submission_id = sys.argv[2]
    private_folders = sys.argv[3]

    # Remove whitespace (if any) and split by comma to get a list
    # of folders that should only be available to Challenge admins
    private_folders = private_folders.strip().split(",")

    # Create the folders
    create_folders(project_name=project_name, submission_id=submission_id, private_folders=private_folders)
