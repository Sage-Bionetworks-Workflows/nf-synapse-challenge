// sends an e-mail to the submitter(s)
process SEND_EMAIL {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    val email_script
    val view_id
    val submission_id
    val email_with_score
    val ready

    script:
    """
    ${email_script} '${view_id}' '${submission_id}' '${email_with_score}'
    """
}
