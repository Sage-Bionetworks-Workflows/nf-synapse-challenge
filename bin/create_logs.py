#!/usr/bin/env python3

import sys
import synapseclient
import synapseutils

def is_new_submitter(syn, submitterid, logs_folder_id):
    """
    Used to check if the submitter is new or already has an existing folder.
    """
    submitter_folders = []
    # Setting ``include_types`` to only Folders so that Files are excluded, and walk is faster.
    for _, logs_folders, _ in synapseutils.walk(syn=syn, synId=logs_folder_id, includeTypes=["folder"]):
        for folder in logs_folders:
            # ``folder`` is a tuple structured as follows: (Folder name, synID). Let's just get the Folder name.
            submitter_folders.append(folder[0])

    if submitterid in submitter_folders:
        return True

    return False

def build_logs_folders():
    """"""

def update_logs_folders():
    """"""

def create_logs(build_or_update="update"):
    """
    This function can either build a new set of log subfolders under 
    a participant folder, or update an existing participant folder with
    new ancilliary files.
    """
    if build_or_update == "build" and is_new_submitter():
        build_logs_folders()
    elif build_or_update == "update":
        update_logs_folders

if __name__ == "__main__":
    build_or_update = sys.argv[1]
    create_logs(build_or_update)