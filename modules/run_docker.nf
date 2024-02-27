// runs docker containers
process RUN_DOCKER {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    cpus "${cpus}"
    memory "${memory}"
    container "ghcr.io/sage-bionetworks-workflows/nf-model2data:latest"
    

    input:
    tuple val(submission_id), val(image_id)
    path staged_path
    val cpus
    val memory
    val ready
    val ready

    output:
    tuple val(submission_id), path('predictions.{csv,zip}')

    script:
    """
    echo \$SYNAPSE_AUTH_TOKEN | docker login docker.synapse.org --username foo --password-stdin
    docker run -v \$PWD/input:/input:ro -v \$PWD:/output:rw $image_id
    """
}
