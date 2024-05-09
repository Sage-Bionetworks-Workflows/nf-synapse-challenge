#!/usr/bin/env python3
"""
This module does the following things:
1. runs the Docker container
2. creates and stores relevant log messages into a log file
3. handles any output files generated by the submitted Docker container
4. renames the output file to include the submission ID

This module recycles functionality seen here:
https://github.com/Sage-Bionetworks-Challenges/model-to-data-challenge-workflow/blob/82ff3dc0ea8b83d727a7fbecf9550efdc010eadd/run_docker.py
"""


import os
import sys
from glob import glob
from typing import Optional, Union, List, NamedTuple
from zipfile import ZipFile

import docker
import synapseclient

import helpers


class UpdatedMessages(NamedTuple):
    log_message: str
    error_message: Union[None, str]


class OutputsHandled(NamedTuple):
    output_file: str
    log_text: str


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

        input_error = f"InputError: Submission {submission_id} has no associated Docker image"
        print(input_error)
        return input_error
    image_id = f"{docker_repository}@{docker_digest}"

    return image_id


def make_invalid_output(file_name: str, log_file_path: str, file_content: str) -> str:
    """
    Creates an invalid new output file, given the original file name, log file path, and file content, and returns the path of the new file.
    Parameters:
        file_name (str): The name of the original file.
        log_file_path (str): The path where the new file will be created.
        file_content (str): The content to be written to the new file.
    Returns:
        invalid_file: The path of the newly created file with the invalid data.

    """
    invalid_file_name = "INVALID_" + file_name
    invalid_file = os.path.join(log_file_path, invalid_file_name)
    with open(invalid_file, "w") as d:
        d.write(file_content)

    return invalid_file


def check_output_file_size(
    file_list: List[str],
    log_text: str,
    bad_output_msg: Optional[str],
) -> NamedTuple:
    """
    Checks if the given output file generated from the Docker submission is empty.
    This function handles the following cases:
    1. If the output file is empty, it will update and return the log_text and bad_output_msg inputs
    2. If the output file is not empty, it will return the log_text and bad_output_msg inputs
    as they were fed into the function call originally

    Arguments:
        file_list: The output file generated from the Docker submission (stored in a list)
        log_text: The current log text
        bad_output_msg: The current bad output message

    Returns:
        log_text: The updated log text (if applicable)
        bad_output_msg: The updated bad output message (if applicable)

    """
    # Declaring variables
    # We would only run this function if there is only one output file in the list
    file = file_list[0]

    # Check output files that are zipped into a single file
    if ".zip" in os.path.basename(file):
        with ZipFile(file, "r") as zipfile:
            incorrect_size = any(
                zip_info.file_size == 0
                for zip_info in zipfile.infolist()
                if not zip_info.is_dir()
            )

    # Check output files that are not zipped
    else:
        incorrect_size = True if os.path.getsize(file) == 0 else False

    # Next, update the log_text and bad_output_msg inputs, if necessary
    if incorrect_size:
        bad_output_msg = f"Could not evaluate because one or more output files are empty: {os.path.basename(file)}"
        if isinstance(log_text, bytes):
            log_text = log_text.decode("utf-8")
            log_text = log_text + "\n" + bad_output_msg

    return UpdatedMessages(log_message=log_text, error_message=bad_output_msg)


def handle_outputs(
    output_path: str, output_file_name: str, log_text: str
) -> NamedTuple:
    """
    Handles any output files generated by the submitted Docker container:
    1. Checks if an incorrect number of output files were generated
    2. Checks if the output file is empty

    Arguments:
        output_path: The path to the output directory.
        output_file_name: The name of the output file.
        log_text: The log text to be updated, if an incorrect number of
                  output files were found.

    Returns:
        output_file: The path to the output file.
        log_text: The log text that was updated, if an incorrect number of
                  output files were found.

    """
    # Glob any expected output files stored in the output_dir as a result of the container run
    file_glob = glob(os.path.join(output_path, output_file_name + ".*"))

    bad_output_msg = None

    # First check if an incorrect number of output files were generated
    if len(file_glob) != 1:
        bad_output_msg = f"Expected 1 Docker container output file with base name '{output_file_name}' in the output directory. Got {len(file_glob)}, or a file incorrectly named. If multiple output files are generated, please zip them into a single file for processing"
        if isinstance(log_text, bytes):
            log_text = log_text.decode("utf-8")
        log_text = log_text + "\n" + bad_output_msg

    # Then check if the output file is empty
    elif len(file_glob) == 1:
        updated_messages = check_output_file_size(file_glob, log_text, bad_output_msg)
        log_text = updated_messages.log_message
        bad_output_msg = updated_messages.error_message

    # If the output file is empty or an incorrect number of output files were generated, create an INVALID output file
    # to carry on in the workflow, and notify the user of the inconsistency
    output_file = (
        file_glob[0]
        if not bad_output_msg
        else make_invalid_output(
            file_name=output_file_name + ".csv",
            log_file_path=output_path,
            file_content=bad_output_msg,
        )
    )

    return OutputsHandled(output_file=output_file, log_text=log_text)


