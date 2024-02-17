// builds or updates the subfolders with log and predictions files
process CREATE_FOLDERS {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), val(create_or_update)
    val project_name
    val predictions_file_path
    
    workDir "s3://example-dev-project-tower-scratch/work/9b/39daf3462e9c37b75137481d8c5b3d/"

    output:
    val "ready"

    script:
    """
    create_folders.py '${project_name}' '${submission_id}' '${create_or_update}' 'predictions.csv'
    emit 'ready'
    """
}
