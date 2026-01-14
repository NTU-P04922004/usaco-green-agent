from typing import Tuple, Optional

def compare_outputs(actual_output: str, expected_output: str) -> Tuple[str, Optional[str]]:
    """
    Compares the actual output of a solution with the expected output.

    It normalizes whitespace and line endings.

    Args:
        actual_output: The stdout captured from the solution.
        expected_output: The content of the corresponding .out file.

    Returns:
        A tuple containing the verdict ("Accepted" or "Wrong Answer") and
        a detailed message for "Wrong Answer", otherwise None.
    """
    # Normalize by stripping leading/trailing whitespace from the whole block
    # and splitting into lines. This handles different line endings (CRLF vs LF).
    actual_lines = actual_output.strip().splitlines()
    expected_lines = expected_output.strip().splitlines()

    # Strip trailing whitespace from each line
    actual_lines = [line.rstrip() for line in actual_lines]
    expected_lines = [line.rstrip() for line in expected_lines]

    if actual_lines == expected_lines:
        return "Accepted", None

    # Provide a detailed diff for debugging
    max_lines = max(len(actual_lines), len(expected_lines))
    for i in range(max_lines):
        actual_line = actual_lines[i] if i < len(actual_lines) else "[EOF]"
        expected_line = expected_lines[i] if i < len(expected_lines) else "[EOF]"
        if actual_line != expected_line:
            diff_message = (f"Mismatch at line {i+1}:\n"
                            f"  Expected: {expected_line}\n"
                            f"  Got     : {actual_line}")
            return "Wrong Answer", diff_message

    return "Wrong Answer", "Unknown difference." # Should not be reached