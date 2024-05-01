// recursively downloads synapse folder given Synapse ID and stages to /input_folder_name
process SYNAPSE_STAGE {
    label "flexible_compute"

    container "sagebionetworks/synapsepythonclient:v2.7.0"
    
    secret 'SYNAPSE_AUTH_TOKEN'

    input:
    val input_id
    val input_folder_name

    output:
    path "${input_folder_name.contains('goldstandard') ? "${input_folder_name}/*" : "${input_folder_name}/"}"

    script:
    """
    synapse get -r --downloadLocation \$PWD/${input_folder_name} ${input_id}
    """
}
