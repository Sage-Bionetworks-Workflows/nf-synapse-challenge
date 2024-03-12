#!/usr/bin/env python3

import sys
import os

def rename_file(submission_id, input_path):

    # Extract the directory from the input path
    dirname = os.path.dirname(input_path)

    # Extract the filename from the input path
    filename = os.path.basename(input_path)

    # Rename the file based on submission_id
    new_filename = f"{submission_id}_{filename}"

    # Create the new path for the renamed file
    new_path = os.path.join(dirname, new_filename)

    # Rename the original file
    os.rename(input_path, new_path)

    # Print the path to the renamed file
    print("File renamed successfully.")
    print("Original file: ", input_path)
    print("Renamed file: ", new_path)

if __name__ == "__main__":
    submission_id = sys.argv[1]
    input_path = sys.argv[2]
    rename_file(submission_id, input_path)