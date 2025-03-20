#!/usr/bin/env python3

import argparse
import synapseclient

from synapseclient.core.constants import concrete_types

def get_args():
    """Set up command-line interface and get arguments without any flags."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-id", "-s", type=str, required=True, help="The ID of submission")
    parser.add_argument("--file-type", "-f", type=str, required=True, help="The type of file the submission should be")

    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    submission_id = args.submission_id
    file_type = args.file_type

    syn = synapseclient.Synapse()
    syn.login(silent=True)

    submission = syn.getSubmission(submission_id, downloadLocation=".")
    entity_type = submission["entity"].concreteType
    file_path = submission["filePath"]
    
    # TODO: Eventually we want to abstract this logic into the `make_invalid_file` function
    # in model-to-data's `run_docker.py`, and move that out somewhere else.
    invalid_file = f"INVALID_predictions.{file_type}"
    error_msg = None

    if entity_type != concrete_types.FILE_ENTITY:
        error_msg = (
            f"Only Files should be submitted. Submission {submission_id} type is: {entity_type}"
        )
    elif not submission["filePath"].lower().endswith(file_type):
        error_msg = f"Incorrect file type. File type should be {file_type.upper()}"

    if error_msg:
        with open(invalid_file, "w") as d:
            d.write(error_msg)
        print(error_msg)
