#!/usr/bin/env python3

import send_email
import synapseclient
import synapseutils
import sys

from typing import Any, List, Tuple, Union


def is_new_submitter(syn, submitter_id, parent_folder_id):
    """
    Used to check if the submitter is new or already has an existing folder.

    This function uses ``synapseutils.walk`` to crawl through the level 1 subfolders
    (i.e. The folders 1 level below the Parent-Folder, that are named after the submitter's synapse ID) to
    verify whether or not a submitter already has an existing folder created.
    """

    submitter_subfolders = []
    # Setting ``include_types`` to only Folders so that Files are excluded, and walk is faster.
    for _, level1_subfolders, _ in synapseutils.walk(syn=syn, synId=parent_folder_id,
                                                     includeTypes=["folder"]
                                                     ):
        for folder_name, synid in level1_subfolders:
            submitter_subfolders.append(folder_name)

    if submitter_id in submitter_subfolders:
        return False

    return True


def build_subfolder(syn: synapseclient.Synapse, folder_name: str, parent_folder: Union[str, synapseclient.Entity]) -> synapseclient.Entity:
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
    subfolder = synapseclient.Folder(
        name=folder_name, parent=parent_folder
    )
    subfolder = syn.store(obj=subfolder)

    return subfolder


# TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
# def update_subfolders():
#     """"""


def update_permissions(syn: synapseclient.Synapse, subfolder: Union[str, synapseclient.Entity],
                       project_folder_id: str, access_type: Any = ["CREATE", "READ", "DOWNLOAD", "UPDATE", "DELETE"]):
    """
    Updates the permissions (local share settings) of the given Folder/File to grant the creators of the Project
    unique permissions.

    Arguments:
        syn: A Synapse Python client instance
        subfolder: The Folder whose permissions will be updated
        project_folder_id: The Project Synapse ID
        access_type: Type of permission to be granted
    """
    organizers_id = syn.get(project_folder_id, downloadFile=False).createdBy
    syn.setPermissions(
        subfolder, principalId=organizers_id, accessType=access_type
        )


def get_parent_and_project_folder_id(syn: synapseclient.Synapse, parent_folder: str, project_name: str) -> Tuple[str, str]:
    """
    Retrieves the Synapse IDs of the Project and Parent Folder.

    Arguments:
        syn: A Synapse Python client instance
        parent_folder: The name of the parent folder
        project_name: The name of the Project

    Returns:
        A tuple containing the Project Synapse ID and the Parent Folder ID
    """
    project_id = syn.findEntityId(name=project_name)
    parent_folder_id = syn.findEntityId(name=parent_folder, parent=project_id)

    return parent_folder_id, project_id


def build_update_subfolders(
        project_name: str, submission_id: str, build_or_update: str, subfolders: List[str] = ["workflow_logs", "predictions"],
        only_admins: str = "predictions", parent_folder: str = "Logs"
        ):
    """
    This function can either build a new set of log subfolders under 
    a participant folder, or update an existing participant folder with
    new ancilliary files.

    The current Challenge Folder structure is as follows:
    >Parent-Folder/
    >>Level 1 Subfolder (Submitter-Folder)/
    >>>Level 2 Subfolder/
    >>>> ...

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

    parent_folder_id, project_id = get_parent_and_project_folder_id(syn, parent_folder, project_name)
    submitter_id = send_email.get_participant_id(syn, submission_id)[0]

    if build_or_update == "build" and is_new_submitter(syn, submitter_id, parent_folder_id):

        # Creating the level 1 (directly under Parent-Folder/) subfolder, which is named
        # after the submitters' team/userIds.
        level1_subfolder = build_subfolder(syn, folder_name=submitter_id, parent_folder=parent_folder_id)
        # Creating the level 2 subfolders that live directly under submitter subfolder.
        for level2_subfolder in subfolders:
            level2_subfolder = build_subfolder(syn, folder_name=level2_subfolder, parent_folder=level1_subfolder)
            # Update the permissions for the folder that should only be accessed by Challenge admins.
            if level2_subfolder.name == only_admins:
                update_permissions(syn, level2_subfolder, project_id)


    # TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
    # elif build_or_update == "update":
    #     update_subfolders(syn, parent_folder_id)


if __name__ == "__main__":
    project_name = sys.argv[1]
    submission_id = sys.argv[2]
    build_or_update = sys.argv[3]
    build_update_subfolders(project_name, submission_id, build_or_update)
