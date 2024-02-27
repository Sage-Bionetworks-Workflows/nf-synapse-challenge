// download submission file(s) for Data to Model Challenges
process DOWNLOAD_SUBMISSION {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/challengeutils:v4.2.0"

    input:
    val(submission_id)

    output:
    tuple val(submission_id), path('*')

    script:
    """
    challengeutils download-submission ${submission_id}
    """
}
