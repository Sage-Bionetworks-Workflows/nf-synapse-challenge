#!/usr/bin/env python3

import argparse
import json
import os
import typing

import tarfile
import numpy as np
from typing import Tuple, List
import synapseclient


INVALID = "INVALID"
SCORED = "SCORED"


def get_args():
    """Set up command-line interface and get arguments without any flags."""
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_id", type=str, help="The ID of submission")
    parser.add_argument("status", type=str, help="The status of submission")
    parser.add_argument(
        "predictions_path", type=str, help="The path to the predictions folder"
    )
    parser.add_argument(
        "groundtruth_path", type=str, help="The path to the ground truth folder"
    )
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        default="results.json",
        help="The path to output file",
    )

    return parser.parse_args()


# Since it's a data-to-model challenge, users will take care of taring their predictions locally
def tar(directory: str, tar_filename: str) -> None:
    """Tar all files in a directory without including the directory
    Arguments:
        directory: Directory path to files to tar
        tar_filename:  tar file path
    """
    with tarfile.open(tar_filename, "w") as tar_o:
        original_dir = os.getcwd()
        os.chdir(directory)
        for file in os.listdir("."):
            tar_o.add(file, arcname=file)
        os.chdir(original_dir)


def untar(directory: str, tar_filename: str, pattern="*") -> None:
    """Untar a tar file into a directory

    Arguments:
        directory: Path to directory to untar files
        tar_filename:  tar file path
        pattern: pattern to match
    """
    with tarfile.open(tar_filename, "r") as tar_f:
        for member in tar_f.getmembers():
            if member.isfile() and member.name.endswith(pattern):
                member.name = os.path.basename(member.name)
                tar_f.extract(member, path=directory)


def ode_forecast(
    truth: np.ndarray, prediction: np.ndarray, k: int, modes: int
) -> Tuple[float, float]:
    """Produce long-time and short-time error scores using ODE metric.

    Arguments:
        truth: groundtruth data
        prediction: predicted data
        k: number of time steps
        modes: number of modes to use

    Returns:
        Tuple of long-time and short-time error scores
    """
    est = np.linalg.norm(truth[:, 0:k] - prediction[:, 0:k], 2) / np.linalg.norm(
        truth[:, 0:k], 2
    )

    yt = truth[-modes:, :]
    M = np.arange(-20, 21, 1)
    M2 = np.arange(0, 51, 1)
    yhistxt, _ = np.histogram(yt[0, :], bins=M)
    yhistyt, _ = np.histogram(yt[1, :], bins=M)
    yhistzt, _ = np.histogram(yt[2, :], bins=M2)

    yp = prediction[-modes:, :]
    yhistxp, _ = np.histogram(yp[0, :], bins=M)
    yhistyp, _ = np.histogram(yp[1, :], bins=M)
    yhistzp, _ = np.histogram(yp[2, :], bins=M2)

    norm_yhistxt = np.linalg.norm(yhistxt, 2)
    eltx = (
        np.linalg.norm(yhistxt - yhistxp, 2) /
        norm_yhistxt if norm_yhistxt > 0 else 0
    )
    norm_yhistyt = np.linalg.norm(yhistyt, 2)
    elty = (
        np.linalg.norm(yhistyt - yhistyp, 2) /
        norm_yhistyt if norm_yhistyt > 0 else 0
    )
    norm_yhistzt = np.linalg.norm(yhistzt, 2)
    eltz = (
        np.linalg.norm(yhistzt - yhistzp, 2) /
        norm_yhistzt if norm_yhistzt > 0 else 0
    )

    elt = (eltx + elty + eltz) / 3

    e1 = 100 * (1 - est)
    e2 = 100 * (1 - elt)

    return e1, e2


