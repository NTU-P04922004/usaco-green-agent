import argparse
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, NamedTuple, Optional

from evaluator import compare_outputs


def get_problem_path(problem_id: str) -> str:
    return f"problems/{problem_id}"


class ExecutionResult(NamedTuple):
    verdict: str
    stdout: str = ""
    stderr: str = ""
    return_code: Optional[int] = None


class JudgeResult(NamedTuple):
    verdict: str


class Judge:
    def __init__(self, problem_path: str):
        self.problem_path = problem_path
        self.problem_config = self._load_problem()

    def _load_problem(self) -> Optional[Dict[str, Any]]:
        """
        Loads problem configuration and validates test case files.
        Returns:
            A dictionary containing the problem configuration or None if loading fails.
        """
        config_path = os.path.join(self.problem_path, "config.json")
        if not os.path.exists(config_path):
            print(f"Error: config.json not found in '{self.problem_path}'")
            return None

        with open(config_path, "r") as f:
            config = json.load(f)

        print(f"Loaded problem: {config['name']}")

        # Validate that all test case files exist
        for i in range(1, config["num_tests"] + 1):
            in_file = os.path.join(self.problem_path, f"{i}.in")
            out_file = os.path.join(self.problem_path, f"{i}.out")
            if not os.path.exists(in_file):
                print(f"Error: Missing input file for test case {i}: {in_file}")
                return None
            if not os.path.exists(out_file):
                print(f"Error: Missing output file for test case {i}: {out_file}")
                return None

        print(f"Found and validated {config['num_tests']} test cases.")
        return config

    @staticmethod
    def _get_resource_limits_fn(time_limit_s: int, memory_limit_mb: int):
        """
        Returns a function that sets resource limits for a child process.
        This is to be used with the preexec_fn argument of subprocess.Popen.
        This function is only effective on Unix-like systems.
        """

        def limit_resources():
            # Set CPU time limit
            if time_limit_s > 0:
                import resource

                resource.setrlimit(resource.RLIMIT_CPU, (time_limit_s, time_limit_s))

            # Set memory limit (address space)
            if memory_limit_mb > 0:
                import resource

                memory_bytes = memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

        return limit_resources

    def _run_solution(self, solution_path: str, input_data: str) -> ExecutionResult:
        """
        Executes a Python solution file and captures its output.
        """
        time_limit_s = self.problem_config["runtime_limit"]
        memory_limit_mb = self.problem_config["memory_limit"]

        preexec_fn = None
        if os.name == "posix":
            preexec_fn = self._get_resource_limits_fn(time_limit_s, memory_limit_mb)

        try:
            result = subprocess.run(
                [sys.executable, solution_path],
                capture_output=True,
                text=True,
                timeout=time_limit_s,
                preexec_fn=preexec_fn,
                input=input_data,
                check=False,
            )

            if result.returncode != 0 or result.stderr:
                return ExecutionResult(
                    verdict="Runtime Error",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode,
                )
            return ExecutionResult(
                verdict="Executed", stdout=result.stdout, return_code=result.returncode
            )

        except FileNotFoundError:
            return ExecutionResult(
                verdict="Judge Error",
                stderr=f"Solution file '{solution_path}' not found.",
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(verdict="Time Limit Exceeded")
        except Exception as e:
            print("YYYYY")
            print(e)
            return ExecutionResult(
                verdict="Judge Error", stderr=f"An unexpected error occurred: {e}"
            )

    def get_problem_description(self) -> str:
        return self.problem_config.get("description", None)

    def run_all_tests(self, solution: str):
        if not self.problem_config:
            print("\nProblem loading failed.")
            sys.exit(1)

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(solution)
            solution_path = f.name

        print("-" * 30)

        for i in range(1, self.problem_config["num_tests"] + 1):
            print(f"Running Test Case #{i}...", end=" ", flush=True)

            in_file_path = os.path.join(self.problem_path, f"{i}.in")
            out_file_path = os.path.join(self.problem_path, f"{i}.out")

            with open(in_file_path, "r") as f:
                input_data = f.read()

            with open(out_file_path, "r") as f:
                expected_output = f.read()

            exec_result = self._run_solution(solution_path, input_data)

            if exec_result.verdict != "Executed":
                print(f"Verdict: {exec_result.verdict}")
                if exec_result.stdout:
                    print(f"STDOUT:\n{exec_result.stdout}")
                if exec_result.stderr:
                    print(f"STDERR:\n{exec_result.stderr}")
                return JudgeResult(verdict=exec_result.verdict)

            verdict, diff = compare_outputs(exec_result.stdout, expected_output)
            print(f"Verdict: {verdict}")
            if diff:
                print(diff)
                return JudgeResult(verdict="Wrong Answer")

        return JudgeResult(verdict="Accepted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A local judge for USACO-style programming problems."
    )
    parser.add_argument("problem_path", help="Path to the problem directory.")
    parser.add_argument(
        "solution_path", help="The path to the Python solution file to be judged."
    )
    args = parser.parse_args()

    try:
        judge = Judge(args.problem_path)
        solution = open(args.solution_path, "r").read()
        if judge.problem_config:
            result = judge.run_all_tests(solution)
            print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
