"""Fails if a layer imports outward, or if an inner layer imports any non-stdlib module."""
import ast
import sys
import unittest
from pathlib import Path

ROOT_PKG = "study_room_booking"
ROOT = Path(__file__).resolve().parent.parent / ROOT_PKG

# layer -> layers it may import from
ALLOWED = {
    "entities": {"entities"},
    "use_cases": {"entities", "use_cases"},
    "interface_adapters": {"entities", "use_cases", "interface_adapters"},
    "frameworks_drivers": {"entities", "use_cases", "interface_adapters", "frameworks_drivers"},
}
STDLIB_ONLY = {"entities", "use_cases", "interface_adapters"}


def imported_modules(path: Path):
    package = [ROOT_PKG, *path.relative_to(ROOT).parent.parts]
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)]
                if node.module:
                    yield base + node.module.split(".")
                else:
                    for alias in node.names:
                        yield base + [alias.name]
            else:
                yield node.module.split(".")


class DependencyRuleTest(unittest.TestCase):
    def test_imports_only_point_inwards(self):
        problems = []
        for layer, allowed in ALLOWED.items():
            for path in (ROOT / layer).rglob("*.py"):
                for parts in imported_modules(path):
                    if parts[0] == ROOT_PKG:
                        target = parts[1] if len(parts) > 1 else None
                        if target in ALLOWED and target not in allowed:
                            problems.append(f"{path.name}: {layer} imports {target}")
                    elif layer in STDLIB_ONLY and parts[0] not in sys.stdlib_module_names:
                        problems.append(f"{path.name}: {layer} imports non-stdlib '{parts[0]}'")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
