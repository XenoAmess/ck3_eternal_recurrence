"""Actual eleven-flag compiled qualifier; no game access."""
from pathlib import Path
import json
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'C:/workspace/ck3_lyd_runtime_20261004/post-r14-clean-build-successor-20261007-001/source-003')
sys.path.insert(0, 'C:/workspace/ck3_lyd_runtime_20261004/post-r14-clean-build-successor-20261007-001/source-003/metadata')
from r14_metadata_common import read_ref, jread
EXPECTED_QUALIFICATION = {'path': 'C:/workspace/ck3_lyd_runtime_20261004/r15-root-metadata-capture-20261007-001/NATIVE-CLEAN-QUALIFICATION.actual.json', 'bytes': 921290, 'sha256': '94d3606519d977b6a52fa4f72caa3e97f8f8769c3227489dbc159bfa3d7a2ea5'}

def validate_actual_r14_build(report, binding, profile):
    actual = jread(read_ref(EXPECTED_QUALIFICATION))
    if report != actual or report.get('source_revision') != binding['source_revision']:
        raise ValueError('Actual new native qualifier differs')
    # Actual qualification is an immutable already-verified build-time fact.
    # A later LastPlayed appmanifest change must not reinterpret that build.
    # Current source/guard/postlaunch binding is checked by the consumer/cold path.
    for stamp in actual['actual_products'].values():
        read_ref(stamp)
    read_ref(actual['new_runtime_library'])
    for name in ('dll', 'injector'):
        product = report['native_artifacts'][name]
        row = profile[name]
        if set(row) != {'path', 'sha256'} or Path(row['path']).resolve() != Path(product['path']).resolve() or row['sha256'] != product['sha256']:
            raise ValueError('Native product differs from managed profile: ' + name)
    return actual
