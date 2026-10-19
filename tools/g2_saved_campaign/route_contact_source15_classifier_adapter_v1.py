"""Pure Queue adapter for the qualified Source15 same-speed omission only.

The retained outer source is read, never copied or modified. Only its route
callee is replaced in a private namespace. No queue state or Game operation.
"""

SOURCE15_ADAPTER_PINS = {
    "outer": "0bff8fae24c072d5f05285ba62c503dfed408f8095690fb8dffec16fe72ec28b",
    "consumer": "b6453a738d341037d98ff6b7cd96342be3027808535b78965612c8415904c10a",
    "qualifier": "3a3c56e8497be8c0b077a5309c7ffe5d456f3294bbfc379877080045f71a2978",
}


def classify_auto_result_credit_v1(body, *, state=None, pending_focus=None,
                                  initial_frame=None, game_pid=None):
    """Keep the original top-level contract and every unrelated classifier."""
    import ast
    import hashlib
    import json
    from pathlib import Path

    def checked(path, key):
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != SOURCE15_ADAPTER_PINS[key]:
            raise ValueError("Source15 route adapter source differs: " + key)
        return raw

    # co_filename is set by the existing Queue installation AST loader.
    root = Path(classify_auto_result_credit_v1.__code__.co_filename).resolve().parent
    outer_path = root / "root_p37c11_prisoner_epoch_classifier.py"
    raw = checked(outer_path, "outer")
    selected = []
    for node in ast.parse(raw.decode("utf-8-sig"), filename=str(outer_path)).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("classify_"):
            selected.append(node)
        elif (isinstance(node, ast.Assign)
              and all(isinstance(target, ast.Name) and target.id.isupper()
                      for target in node.targets)):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            selected.append(node)
    env = dict(globals())
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(outer_path), "exec"), env)

    original_binding = env["classify_gameplay_start_binding_v1"]

    def route(row, *, initial_frame=None, game_pid=None):
        step = row.get("selected_step") if isinstance(row, dict) else None
        if not isinstance(step, str) or not step.startswith("advance-route-contact-horizon-v1-"):
            return None
        consumer_path = root / "route_contact_exact_day_outcome.py"
        consumer = {}
        exec(compile(checked(consumer_path, "consumer"), str(consumer_path), "exec"), consumer)
        qualifier_path = root / "route_contact_same_speed_source_v1.py"
        # Avoid import-path ambiguity: inject this hash-qualified consumer constant.
        tree = ast.parse(checked(qualifier_path, "qualifier"), filename=str(qualifier_path))
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)
                   and node.module == "route_contact_exact_day_outcome"]
        if (len(imports) != 1 or len(imports[0].names) != 1
                or imports[0].names[0].name != "SOURCE15_SAME_SPEED_PINS"
                or imports[0].names[0].asname is not None):
            raise ValueError("Source15 qualifier consumer import differs")
        tree.body.remove(imports[0])
        qualifier = {"SOURCE15_SAME_SPEED_PINS": consumer["SOURCE15_SAME_SPEED_PINS"]}
        exec(compile(tree, str(qualifier_path), "exec"), qualifier)
        inner = row.get("result") if isinstance(row.get("result"), dict) else {}
        actions = inner.get("actions")
        proof = None
        if isinstance(actions, list) and len(actions) == 3:
            binding = original_binding(row, initial_frame=initial_frame, game_pid=game_pid)
            proof = qualifier["build_source15_same_speed_proof"](
                freeze_path=root / "ROOT-FINAL-SDK-FREEZE-P37C18.json",
                driver_mode_path=root.parent.parent / "p51-fresh1066-v20261019-prepare01" /
                    "c18-route10416-classifier-failure94" / "driver_mode.json",
                start_binding=binding, requested_speed=inner.get("timeline_speed"))
        return consumer["classify_route_contact_horizon_one_day_v1"](
            row, bind_gameplay_frame=original_binding, initial_frame=initial_frame,
            game_pid=game_pid, same_speed_source_proof=proof)

    env["classify_route_contact_horizon_one_day_v1"] = route
    return env["classify_auto_result_credit_v1"](
        body, state=state, pending_focus=pending_focus,
        initial_frame=initial_frame, game_pid=game_pid)
