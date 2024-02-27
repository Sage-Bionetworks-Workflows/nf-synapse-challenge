// Gets Dockerized Submissions for Model to Data Challenges
process GET_SUBMISSION_IMAGE {
    tag "${submission_id}"

    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    val submission_id

    output:
    tuple val(submission_id), stdout

    script:
    """
    get_submission_image.py '${submission_id}'
    """
}
