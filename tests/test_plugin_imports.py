"""Guard: names imported across the plugin package must exist.

The Calibre/Qt modules cannot be imported outside Calibre, so a renamed or
removed helper that is still imported elsewhere (e.g. ``main`` importing a
helper from ``chart_dialog``) would not be caught by running the code.
This parses every module with ``ast`` and checks that each
``from calibre_plugins.readingprogress.X import Y`` resolves to a name
defined (or imported) anywhere in module X.
"""

import ast
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parent.parent / "readingprogress"
_PREFIX = "calibre_plugins.readingprogress."


def _bound_names(tree):
    """Every name bound anywhere in ``tree`` (defs, classes, assignments,
    imports). Deep on purpose, so a name defined in a top-level ``if`` or
    ``try`` is not reported as missing."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def test_cross_module_imports_resolve():
    trees = {}
    defined = {}
    for path in sorted(_PLUGIN.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        trees[path.name] = tree
        defined[path.stem] = _bound_names(tree)

    problems = []
    for filename, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = node.module or ""
            if not module.startswith(_PREFIX):
                continue
            target = module[len(_PREFIX):].split(".")[0]
            if target not in defined:
                continue
            for alias in node.names:
                if alias.name != "*" and alias.name not in defined[target]:
                    problems.append(
                        f"{filename}: {module} has no '{alias.name}'")
    assert problems == []
