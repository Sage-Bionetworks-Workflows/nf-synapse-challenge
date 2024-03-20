#!/usr/bin/env python3

import os
from typing import List

import synapseclient


def get_participant_id(syn: synapseclient.Synapse, submission_id: str) -> List[str]:
    """
    Retrieves the teamId of the participating team that made
    the submission. If the submitter is an individual rather than
    a team, the userId for the individual is retrieved.

    Arguments:
      syn: A Synapse Python client instance
      submission_id: The ID for an individual submission within an evaluation queue

    Returns:
      The synID of a team or individual participant

    """
    # Retrieve a Submission object
    submission = syn.getSubmission(submission_id, downloadFile=False)

    # Get the teamId or userId of submitter
    participant_id = submission.get("teamId") or submission.get("userId")

    # Ensure that the participant_id returned is a list
    # so it can be fed into syn.sendMessage(...) later.
    return [participant_id]


def rename_file(submission_id: str, input_path: str) -> None:
    """
    Prefixes the name of a file with the given ``submission_id``.
    E.g: Given ``submission_id``="123", the file ``path/to/file.txt`` is
    renamed as ``path/to/123_file.txt``.

    Arguments:
        submission_id: The ID used to rename the file
        input_path: The path of the file to be renamed

    """
    # Extract the directory from the input path
    dirname = os.path.dirname(input_path)

    # Extract the filename from the input path
    filename = os.path.basename(input_path)

    # Rename the file based on submission_id
    new_filename = f"{submission_id}_{filename}"

    # Create the new path for the renamed file
    new_path = os.path.join(dirname, new_filename)

    # Rename the original file
    os.rename(input_path, new_path)

    # Print the path to the renamed file
    print("File renamed successfully.")
    print("Original file: ", input_path)
    print("Renamed file: ", new_path)
