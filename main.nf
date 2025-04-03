nextflow.enable.dsl = 2

valid_entry_points = ['data_to_model', 'model_to_data']
if (!params.entry) {
    error "Entry point must be specified using --entry. Select one of: ${valid_entry_points.join(', ')}"
}
if (!valid_entry_points.contains(params.entry)) {
    error "Invalid entry point: '${params.entry}'. Valid options are: ${valid_entry_points.join(', ')}"
}

// Run this for data to model challenges
include { DATA_TO_MODEL } from './workflows/DATA_TO_MODEL.nf'

// Run this for model to data challenges
include { MODEL_TO_DATA } from './workflows/MODEL_TO_DATA.nf'

workflow {
    if (params.entry == 'data_to_model') {
        DATA_TO_MODEL ()
    } else if (params.entry == 'model_to_data') {
        MODEL_TO_DATA ()
    } else {
        error "Invalid entry point: '${params.entry}'. Valid options are: ${valid_entry_points.join(', ')}"
    }
}
