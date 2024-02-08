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
    val ready
    val build_or_update
    val project_name

    output:
    tuple val(submission_id), path('predictions.csv')

    script:
    """
    echo \$SYNAPSE_AUTH_TOKEN | docker login docker.synapse.org --username foo --password-stdin
    docker run -v \$PWD/input:/input:ro -v \$PWD:/output:rw $container

    build_update_subfolders.py '${project_name}' '${submission_id}' '${build_or_update}' \$PWD:/output/predictions.csv
    """
}
