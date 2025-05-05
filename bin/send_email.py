#!/usr/bin/env python3

import sys
from typing import List, NamedTuple

import synapseclient

import helpers

class SubmissionAnnotations(NamedTuple):
    status: str
    score: List[int]
    reason: str


def get_score_dict(score):
    strings = [""]
    for key in score.keys():
        string = f"{key} : {score[key][0]}" + "\n"
        strings.append(string)

    return strings


def email_template(
    status: str,
    email_with_score: bool,
    submission_id: str,
    view_id: str,
    score: int,
    reason: str,
) -> str:
    """
    Selects a pre-defined e-mail template based on user-fed email_with_score, and the validation
    status of the particular submission.

    Arguments:
      status: The submission status
      email_with_score: "no" if e-mail should not include score value / link to submissions views. Otherwise "yes".
      submission_id: The submission ID of the given submission on Synapse
      view_id: The submission view ID on Synapse
      score: The score value of the submission
      reason: The reason for the validation error, if present.

    Returns:
      A string for that represents the body of the e-mail to be sent out to submitting team or individual.

    """
    templates = {
        (
            "VALIDATED",
            "yes",
        ): f"Submission {submission_id} has been evaluated with the following scores:\n"
        + "\n".join(get_score_dict(score))
        + f"\nView all your scores here: https://www.synapse.org/#!Synapse:{view_id}/tables/",
        (
            "VALIDATED",
            "no",
        ): f"Submission {submission_id} has been evaluated. Your score will be available after Challenge submissions are closed. Thank you for participating!",
        (
            "INVALID",
            "yes",
        ): f"Evaluation failed for Submission {submission_id}."
        + "\n"
        + f"Reason: '{reason}'."
        + "\n\n"
        + f"View your submissions here: https://www.synapse.org/#!Synapse:{view_id}/tables/, and contact the organizers for more information.",
        (
            "INVALID",
            "no",
        ): f"Evaluation failed for Submission {submission_id}."
        + "\n"
        + f"Reason: '{reason}'."
        + "\n"
        + "Please contact the organizers for more information.",
    }

    body = templates.get((status, email_with_score))

    # If there is a typo in ``email_with_score``, ``body`` will be None;
    # Raise an error if so, to avoid sending empty e-mails...
    if body is None:
        raise ValueError(
            f"Incorrect status and/or email_with_score arguments. Got status: {status}, email_with_score: {email_with_score}."
        )

    return body


def get_annotations(syn: synapseclient.Synapse, submission_id: str) -> NamedTuple:
    """
    Gets the ``status`` ``score`` and ``reason`` annotations for the given
    submission on Synapse.

    1. ``status`` is the submission status, as defined by the last begun stage
    in the MODEL_TO_SYNAPSE workflow.
    2. ``score`` is the score of the model, used to determine its accuracy.
    3. ``reason`` is the reason for the validation error, if there was one.
    It remains an empty string (None) if no validation error.

    """
    submission_annotations = syn.getSubmissionStatus(submission_id)[
        "submissionAnnotations"
    ]
    submission_status = submission_annotations.get("validation_status")[0]
    error_reason = submission_annotations.get("validation_errors")[0]

    # TODO: A more elegant way to only get the score annotations?
    non_score_annotations = [
        "score_errors",
        "score_status",
        "validation_errors",
        "validation_status",
        "predictions_id",
        "docker_logs_id"
    ]
    submission_scores = {
        key: submission_annotations.get(key)
        for key in submission_annotations.keys()
        if key not in non_score_annotations
    }
    return SubmissionAnnotations(
        status=submission_status, score=submission_scores, reason=error_reason
    )


def send_email(view_id: str, submission_id: str, email_with_score: str, notification_type: str, project_name: str):
    """
    Sends an e-mail on the status of the individual submission
    to the submitting team or individual.

    Arguments:
      view_id: The view Id of the Submission View on Synapse
      submission_id: The ID for an individual submission within an evaluation queue
      email_with_score: Whether to include the score in the e-mail
      notification_type: The type of notification to send (determines the subject and body of e-mail)

    """
    # Initiate connection to Synapse
    syn = synapseclient.login()

    # Get MODEL_TO_DATA annotations for the given submission
    submission_annotations = get_annotations(syn, submission_id)

    # Get the Synapse users to send an e-mail to
    ids_to_notify = helpers.get_participant_id(syn, submission_id)

    # Get the name of the participant(s)
    participant_name = helpers.get_participant_name(syn, submission_id)

    # Create the subject and body of the e-mail message, depending on
    # the notification type and submission status:
    if notification_type.upper() == "BEFORE":
        # Before-evaluation notification
        subject = f"Evaluation Started: {submission_id}"
        body = (
            f"Dear {participant_name},\n\n"
            f"Your submission <b>{submission_id}</b> for the {project_name} project is now being evaluated. "
            "We will notify you again once the evaluation completes.\n\n"
            "Thank you for your participation!\n\n"
            "The Challenge Organizers"
        )
    else:
        # After-evaluation notification
        subject = (
            f"Evaluation Success: {submission_id}"
            if submission_annotations.status == "VALIDATED"
            else f"Evaluation Failed: {submission_id}"
        )
        body = email_template(
            submission_annotations.status,
            email_with_score,
            submission_id,
            view_id,
            submission_annotations.score,
            submission_annotations.reason,
        )

    syn.sendMessage(userIds=ids_to_notify, messageSubject=subject, messageBody=body)


if __name__ == "__main__":
    view_id = sys.argv[1]
    submission_id = sys.argv[2]
    email_with_score = sys.argv[3]
    notification_type = sys.argv[4]
    project_name = sys.argv[5]

    send_email(view_id, submission_id, email_with_score, notification_type, project_name)
