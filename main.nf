nextflow.enable.dsl = 2

// Run this for data to model challenges
include { DATA_TO_MODEL } from './workflows/DATA_TO_MODEL.nf'

workflow DATA_TO_MODEL_CHALLENGE {
    DATA_TO_MODEL ()
}

// Run this for model to data challenges
include { MODEL_TO_DATA } from './workflows/MODEL_TO_DATA.nf'

workflow MODEL_TO_DATA_CHALLENGE {
    MODEL_TO_DATA ()
}
