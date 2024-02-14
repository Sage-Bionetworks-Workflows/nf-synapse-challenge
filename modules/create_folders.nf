// builds or updates the subfolders with log and predictions files
process CREATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(build_or_update)
    val project_name
    val ready

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${build_or_update}'
    """
}
