// sends an e-mail to the submitter(s)
process SEND_EMAIL {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.1.1"

    input:
    val email_script
    val view_id
    val project_name
    val submission_id
    val notification_type
    val email_with_score
    val ready

    output:
    val "ready"

    script:
    """
    ${email_script} '${view_id}' '${submission_id}' '${email_with_score}' '${notification_type}' '${project_name}'
    """
}
