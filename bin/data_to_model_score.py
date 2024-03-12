#!/usr/bin/env python3

import json
import os
import sys
import typing


INVALID = "INVALID"
SCORED = "SCORED"


def score_submission(predictions_path: str, status: str) -> typing.Tuple[str, dict]:
    """Determine the score of a submission. This is a placeholder function.

    Args:
        predictions_path: path to the predictions file
        status: current submission status

    Returns:
        result: dictionary containing score, status and errors
    """
    if status == INVALID:
        score_status = INVALID
        score = None
        message = f"Submission was not scored due to {INVALID} status"
    else:
        # placeholder file reading
        with open(predictions_path, "r") as sub_file:
            predictions_contents = sub_file.read()
        try:
            # placeholder scoring
            score = 1 + 1
            score_status = SCORED
            message = ""
        except Exception as e:
            message = f"Error {e} occurred while scoring"
            score = None
            score_status = INVALID
    result = {
        "auc": score,
        "score_status": score_status,
        "score_errors": message,
    }
    return score_status, result


def update_json(results_path: str, result: dict) -> None:
    """Update the results.json file with the current score and status

    Args:
        results_path: path to the results.json file
        result: dictionary containing score, status and errors
    """
    file_size = os.path.getsize(results_path)
    with open(results_path, "r") as o:
        data = json.load(o) if file_size else {}
    data.update(result)
    with open(results_path, "w") as o:
        o.write(json.dumps(data))


if __name__ == "__main__":
    submission_id = sys.argv[1]
    status = sys.argv[2]
    predictions_path = sys.argv[3]
    staged_path = sys.argv[4]
    results_path = sys.argv[5]
    score_status, result = score_submission(predictions_path, status)
    update_json(results_path, result)
    print(score_status)
