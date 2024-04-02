// Find your tower s3 bucket and upload your input files into it
// The tower space is PHI safe
nextflow.enable.dsl = 2
// Empty string default to avoid warning
params.submissions = ""
// Project Name (case-sensitive)
params.project_name = "DPE-testing"
// Synapse ID for Submission View
params.view_id = "syn53770151"
// Synapse ID for Input Data folder
params.input_id = "syn51390589"
// E-mail template (case-sensitive. "no" to send e-mail without score update, "yes" to send an e-mail with)
params.email_with_score = "yes"
// Ensuring correct input parameter values
assert params.email_with_score in ["yes", "no"], "Invalid value for ``email_with_score``. Can either be ''yes'' or ''no''."
// Default CPUs to dedicate to RUN_DOCKER
params.cpus = "4"
// Default Memory to dedicate to RUN_DOCKER
params.memory = "16.GB"
// Scoring Script
params.scoring_script = "model_to_data_score.py"
// Validation Script
params.validation_script = "validate.py"
// Toggle email notification
params.send_email = true
// Set email script
params.email_script = "send_email.py"
// The folder(s) below will be private (available only to admins)
params.private_folders = "predictions"

// import modules
include { CREATE_SUBMISSION_CHANNEL } from '../subworkflows/create_submission_channel.nf'
include { SYNAPSE_STAGE } from '../modules/synapse_stage.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_BEFORE_RUN } from '../modules/update_submission_status.nf'
include { CREATE_FOLDERS } from '../modules/create_folders.nf'
include { UPDATE_FOLDERS } from '../modules/update_folders.nf'
include { RUN_DOCKER } from '../modules/run_docker.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_RUN } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_SCORE } from '../modules/update_submission_status.nf'
include { VALIDATE } from '../modules/validate.nf'
include { SCORE_MODEL_TO_DATA as SCORE } from '../modules/score_model_to_data.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_VALIDATE } from '../modules/annotate_submission.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_SCORE } from '../modules/annotate_submission.nf'
include { SEND_EMAIL } from '../modules/send_email.nf'

workflow MODEL_TO_DATA {
    submission_ch = CREATE_SUBMISSION_CHANNEL()
    SYNAPSE_STAGE(params.input_id, "input")
    CREATE_FOLDERS(submission_ch, params.project_name, params.private_folders)
    UPDATE_SUBMISSION_STATUS_BEFORE_RUN(submission_ch, "EVALUATION_IN_PROGRESS")
    RUN_DOCKER(submission_ch, SYNAPSE_STAGE.output, params.cpus, params.memory, CREATE_FOLDERS.output, UPDATE_SUBMISSION_STATUS_BEFORE_RUN.output)
    UPDATE_FOLDERS(submission_ch, params.project_name, RUN_DOCKER.output.map { it[1] }, RUN_DOCKER.output.map { it[2] })
    UPDATE_SUBMISSION_STATUS_AFTER_RUN(RUN_DOCKER.output.map { it[0] }, "ACCEPTED")
    VALIDATE(RUN_DOCKER.output, UPDATE_SUBMISSION_STATUS_AFTER_RUN.output, params.validation_script)
    UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE(submission_ch, VALIDATE.output.map { it[2] })
    ANNOTATE_SUBMISSION_AFTER_VALIDATE(VALIDATE.output)
    SCORE(VALIDATE.output, UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE.output, ANNOTATE_SUBMISSION_AFTER_VALIDATE.output, params.scoring_script)
    UPDATE_SUBMISSION_STATUS_AFTER_SCORE(submission_ch, SCORE.output.map { it[2] })
    ANNOTATE_SUBMISSION_AFTER_SCORE(SCORE.output)
    if (params.send_email) {
        SEND_EMAIL(params.email_script, params.view_id, submission_ch, "AFTER", params.email_with_score, ANNOTATE_SUBMISSION_AFTER_SCORE.output)
    }
}
