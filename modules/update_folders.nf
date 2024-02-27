// Takes in (submission_id, create_or_update), project_name, and predictions_file_path
// fed by RUN_DOCKER, to update the subfolders created in CREATE_FOLDERS

process UPDATE_FOLDERS {
    tag "${submission_id}"

    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    val submission_id
    val create_or_update
    val project_name
    path predictions_file_path

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${create_or_update}' '${predictions_file_path}'
    """
}
