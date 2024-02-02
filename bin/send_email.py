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


def send_email(view_id: str, submission_id: str):
    """
    Sends an e-mail on the status of the individual submission
    to the participant team or participant individual.

    Arguments:
      view_id: The view Id of the Submission View on Synapse
      submission_id: The ID for an individual submission within an evaluation queue
    """
    syn = synapseclient.login()
    status = syn.getSubmissionStatus(submission_id)["submissionAnnotations"]["validation_status"]

    # Get the synapse users to send an e-mail to
    ids_to_notify = get_participant_id(syn, submission_id)

    # Sends an e-mail notifying participant(s) that the evaluation succeeded
    if status == ["VALIDATED"]:
      subject = f"Evaluation Success: {submission_id}"
      body = f"Submission {submission_id} has been evaluated. View your scores here: https://www.synapse.org/#!Synapse:{view_id}/tables/"

    # Otherwise, send an error message to participant(s) and engineers of the infrastructure
    else:
      subject = f"Evaluation Failed: {submission_id}"
      body = f"Evaluation failed for Submission {submission_id}. Submission was left with a validation status of {status}. View your submissions here: https://www.synapse.org/#!Synapse:{view_id}/tables/"

    syn.sendMessage(userIds=ids_to_notify,
                    messageSubject=subject,
                    messageBody=body)

if __name__ == "__main__":
    view_id = sys.argv[1]
    submission_id = sys.argv[2]
    send_email(view_id, submission_id)
