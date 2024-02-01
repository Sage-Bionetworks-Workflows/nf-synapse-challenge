// sends an e-mail to the submitter 
// questions:
// 1. do we want to send the e-mail to the whole team or just the individual submitter?
// A: preference is sending e-mail to team first, then send to individual user_id if team id is not available. send failure e-mails to organizers + participants.
// 2. if people want to opt-out, how would they be able to?
// A: they can opt out through the Synapse service since challengutils is calling the py client which is calling the API
// 3. do we want the e-mail sent at the end of the workflow?
// 4. how to send a failure e-mail if submission is not accepted?
// 5. do we want to send an e-mail per submission found (per row in Table view, per channel) or per execution of MODEL_TO_DATA
process SEND_EMAIL {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    val view_id
    val submission_id
    val annotate_after_score

    script:
    """
    if [ "$annotate_after_score" == "ready" ]; then
        send_email.py '${view_id}' '${submission_id}' 'pass'
    else
        send_email.py '${view_id}' '${submission_id}' 'fail'
    fi
    """
}
