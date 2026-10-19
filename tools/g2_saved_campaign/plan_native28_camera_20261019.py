"""Write only the small Native28 plan from exact existing camera/build metadata."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
sys.dont_write_bytecode = True
import build_native26_performance_20261019 as b

REPO = Path(__file__).resolve().parents[2]
C = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/realm-camera-native-candidate01')
R26 = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-native26-performance01')
R27 = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-native27-termination01')
ROOT = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-native28-camera01')
OUT = REPO/'docs/ck3-native-ai/evidence/native28-camera-build-plan-2026-10-19.json'


def main():
    machine = subprocess.check_output([sys.executable, '-B', str(REPO/'tools/ck3_live_run_id.py'), 'machine'], text=True).strip()
    assert machine == 'xenoamess-full-tower-eb9d2c1186'
    recipe = b.read(C/'camera_presentation_v1.compile.json')
    deps = b.read(C/'camera_presentation_v1.dependencies.json')
    assert len(recipe['actual_include_pins']) == len(deps['Data']['Includes']) == 395
    source = REPO/'ck3_autonomous_player/native_bridge/src/camera_presentation_v1.cpp'
    header = REPO/'ck3_autonomous_player/native_bridge/include/xar_bridge/camera_presentation_v1.hpp'
    oldheader = C/'sources/include/xar_bridge/camera_presentation_v1.hpp'
    pattern = r'enum class Status : std::uint32_t \{.*?\n\};'
    old = oldheader.read_text(encoding='utf-8-sig')
    new = header.read_text(encoding='utf-8-sig')
    assert re.sub(pattern, '', old, flags=re.S) == re.sub(pattern, '', new, flags=re.S)
    statuses = dict((name, int(value)) for name, value in re.findall(r'(\w+)\s*=\s*(\d+)', re.search(pattern, new, re.S).group()))
    assert set(statuses.values()) == set(range(9)) | set(range(16, 29))
    cpp = source.read_text(encoding='utf-8-sig')
    assert 'IsIconic' not in cpp and 'snapshot.active_wars' not in cpp and 'snapshot.player_armies' not in cpp
    assert all(('Status::'+name) in cpp for name, value in statuses.items() if value >= 16)
    assert 'client.right <= client.left' in cpp and 'client.bottom <= client.top' in cpp
    assert 'search.count == 1 && search.hwnd == hwnd' in cpp
    assert cpp.count('sequence != static_cast<std::uint32_t>(InterlockedCompareExchange(') == 2
    assert b.sha(source) == '656055437114c216f8703197cc010f4443025969d16cece5fd63333bce3c6abf'
    assert b.sha(header) == '976491c0821a651fd6d38ff05427a5a6ed0810ae06776ecede16241348cbfc10'
    closed = b.read(R27/'FILES-CLOSED.json')
    assert b.sha(R27/'FILES-CLOSED.json') == 'ffec55d7a3299dc8f000cb6b8fc2dc23917ef2c84939c475b169dc36ae030861'
    pins = {b.norm(row['path']): row for row in closed['files_excluding_this_manifest']}
    selected = ['QUALIFICATION.json', 'PREPARED.json', 'LINK-RESULT.json', 'build/native27-link.rsp', 'build/native27.dll', 'build/native27.map', 'build/router/attempt01/nonwar12004.obj']
    baseline = {name: pins[b.norm(R27/name)] for name in selected}
    rsp = b.tokens(R27/'build/native27-link.rsp')
    direct = [x for x in rsp if x.lower().endswith('.obj')]
    assert len(direct) == 356 and sum(b.norm(x) == b.norm(C/'camera_presentation_v1.obj') for x in direct) == 1
    assert any(x.upper() == '/INCREMENTAL:NO' for x in rsp)
    assert not any(x.upper().startswith('/DEBUG') for x in rsp)
    project = [p for p in recipe['actual_include_pins'] if 'xar_bridge' in b.norm(p['path']) or 'ck3_autonomous_player' in b.norm(p['path'])]
    named = [b.pin(p['path']) for p in recipe['actual_include_pins'] if Path(p['path']).name in ('camera_presentation_v1.hpp', 'realm_camera_geometry_v1.hpp', 'ck3_12004_title_map.hpp', 'title_map_navigation_v1_camera.hpp')]
    plan = {
        'schema': 'xar.ck3.native28-camera-source-plan/v1', 'machine_id': machine,
        'observed_at_utc': b.now(), 'status': 'SOURCE_FROZEN_AWAITING_CHILD_ADMISSION',
        'proposed_root': str(ROOT), 'baseline_root': str(R27), 'baseline_native26_root': str(R26),
        'source_pins': {'candidate_cpp': b.pin(source), 'candidate_header': b.pin(header),
                        'original_cpp': b.pin(C/'sources/src/camera_presentation_v1.cpp'),
                        'original_header': b.pin(oldheader), 'original_object': b.pin(C/'camera_presentation_v1.obj')},
        'baseline_pins': baseline, 'baseline_closed': b.pin(R27/'FILES-CLOSED.json'),
        'original_compile_recipe': b.pin(C/'camera_presentation_v1.compile.json'),
        'original_dependencies': b.pin(C/'camera_presentation_v1.dependencies.json'),
        'original_header_pins_field': '/actual_include_pins', 'original_includes_count': 395,
        'original_project_header_count': len(project),
        'original_project_header_digest': hashlib.sha256(b.canonical(project)).hexdigest(),
        'named_actual_headers': named,
        'build_scope': {
            'production_TUs': 1, 'new_archive_members': 0, 'retained_other_direct_objects': 355,
            'retained_archive_members': 612, 'old_inputs_copied': 0,
            'archive': {'path': str(R26/'build/native26-runtime.lib'), 'bytes': 179605836,
                        'sha256': '34fc1901f60e9f968b954fd1f4f9b7646bc2f6fd84ad04c8b760344aca56f5c6'},
            'compile': 'Original camera argv verbatim except source/output/dependencies/Fd paths and one first /I new source/include overlay containing only the revised camera_presentation_v1.hpp. Original remaining include order/macros/flags retained; no mutable master includes.',
            'include_check': 'Actual 395 sourceDependencies Includes must equal original order with only the first camera header path replaced by the exact new overlay; every other actual header SHA must match original actual_include_pins. Verify overlay header is unique effective camera header.',
            'link': 'Original Native27 response tokens/order unchanged except exactly one original camera direct object and output/map/implib/PDB path tokens. /INCREMENTAL:NO and absence of /DEBUG retained. No PDB emitted; stop if PDB/ILK/EXE appears.',
            'reuse_basis': 'Header delta is only explicit uint32 Status enumerators. Mode, old0-8, all struct/class tokens, fields, methods, offsets, alignment and symbols unchanged. Existing bridge initializes/pumps the unchanged class and does not use added status values. No M1 faction struct/layout/header adopted; original 395 camera Includes remain pinned.',
            'M1_ABI_adopted': False, 'workers': 1, 'priority': 'BELOW_NORMAL', 'attempts': 1,
            'TEMP_TMP': 'All compile/link/fixture TEMP and TMP under exact new root; old roots read-only.',
            'compiler': {'path': 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe', 'bytes': 893288, 'sha256': '315a654ea116864516a1674858e587e535e3bc3045ff32ed2f2739a2c1ec5640'},
            'tool_pin_source': 'Native27 PREPARED.json tools.compiler/linker_fresh/dumpbin_fresh; fresh exact SHA recheck before launch. Original camera short cl path must resolve to same compiler body.',
            'new_EXE_outputs': 0, 'production_DLL_loaded': False, 'Game_RPC_desktop_actions': 0},
        'status_values': statuses, 'reserved_status_values': list(range(9, 16)),
        'source_behavior': [
            'Allow managed minimized HWND with unique current-process Crusader Kings III title, real positive GetClientRect, no show/restore/activation/move or synthetic viewport.',
            'Remove broad ordinary-war/active-army realm preempt; Python current actual battle/siege/march hotspot policy controls display priority. Mandatory event/interaction preempt remains.',
            'Keep actor/date/main-thread/map/alive guards, all title/county and target guards; check latest request sequence and expiry again immediately before target writes.',
            'Split the same original reads in the same short-circuit order into statuses16-28. No additional Game memory reads, no write guard relaxation, v1 layout stays fixed.'],
        'offline': {
            'kind': 'One bounded no-EXE independent Python ctypes fixture DLL; no production DLL load.',
            'new_fixture_objects': 1,
            'checks': [
                'C++ static_assert sizeof/offsetof Request/Result/Shared and old/new enum values, compared to literal frozen v1 contract; M4 actual Python ctypes parser pairing already passes.',
                'Extract verbatim actual new GameWindowSearch/FindGameWindow/IsUniqueGameWindow bodies; remap only Win32 window APIs to deterministic mocks before compilation. Test unique/duplicate/wrong PID/title/invalid/enumeration failure without desktop calls.',
                'Use exact original pinned realm_camera_geometry_v1.hpp functions to test valid bounds/unions, actual wide/tall viewport and invalid/small viewport/padding/bucket edges; no projection or live pixel claim.',
                'Static source check retains mandatory/actor/date/mainthread guards, no IsIconic/active_wars/active_army gate, new latest sequence check before target writes, statuses16-28 all wired.',
                'Production object in new DLL map owns CameraPresentationRuntimeV1; other355 direct objects/archive identities unchanged; five export names/ordinals equal Native27 and record actual new RVAs.'],
            'scope_limit': 'Offline checks qualify source/binary routing/layout only. Old seq106 actual reason and real camera movement/coverage require runtime fresh SAVE/cold adoption and original pixels; no gameplay credit.'},
        'storage': {'hard_limit_bytes': 384*b.MIB, 'expected_peak_bound_bytes': 320*b.MIB,
            'phase_total_MiB': {'prepare': 16, 'compile': 128, 'link': 320, 'offline_and_close': 320},
            'peak_components_MiB': {'retained_source_obj_DLL_map_fixture_logs': 64, 'bounded_link_temporary_files': 256, 'uncommitted_margin': 64},
            'basis': 'Native27 actual closed AllocationSize45,928,984B from storage. Its linker writes DLL18,442,752B/map25,042,091B; no archive copy or incremental/debug/PDB. Historical transient peak was not recorded and remains unknown. The 320MiB estimate is a new bounded plan, not measured historical peak; memory usage is excluded.',
            'guard': 'Before link require actual child plus256MiB <=384MiB; check exact child cumulative files during each subprocess and every phase. Stop/kill on ceiling or unexpected outputs; retain all failure/temp files in same child, never retry automatically.',
            'new_root_created': False, 'heavy_output_started': False, 'future_writes_after_close': 0,
            'parent_or_old_child_credit_released': False, 'allocated_bytes_now': None},
        'old_failure_limit': {'source': 'Runtime/M4 CAMERA-SHARED-STATUS-ONCE.json seq106, 2026-10-19T09:20:56Z same machine',
            'observed': 'unavailable; bbox point1787,2510; client2560x1440; zoom_index-1; target/current zero. Bounds are assigned after original window gate, so this old request already passed that gate.',
            'reason': 'not_observed; ResolveCamera/blocked/transient/extent/bucket before index remain candidates. Window repair does not prove the old failure is fixed.'},
        'exact4_camera_source_comparison': {'path': 'D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/native_bridge/src/ck3_12004_title_map_camera.cpp',
            'legacy_recipe_pointer': '/compile_jobs/252', 'retained_object': 'native-p0253.obj in original runtime archive',
            'source_spans': 'ResolveHandlerAndCamera173-211; BindTitleMapNavigationCameraEnvironmentV1 652-684',
            'result': 'Same root slot -> root+0x10 -> runtime dynamic cast -> cast+0x88 -> exact.4 handler+0x670 -> camera; both handler and camera vtable checks match. No source-proven root/offset discrepancy; do not introduce speculative resolver changes.',
            'source_pin_scope': 'Existing recipe metadata locates source; this plan does not claim a newly obtained historical source hash for this executor.'},
        'current_live_adoption': 'Native26/C9 runtime separately owned. No deployment, restart, injector or Game changes authorized to this producer.'}
    encoded = json.dumps(plan, ensure_ascii=True, indent=2).encode()+b'\n'
    assert len(encoded) <= 16*1024
    OUT.write_bytes(encoded)
    print(json.dumps({'plan': b.pin(OUT), 'producer': b.pin(__file__), 'source_pins': plan['source_pins'], 'project_headers': len(project), 'status': plan['status']}))


if __name__ == '__main__':
    main()