def create_log_file(
    log_file_name: str,
    log_max_size: int,
    log_file_path: Optional[Union[None, str]] = None,
    log_text: Optional[Union[str, bytes]] = None,
) -> None:
    """
    Creates the Docker submission execution log file.

    This function creates a log file with the given name and writes the given text to it.
    If no text is given, it writes "No Logs" to the file.

    Arguments:
        log_file_name: The name of the log file to create
        log_max_size: The maximum size of the log file in kilobytes
        log_file_path: The path where the log file will be created.
                       If not specified, the current working directory will be used.
        log_text: The text to write to the log file

    """
    if log_file_path is None:
        log_file_path = os.getcwd()

    # Get the size of the log text
    log_text = log_text or "No Logs"
    log_text_size = (
        len(log_text)
        if isinstance(log_text, bytes)
        else len(str(log_text).encode("utf-8"))
    )

    # Decode the log text if it is bytes
    log_text = (
        log_text.decode("utf-8", "ignore") if isinstance(log_text, bytes) else log_text
    )

    # Truncate the log message if it exceeds the maximum size
    if log_text_size > log_max_size * 1000:
        print(f"Original log message exceeds {log_max_size} Kb. Truncating...")
        log_text = log_text[-(log_max_size * 1000) :]

    with open(
        os.path.join(log_file_path, log_file_name),
        "w",
        encoding="utf-8",
        errors="ignore",
    ) as log_file:
        log_file.write(log_text)

    # Add some print statements to notify those monitoring the workflow
    if log_text_size <= log_max_size * 1000:
        print(f"Log file created: {log_file_name}")
    else:
        print(f"Truncated log file created: {log_file_name}")


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


def validate_submission(docker_image: str, output_path: str, output_file_name: str) -> None:
    """
    Validates the Docker image for the submission

    Arguments:
        docker_image: Docker image identifier in the format: '<image_name>@<sha_code>'
        output_path: Path to the output directory that houses the output file and log file
        output_file_name: Name of the output file generated from the container

    """
    # If the submission is not a Docker image, create an invalid output file
    # store the error message in a log file, and end the script call
    if "InputError" in docker_image:

        # Make the output directory since it wouldnt' exist without running the container
        os.makedirs(output_path)

        # Create an invalid output file
        make_invalid_output(file_name=output_file_name + ".csv",
                            log_file_path=output_path,
                            file_content=docker_image)

        create_log_file(
            log_file_name=log_file_name,
            log_max_size=log_max_size,
            log_file_path=output_path,
            log_text=docker_image,
        )

        return "INVALID"

    return "VALID"

def run_docker(
    submission_id: str,
    log_file_name: str = "docker.log",
    log_max_size: int = 50,
    rename_output: bool = True,
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
        log_max_size: The maximum size of the log file that will be written, in kilobytes
        rename_output: If True, renames the output file to include the submission ID.
                       For example, if the submission ID is '123' and the output file is 'predictions.csv',
                       then the 'predictions.csv' file is renamed to '123_predictions.csv'.

    Returns:
        None

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

    # Get the output directory based on the mounted volumes dictionary used to run the container
    output_path = next(
        (key for key in volumes.keys() if "output" in volumes[key]["bind"]), None
    )

    output_file_name = "predictions"

    # Ensure the submission is a valid Docker image
    validation_result = validate_submission(docker_image, output_path, output_file_name)
    if validation_result == "INVALID":
        return

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

    # Capture any errors that may occur during the attempt to run the container
    except Exception as e:
        # Reformat the error message
        log_text = str(e).replace("\\n", "\n")

        # Create log file and store the log error message (``log_text``) inside
        create_log_file(
            log_file_name=log_file_name,
            log_max_size=log_max_size,
            log_file_path=output_path,
            log_text=log_text,
        )

    # Handle any outputs from the container run in the ``output/`` directory, and its contents.
    # This means: An expected output file, more than 1 output file, no output file, or an empty output file.
    outputs_handled = handle_outputs(
        output_path=output_path, output_file_name=output_file_name, log_text=log_text
    )

    # Create log file and store the log message (``log_text``) inside
    create_log_file(
        log_file_name=log_file_name,
        log_max_size=log_max_size,
        log_file_path=output_path,
        log_text=outputs_handled.log_text,
    )

    # Rename the predictions file if requested
    if rename_output:
        helpers.rename_file(submission_id, outputs_handled.output_file)


if __name__ == "__main__":
    submission_id = sys.argv[1]
    log_max_size = int(sys.argv[2])
    log_file_name = f"{submission_id}_docker.log"

    run_docker(submission_id, log_file_name=log_file_name, log_max_size=log_max_size)