def pde_forecast(
    truth: np.ndarray, prediction: np.ndarray, k: int, modes: int
) -> Tuple[float, float]:
    """Produce long-time and short-time error scores using PDE metric.

    Arguments:
        truth: groundtruth data
        prediction: predicted data
        k: number of time steps
        modes: number of modes to use

    Returns:
        Tuple of long-time and short-time error scores
    """
    [m, n] = truth.shape
    est = np.linalg.norm(truth[:, 0:k] - prediction[:, 0:k], 2) / np.linalg.norm(
        truth[:, 0:k], 2
    )

    m2 = 2 * modes + 1
    pt = np.empty((m2, 0))
    pp = np.empty((m2, 0))

    # LONG TIME:  Compute least-square fit to power spectra
    for j in range(1, k + 1):
        p_truth = np.multiply(
            np.abs(np.fft.fft(truth[:, n - j])
                   ), np.abs(np.fft.fft(truth[:, n - j]))
        )
        p_prediction = np.multiply(
            np.abs(np.fft.fft(prediction[:, n - j])),
            np.abs(np.fft.fft(prediction[:, n - j])),
        )
        pt3 = np.fft.fftshift(p_truth)
        pp3 = np.fft.fftshift(p_prediction)
        ptnew = pt3[int(m / 2) - modes: int(m / 2) + modes + 1]
        ppnew = pp3[
            int(m / 2) - modes: int(m / 2) + modes + 1
        ]  # Fixed the variable name

        pt = np.column_stack((pt, np.log(ptnew)))
        pp = np.column_stack((pp, np.log(ppnew)))

    elt = np.linalg.norm(pt - pp, 2) / np.linalg.norm(pt, 2)

    e1 = 100 * (1 - est)
    e2 = 100 * (1 - elt)

    return e1, e2


def pde_forecast_2d(
    truth: np.ndarray, prediction: np.ndarray, k: int, modes: int, nf: int
) -> Tuple[float, float]:
    """Produce long-time and short-time error scores on 2D dataset using PDE metric.

    Arguments:
        truth: comparison data
        prediction: predicted data
        k: number of time steps
        modes: number of modes to use
        nf: number of frequencies

    Returns:
        Tuple of long-time and short-time error scores
    """
    [_, n] = truth.shape
    est = np.linalg.norm(truth[:, 0:k] - prediction[:, 0:k], 2) / np.linalg.norm(
        truth[:, 0:k], 2
    )

    m2 = 2 * modes + 1
    pt = np.empty((m2, 0))
    pp = np.empty((m2, 0))

    # LONG TIME:  Compute least-square fit to power spectra
    for j in range(1, k + 1):
        truth_fft = np.abs(np.fft.fft2(
            truth[:, n - j].reshape((nf, nf), order="F")))
        prediction_fft = np.abs(
            np.fft.fft2(prediction[:, n - j].reshape((nf, nf), order="F"))
        )
        p_truth = np.multiply(truth_fft, truth_fft)
        p_prediction = np.multiply(prediction_fft, prediction_fft)
        #        P_truth = np.multiply(np.abs(np.fft.fft(truth[:, n-j])), np.abs(np.fft.fft(truth[:, n-j])))
        #        P_prediction = np.multiply(np.abs(np.fft.fft(prediction[:, n-j])), np.abs(np.fft.fft(prediction[:, n-j])))
        pt3 = np.fft.fftshift(p_truth[:, int(nf / 2) + 1])
        pp3 = np.fft.fftshift(p_prediction[:, int(nf / 2) + 1])

        ptnew = pt3[int(nf / 2) - modes: int(nf / 2) + modes + 1]
        # Fixed the variable name
        ppnew = pp3[int(nf / 2) - modes: int(nf / 2) + modes + 1]

        pt = np.column_stack((pt, np.log(ptnew)))
        pp = np.column_stack((pp, np.log(ppnew)))

    elt = np.linalg.norm(pt - pp, 2) / np.linalg.norm(pt, 2)
    e1 = 100 * (1 - est)
    e2 = 100 * (1 - elt)

    return e1, e2


