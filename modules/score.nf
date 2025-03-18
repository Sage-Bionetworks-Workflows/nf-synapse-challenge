// score submission results for model to data challenges
process SCORE {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.challenge_container

    input:
    tuple val(submission_id), path(predictions), val(status), path(results)
    path groundtruth
    val status_ready
    val annotate_ready
    val execute_scoring

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    status=\$(${execute_scoring} -p '${predictions}' -g '${groundtruth}' -o '${results}')
    """
}
