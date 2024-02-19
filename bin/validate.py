#!/usr/bin/env python3

import glob
import json
import os
import sys
import zipfile

if __name__ == "__main__":
    predictions_path = sys.argv[1]
    invalid_reasons = []
    if predictions_path is None:
        prediction_status = "INVALID"
        invalid_reasons.append("Predictions file not found")
    else:
        if ".zip" in os.path.basename(predictions_path):
            # Unzipping the predictions and extracting the files in
            # the current working directory
            with zipfile.ZipFile(predictions_path, 'r') as zip_ref:
                zip_ref.extractall(os.getcwd())

        # Grabbing the extracted predictions files
        predictions_files = glob.glob(os.path.join(os.getcwd(), "*.csv"))
        for file in predictions_files:
            with open(file, "r") as sub_file:
                message = sub_file.read()
            prediction_status = "VALIDATED"
            if message is None:
                prediction_status = "INVALID"
                invalid_reasons.append("At least one predictions file is empty")
    result = {
        "validation_status": prediction_status,
        "validation_errors": ";".join(invalid_reasons),
    }

    with open("results.json", "w") as o:
        o.write(json.dumps(result))
    print(prediction_status)
