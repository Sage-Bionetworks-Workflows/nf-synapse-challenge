// score submission results for model to data challenges
process SCORE_MODEL_TO_DATA {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container params.scoring_container

    input:
    tuple val(submission_id), path(predictions), val(status), path(results)
    path goldstandard
    val status_ready
    val annotate_ready
    val scoring_script

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
        status=\$(${scoring_script} '${predictions}' '${goldstandard}' '${results}')
    fi
    """
}
