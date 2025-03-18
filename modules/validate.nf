// validate submission results for model-to-data submissions
process VALIDATE {
    tag "${submission_id}"
    label "flexible_compute"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.challenge_container

    input:
    tuple val(submission_id), path(predictions)
    path goldstandard
    val ready
    val execute_validation

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    status=\$(${execute_validation} -p '${predictions}' -g '${goldstandard}' -o 'results.json')
    """
}
