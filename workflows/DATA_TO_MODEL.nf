// Find your tower s3 bucket and upload your input files into it
// The tower space is PHI safe
nextflow.enable.dsl = 2
// Empty string default to avoid warning
params.submissions = ""
// Synapse ID for Submission View
params.view_id = "syn52576179"
// The container that houses the scoring and validation scripts
params.challenge_container = "ghcr.io/jaymedina/jenny-test-evaluation:latest"
// The command used to execute the Challenge scoring script in the base directory of the challenge_container: e.g. `python3 path/to/score.py`
params.execute_scoring = "python3 /usr/local/bin/score.py"
// The command used to execute the Challenge validation script in the base directory of the challenge_container: e.g. `python3 path/to/validate.py`
params.execute_validation = "python3 /usr/local/bin/validate.py"
// Synapse ID for the Groundtruth file
params.groundtruth_id = "syn51390589"
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
    if (params.send_email) {
        SEND_EMAIL_BEFORE(params.email_script, params.view_id, submission_ch, "BEFORE", params.email_with_score, "ready")
    }

    // Phase 2: Prepare the data: Download the submission and stage the groundtruth data on S3
    SYNAPSE_STAGE_GROUNDTRUTH(params.groundtruth_id, "groundtruth_${params.groundtruth_id}")
    DOWNLOAD_SUBMISSION(submission_ch, UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION.output)
    UPDATE_SUBMISSION_STATUS_BEFORE_EVALUATION(submission_ch, "EVALUATION_IN_PROGRESS")

    // Phase 3: Validation of the submission
    VALIDATE(DOWNLOAD_SUBMISSION.output, SYNAPSE_STAGE_GROUNDTRUTH.output, "ready", params.execute_validation)
    UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE(submission_ch, VALIDATE.output.map { it[2] })
    ANNOTATE_SUBMISSION_AFTER_VALIDATE(VALIDATE.output)

    // Phase 4: Scoring of the submission + send email
    SCORE(VALIDATE.output, SYNAPSE_STAGE_GROUNDTRUTH.output, UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE.output, ANNOTATE_SUBMISSION_AFTER_VALIDATE.output, params.execute_scoring)
    UPDATE_SUBMISSION_STATUS_AFTER_SCORE(submission_ch, SCORE.output.map { it[2] })
    ANNOTATE_SUBMISSION_AFTER_SCORE(SCORE.output)
    if (params.send_email) {
        SEND_EMAIL_AFTER(params.email_script, params.view_id, submission_ch, "AFTER", params.email_with_score, ANNOTATE_SUBMISSION_AFTER_SCORE.output)
    }
}
