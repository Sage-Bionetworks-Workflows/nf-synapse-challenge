process UPDATE_FOLDERS {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.1.1"

    input:
    val submission_id
    val project_name
    path predictions_file
    path docker_log_file

    output:
    val "ready"

    script:
    """
    update_folders.py '${project_name}' '${submission_id}' 'predictions' '${predictions_file}'
    update_folders.py '${project_name}' '${submission_id}' 'docker_logs' '${docker_log_file}'
    """
}
