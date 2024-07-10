#!/usr/bin/env python3

import argparse
import sys

import synapseclient

def get_args():
    """Set up command-line interface and get arguments without any flags."""
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_id", type=str, help="The ID of submission")

    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    submission_id = args.submission_id

    syn = synapseclient.Synapse()
    syn.login(silent=True)

    submission = syn.getSubmission(submission_id, downloadLocation=".")
    entity_type = submission["entity"].concreteType
    if entity_type != "org.sagebionetworks.repo.model.FileEntity":
        open("dummy.txt", 'w').close()

    print(entity_type)
