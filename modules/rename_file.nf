// Renames a given input file by prefixing it with the given submission_id
process RENAME_FILE {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.1.1"

    input:
    val submission_id
    path input_file

    output:
    path("${submission_id}_*") renamed_file

    script:
    """
    rename_file.py '${submission_id}' '${input_file}'
    """
}
