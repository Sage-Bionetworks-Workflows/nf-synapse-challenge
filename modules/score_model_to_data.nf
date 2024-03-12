// score submission results for model to data challenges
process SCORE_MODEL_TO_DATA {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "python:3.12.0rc1"

    input:
    tuple val(submission_id), path(predictions), val(status), path(results)
    val status_ready
    val annotate_ready
    val scoring_script

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    status=\$(${scoring_script} '${predictions}' '${results}' '${status}')
    """
}
