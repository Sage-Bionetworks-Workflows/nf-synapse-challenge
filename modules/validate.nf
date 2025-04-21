// validate submission results for model-to-data submissions
process VALIDATE {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.challenge_container

    input:
    tuple val(submission_id), path(predictions)
    path groundtruth
    val ready
    val execute_validation
    val task_number

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    status=\$(${execute_validation} -p '${predictions}' -g '${groundtruth}' -o 'results.json' -t '${task_number}')
    """
}
