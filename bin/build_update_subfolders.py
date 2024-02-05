#!/usr/bin/env python3

import send_email
import synapseclient
import synapseutils
import sys

from synapseclient import Folder


def is_new_submitter(syn, submitter_id, parent_folder_id):
    """
    Used to check if the submitter is new or already has an existing folder.

    This function uses ``synapseutils.walk`` to crawl through the level 1 subfolders
    (i.e. The folders 1 level below the Parent-Folder, that are named after the submitter's synapse ID) to
    verify whether or not a submitter already has an existing folder created.
    """
    submitter_subfolders = []
    # Setting ``include_types`` to only Folders so that Files are excluded, and walk is faster.
    for _, level1_subfolders, _ in synapseutils.walk(syn=syn, synId=parent_folder_id, includeTypes=["folder"]):
        for subfolder in level1_subfolders:
            # ``folder`` is a tuple structured as follows: (Folder name, synID). Let's just get the Folder name.
            submitter_subfolders.append(subfolder[0])

    if submitter_id in submitter_subfolders:
        return False

    return True


def build_subfolder(syn, folder_name, parent_folder):
    """
    """

    # Create Folder object for
    subfolder = Folder(
        name=folder_name, parent=parent_folder
    )
    subfolder = syn.store(obj=subfolder)

    return subfolder


# TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
# def update_subfolders():
#     """"""


def update_permissions(syn):
    """Updates the permissions (local share settings) of the given Folder/File"""
    syn.setPermissions(
        synid, principalId=pid, accessType=["READ", "DOWNLOAD"]
        )


def get_parent_folder_id(syn, parent_folder, project_name):
    """"""
    project_id = syn.findEntityId(name=project_name)
    parent_folder_id = syn.findEntityId(name=parent_folder, parent=project_id)

    return parent_folder_id


def build_update_subfolders(project_name, submission_id, build_or_update, parent_folder="Logs", subfolders=["workflow_logs", "permissions"], only_admins="permissions"):
    """
    This function can either build a new set of log subfolders under 
    a participant folder, or update an existing participant folder with
    new ancilliary files.

    The Folder structure is as follows:
    >Parent-Folder/
    >>Level 1 Subfolder (Submitter-Folder)/
    >>>Level 2 Subfolder/
    >>>> ...
    """
    # Establish access to the Synapse API
    syn = synapseclient.login()

    parent_folder_id = get_parent_folder_id(syn, parent_folder, project_name)
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
                update_permissions(syn, )


    # TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
    # elif build_or_update == "update":
    #     update_subfolders(syn, parent_folder_id)


if __name__ == "__main__":
    build_or_update = sys.argv[1]
    build_update_subfolders(build_or_update)
