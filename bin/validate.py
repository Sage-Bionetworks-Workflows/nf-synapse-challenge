#!/usr/bin/env python3

import json
import sys

if __name__ == "__main__":
    predictions_path = sys.argv[1]
    invalid_reasons = []
    if predictions_path is None:
        prediction_status = "INVALID"
        invalid_reasons.append("Predictions file not found")
    else:
        with open(predictions_path, "r") as sub_file:
            message = sub_file.read()
        prediction_status = "VALIDATED"
        if message is None:
            prediction_status = "INVALID"
            invalid_reasons.append("Predicitons file is empty")
    result = {
        "validation_status": prediction_status,
        "validation_errors": ";".join(invalid_reasons),
    }

    with open("results.json", "w") as o:
        o.write(json.dumps(result))
    print(prediction_status)
