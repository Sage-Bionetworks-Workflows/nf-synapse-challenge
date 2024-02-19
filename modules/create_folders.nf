// Takes in (submission_id, create_or_update) and project_name to create
// root and subfolders for the designated Challenge Project on Synapse

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
