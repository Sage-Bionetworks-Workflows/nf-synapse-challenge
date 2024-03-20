#!/usr/bin/env python3
"""
This module runs the docker container and outputs relevant log messages into a log file
which then gets stored on Synapse under its corresponding log folder.

This module recycles functionality seen here:
https://github.com/Sage-Bionetworks-Challenges/model-to-data-challenge-workflow/blob/82ff3dc0ea8b83d727a7fbecf9550efdc010eadd/run_docker.py
"""

import os
import sys
from glob import glob
from typing import Optional, Union

import docker
import synapseclient

import helpers


def get_submission_image(syn: synapseclient.Synapse, submission_id: str) -> str:
    """
    Retrieves Docker Image ID from submission

    Arguments:
        submission_id: Submission ID to be queried

    Returns:
        image_id: Docker image identifier in the format: '<image_name>@<sha_code>'

    Raises:
        ValueError: If submission has no associated Docker image

    """
    submission = syn.getSubmission(submission_id)
    docker_repository = submission.get("dockerRepositoryName", None)
    docker_digest = submission.get("dockerDigest", None)
    if not docker_digest or not docker_repository:
        raise ValueError(f"Submission {submission_id} has no associated Docker image.")
    image_id = f"{docker_repository}@{docker_digest}"

    return image_id


def create_log_file(
    log_file_name: str,
    log_file_path: Optional[Union[None, str]] = None,
    log_text: Optional[Union[str, bytes]] = None,
) -> None:
    """
    Creates the Docker submission execution log file.

    This function creates a log file with the given name and writes the given text to it.
    If no text is given, it writes "No Logs" to the file.

    Arguments:
        log_filename: The name of the log file to create
        log_text: The text to write to the log file. If given as a byte string,
                  it will be decoded as UTF-8 before being written.

    """
    if not log_file_path:
        log_file_path = os.getcwd()

    with open(
        os.path.join(log_file_path, log_file_name),
        "w",
        encoding="ascii",
        errors="ignore",
    ) as log_file:
        if log_text is not None:
            if isinstance(log_text, bytes):
                log_text = log_text.decode("utf-8")
            log_file.write(log_text)
        else:
            log_file.write("No Logs")


def mount_volumes() -> dict:
    """
    Mount volumes onto a docker container.

    This function returns a dictionary of volumes to mount on a docker
    container, in the format required by the Docker Python API. The
    dictionary keys are the paths on the host machine, and the values are
    dictionaries with the following keys:

    - bind: The path on the container where the volume will be mounted
    - mode: The permissions on the mounted volume ("ro" for read-only or
      "rw" for read-write)

    The volumes mounted are:

    - The current working directory's output/ directory, mounted as read-write
    - The current working directory's input/ directory, mounted as read-only
    """
    output_dir = os.path.join(os.getcwd(), "output")
    input_dir = os.path.join(os.getcwd(), "input")

    mounted_volumes = {
        output_dir: {"bind": "/output", "mode": "rw"},
        input_dir: {"bind": "/input", "mode": "ro"},
    }

    volumes = {}
    for vol in mounted_volumes.keys():
        volumes[vol] = mounted_volumes[vol]

    return volumes


def run_docker(
    submission_id: str, log_file_name: str = "docker.log", rename_output: bool = True
) -> None:
    """
    A function to run a Docker container with the specified image and handle any exceptions that may occur.

    This function will run a Docker container using the image specified by the
    ``submission_id`` argument, and will mount the input/ and output/ directories
    in the current working directory to the corresponding locations in the
    container. If the container runs successfully, the function will store any
    generated predictions file in the /output directory to Synapse, along with
    any logs generated. If the container run fails, the function will store the
    error message in a log file on Synapse.

    Args:
        submission_id: The ID of the submission to run.
        log_file_name: The name of the log file to create.
        rename_output: If True, renames the output file to include the submission ID.
                       For example, if the submission ID is '123' and the output file is 'predictions.csv',
                       then the 'predictions.csv' file is renamed to '123_predictions.csv'.

    Returns:
        None

    Raises:
        ValueError: If the output directory does not exist, or if the predictions file is not found
                    in the output directory after running the Docker container.

    """
    # Get the Synapse authentication token from the environment variable
    synapse_auth_token: str = os.environ["SYNAPSE_AUTH_TOKEN"]

    # Communication with the Docker client
    client = docker.from_env()

    # Log into Synapse
    syn = synapseclient.login(silent=True)

    # Login to the Docker registry using SYNAPSE_AUTH_TOKEN
    client.login(
        username="foo",
        password=synapse_auth_token,
        registry="https://docker.synapse.org",
    )

    # Mount the input/ and output/ volumes that will exist in the submission container
    volumes = mount_volumes()

    # Get the Docker image ID from the submission
    docker_image = get_submission_image(syn, submission_id)

    # Assign the path to the log file
    log_file_path = os.path.join(os.getcwd(), "output")

    # Run the docker image using the client:
    # We use ``detach=False`` and ``stderr=True``
    # to catch for and log possible errors in the logfile.
    try:
        container = client.containers.run(
            docker_image,
            detach=False,
            volumes=volumes,
            network_disabled=True,
            mem_limit="6g",
            stderr=True,
        )

        log_text = container

    except Exception as e:
        log_text = str(e).replace("\\n", "\n")
        create_log_file(
            log_file_name=log_file_name, log_file_path=log_file_path, log_text=log_text
        )

        raise

    # Create log file and store the log message (``log_text``) inside
    create_log_file(
        log_file_name=log_file_name, log_file_path=log_file_path, log_text=log_text
    )

    # Rename the predictions file if requested
    if rename_output:
        # Get the output directory based on the mounted volumes dictionary used to run the container
        output_dir = next(
            (key for key in volumes.keys() if "output" in volumes[key]["bind"]), None
        )
        if not os.path.exists(output_dir):
            raise ValueError("Output directory found in ``volumes`` does not exist.")

        # Get the predictions file, assuming the file exists. Otherwise, ``predictions_file = None``
        predictions_file = next(
            (
                file
                for file in glob(os.path.join(output_dir, "predictions.*"))
                if os.path.exists(file)
            ),
            None,
        )
        if predictions_file is None:
            raise ValueError("No predictions file found in output directory.")

        # Rename the predictions file to include the submission ID
        helpers.rename_file(submission_id, predictions_file)


if __name__ == "__main__":
    submission_id = sys.argv[1]
    log_file_name = f"{submission_id}_docker.log"

    run_docker(submission_id, log_file_name=log_file_name)
