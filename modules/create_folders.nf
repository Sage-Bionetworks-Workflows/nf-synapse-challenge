// builds or updates the subfolders with log and predictions files
process CREATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(create_or_update)
    val project_name
    path predictions_file_path, stageAs: 'predictions.csv'
    val ready

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${create_or_update}' '${predictions_file_path}'
    """
}
