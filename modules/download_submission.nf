// download submission file(s) for Data to Model Challenges
process DOWNLOAD_SUBMISSION {
    debug true
    tag "${submission_id}"
    label "flexible_compute"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/challengeutils:v4.2.0"

    input:
    val submission_id
    val ready

    output:
    tuple val(submission_id), path('*')

    script:
    """
    download_output=\$(challengeutils download-submission ${submission_id})

    if [[ ! ${download_output} == *"org.sagebionetworks.repo.model.FileEntity"* ]];
    then
        echo "download failed"
        echo "${download_output}"
        touch dummy.txt
    """
}
