"""Exact old/new build tuples on inert full checkpoint qualification inputs."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode=True
P=Path(__file__).parents[1]
sys.path.insert(0,str(P/'reader'))
sys.path.insert(0,str(P/'reader/dependencies'))
sys.path.insert(0,str(P/'tests'))
import sdk_checkpoint_qualification as strict
import sdk_checkpoint_transition_qualification_v2 as transition
import test_sdk_checkpoint_seam as old
import test_checkpoint_transition_v2 as changing

SHA3='94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'
SHA4='98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'
INDEX4='5f5a1005711ef523bcd228c1b2ff2822a9767e13c1b9a934f9a3a87f37287e3d'

def build(d,version):
    image=SHA3 if version=='1.20.0.3' else SHA4
    for side in ('snapshot_before','snapshot_after'):
        d['checkpoint'][side]['diagnostics']['hello'].update(expected_ck3_version=version,
            expected_ck3_sha256=image,game_adapter_id='ck3-'+version+'-msvc-x64')
    for number,operation,nested in [(2,'assembly-predicates','confucian_assembly_predicates'),
                                    (3,'religious-title','confucian_religious_title')]:
        raw=d['g'+str(number)]['result']['native_result']
        raw.update(game_version=version,executable_sha256=image,
            backend_id='ck3-'+version+'-native-confucian-'+operation+'-v1')
        raw[nested].update(game_version=version,executable_sha256=image)
        if number==3 and version=='1.20.0.4':
            for name in ('title_properties_index_sha256','title_laws_index_sha256','head_getters_index_sha256'):
                raw[nested]['qualification'][name]=INDEX4
    return d

def variants():
    return [(strict,old.fixture,old.run),(transition,changing.fixture,changing.convert)]

class ExactBuildPairTests(unittest.TestCase):
    def test_old_and_new_full_checkpoint_paths_keep_wire_and_unknown_credit(self):
        for seam,factory,run in variants():
            for version in ('1.20.0.3','1.20.0.4'):
                with self.subTest(seam=seam.__name__,version=version):
                    data=build(factory(),version)
                    before=json.dumps(data,sort_keys=True)
                    out=run(data)
                    self.assertEqual(out['G2_status'],'BOUND_COMPLETE_NATIVE_OBSERVATION')
                    self.assertEqual(out['G3_raw_public']['native_result']['game_version'],version)
                    self.assertEqual(out['G3_raw_public']['native_result']['confucian_religious_title']['schema'],
                                     'ck3_12003_confucian_religious_title_v1')
                    self.assertEqual(len(seam.frame_binding(data['checkpoint']['snapshot_after'])),7)
                    self.assertIsNone(out['actual_pass'])
                    self.assertIsNone(out['formal_mandate_credit'])
                    self.assertFalse(out['full_product_acceptance_credit'])
                    self.assertEqual(json.dumps(data,sort_keys=True),before)

    def test_mixed_hello_version_image_adapter_and_unknown_build_rejected(self):
        changes=[{'expected_ck3_version':'1.20.0.3'},
                 {'expected_ck3_sha256':SHA3},
                 {'game_adapter_id':'ck3-1.20.0.3-msvc-x64'},
                 {'expected_ck3_version':'1.20.0.5'},
                 {'expected_ck3_sha256':None}]
        for seam,factory,run in variants():
            for change in changes:
                with self.subTest(seam=seam.__name__,change=change):
                    data=build(factory(),'1.20.0.4')
                    for side in ('snapshot_before','snapshot_after'):
                        data['checkpoint'][side]['diagnostics']['hello'].update(change)
                    with self.assertRaises(ValueError):run(data)

    def test_mixed_envelope_nested_backend_or_checkpoint_build_rejected(self):
        for seam,factory,run in variants():
            def wrong_image(d):d['g2']['result']['native_result']['executable_sha256']=SHA3
            def wrong_backend(d):d['g2']['result']['native_result']['backend_id']='ck3-1.20.0.3-native-confucian-assembly-predicates-v1'
            def wrong_payload(d):
                d['g3']['result']['native_result']['confucian_religious_title'].update(game_version='1.20.0.3',executable_sha256=SHA3)
            def wrong_snapshot(d):
                for side in ('snapshot_before','snapshot_after'):
                    d['checkpoint'][side]['diagnostics']['hello'].update(expected_ck3_version='1.20.0.3',
                        expected_ck3_sha256=SHA3,game_adapter_id='ck3-1.20.0.3-msvc-x64')
            def crossed_before(d):
                d['checkpoint']['snapshot_before']['diagnostics']['hello'].update(expected_ck3_version='1.20.0.3',
                    expected_ck3_sha256=SHA3,game_adapter_id='ck3-1.20.0.3-msvc-x64')
            def wrong_static(d):
                d['g3']['result']['native_result']['confucian_religious_title']['qualification']['title_laws_index_sha256']='9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60'
            for mutate in (wrong_image,wrong_backend,wrong_payload,wrong_snapshot,crossed_before,wrong_static):
                with self.subTest(seam=seam.__name__,mutation=mutate.__name__):
                    data=build(factory(),'1.20.0.4');mutate(data)
                    with self.assertRaises(ValueError):run(data)

    def test_current_codec_body_changed_still_rejected(self):
        from tempfile import TemporaryDirectory
        import sdk_artifact_lineage as lineage
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'mixed_codec.py'
            path.write_bytes((P/'tests/fixtures/inert_sdk_codec.py').read_bytes().replace(
                b"if value.get('schema')!=schema:",b"if False:"))
            import hashlib
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            with self.assertRaisesRegex(ValueError,'_common_payload'):
                lineage.verify_codec_artifact({'path':str(path),'bytes':len(raw),'sha256':digest},digest)

if __name__=='__main__':unittest.main(verbosity=2)
