#!/usr/bin/env python3

import sys

import synapseclient

submission_id = sys.argv[1]

syn = synapseclient.Synapse()
syn.login(silent=True)

submission = syn.getSubmission(submission_id)
entity_type = submission["entity"].concreteType
if entity_type != "org.sagebionetworks.repo.model.FileEntity":
    open("dummy.txt", 'w').close()

print(entity_type)
