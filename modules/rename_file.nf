process RENAME_FILE {
    tag "${submission_id}"
    
    secret "SYNAPSE_AUTH_TOKEN"
    container "sagebionetworks/synapsepythonclient:v4.1.1"

    input:
    val submission_id
    path input_file

    output:
    path 'output/*_predictions.{csv,zip}'

    script:
    """
    #!/usr/bin/env python3

    import os

    file_name = os.path.basename(${input_file})
    new_file_name = f"{${submission_id}}_{file_name}"
    os.rename(file_name, os.path.join(os.path.dirname(file_name), new_file_name))
    print("File name changed:", new_file_name)
    """
}