// runs docker containers
process RUN_DOCKER {
    tag "${submission_id}"

    secret "SYNAPSE_AUTH_TOKEN"
    cpus "${cpus}"
    memory "${memory}"
    container "ghcr.io/sage-bionetworks-workflows/nf-synapse-challenge:4.0"
    

    input:
    val submission_id
    val container_timeout
    val poll_interval
    path staged_path
    val cpus
    val memory
    val log_max_size
    val ready
    val ready

    output:
    tuple val(submission_id), path('output/*_predictions.{csv,zip}'), path('output/*.log')

    script:
    """
    run_docker.py '${submission_id}' '${container_timeout}' '${poll_interval}' '${log_max_size}'
    """
}
