#!/usr/bin/env python3

import sys
import synapseclient

from typing import List


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
    templates = {
        (
            "VALIDATED",
            "True",
        ): f"Submission {submission_id} has been evaluated with a score value of {str(score)}. View all your scores here: https://www.synapse.org/#!Synapse:{view_id}/tables/",
        (
            "VALIDATED",
            "False",
        ): f"Submission {submission_id} has been evaluated. Your score will be available after Challenge submissions are closed. Thank you for participating!",
        (
            "INVALID",
            "True",
        ): f"Evaluation failed for Submission {submission_id}. Reason: {reason}. View your submissions here: https://www.synapse.org/#!Synapse:{view_id}/tables/. Please contact the organizers for more information.",
        (
            "INVALID",
            "False",
        ): f"Evaluation failed for Submission {submission_id}. Reason: {reason}. Please contact the organizers for more information.",
    }

    body = templates.get((status, email_with_score))

    return body


def send_email(view_id: str, submission_id: str, email_with_score: bool):
    """
    Sends an e-mail on the status of the individual submission
    to the participant team or participant individual.

    Arguments:
      view_id: The view Id of the Submission View on Synapse
      submission_id: The ID for an individual submission within an evaluation queue
    """
    syn = synapseclient.login()
    # TODO: Consolidate calls to submission Annotations
    status = syn.getSubmissionStatus(submission_id)["submissionAnnotations"][
        "validation_status"
    ][0]
    # TODO: "auc" may not always be the annotation name for score. How to generalize?
    score = syn.getSubmissionStatus(submission_id)["submissionAnnotations"]["auc"][0]
    reason = syn.getSubmissionStatus(submission_id)["submissionAnnotations"][
        "validation_errors"
    ][0]

    # Get the synapse users to send an e-mail to
    ids_to_notify = get_participant_id(syn, submission_id)

    # Sends an e-mail notifying participant(s) that the evaluation succeeded or failed
    # depending on status
    subject = (
        f"Evaluation Success: {submission_id}"
        if status == "VALIDATED"
        else f"Evaluation Failed: {submission_id}"
    )
    body = email_template(
        status, email_with_score, submission_id, view_id, score, reason
    )

    syn.sendMessage(userIds=ids_to_notify, messageSubject=subject, messageBody=body)


if __name__ == "__main__":
    view_id = sys.argv[1]
    submission_id = sys.argv[2]
    email_with_score = sys.argv[3]
    send_email(view_id, submission_id, email_with_score)
