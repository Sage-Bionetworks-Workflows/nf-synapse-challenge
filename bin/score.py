#!/usr/bin/env python3

import json
import os
import sys


def score_submission(predictions_path: str, status: str) -> dict:
    """Determine the score of a submission. This is a placeholder function.

    Args:
        predictions_path (str): path to the predictions file
        status (str): current submission status

    Returns:
        result (dict): dictionary containing score, status and errors
    """
    if status == "INVALID":
        score_status = "INVALID"
        score1, score2, score3 = None, None, None
    else:
        # placeholder file reading
        with open(predictions_path, "r") as sub_file:
            predictions_contents = sub_file.read()
        try:
            # placeholder scoring
            score1 = 1 + 1
            score2 = score1 * 2
            score3 = score1 * 3
            score_status = "SCORED"
            message = ""
        except Exception as e:
            message = f"Error {e} occurred while scoring"
            score1, score2, score3 = None, None, None
            score_status = "INVALID"
    result = {
        "score1": score1,
        "score2": score2,
        "score3": score3,
        "score_status": score_status,
        "score_errors": message,
    }
    return score_status, result


def update_json(results_path: str, result: dict) -> None:
    """Update the results.json file with the current score and status

    Args:
        results_path (str): path to the results.json file
        result (dict): dictionary containing score, status and errors
    """
    file_size = os.path.getsize(results_path)
    with open(results_path, "r") as o:
        data = json.load(o) if file_size else {}
    data.update(result)
    with open(results_path, "w") as o:
        o.write(json.dumps(data))


if __name__ == "__main__":
    predictions_path = sys.argv[1]
    results_path = sys.argv[2]
    status = sys.argv[3]
    score_status, result = score_submission(predictions_path, status)
    update_json(results_path, result)
    print(score_status)
