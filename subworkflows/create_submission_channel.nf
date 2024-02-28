workflow CREATE_SUBMISSION_CHANNEL {
    if (params.submissions) {
    // replace commas with newlines for split
    log.info("Processing submissions from string: ${params.submissions}")
    submissions = params.submissions.replaceAll(',', '\n')
    submission_ch = Channel
        .of(submissions)
        .splitText() { it.replaceAll('\n', '') }
    } else {
        if (params.manifest) {
            log.info("Processing submissions from manifest: ${params.manifest}")
            params.manifest = file(params.manifest)
            submission_ch = Channel
                .fromPath(params.manifest)
                .splitCsv(header:true) 
                .map { row -> row.submission_id }
        } else {
        exit 1, 'You either need to provide either a list of submissions or a submission manifest'
    } 
    }
    emit:
    submission_ch
}
