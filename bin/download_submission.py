#!/usr/bin/env python3

import argparse
import sys

import synapseclient

def get_args():
    """Set up command-line interface and get arguments without any flags."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-id", "-s", type=str, required=True, help="The ID of submission")
    parser.add_argument("--file-type", "-f", type=str, required=True, help="The type of file the submission should be")

    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    submission_id = args.submission_id

    syn = synapseclient.Synapse()
    syn.login(silent=True)

    submission = syn.getSubmission(submission_id, downloadLocation=".")
    entity_type = submission["entity"].concreteType
    
    # TODO: Eventually we want to abstract this logic into the `make_invalid_file` function
    # in model-to-data's `run_docker.py`, and move that out somewhere else.
    if entity_type != "org.sagebionetworks.repo.model.FileEntity":
        invalid_file = "INVALID_predictions.csv"
        with open(invalid_file, "w") as d:
            d.write(f"Submission Entities must be of type 'org.sagebionetworks.repo.model.FileEntity', submitted Entity is '{entity_type}'")

    print(f"Submission Entities must be of type 'org.sagebionetworks.repo.model.FileEntity', submitted Entity is '{entity_type}'")
