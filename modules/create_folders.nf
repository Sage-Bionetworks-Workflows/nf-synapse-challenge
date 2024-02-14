// builds or updates the subfolders with log and predictions files
process BUILD_UPDATE_SUBFOLDERS {
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
    build_update_subfolders.py '${project_name}' '${submission_id}' '${build_or_update}'
    """
}
