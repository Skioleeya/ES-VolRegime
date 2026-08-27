import ast
from pathlib import Path


def test_once_mode_guards_the_research_window():
    source = Path("scripts/poll_ibkr_latest.py").read_text()
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "_require_active_session" in functions
    assert "--once requires an active CME research session" in source
