// validate submission results
process VALIDATE {
    tag "${submission_id}"
    label "flexible_compute"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.validation_container

    input:
    tuple val(submission_id), path(predictions)
    path goldstandard
    val ready
    val validation_script

    output:
    tuple val(submission_id), path(predictions), env(status), path("results.json")

    script:
    """
    GS_FILE=\$(ls -1 ${goldstandard} | head -n 1)

    if [ -f "${input_folder_name}/\$GS_FILE" ]; then
        status=\$(${validation_script} '${predictions}' '${goldstandard}/\$GS_FILE' 'results.json')
    else
        echo "No file to process or the file is not a regular file."
    fi
    """
}
