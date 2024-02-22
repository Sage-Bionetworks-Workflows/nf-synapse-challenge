// Gets submissions from view
process ANNOTATE_SUBMISSION {
    tag "${submission_id}"

    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/challengeutils:v4.2.1"

    input:
    tuple val(submission_id), path(predictions), val(status), path(results)

    output:
    val "ready"

    script:
    """
    challengeutils annotate-submission -f ${submission_id} ${results}
    """
}
