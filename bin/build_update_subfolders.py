#!/usr/bin/env python3

import sys
from typing import List, Union

import send_email
import synapseclient


def build_subfolder(
    syn: synapseclient.Synapse,
    folder_name: str,
    parent_folder: Union[str, synapseclient.Entity],
) -> synapseclient.Entity:
    """
    Builds a subfolder under the designated ``parent_folder``.

    Arguments:
        syn: A Synapse Python client instance
        folder_name: The name of the subfolder to be created
        parent_folder: A synapse Id or Entity of the parent folder under which the subfolder will live

    Returns:
        The created Synapse Folder entity
    """

    # Create Folder object
    subfolder = synapseclient.Folder(name=folder_name, parent=parent_folder)
    subfolder = syn.store(obj=subfolder)

    return subfolder


# TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
# def update_subfolders():
#     """"""


def update_permissions(
    syn: synapseclient.Synapse,
    subfolder: Union[str, synapseclient.Entity],
    project_folder_id: str,
    principal_id: str = None,
    access_type: List[str] = [],
):
    """
    Updates the permissions (local share settings) of the given Folder/File to change access for the given principalId.
    By default it will always revoke all access types for all challenge participants and the public.

    Arguments:
        syn: A Synapse Python client instance
        subfolder: The Folder whose permissions will be updated
        project_folder_id: The Project Synapse ID
        principal_id: The synapse ID to change permissions for
        access_type: Type of permission to be granted
    """

    # New ACL has all access types revoked for everyone except Project maintainers by default
    all_participants = syn.restGET(f"/entity/{project_folder_id}/challenge").get(
        "participantTeamId"
    )
    registered_users = synapseclient.AUTHENTICATED_USERS
    public = synapseclient.PUBLIC

    for id in [all_participants, registered_users, public]:
        syn.setPermissions(subfolder, principalId=id, accessType=[])

    # Also update the access type for the designated principalId if there is one
    if principal_id:
        syn.setPermissions(subfolder, principalId=principal_id, accessType=access_type)


def build_update_subfolders(
    project_name: str,
    submission_id: str,
    build_or_update: str,
    subfolders: List[str] = ["workflow_logs", "predictions"],
    only_admins: str = "predictions",
    parent_folder: str = "Logs",
):
    """
    This function can either build/rebuild a set of log subfolders under
    a participant folder, or update an existing participant folder with
    new ancilliary files.

    The current Challenge Folder structure is as follows:

    Parent-Folder/
    |--Level 1 Subfolder (Submitter-Folder)/
    |  |--Level 2 Subfolder/
    |  |  |-- ...

    Arguments:
        project_name: The name of the Project
        submission_id: The Submission ID of the submission being processed
        build_or_update: Determines whether the Folder structure will be built
                         from scratch, or updated with new output files. Value
                         can either be ''build'' or ''update''.
        subfolders: The subfolders to be created under the parent folder.
        only_admins: The name of the subfolder that will have local share settings
                     differing from the other subfolders.
        parent_folder: The name of the parent folder. Default is ''Logs''.

    """
    # Establish access to the Synapse API
    syn = synapseclient.login()

    project_id = syn.findEntityId(name=project_name)
    parent_folder_id = syn.findEntityId(name=parent_folder, parent=project_id)
    submitter_id = send_email.get_participant_id(syn, submission_id)[0]

    if build_or_update == "build":
        # Creating the level 1 (directly under Parent-Folder/) subfolder, which is named
        # after the submitters' team/userIds.
        level1_subfolder = build_subfolder(
            syn, folder_name=submitter_id, parent_folder=parent_folder_id
        )
        update_permissions(
            syn,
            subfolder=level1_subfolder,
            project_folder_id=project_id,
            principal_id=submitter_id,
            access_type=["READ", "DOWNLOAD"],
        )
        # Creating the level 2 subfolders that live directly under submitter subfolder.
        for level2_subfolder in subfolders:
            level2_subfolder = build_subfolder(
                syn, folder_name=level2_subfolder, parent_folder=level1_subfolder
            )
            # The level 2 subfolders will inherit the permissions set on the level 1 subfolder above.
            # The subfolder denoted under ``only_admins`` will have its own ACL, and will be only accessed by
            # Project maintainers:
            if level2_subfolder.name == only_admins:
                update_permissions(
                    syn,
                    subfolder=level2_subfolder,
                    project_folder_id=project_id,
                    principal_id=submitter_id,
                    access_type=[],
                )

    # TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
    # elif build_or_update == "update":
    #     update_subfolders(syn, parent_folder_id)


if __name__ == "__main__":
    project_name = sys.argv[1]
    submission_id = sys.argv[2]
    build_or_update = sys.argv[3]
    build_update_subfolders(project_name, submission_id, build_or_update)
