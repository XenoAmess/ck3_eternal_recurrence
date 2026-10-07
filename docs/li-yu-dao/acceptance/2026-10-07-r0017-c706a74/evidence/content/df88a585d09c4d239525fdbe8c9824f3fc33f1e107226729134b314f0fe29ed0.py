"""Actual eleven-flag compiled qualifier; no game access."""
from pathlib import Path
import json
import sys
sys.dont_write_bytecode = True
from r14_metadata_common import read_ref, jread
EXPECTED_QUALIFICATION = {'path': 'C:/workspace/ck3_lyd_runtime_20261004/r17-actual-sdk-metadata-20261007-001/NATIVE-CLEAN-QUALIFICATION.actual.json', 'bytes': 980692, 'sha256': '71e6eab48fffbccfffda2d6a79f5a661508c38c67944425eff7a3f6ba3a69bd3'}

def validate_actual_r14_build(report, binding, profile):
    actual = jread(read_ref(EXPECTED_QUALIFICATION))
    if report != actual or report.get('source_revision') != binding['source_revision'] or report.get('schema')!='lyd.next-cold.clean-export-native-byte-qualification.grant-numeric.v1' or report.get('grant_title_picker_opt_in') is not True or len(report.get('actual_private_flags_ON',[]))!=12 or len(report.get('actual_products',{}))!=7 or len(report.get('actual_focused_tests',[]))!=5:
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