def forecast(truth: np.ndarray, prediction: np.ndarray, system: str) -> List[float]:
    """Forecast scores.

    Arguments:
        truth: groundtruth data
        prediction: predicted data
        system: name of the system

    Returns:
        List of forecast scores
    """

    system_to_forecast = {
        "doublependulum": {
            "function": ode_forecast,
            "params": {"k": 20, "modes": 1000},
        },
        "Lorenz": {"function": ode_forecast, "params": {"k": 20, "modes": 1000}},
        "Rossler": {"function": ode_forecast, "params": {"k": 20, "modes": 1000}},
        "KS": {"function": pde_forecast, "params": {"k": 20, "modes": 100}},
        "Lorenz96": {"function": pde_forecast, "params": {"k": 20, "modes": 30}},
        "Kolmogorov": {
            "function": pde_forecast_2d,
            "params": {"k": 20, "modes": 30, "nf": 128},
        },
    }

    if system in system_to_forecast:
        forecast_func = system_to_forecast[system]["function"]
        forecast_params = system_to_forecast[system]["params"]
        scores = forecast_func(truth, prediction, **forecast_params)
        return list(scores)
    else:
        return []


def reconstruction(truth: np.ndarray, prediction: np.ndarray) -> float:
    """Produce reconstruction fit score.

    Arguments:
        truth: groundtruth data
        prediction: predicted data

    Returns:
        e1: reconstruction fit score
    """
    est = np.linalg.norm(truth - prediction, 2) / np.linalg.norm(truth, 2)

    e1 = 100 * (1 - est)

    return e1


def house_zero_score(truth: np.ndarray, prediction: np.ndarray) -> Tuple[float, float, float]:
    '''Produce errors for the HouseZero model.'''
    error_room_temp = 100 * \
        (1 - np.linalg.norm((prediction[:, 1] -
         truth[:, 1])**2)/np.linalg.norm(truth[:, 1]**2))

    error_slab_temp = 100 * \
        (1 - np.linalg.norm((prediction[:, 2] -
         truth[:, 2])**2)/np.linalg.norm(truth[:, 2]**2))

    error_co2 = 100 * \
        (1 - np.linalg.norm((prediction[:, 0] -
         truth[:, 0])**2)/np.linalg.norm(truth[:, 0]**2))
    return error_room_temp, error_slab_temp, error_co2


def calculate_all_scores(
    groundtruth_path: str, predictions_path: str, evaluation_id: str
) -> dict:
    """Calculate scores across all testing datasets.

    Arguments:
        groundtruth_path: path to the groundtruth folder
        predictions_path: path to the predictions file
        evaluation_id: id of the evaluation queue

    Returns:
        score_result: dictionary containing scores
    """
    score_result = {}
    task_mapping = {
        "9615379": [("X1", "forecast", ["stf_E1", "ltf_E2"], [0, 1])],  # Task1
        "9615532": [  # Task2
            ("X2", "reconstruction", ["recon_E3"], [0]),
            ("X3", "forecast", ["ltf_E4"], [1]),
            ("X4", "reconstruction", ["recon_E5"], [0]),
            ("X5", "forecast", ["ltf_E6"], [1]),
        ],
        "9615534": [("X6", "forecast", ["stf_E7", "ltf_E8"], [0, 1])],  # Task3
        "9615535": [  # Task4
            ("X7", "forecast", ["stf_E9", "ltf_E10"], [0, 1]),
            ("X8", "reconstruction", ["recon_E11"], [0]),
            ("X9", "reconstruction", ["recon_E12"], [0]),
        ],
        "9615601": [  # Task5
            ("X21", "HouseZeroScore", [
             "rt_E21", "st_E21", "co2_E21"], [0, 1, 2]),
            ("X74", "HouseZeroScore", [
             "rt_E74", "st_E74", "co2_E74"], [0, 1, 2]),
        ]
    }

    # get mapping of inputs and outs for specific task
    task_info = task_mapping.get(evaluation_id)

    # get unique systems
    pred_files = os.listdir(predictions_path)
    pred_systems = list(set(f.split("_")[0] for f in pred_files))
    if evaluation_id == "9615601":
        true_systems = ["HouseZero"]
    else:
        true_systems = ["doublependulum", "Lorenz",
                        "Rossler", "Lorenz96", "KS", "Kolmogorov"]
    unique_systems = list(set(true_systems) & set(pred_systems))

    for system in unique_systems:
        for prefix, score_metric, score_keys, score_indices in task_info:
            truth_path = os.path.join(
                groundtruth_path, f"Test_{system}/{prefix}test.npy"
            )
            pred_path = os.path.join(
                predictions_path, f"{system}_{prefix}prediction.npy"
            )

            # score provided required files
            if os.path.exists(pred_path):
                truth = np.load(truth_path)
                pred = np.load(pred_path)

                if score_metric == "forecast":
                    scores = forecast(truth, pred, system)
                elif score_metric == "reconstruction":
                    scores = (reconstruction(truth, pred),)
                else:
                    scores = house_zero_score(truth, pred)

                for key, index in zip(score_keys, score_indices):
                    score_result[f"{system}_{key}"] = scores[index]

    return score_result


