"""Materialize two new case metadata fragments only after actual demotion Save."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import faith_e02_h1_queue as Q
import faith_e02_h1_new_mother_contract as N
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as H
# Import the exact adapter.path source without extending a regular host package.
sys.path.insert(0, str(Path(__file__).resolve().parent / "ck3_mod_acceptance_cases"))
import faith_e02_h1_new_mother_adapter as A


def make_contract(branch: Q.Arm, mother: N.Mother, qualification: Path, dependencies: list[Q.Pin]) -> Q.Obj:
    Q.qualified_hof_cohort(Q.pin(qualification))
    return {"schema": N.SCHEMA, "case": N.CASES[branch], "product": "faith-engine", "machine_id": N.MACHINE,
        "arm": branch, "new_common_mother": mother.manifest, "preparation_result": mother.preparation,
        "saved_input": mother.saved, "parent_h2_case_contract": mother.parent_h2,
        "once_ledger_root": str(mother.ledger), "prior_setup_disclosure": mother.disclosure,
        "holy_site_id": 32, "profile": {"enabled_mods": [], "product_files": []},
        "native_culture_observed": False, "culture_control": N.CULTURE,
        "native_qualification": Q.pin(qualification), "dependencies": dependencies,
        "max_public_calls": N.MAX_CALLS, "h1_public_call_cap": Q.MAX_CALLS,
        "promotion_limit": 1 if branch == "promote" else 0,
        "hof_confirm_limit": 1 if branch == "promote" else 0,
        "h3_readonly_limit": 2 if branch == "promote" else 0,
        "ghw_launch_confirmation_allowed": False, "war_command_limit": 0}


def make_spec(contract: Q.Obj, contract_path: Path, plan_path: Path, state_dir: Path) -> Q.Obj:
    branch = Q.arm(contract.get("arm"))
    return {"id": N.CASES[branch], "status": "ready", "adapter": {
        "module": "tools.ck3_mod_acceptance_cases.faith_e02_h1_new_mother_adapter",
        "path": str(Path(A.__file__).resolve()), "config": str(contract_path)},
        "initial_plan": str(plan_path), "startup": {"mode": "saved_campaign", "state_dir": str(state_dir),
        "saved_campaign": contract["saved_input"]}, "budgets": {"command_timeout": 300,
        "readiness_timeout": 1800, "timeout": 5400, "hold_seconds": 1800, "poll_interval": 0.5},
        "required_mcp_tools": sorted(N.required(branch)), "opt_in_read_only_mcp_tools": sorted(N.readonly(branch)),
        **{key: False for key in H.CLOSED}, "business_contract_applicable": False,
        "whole_product_acceptance_credit": False}


def make_metadata(template_catalog: Path, mother_manifest: Path, preparation_result: Path, qualification: Path,
                  ordinary_state: Path, promoted_state: Path, output: Path) -> None:
    """No future target allocation/prepared/runtime is read or required here."""
    mother = N.load_mother(Q.pin(mother_manifest), Q.pin(preparation_result))
    template = Q.read(template_catalog)
    Q.require(template.get("schema") == "ck3-mod-acceptance-products-v1", "Original plain product catalog required")
    products = Q.obj(template.get("products"))
    product = Q.obj(products.get("faith-engine"))
    N.reject_parent_hof_claim(mother)
    Q.require(output.is_absolute() and not output.exists() and ordinary_state.is_absolute()
              and promoted_state.is_absolute() and not ordinary_state.exists() and not promoted_state.exists()
              and ordinary_state.resolve() != promoted_state.resolve(), "Unused independent future state paths required")
    import faith_e02_h1_new_mother_join as J
    paths = A.source_paths() | {Path(__file__).resolve(), Path(J.__file__).resolve()}
    dependencies = [Q.pin(path) for path in sorted(paths)]
    # Validate both complete contracts before creating any metadata output.
    contracts = {branch: make_contract(branch, mother, qualification, dependencies) for branch in N.CASES}
    output.mkdir(parents=True, exist_ok=False)
    fragments: list[Q.Pin] = []
    cases: list[Q.Obj] = []
    for branch, state in (("ordinary", ordinary_state), ("promote", promoted_state)):
        selected = Q.arm(branch)
        folder = output / selected
        folder.mkdir()
        config, plan = folder / "case-contract.json", folder / "initial-plan.json"
        Q.write_once(config, contracts[selected])
        Q.write_once(plan, {"steps": [Q.validate_step("h1-new-mother-initial-capabilities", "ck3_get_capabilities", {}, selected, 32)]})
        fragment = folder / "case-fragment.json"
        spec = make_spec(contracts[selected], config, plan, state)
        Q.write_once(fragment, spec)
        cases.append(spec)
        fragments.append(Q.pin(fragment))
    products["faith-engine"] = {**product, "cases": cases}
    Q.write_once(output / "products.json", {**template, "runtime": None, "products": products})
    Q.write_once(output / "pair-source.json", {"schema": "faith-e02-h1-new-mother-pair-source-v1",
        "machine_id": N.MACHINE, "new_common_mother": mother.manifest, "preparation_result": mother.preparation,
        "fragments": fragments, "template_catalog": Q.pin(template_catalog),
        "target_runtime_may_be_unbound": True, "actual_target_allocation_required": False,
        "game_or_profile_started": False, "automatic_retry": False})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-catalog", type=Path, required=True)
    parser.add_argument("--new-common-mother", type=Path, required=True)
    parser.add_argument("--preparation-result", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--ordinary-state-dir", type=Path, required=True)
    parser.add_argument("--promote-state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    values: list[object] = [args.template_catalog, args.new_common_mother, args.preparation_result, args.qualification,
                            args.ordinary_state_dir, args.promote_state_dir, args.output]
    if not all(isinstance(v, Path) for v in values):
        raise ValueError("Parsed file paths required")
    make_metadata(args.template_catalog, args.new_common_mother, args.preparation_result, args.qualification,
                  args.ordinary_state_dir, args.promote_state_dir, args.output)


if __name__ == "__main__":
    main()
