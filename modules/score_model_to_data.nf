// score submission results for model to data challenges
process SCORE_MODEL_TO_DATA {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.challenge_container

    input:
    tuple val(submission_id), path(predictions), val(status), path(results)
    path goldstandard
    val status_ready
    val annotate_ready
    val execute_scoring

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    status=\$(${execute_scoring} '${predictions}' '${goldstandard}' '${results}')
    """
}
