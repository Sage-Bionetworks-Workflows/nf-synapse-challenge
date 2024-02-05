#!/usr/bin/env python3

import send_email
import synapseclient
import synapseutils
import sys

from synapseclient import Folder


def is_new_submitter(syn, submitterid, logs_folder_id):
    """
    Used to check if the submitter is new or already has an existing folder.
    """
    submitter_subfolders = []
    # Setting ``include_types`` to only Folders so that Files are excluded, and walk is faster.
    for _, logs_subfolders, _ in synapseutils.walk(syn=syn, synId=logs_folder_id, includeTypes=["folder"]):
        for subfolder in logs_subfolders:
            # ``folder`` is a tuple structured as follows: (Folder name, synID). Let's just get the Folder name.
            submitter_subfolders.append(subfolder[0])

    if submitterid in submitter_subfolders:
        return False

    return True


def build_logs_subfolders(syn, submitterid, subfolders, logs_folder_id):
    """"""

    # Create submitter folder

    submitter_folder = Folder(
        name=submitterid, parent=logs_folder_id
    )
    submitter_folder = syn.store(obj=submitter_folder)

    # Create Folder object(s) and store it/them in submitter folder
    for subfolder in subfolders:
        logs_subfolder = Folder(
            name=subfolder, parent=submitter_folder
        )

        syn.store(obj=logs_subfolder)


# TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
# def update_logs_folders():
#     """"""


def update_permissions():
    """"""


def get_logs_folder_id(syn, project_name):
    """"""
    project_id = syn.findEntityId(name=project_name)
    logs_folder_id = syn.findEntityId(name="Logs", parent=project_id)

    return logs_folder_id


def create_logs(project_name, submission_id, build_or_update, subfolders=["workflow_logs", "permissions"]):
    """
    This function can either build a new set of log subfolders under 
    a participant folder, or update an existing participant folder with
    new ancilliary files.
    """
    # Establish access to the Synapse API
    syn = synapseclient.login()

    logs_folder_id = get_logs_folder_id(syn, project_name)
    submitterid = send_email.get_participant_id(syn, submission_id)[0]

    if build_or_update == "build" and is_new_submitter(syn, submitterid, logs_folder_id):
        build_logs_subfolders(syn, submitterid, subfolders, logs_folder_id)

    # TODO: https://sagebionetworks.jira.com/browse/IBCDPE-809
    # elif build_or_update == "update":
    #     update_logs_folders(syn, logs_folder_id)


if __name__ == "__main__":
    build_or_update = sys.argv[1]
    create_logs(build_or_update)
