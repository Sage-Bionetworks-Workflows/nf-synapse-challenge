// download submission file(s) for Data to Model Challenges
process DOWNLOAD_SUBMISSION {
    tag "${submission_id}"
    label "flexible_compute"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    val submission_id
    val file_type_lower
    val ready

    output:
    tuple val(submission_id), path("*.${file_type_lower}")

    script:
    """
    download_submission.py -s '${submission_id}' -f '${file_type_lower}'
    """
}
