// builds or updates the subfolders with log and predictions files
process CREATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(build_or_update)
    val project_name
    val predictions_file_path

    output:
    val "ready"

    script:
    """
<<<<<<< HEAD:modules/create_folders.nf
    create_folders.py '${project_name}' '${submission_id}' '${build_or_update}'
=======
    build_update_subfolders.py '${project_name}' '${submission_id}' '${build_or_update}' '${predictions_file_path}'
>>>>>>> 027b01b (Updating nextflow workflows):modules/build_update_subfolders.nf
    """
}
