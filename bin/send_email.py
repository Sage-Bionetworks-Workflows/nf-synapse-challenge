#!/usr/bin/env python3

import sys
import synapseclient

from typing import List, NamedTuple


class SubmissionAnnotations(NamedTuple):
    status: str
    score: int
    reason: str


def get_participant_id(syn: synapseclient.Synapse, submission_id: str) -> List[str]:
    """
    Retrieves the teamId of the participating team that made
    the submission. If the submitter is an individual rather than
    a team, the userId for the individual is retrieved.

    Arguments:
      syn: A Synapse Python client instance
      submission_id: The ID for an individual submission within an evaluation queue

    Returns:
      Returns the synID of a team or individual participant
    """
    # Retrieve a Submission object
    submission = syn.getSubmission(submission_id, downloadFile=False)

    # Get the teamId or userId of submitter
    participant_id = submission.get("teamId") or submission.get("userId")

    # Ensure that the participant_id returned is a list
    # so it can be fed into syn.sendMessage(...) later.
    return [participant_id]


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
        ): f"Submission {submission_id} has been evaluated with a score value of {str(score)}. View all your scores here: https://www.synapse.org/#!Synapse:{view_id}/tables/",
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
        + "\n"
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

    body = templates.get((status, email_with_score.lower()))

    # If there is a typo in ``email_with_score``, ``body`` will be None;
    # Raise an error if so, to avoid sending empty e-mails...
    if body is None:
        raise ValueError(
            f"``email_with_score`` can either be yes/no. Got {email_with_score}."
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
    # TODO: "auc" may not always be the annotation name for score.
    # Should enforce annotation names in the score/validation scripts.
    submission_status = submission_annotations.get("validation_status")[0]
    submission_score = submission_annotations.get("auc")[0]
    error_reason = submission_annotations.get("validation_errors")[0]

    return SubmissionAnnotations(
        status=submission_status, score=submission_score, reason=error_reason
    )


def send_email(view_id: str, submission_id: str, email_with_score: str):
    """
    Sends an e-mail on the status of the individual submission
    to the submitting team or individual.

    Arguments:
      view_id: The view Id of the Submission View on Synapse
      submission_id: The ID for an individual submission within an evaluation queue

    """
    # Initiate connection to Synapse
    syn = synapseclient.login()

    # Get MODEL_TO_DATA annotations for the given submission
    submission_annotations = get_annotations(syn, submission_id)

    # Get the Synapse users to send an e-mail to
    ids_to_notify = get_participant_id(syn, submission_id)

    # Create the subject and body of the e-mail message, depending on submission status
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

    # Sends an e-mail notifying participant(s) that the evaluation succeeded or failed
    message = syn.sendMessage(
        userIds=ids_to_notify, messageSubject=subject, messageBody=body
    )


if __name__ == "__main__":
    view_id = sys.argv[1]
    submission_id = sys.argv[2]
    email_with_score = sys.argv[3]

    send_email(view_id, submission_id, email_with_score)
