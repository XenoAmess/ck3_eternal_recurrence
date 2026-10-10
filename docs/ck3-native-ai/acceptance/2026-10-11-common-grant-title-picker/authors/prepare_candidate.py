"""Create a bounded review patch; never copy/freeze source, start CK3 or apply MAIN."""
from __future__ import annotations
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path

OWNED = (
    'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py',
    'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py',
    'tools/ck3_mod_acceptance.py',
)

SERVICE = '''    def grant_title_picker_v1(self, operation: str, recipient_id: int, *,
            expected_revision: int, requested_title_full_ids: list[int],
            expected_selected_title_full_ids: list[int], title_full_id: int | None = None,
            desired_selected: bool | None = None) -> dict[str, object]:
        """Use the existing guarded driver; no permission escalation or automatic selection."""
        from .grant_title_picker_v1 import PERMISSION, request_fields
        if getattr(self.driver, PERMISSION, False) is not True:
            raise UnsupportedStepError("stock grant tools require explicit shared admission")
        if type(expected_revision) is not int or not 0 < expected_revision < 2**64:
            raise ValueError("requires the current positive public revision")
        request_fields(operation, recipient_id, requested_title_full_ids,
                       expected_selected_title_full_ids, title_full_id, desired_selected)
        method = getattr(self.driver, "grant_title_picker_v1", None)
        if not callable(method):
            raise UnsupportedStepError("selected backend lacks the stock grant Title picker")
        return method(operation, recipient_id, expected_revision=expected_revision,
            requested_title_full_ids=requested_title_full_ids,
            expected_selected_title_full_ids=expected_selected_title_full_ids,
            title_full_id=title_full_id, desired_selected=desired_selected)

'''

ALIASES = '''from .grant_title_picker_v1 import PERMISSION as GRANT_TITLE_PICKER_PERMISSION_V1, title_ids as validate_grant_title_ids_v1

GrantTitleFullIdV1 = Annotated[int, Field(strict=True, ge=0, lt=2**32-1)]
GrantTitleIdsV1 = Annotated[list[GrantTitleFullIdV1],
    Field(strict=True, max_length=64, json_schema_extra={"uniqueItems": True}),
    AfterValidator(validate_grant_title_ids_v1)]
GrantSendTitleIdsV1 = Annotated[list[GrantTitleFullIdV1],
    Field(strict=True, min_length=1, max_length=64, json_schema_extra={"uniqueItems": True}),
    AfterValidator(validate_grant_title_ids_v1)]
GrantDesiredSelectedV1 = Annotated[bool, Field(strict=True)]

'''

REGISTER = '''def register_stock_grant_title_picker_tools(server, service, driver) -> None:
    """Expose existing stock operations only when the shared host admitted them."""
    if getattr(driver, GRANT_TITLE_PICKER_PERMISSION_V1, False) is not True:
        return
    from mcp.types import ToolAnnotations
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                             idempotentHint=True, openWorldHint=False))
    def ck3_query_grant_title_picker_v1(recipient_id: OrdinaryRecipientIdV1,
            title_full_ids: GrantTitleIdsV1, expected_revision: NormalExitRevisionV1) -> dict[str, object]:
        """Read the actual stock grant window; no title is selected or transferred."""
        return service.grant_title_picker_v1("query", recipient_id, expected_revision=expected_revision,
            requested_title_full_ids=title_full_ids, expected_selected_title_full_ids=[])
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_prepare_grant_title_picker_v1(recipient_id: OrdinaryRecipientIdV1,
            title_full_ids: GrantTitleIdsV1, expected_revision: NormalExitRevisionV1) -> dict[str, object]:
        """Open the existing stock grant window; this is not a transfer receipt."""
        return service.grant_title_picker_v1("prepare", recipient_id, expected_revision=expected_revision,
            requested_title_full_ids=title_full_ids, expected_selected_title_full_ids=[])
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_select_grant_title_picker_v1(recipient_id: OrdinaryRecipientIdV1,
            title_full_id: GrantTitleFullIdV1, desired_selected: GrantDesiredSelectedV1,
            expected_selected_title_full_ids: GrantTitleIdsV1,
            expected_revision: NormalExitRevisionV1) -> dict[str, object]:
        """Select one exact full Title ID and read the complete resulting selection."""
        targets = list(expected_selected_title_full_ids)
        if title_full_id not in targets:
            targets.append(title_full_id)
        return service.grant_title_picker_v1("select", recipient_id, expected_revision=expected_revision,
            requested_title_full_ids=targets, expected_selected_title_full_ids=expected_selected_title_full_ids,
            title_full_id=title_full_id, desired_selected=desired_selected)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True,
                                             idempotentHint=False, openWorldHint=False))
    def ck3_send_grant_title_picker_v1(recipient_id: OrdinaryRecipientIdV1,
            expected_selected_title_full_ids: GrantSendTitleIdsV1,
            expected_revision: NormalExitRevisionV1) -> dict[str, object]:
        """Send once through stock; actual holder readback is required for transfer verification."""
        return service.grant_title_picker_v1("send", recipient_id, expected_revision=expected_revision,
            requested_title_full_ids=expected_selected_title_full_ids,
            expected_selected_title_full_ids=expected_selected_title_full_ids)
    for name in ("ck3_query_grant_title_picker_v1", "ck3_prepare_grant_title_picker_v1",
                 "ck3_select_grant_title_picker_v1", "ck3_send_grant_title_picker_v1"):
        _forbid_unknown_tool_arguments_v1(server, name)


'''

HOST_BIND = '''def bind_stock_grant_title_picker_permission(driver, enabled: bool) -> None:
    """The global shared host feature is the only admission source for these tools."""
    from xar_autoplayer.bridge.grant_title_picker_v1 import PERMISSION
    if type(enabled) is not bool:
        raise ValueError("stock grant admission requires an explicit boolean")
    setattr(driver, PERMISSION, enabled)


'''

def replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError('source preimage is not unique: ' + repr(before[:100]))
    return source.replace(before, after, 1)

def candidate_sources(repo: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    before = {name: (repo / name).read_bytes() for name in OWNED}
    texts = {name: raw.decode('utf-8').replace('\r\n', '\n') for name, raw in before.items()}
    name = OWNED[0]
    texts[name] = replace_once(texts[name], '    def query_confucian_assembly_predicates_v1(',
                              SERVICE + '    def query_confucian_assembly_predicates_v1(')
    name = OWNED[1]
    texts[name] = replace_once(texts[name], 'NormalExitSignatureV1 = ', ALIASES + 'NormalExitSignatureV1 = ')
    texts[name] = replace_once(texts[name], 'def _forbid_unknown_tool_arguments_v1(',
                              REGISTER + 'def _forbid_unknown_tool_arguments_v1(')
    texts[name] = replace_once(texts[name], '    register_succession_title_readonly_tools(server, service, driver)\n',
        '    register_succession_title_readonly_tools(server, service, driver)\n'
        '    register_stock_grant_title_picker_tools(server, service, driver)\n')
    name = OWNED[2]
    texts[name] = replace_once(texts[name], '    driver.case_declared_read_only_mcp_tools = ',
        '    bind_stock_grant_title_picker_permission(driver, getattr(args, "private_grant_title_picker", False))\n'
        '    driver.case_declared_read_only_mcp_tools = ')
    texts[name] = replace_once(texts[name], '    if getattr(args, "private_confucian_challenger_readonly", False):\n'
        '        child_args.append("--private-confucian-challenger-readonly")\n',
        '    if getattr(args, "private_confucian_challenger_readonly", False):\n'
        '        child_args.append("--private-confucian-challenger-readonly")\n'
        '    if getattr(args, "private_grant_title_picker", False):\n'
        '        child_args.append("--private-grant-title-picker")\n')
    texts[name] = replace_once(texts[name], 'def parser() -> argparse.ArgumentParser:',
                              HOST_BIND + 'def parser() -> argparse.ArgumentParser:')
    texts[name] = replace_once(texts[name], '    result.add_argument("--frontend-mod-load-observation",',
        '    result.add_argument("--private-grant-title-picker", action="store_true",\n'
        '                        help="Explicit shared admission of existing stock grant Title query/prepare/select/send; default off")\n'
        '    result.add_argument("--frontend-mod-load-observation",')
    name = OWNED[3]
    texts[name] = replace_once(texts[name], '{"succession_title_readonly", "confucian_challenger_readonly",',
        '{"succession_title_readonly", "confucian_challenger_readonly", "stock_grant_title_picker",')
    texts[name] = replace_once(texts[name], '        if features.get("confucian_challenger_readonly"):\n'
        '            argv += ["--private-confucian-challenger-readonly"]\n',
        '        if features.get("confucian_challenger_readonly"):\n'
        '            argv += ["--private-confucian-challenger-readonly"]\n'
        '        if features.get("stock_grant_title_picker"):\n'
        '            argv += ["--private-grant-title-picker"]\n')
    after = {}
    for name, text in texts.items():
        ast.parse(text.lstrip('\ufeff'), filename=name)
        newline = '\r\n' if b'\r\n' in before[name] else '\n'
        after[name] = text.replace('\n', newline).encode('utf-8')
    return before, after

def pin(raw: bytes) -> dict:
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    before, after = candidate_sources(args.repo)
    args.output.mkdir(parents=False, exist_ok=False)
    patch = []
    rows = []
    for name in OWNED:
        patch.extend(difflib.unified_diff(before[name].decode('utf-8').replace('\r\n','\n').splitlines(True),
            after[name].decode('utf-8').replace('\r\n','\n').splitlines(True),
            fromfile='a/'+name, tofile='b/'+name))
        rows.append({'relative_path': name, 'before': pin(before[name]), 'after': pin(after[name]),
                     'bom_preserved': before[name].startswith(b'\xef\xbb\xbf') == after[name].startswith(b'\xef\xbb\xbf'),
                     'newline_preserved': before[name].count(b'\r\n') == 0 or b'\r\n' in after[name]})
    test = Path(__file__).with_name('test_ck3_mod_acceptance_grant_title_picker.py').read_bytes()
    test_name = 'tools/test_ck3_mod_acceptance_grant_title_picker.py'
    ast.parse(test.decode('utf-8-sig'), filename=test_name)
    patch.extend(difflib.unified_diff([], test.decode('utf-8').splitlines(True),
        fromfile='/dev/null', tofile='b/'+test_name))
    rows.append({'relative_path': test_name, 'before': None, 'after': pin(test)})
    diff = ''.join(patch).encode('utf-8')
    (args.output/'PUBLIC-GRANT.incremental.patch').write_bytes(diff)
    manifest = {'schema':'lyd.common-grant-public-source-only.v1', 'status':'SOURCE_ONLY_NOT_RUN',
        'authoring_head':'ddbe2b97058b465b8a4bbe7484d658069ff43c6d',
        'source_copies_created':0, 'MAIN_mutations':0, 'native_changes':0,
        'existing_O13_unchanged':True, 'R54_unchanged':True, 'future_source_head':None,
        'future_title_full_id':None, 'business_credit':None, 'files':rows,
        'patch':{'path':str(args.output/'PUBLIC-GRANT.incremental.patch'), **pin(diff)}}
    (args.output/'INTEGRATION-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':manifest['status'], 'files':len(rows), 'patch':manifest['patch']}))

if __name__ == '__main__':
    main()
