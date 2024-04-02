// Takes in (submission_id, create_or_update) and project_name to create
// root and subfolders for the designated Challenge Project on Synapse

process CREATE_FOLDERS {
    tag "${submission_id}"

    maxForks 1
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.1.1"

    input:
    val submission_id
    val project_name
    val private_folders

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${private_folders}'
    """
}
