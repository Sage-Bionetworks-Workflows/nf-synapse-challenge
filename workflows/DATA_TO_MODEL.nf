// Find your tower s3 bucket and upload your input files into it
// The tower space is PHI safe
nextflow.enable.dsl = 2
// Empty string default to avoid warning
params.submissions = ""
// The expected file type for the submissions
params.file_type = "csv"
// The challenge task for which the submissions are made
params.task_number = 1
// The command used to execute the Challenge scoring script in the base directory of the challenge_container: e.g. `python3 path/to/score.py`
params.execute_scoring = "python3 /home/user/score.py"
// The command used to execute the Challenge validation script in the base directory of the challenge_container: e.g. `python3 path/to/validate.py`
params.execute_validation = "python3 /home/user/validate.py"
// E-mail template (case-sensitive. "no" to send e-mail without score update, "yes" to send an e-mail with)
params.email_with_score = "yes"
// toggle email notification
params.send_email = true
// set email script
params.email_script = "send_email.py"

// Ensuring correct input parameter values
params.file_type_lower = params.file_type?.toLowerCase()
assert params.email_with_score in ["yes", "no"], "Invalid value for ``email_with_score``. Can either be ''yes'' or ''no''."

// import modules
include { CREATE_SUBMISSION_CHANNEL } from '../subworkflows/create_submission_channel.nf'
include { SYNAPSE_STAGE as SYNAPSE_STAGE_GROUNDTRUTH} from '../modules/synapse_stage.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION } from '../modules/update_submission_status.nf'
include { DOWNLOAD_SUBMISSION } from '../modules/download_submission.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE } from '../modules/update_submission_status.nf'
include { UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_SCORE } from '../modules/update_submission_status.nf'
include { VALIDATE } from '../modules/validate.nf'
include { SCORE } from '../modules/score.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_VALIDATE } from '../modules/annotate_submission.nf'
include { ANNOTATE_SUBMISSION as ANNOTATE_SUBMISSION_AFTER_SCORE } from '../modules/annotate_submission.nf'
include { SEND_EMAIL as SEND_EMAIL_BEFORE } from '../modules/send_email.nf'
include { SEND_EMAIL as SEND_EMAIL_AFTER } from '../modules/send_email.nf'

workflow DATA_TO_MODEL {

    // Phase 0: Each submission is evaluated in its own separate channel
    submission_ch = CREATE_SUBMISSION_CHANNEL()

    // Phase 1: Notify users that evaluation of their submission has begun
    UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION(submission_ch, "EVALUATION_IN_PROGRESS")
    if (params.send_email) {
        SEND_EMAIL_BEFORE(params.email_script, params.view_id, submission_ch, "BEFORE", params.email_with_score, "ready")
    }

    // Phase 2: Prepare the data: Download the submission and stage the groundtruth data on S3
    SYNAPSE_STAGE_GROUNDTRUTH(params.groundtruth_id, "groundtruth_${params.groundtruth_id}")
    download_submission_outputs = DOWNLOAD_SUBMISSION(submission_ch, params.file_type_lower, UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION.output, SEND_EMAIL_BEFORE.output)
    //// Explicit output handling
    download_submission_id = download_submission_outputs.map { submission_id, predictions -> submission_id }
    download_submission_predictions = download_submission_outputs.map { submission_id, predictions -> predictions }

    // Phase 3: Validating the submission
    validate_outputs = VALIDATE(DOWNLOAD_SUBMISSION.output, SYNAPSE_STAGE_GROUNDTRUTH.output, "ready", params.execute_validation, params.task_number)
    //// Explicit output handling
    validate_submission = validate_outputs.map { submission_id, predictions, status, results -> submission_id }
    validate_status = validate_outputs.map { submission_id, predictions, status, results -> status }
    //// Updating the status and annotations
    UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE(validate_submission, validate_status)
    ANNOTATE_SUBMISSION_AFTER_VALIDATE(validate_outputs)

    // Phase 4: Scoring the submission + send email
    score_outputs = SCORE(VALIDATE.output, SYNAPSE_STAGE_GROUNDTRUTH.output, UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE.output, ANNOTATE_SUBMISSION_AFTER_VALIDATE.output, params.execute_scoring, params.task_number)
    //// Explicit output handling
    score_submission = score_outputs.map { submission_id, predictions, status, results -> submission_id }
    score_status = score_outputs.map { submission_id, predictions, status, results -> status }
    //// Updating the status and annotations
    UPDATE_SUBMISSION_STATUS_AFTER_SCORE(score_submission, score_status)
    ANNOTATE_SUBMISSION_AFTER_SCORE(score_outputs)
    //// Send email
    if (params.send_email) {
        SEND_EMAIL_AFTER(params.email_script, params.view_id, params.project_name, submission_ch, "AFTER", params.email_with_score, ANNOTATE_SUBMISSION_AFTER_SCORE.output)
    }
}
