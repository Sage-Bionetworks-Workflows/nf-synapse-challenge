#!/usr/bin/env python3

import argparse
import tarfile
from typing import List
import synapseclient
import json
import os


INVALID = "INVALID"
VALIDATED = "VALIDATED"


def get_args():
    """Set up command-line interface and get arguments without any flags."""
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_id", type=str, help="The ID of submission")
    parser.add_argument(
        "predictions_path", type=str, help="The path to the predictions folder"
    )
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        default="results.json",
        help="The path to output file",
    )

    return parser.parse_args()


def get_expected_filenames(eval_id: str) -> List[str]:
    """Generates a list of expected filename patterns based on the evaluation ID.

    Arguments:
        eval_id: The evaluation ID.

    Returns:
        A list of expected filename patterns.
    """
    if eval_id == "9615601":
        expected_systems = ["HouseZero"]
    else:
        expected_systems = [
            "doublependulum",
            "Lorenz",
            "Rossler",
            "Lorenz96",
            "KS",
            "Kolmogorov",
        ]
    task_mapping = {
        "9615379": ["X1"],  # Task1
        "9615532": ["X2", "X3", "X4", "X5"],  # Task2
        "9615534": ["X6"],  # Task3
        "9615535": ["X7", "X8", "X9"],  # Task4
        '9615601': ["X21", "X74"],  # Task5
    }
    expected_patterns = []
    for file_prefix in task_mapping[eval_id]:
        for system in expected_systems:
            expected_patterns.append(f"{system}_{file_prefix}prediction.npy")
    return expected_patterns


def untar(directory: str, tar_filename: str, pattern="*") -> None:
    """Untar a tar file into a directory

    Arguments:
        directory: Path to directory to untar files
        tar_filename:  tar file path
    """
    with tarfile.open(tar_filename, "r") as tar:
        for member in tar.getmembers():
            if member.isfile() and member.name.endswith(pattern):
                member.name = os.path.basename(member.name)
                tar.extract(member, path=directory)


def get_eval_id(syn: synapseclient.Synapse, submission_id: str) -> str:
    """Get evaluation id for the submission

    Arguments:
        syn: Synapse connection
        submission_id: the id of submission

    Returns:
        sub_id: the evaluation ID, or None if an error occurs.
    """
    try:
        eval_id = syn.getSubmission(submission_id).get("evaluationId")
        return eval_id
    except Exception as e:
        print(
            f"An error occurred while retrieving the evaluation ID for submission {submission_id}: {e}"
        )


if __name__ == "__main__":

    args = get_args()
    sub_id = args.submission_id
    predictions_path = args.predictions_path
    results_path = args.output

    # login to synapase
    syn = synapseclient.Synapse()
    syn.login(silent=True)

    # get the evaluation ID to identify corresponding scoring parameters
    eval_id = get_eval_id(syn, sub_id)

    invalid_reasons = []

    if predictions_path is None or os.path.basename(predictions_path) != 'predictions.tar':
        prediction_status = INVALID
        invalid_reasons.append('Error:  No "predictions.tar" found')
    else:
        expected_files = get_expected_filenames(eval_id)
        untar("val_predictions", tar_filename=predictions_path, pattern=".npy")
        pred_files = os.listdir("val_predictions")

        matched_files = [f for f in pred_files if f in expected_files]

        if not matched_files:
            prediction_status = INVALID
            invalid_reasons.append(
                f'Error: No expected prediction file(s) found in the {os.path.basename(predictions_path)}.'
            )
        else:
            prediction_status = VALIDATED

    result = {
        "validation_status": prediction_status,
        "validation_errors": ";".join(invalid_reasons),
    }

    with open(results_path, "w") as o:
        o.write(json.dumps(result))
    print(prediction_status)
