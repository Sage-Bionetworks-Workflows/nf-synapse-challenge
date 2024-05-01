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
    # Find the first file in the directory, assuming it's there is only 1 (the gold standard file)
    FILE=$(find ${goldstandard} -type f | head -n 1)
    
    # Count the number of files in the directory to ensure only 1
    FILE_COUNT=$(find ${goldstandard} -type f | wc -l)

    # Validate only if there is exactly 1 file
    if [[ "$FILE_COUNT" == "1" ]]; then
        echo "Processing gold standard file: $FILE"
        status=\$(${validation_script} '${predictions}' '${goldstandard}' 'results.json')
    fi
    """
}
