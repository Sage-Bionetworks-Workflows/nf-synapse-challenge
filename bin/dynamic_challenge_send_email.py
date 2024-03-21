#!/usr/bin/env python3
"""
This module uses functions from send_email.py and some custom logic to
send email notofications for the dynamic challenge
"""

import sys
import synapseclient

from typing import Tuple

from helpers import get_participant_id
from send_email import (
    get_score_dict,
    get_annotations,
)


BEFORE = "BEFORE"
AFTER = "AFTER"


def email_template(
    status: str,
    email_with_score: bool,
    submission_id: str,
    target_link: str,
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
      target_link: The redirection link to display participants' own submissions
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
        + f"\nView all your submissions here: {target_link}.",
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
        + f"View your submissions here: {target_link}."
        + "\n"
        + "Please contact the organizers for more information.",
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


def get_evaluation(syn: synapseclient.Synapse, submission_id: str) -> Tuple[str, str]:
    """Get evaluation id for the submission

    Arguments:
        syn: Synapse connection
        submission_id: The id of submission

    Returns:
        eval: the tuple of evaluation ID and evaluation name.

    Raises:
        Exception: if an error occurs
    """
    try:
        eval_id = syn.getSubmission(submission_id, downloadFile=False).get(
            "evaluationId"
        )
        eval_name = syn.getEvaluation(eval_id).get("name")
        return eval_id, eval_name
    except Exception as e:
        print(
            f"An error occurred while retrieving the evaluation for submission {submission_id}: {e}"
        )


def get_target_link(synapse_client: synapseclient.Synapse, eval_id: str) -> str:
    """
    Retrieves the redirection link returned in the email to view submissions for a given submission evaluation ID.

    Arguments:
        syn: Synapse connection
        eval_id: the evaluation id of submission.

    Returns:
        link: The redirection link to the submission page.
    """

    EVAL_TO_LINK = {
        "9615379": "https://www.synapse.org/#!Synapse:syn52052735/wiki/626195",
        "9615532": "https://www.synapse.org/#!Synapse:syn52052735/wiki/626203",
        "9615534": "https://www.synapse.org/#!Synapse:syn52052735/wiki/626211",
        "9615535": "https://www.synapse.org/#!Synapse:syn52052735/wiki/626216",
    }
    link = EVAL_TO_LINK.get(eval_id, None)
    if link:
        return link
    project_id = synapse_client.getEvaluation(eval_id).get("contentSource")
    return f"https://www.synapse.org/#!Synapse:{project_id}"


def send_email(
    submission_id: str, email_with_score: str, notification_type: str
) -> None:
    """
    Sends an e-mail on the status of the individual submission
    to the submitting team or individual.

    Arguments:
      submission_id: The ID for an individual submission within an evaluation queue
      email_with_score: Whether to include the score in the e-mail
      notification_type: The type of notification to send

    Raises:
      ValueError: if an incorrect type is provided for notification_type
    """
    if notification_type not in [BEFORE, AFTER]:
        raise ValueError(f"Invalid notification_type. Must be '{BEFORE}' or '{AFTER}'")
    # Initiate connection to Synapse
    syn = synapseclient.login()

    # Get the Synapse users to send an e-mail to
    ids_to_notify = get_participant_id(syn, submission_id)

    if notification_type == BEFORE:
        subject = f"Evaluation for Submission {submission_id} is In Progress"
        body = (
            f"Evaluation for Submission {submission_id} is In Progress. "
            "Further notification will be provided when evaluation is complete."
        )
    if notification_type == AFTER:
        # Get MODEL_TO_DATA annotations for the given submission
        submission_annotations = get_annotations(syn, submission_id)

        # Get the evaluation's Id and name for the given submission
        eval_id, eval_name = get_evaluation(syn, submission_id)

        # Get the redirection link to view submission page
        target_link = get_target_link(syn, eval_id)

        # Create the subject and body of the e-mail message, depending on submission status
        subject = (
            f"Submission to '{eval_name}' Success: {submission_id}"
            if submission_annotations.status == "VALIDATED"
            else f"Submission to '{eval_name}' Failed: {submission_id}"
        )
        body = email_template(
            submission_annotations.status,
            email_with_score,
            submission_id,
            target_link,
            submission_annotations.score,
            submission_annotations.reason,
        )

    # Sends an e-mail notifying participant(s) that the evaluation succeeded or failed
    syn.sendMessage(userIds=ids_to_notify, messageSubject=subject, messageBody=body)


if __name__ == "__main__":
    # Keeping view_id in despite not being used.
    # This is so that we can still use one `send_email.nf` process while supporting both `BEFORE` and `AFTER` notifications
    view_id = sys.argv[1]
    submission_id = sys.argv[2]
    email_with_score = sys.argv[3]
    notification_type = sys.argv[4]

    send_email(submission_id, email_with_score, notification_type)
