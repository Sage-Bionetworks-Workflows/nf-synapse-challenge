// validate submission results
process VALIDATE {
    tag "${submission_id}"
    label "flexible_compute"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.validation_container

    input:
    tuple val(submission_id), path(predictions)
    path goldstandard from "${goldstandard_path}/*"
    val ready
    val validation_script

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    python status=\$(${validation_script} '${predictions}' '${goldstandard}' 'results.json')
    """
}
