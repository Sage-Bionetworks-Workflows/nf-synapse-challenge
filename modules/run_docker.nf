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
    val project_name
    val cpus
    val memory
    val ready
    val ready

    output:
    tuple val(submission_id), path('output/predictions.{csv,zip}')

    script:
    """
    run_docker.py '${project_name}' '${submission_id}'
    """
}
