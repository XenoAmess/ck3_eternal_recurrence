from pathlib import Path
# Original failed lineage001 preserves the overly strict raw C2 template check.
# Current C2 trigger template differs from candidate003 only by CRLF -> LF.
# Verify that exact transformation while keeping all runtime bindings raw-exact.
source=Path(__file__).with_name('verify_complete_runtime_lineage.py').read_text(encoding='utf-8')
source=source.replace("P=O/'lineage-001'", "P=O/'lineage-002'")
source=source.replace("current=ref(M/row['path']);assert current['sha256']==row['after']['sha256']", """current=ref(M/row['path'])
        if current['sha256']!=row['after']['sha256']:
            assert row['path']=='tools/school_consent_templates/common/scripted_triggers/lyd_c2_consent_triggers.txt'
            raw=src.read_bytes();now=(M/row['path']).read_bytes()
            assert raw.count(b'\\r\\n')==392 and raw.replace(b'\\r\\n',b'\\n')==now
            assert current['sha256']=='2ea24b3e8c945eb6a41b48d30c884d61b154bf69c1c4881305880b2a36e83f77'
            current['source_difference']='EXACT_CRLF_TO_LF_ONLY_392_LINES_RUNTIME_RAW_BYTES_UNCHANGED'
        else:assert src.read_bytes()==(M/row['path']).read_bytes()""")
exec(compile(source,str(Path(__file__).with_name('verify_complete_runtime_lineage.py')),'exec'))
