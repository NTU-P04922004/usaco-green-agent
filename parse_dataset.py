import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from zipfile import ZipFile

import requests
from tqdm import tqdm


def process_problem(item):
    problem_id, problem_info = item
    if problem_id not in [
        "259_bronze_cow_race",
        "396_bronze_secret_code",
        "987_bronze_word_processor",
        "1179_bronze_herdle",
        "1301_bronze_watching_mooloo",
    ]:
        return None

    outpu_path = "problems"
    key_list = [
        "problem_id",
        "cp_id",
        "problem_level",
        "name",
        "description",
        "test_data_link",
        "num_tests",
        "runtime_limit",
        "memory_limit",
        "description_no_samples",
        "num_samples",
        "samples",
    ]

    try:
        problem_path = os.path.join(outpu_path, problem_id)
        os.makedirs(problem_path, exist_ok=True)

        config = {k: problem_info[k] for k in key_list}
        filename = os.path.join(problem_path, "config.json")
        with open(filename, "w") as f:
            json.dump(config, f, indent=4)

        response = requests.get(config["test_data_link"], timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        with ZipFile(BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(problem_path)

        # Validate that all test case files exist
        for i in range(1, config["num_tests"] + 1):
            in_file = os.path.join(problem_path, f"{i}.in")
            out_file = os.path.join(problem_path, f"{i}.out")
            if not os.path.exists(in_file):
                in_file = os.path.join(problem_path, f"I.{i}")
                if os.path.exists(in_file):
                    new_in_file = os.path.join(problem_path, f"{i}.in")
                    os.rename(in_file, new_in_file)
                else:
                    return f"Error for {problem_id}: Missing input file for test case {i}: {in_file}"
            if not os.path.exists(out_file):
                out_file = os.path.join(problem_path, f"O.{i}")
                if os.path.exists(out_file):
                    new_out_file = os.path.join(problem_path, f"{i}.out")
                    os.rename(out_file, new_out_file)
                else:
                    return f"Error for {problem_id}: Missing output file for test case {i}: {out_file}"
        return f"Successfully processed {problem_id}"
    except requests.exceptions.RequestException as e:
        return f"Failed to download for {problem_id}: {e}"
    except Exception as e:
        return f"An error occurred while processing {problem_id}: {e}"


def parse_dataset():
    input_json_path = "usaco_subset307_dict.json"

    with open(input_json_path, "r") as json_file:
        data = json.load(json_file)

    max_workers = os.cpu_count()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_problem, item) for item in data.items()]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing problems"
        ):
            result = future.result()
            if result and ("Error" in result or "Failed" in result):
                print(result)


parse_dataset()
