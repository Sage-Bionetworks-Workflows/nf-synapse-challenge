// Find your tower s3 bucket and upload your input files into it
// The tower space is PHI safe
nextflow.enable.dsl = 2

// Synapse ID for Submission View
params.view_id = "syn52658661"
// Scoring Script
params.scoring_script = "score.py"
// Validation Script
params.validation_script = "validate.py"
// Testing Data
params.testing_data = "syn53627077"

// import modules
include { SYNAPSE_STAGE } from '../modules/synapse_stage.nf'
include { GET_SUBMISSIONS } from '../modules/get_submissions.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_BEFORE_RUN } from '../modules/update_submission_status.nf'
include { DOWNLOAD_SUBMISSION } from '../modules/download_submission.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_SCORE } from '../modules/update_submission_status.nf'
include { VALIDATE } from '../modules/validate.nf'
include { SCORE_DATA_TO_MODEL as SCORE } from '../modules/score_data_to_model.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_VALIDATE } from '../modules/annotate_submission.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_SCORE } from '../modules/annotate_submission.nf'

workflow DATA_TO_MODEL {
    SYNAPSE_STAGE(params.testing_data, "testing_data")
    GET_SUBMISSIONS(params.view_id)
    image_ch = GET_SUBMISSIONS.output 
        .splitCsv(header:true) 
        .map { row -> tuple(row.submission_id, row.image_id) }
    UPDATE_SUBMISSION_STATUS_BEFORE_RUN(image_ch.map { tuple(it[0], "EVALUATION_IN_PROGRESS") })
    DOWNLOAD_SUBMISSION(image_ch.map {it[0]})
    VALIDATE(DOWNLOAD_SUBMISSION.output, "ready", params.validation_script)
    UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE(VALIDATE.output.map { tuple(it[0], it[2]) })
    ANNOTATE_SUBMISSION_AFTER_VALIDATE(VALIDATE.output)
    SCORE(VALIDATE.output, SYNAPSE_STAGE.output, UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE.output, "ready", params.scoring_script)
    UPDATE_SUBMISSION_STATUS_AFTER_SCORE(SCORE.output.map { tuple(it[0], it[2]) })
    ANNOTATE_SUBMISSION_AFTER_SCORE(SCORE.output)
}
