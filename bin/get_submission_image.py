#!/usr/bin/env python3

import sys
import pandas as pd
import synapseclient


def get_submission_image(submission_id: str) -> str:
    """
    Retrieves Docker Image ID from submission

    Arguments:
        submission_id: Submission ID to be queried

    Returns:
        image_id: Docker image identifier in the format: '<image_name>@<sha_code>'

    Raises:
        ValueError: If submission has no associated Docker image
    """
    syn = synapseclient.login(silent=True)
    submission = syn.getSubmission(submission_id)
    docker_repository = submission.get("dockerRepositoryName", None)
    docker_digest = submission.get("dockerDigest", None)
    if not docker_digest or not docker_repository:
        raise ValueError(f"Submission {submission_id} has no associated Docker image.")
    image_id = f"{docker_repository}@{docker_digest}"
    return image_id


if __name__ == "__main__":
    submission_id = sys.argv[1]
    image_id = get_submission_image(submission_id)
    print(image_id)
