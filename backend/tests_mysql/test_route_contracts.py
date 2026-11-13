"""Pin all original route contracts and ensure the runtime has no Mongo access."""
import ast
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _routes(path):
    module = ast.parse(path.read_text())
    prefix = ""
    for node in module.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "APIRouter":
            prefix = next((ast.literal_eval(k.value) for k in node.value.keywords if k.arg == "prefix"), "")
    routes = []
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name) and d.func.value.id == "router" and d.args:
                    routes.append([d.func.attr.upper(), prefix + ast.literal_eval(d.args[0])])
    return sorted(routes)


def test_original_routes_are_preserved_except_replaced_google_broker():
    expected = json.loads((BACKEND / "tests_mysql/fixtures/legacy_routes.json").read_text())
    for name, routes in expected.items():
        actual = {tuple(route) for route in _routes(BACKEND / name)}
        retired = {('POST', '/auth/google-session')} if name == 'routes_auth.py' else set()
        # The Google authentication replacement explicitly retires the broker.
        # Every other original API contract remains required by this fixture.
        assert ({tuple(route) for route in routes} - retired).issubset(actual), name
        assert not (actual & retired), name
        if name == 'routes_auth.py':
            assert {('GET', '/auth/google/config'), ('POST', '/auth/google')}.issubset(actual)
    assert sum(map(len, expected.values())) == 159


def test_no_mongo_driver_or_document_queries_in_runtime():
    runtime = list(BACKEND.glob("*.py")) + list((BACKEND / "mysql").rglob("*.py")) + list((BACKEND / "integrations").rglob("*.py"))
    for path in runtime:
        module = ast.parse(path.read_text())
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                assert not any(a.name.split(".")[0] in {"motor", "pymongo"} for a in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in {"motor", "pymongo"}, path
                assert not (node.module == "database" and any(a.name == "db" for a in node.names)), path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"find_one", "insert_one", "insert_many", "update_one", "update_many", "delete_one", "delete_many", "count_documents", "aggregate"}, (path, node.func.attr)