def score_submission(
    groundtruth_path: str, predictions_path: str, evaluation_id: str, status: str
) -> typing.Tuple[str, dict]:
    """Determine the score of a submission.

    Arguments:
        groundtruth_path: path to the groundtruth folder
        predictions_path: path to the predictions file
        evaluation_id: id of the evaluation queue
        status: current submission status

    Returns:
        Tuple: score status string and dictionary containing score, status and errors
    """
    if status == INVALID:
        score_status = INVALID
        scores = None
        message = f"Submission was not scored due to {INVALID} status"
    else:
        try:
            # assume predictions are compressed into a tarball file
            # untar the predictions into 'predictions' folder
            untar("predictions", tar_filename=predictions_path, pattern=".npy")
            # score the predictions
            scores = calculate_all_scores(
                groundtruth_path, "predictions", evaluation_id
            )
            score_status = SCORED
            message = ""
        except Exception as e:
            message = f"Error {e} occurred while scoring"
            scores = None
            score_status = INVALID

    result = {
        "score_status": score_status,
        "score_errors": message,
    }

    if scores:
        result.update(scores)

    return score_status, result


def get_eval_id(syn: synapseclient.Synapse, submission_id: str) -> str:
    """Get evaluation id for the submission

    Arguments:
        syn: Synapse connection
        submission_id: the id of submission

    Returns:
        sub_id: the evaluation ID, or None if an error occurs.

    Raises:
        Exception: if an error occurs
    """
    try:
        eval_id = syn.getSubmission(submission_id).get("evaluationId")
        return eval_id
    except Exception as e:
        print(
            f"An error occurred while retrieving the evaluation ID for submission {submission_id}: {e}"
        )


def update_json(results_path: str, result: dict) -> None:
    """Update the results.json file with the current score and status

    Arguments:
        results_path: path to the results.json file
        result: dictionary containing score, status and errors
    """
    file_size = os.path.getsize(results_path)
    with open(results_path, "r") as o:
        data = json.load(o) if file_size else {}
    data.update(result)
    with open(results_path, "w") as o:
        o.write(json.dumps(data))


if __name__ == "__main__":
    args = get_args()
    sub_id = args.submission_id
    status = args.status
    predictions_path = args.predictions_path
    groundtruth_path = args.groundtruth_path
    results_path = args.output

    # login to synapase
    syn = synapseclient.Synapse()
    syn.login(silent=True)

    # get the evaluation ID to identify corresponding scoring parameters
    eval_id = get_eval_id(syn, sub_id)

    # get scores of submission
    score_status, result = score_submission(
        groundtruth_path, predictions_path, eval_id, status
    )

    # update the scores and status for the submsision
    update_json(results_path, result)

    # print the status - captured by the workflow outputs
    print(score_status)
