// Find your tower s3 bucket and upload your input files into it
// The tower space is PHI safe
nextflow.enable.dsl = 2
// Empty string default to avoid warning
params.submissions = ""
// Synapse ID for Submission View
params.view_id = "syn52576179"
// Scoring Script
params.scoring_script = "data_to_model_score.py"
// Validation Script
params.validation_script = "validate.py"
// Testing Data
params.testing_data = "syn51390589"
// E-mail template (case-sensitive. "no" to send e-mail without score update, "yes" to send an e-mail with)
params.email_with_score = "yes"
// Ensuring correct input parameter values
assert params.email_with_score in ["yes", "no"], "Invalid value for ``email_with_score``. Can either be ''yes'' or ''no''."
// toggle email notification
params.send_email = true
// set email script
params.email_script = "send_email.py"

// import modules
include { CREATE_SUBMISSION_CHANNEL } from '../subworkflows/create_submission_channel.nf'
include { SYNAPSE_STAGE } from '../modules/synapse_stage.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION } from '../modules/update_submission_status.nf'
include { DOWNLOAD_SUBMISSION } from '../modules/download_submission.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_SCORE } from '../modules/update_submission_status.nf'
include { VALIDATE } from '../modules/validate.nf'
include { SCORE_DATA_TO_MODEL as SCORE } from '../modules/score_data_to_model.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_VALIDATE } from '../modules/annotate_submission.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_SCORE } from '../modules/annotate_submission.nf'
include { SEND_EMAIL as SEND_EMAIL_BEFORE } from '../modules/send_email.nf'
include { SEND_EMAIL as SEND_EMAIL_AFTER } from '../modules/send_email.nf'

workflow DATA_TO_MODEL {
    submission_ch = CREATE_SUBMISSION_CHANNEL()
    if (params.send_email) {
        SEND_EMAIL_BEFORE(params.email_script, params.view_id, submission_ch, "BEFORE", params.email_with_score, "ready")
    }
    SYNAPSE_STAGE(params.testing_data, "testing_data")
    UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION(submission_ch, "EVALUATION_IN_PROGRESS")
    DOWNLOAD_SUBMISSION(submission_ch, UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION.output)
    VALIDATE(DOWNLOAD_SUBMISSION.output, "ready", params.validation_script)
    UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE(submission_ch, VALIDATE.output.map { it[2] })
    ANNOTATE_SUBMISSION_AFTER_VALIDATE(VALIDATE.output)
    SCORE(VALIDATE.output, SYNAPSE_STAGE.output, UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE.output, ANNOTATE_SUBMISSION_AFTER_VALIDATE.output, params.scoring_script)
    UPDATE_SUBMISSION_STATUS_AFTER_SCORE(submission_ch, SCORE.output.map { it[2] })
    ANNOTATE_SUBMISSION_AFTER_SCORE(SCORE.output)
    if (params.send_email) {
        SEND_EMAIL_AFTER(params.email_script, params.view_id, submission_ch, "AFTER", params.email_with_score, ANNOTATE_SUBMISSION_AFTER_SCORE.output)
    }
}
