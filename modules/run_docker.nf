// runs docker containers
process RUN_DOCKER {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    cpus "${cpus}"
    memory "${memory}"
    container "ghcr.io/sage-bionetworks-workflows/nf-synapse-challenge:4.0"
    

    input:
    val submission_id
    path staged_path
    val cpus
    val memory
    val ready
    val ready

    output:
    tuple val(submission_id), path('output/*predictions.{csv,zip}'), path('output/*.log')

    script:
    """
    run_docker.py '${submission_id}'
    """
}
