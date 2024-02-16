// builds or updates the subfolders with log and predictions files
process CREATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(create_or_update)
    val project_name
    val predictions_file_path

    output:
    val "ready"

    script:
    """
    if (${predictions_file_path} != None) {
        workDir ${predictions_file_path}
    }
    create_folders.py '${project_name}' '${submission_id}' '${create_or_update}' 'predictions.csv'
    """
}
