// validate submission results
process VALIDATE {
    tag "${submission_id}"
    label "flexible_compute"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), path(predictions)
    val ready
    val validation_script

    output:
    tuple val(submission_id), path(predictions), stdout, path("results.json")

    script:
    """
    ${validation_script} '${submission_id}' '${predictions}'
    """
}
