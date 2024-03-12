process RENAME_FILE {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.1.1"

    input:
    val submission_id
    path input_file

    output:
    path "${input_file.path}${input_file.baseName}_renamed${input_file.extension}"

    script:
    """
    mv ${input_file} ${input_file.path}${input_file.baseName}_renamed${input_file.extension}
    """
}