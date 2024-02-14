// Find your tower s3 bucket and upload your input files into it
// The tower space is PHI safe
nextflow.enable.dsl = 2

// Project Name (case-sensitive)
params.project_name = "DPE-testing"
// Synapse ID for Submission View
params.view_id = "syn53475818"
// Synapse ID for Input Data folder
params.input_id = "syn51390589"
// E-mail template (case-sensitive. "no" to send e-mail without score update, "yes" to send an e-mail with)
params.email_with_score = "yes"
// Default CPUs to dedicate to RUN_DOCKER
params.cpus = "4"
// Default Memory to dedicate to RUN_DOCKER
params.memory = "16.GB"
// Scoring Script
params.scoring_script = "score.py"
// Validation Script
params.validation_script = "validate.py"

// Ensuring correct input parameter values
assert params.email_with_score in ["yes", "no"], "Invalid value for ``email_with_score``. Can either be ''yes'' or ''no''."

// import modules
include { SYNAPSE_STAGE } from '../modules/synapse_stage.nf'
include { GET_SUBMISSIONS } from '../modules/get_submissions.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_BEFORE_RUN } from '../modules/update_submission_status.nf'
include { BUILD_UPDATE_SUBFOLDERS as BUILD_SUBFOLDERS } from '../modules/build_update_subfolders.nf'
include { RUN_DOCKER } from '../modules/run_docker.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_RUN } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_SCORE } from '../modules/update_submission_status.nf'
include { VALIDATE } from '../modules/validate.nf'
include { SCORE } from '../modules/score.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_VALIDATE } from '../modules/annotate_submission.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_SCORE } from '../modules/annotate_submission.nf'
include { SEND_EMAIL } from '../modules/send_email.nf'

workflow MODEL_TO_DATA {
    SYNAPSE_STAGE(params.input_id)
    GET_SUBMISSIONS(params.view_id)
    image_ch = GET_SUBMISSIONS.output 
        .splitCsv(header:true) 
        .map { row -> tuple(row.submission_id, row.image_id) }
    UPDATE_SUBMISSION_STATUS_BEFORE_RUN(image_ch.map { tuple(it[0], "EVALUATION_IN_PROGRESS") })
    BUILD_SUBFOLDERS(image_ch.map { tuple(it[0], "build") }, params.project_name, UPDATE_SUBMISSION_STATUS_BEFORE_RUN.output)
    RUN_DOCKER(image_ch, SYNAPSE_STAGE.output, params.cpus, params.memory, BUILD_SUBFOLDERS.output)
    UPDATE_SUBMISSION_STATUS_AFTER_RUN(RUN_DOCKER.output.map { tuple(it[0], "ACCEPTED") })
    VALIDATE(RUN_DOCKER.output, UPDATE_SUBMISSION_STATUS_AFTER_RUN.output, params.validation_script)
    UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE(VALIDATE.output.map { tuple(it[0], it[2]) })
    ANNOTATE_SUBMISSION_AFTER_VALIDATE(VALIDATE.output)
    SCORE(VALIDATE.output, UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE.output, ANNOTATE_SUBMISSION_AFTER_VALIDATE.output, params.scoring_script)
    UPDATE_SUBMISSION_STATUS_AFTER_SCORE(SCORE.output.map { tuple(it[0], it[2]) })
    ANNOTATE_SUBMISSION_AFTER_SCORE(SCORE.output)
    SEND_EMAIL(params.view_id, image_ch.map { it[0] }, params.email_with_score, ANNOTATE_SUBMISSION_AFTER_SCORE.output)
}
