from __future__ import annotations

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("example", list(find_examples("README.md", "docs")), ids=str)
def test_docs(example: CodeExample, eval_example: EvalExample) -> None:
    eval_example.set_config(line_length=100, quotes="double")
    if eval_example.update_examples:
        eval_example.format(example)
        eval_example.run_print_update(example)
    else:
        eval_example.lint(example)
        eval_example.run_print_check(example)
