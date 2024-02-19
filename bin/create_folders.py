#!/usr/bin/env python3

import sys
from typing import List, Union

import send_email
import synapseclient
import synapseutils


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
    predictions_file_name = f"{prefix_name}_{filename}"

    updated_file_entity = synapseutils.changeFileMetaData(
        syn,
        entity=old_file_entity,
        downloadAs=predictions_file_name,
        forceVersion=False,
    )
    updated_file_entity.name = predictions_file_name
    syn.store(updated_file_entity)


def update_subfolders(
    syn: synapseclient.Synapse,
    predictions_file: str,
    submitter_id: str,
    parent_id: Union[str, synapseclient.Entity],
) -> synapseclient.File:
    """
    Update subfolders based on the given predictions file, submitter ID, and parent ID, and returns the file entity.

    Arguments:
        syn: A Synapse Python client instance
        predictions_file: The name of the predictions file
        submitter_id: The ID of the submitter
        parent_id: The ID of the parent folder
    """
    submitter_folder = syn.findEntityId(submitter_id, parent_id)

    predictions_folder = syn.findEntityId("predictions", submitter_folder )

    if not predictions_folder:
        raise ValueError(f"Could not find predictions subfolder on Synapse for submitter ID: {submitter_id}")

    file_entity = syn.store(
        synapseclient.File(predictions_file, parentId=predictions_folder)
    )
    return file_entity


def update_permissions(
    syn: synapseclient.Synapse,
    subfolder: Union[str, synapseclient.Entity],
    project_id: str,
    principal_id: str = None,
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
    subfolders: List[str] = ["workflow_logs", "predictions"],
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
        subfolders: The subfolders to be created under the parent folder.
        only_admins: The name of the subfolder that will have local share settings
                     differing from the other subfolders.
        root_folder_name: The name of the root folder under the Project. Default is ''Logs''.

    """
    # Establish access to the Synapse API
    syn = synapseclient.login()

    # Retrieving Synapse IDs that will be necessary later
    project_id = syn.findEntityId(name=project_name)
    submitter_id = send_email.get_participant_id(syn, submission_id)[0]

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

        if not predictions_file:
            raise ValueError(
                "Predictions file(s) must be provided to update folders. Exiting."
            )

        root_folder_id = syn.findEntityId(name=root_folder_name, parent=project_id)

        file_entity = update_subfolders(
            syn,
            predictions_file=predictions_file,
            submitter_id=submitter_id,
            parent_id=root_folder_id,
        )
        prefix_filename(syn, prefix_name=submission_id, old_file_entity=file_entity)

    else:
        raise ValueError(
            "``create_or_update`` must be either 'create' or 'update'. Exiting."
        )


if __name__ == "__main__":
    project_name = sys.argv[1]
    submission_id = sys.argv[2]
    create_or_update = sys.argv[3]
    predictions_file = sys.argv[4] if len(sys.argv) > 4 else None

    create_folders(
        project_name=project_name,
        submission_id=submission_id,
        create_or_update=create_or_update,
        predictions_file=predictions_file,
    )
