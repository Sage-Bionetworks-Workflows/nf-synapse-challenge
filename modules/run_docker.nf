// runs docker containers
process RUN_DOCKER {
    secret "SYNAPSE_AUTH_TOKEN"
    cpus "${cpus}"
    memory "${memory}"
    container "ghcr.io/sage-bionetworks-workflows/nf-model2data:latest"
    

    input:
    tuple val(submission_id), val(container)
    path staged_path
    val cpus
    val memory
    val notready

    output:
    //tuple val(submission_id), path('predictions.csv')
    tuple val(submission_id)

    script:
    """
    echo \$SYNAPSE_AUTH_TOKEN | docker login docker.synapse.org --username foo --password-stdin
    docker run -v \$PWD/input:/input:ro -v \$PWD:/output:rw $container
    """
}
