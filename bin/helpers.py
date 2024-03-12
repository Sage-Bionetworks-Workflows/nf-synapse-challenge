
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
