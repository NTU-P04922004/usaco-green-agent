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
    def __init__(self, problem_data: Dict[str, Any]):
        self.problem_data = problem_data

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
        time_limit_s = self.problem_data["runtime_limit"]
        memory_limit_mb = self.problem_data["memory_limit"]

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

    def run_all_tests(self, solution: str):
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(solution)
            solution_path = f.name

        print("-" * 30)

        for i in range(1, self.problem_data["num_tests"] + 1):
            print(f"Running Test Case #{i}...", end=" ", flush=True)

            input_data = self.problem_data["input"][str(i)]
            expected_output = self.problem_data["output"][str(i)]

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
