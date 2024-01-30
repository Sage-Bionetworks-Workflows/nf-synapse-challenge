// sends an e-mail to the submitter 
// questions:
// 1. do we want to send the e-mail to the whole team or just the individual submitter?
// 2. if people want to opt-out, how would they be able to?
// A: they can opt out through the Synapse service since challengutils is calling the py client which is calling the API
// 3. do we want the e-mail sent at the end of the workflow?
// 4. how to send a failure e-mail if submission is not accepted?
// 5. do we want to send an e-mail per submission found (per row in Table view, per channel) or per execution of MODEL_TO_DATA
process SEND_EMAIL {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/challengeutils:v4.2.0"

    input:
    val user_id
    val view_id
    val submission_id

    script:
    """
    challengeutils send-email --userids ${user_id} --subject status of ${submission_id} --message your submission for ${submission_id} passed! submission view ID: ${view_id}
    """
}
