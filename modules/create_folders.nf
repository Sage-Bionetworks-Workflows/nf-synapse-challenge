// This Nextflow script contains 2 tasks:
// 1. CREATE_FOLDERS : Takes in (submission_id, create_or_update) and project_name to create
// root and subfolders for the designated Challenge Project on Synapse
// 2. UPDATE_FOLDERS : Takes in (submission_id, create_or_update), project_name, and predictions_file_path
// fed by RUN_DOCKER, to update the subfolders created in CREATE_FOLDERS

process CREATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(create_or_update)
    val project_name

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${create_or_update}'
    """
}

process UPDATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(create_or_update)
    val project_name
    path predictions_file_path, stageAs: "${submission_id}_predictions.csv"

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${create_or_update}' '${predictions_file_path}'
    """
}