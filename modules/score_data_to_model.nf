// score submission results for data to model challenges
process SCORE_DATA_TO_MODEL {
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.0.0"

    input:
    tuple val(submission_id), path(predictions), val(status), path(results)
    path staged_path
    val status_ready
    val annotate_ready
    val scoring_script

    output:
    tuple val(submission_id), path(predictions), stdout, path("results.json")

    script:
    """
    ${scoring_script} '${submission_id}' '${status}' '${predictions}' '${staged_path}' '${results}'
    """
}
