"""Offline host permits using a frozen synthetic save/readback verifier."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from xar_autoplayer.bridge import ordinary_interaction_contract as c
from xar_autoplayer.bridge.ordinary_interaction_host_release import OrdinaryClaimReleaseHost
from test_ordinary_interaction import MemoryDriver, KEY, RECIPIENT

VERIFIER_SOURCE = '''import hashlib
import json
def verify_consumption(*, claim, manifest, artifacts):
    before = json.loads(artifacts['before_artifact'])
    after = json.loads(artifacts['after_artifact'])
    identity = claim['action_identity']
    for saved in (before, after):
        if saved['actor_id'] != identity['actor_id'] or saved['recipient_id'] != identity['recipient_id'] or saved['interaction_key'] != identity['interaction_key']:
            raise ValueError('synthetic save identity differs')
    if after['round_nonce'] != before['round_nonce'] + 1:
        raise ValueError('synthetic save has no consumed nonce delta')
    return {'schema':'ck3-ordinary-interaction-independent-consumption-v1',
        'claim_request_id':claim['request_id'],'action_identity':identity,
        **{key+'_sha256':hashlib.sha256(artifacts[key]).hexdigest() if artifacts[key] is not None else None
           for key in ('packet','native_result','unknown','before_artifact','after_artifact')},
        'consumption':{'kind':'save_round_delta','field_name':'round_nonce',
            'before_value':before['round_nonce'],'after_value':after['round_nonce'],
            'actor_id':identity['actor_id'],'recipient_id':identity['recipient_id'],'interaction_key':identity['interaction_key']}}
'''

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path': str(path.resolve()), 'sha256': sha(path)}
def write(path, obj): path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8'); return path

class HostReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()

    def fixture(self, *, timeout=False, verifier_source=VERIFIER_SOURCE):
        driver = MemoryDriver(self.root)
        driver.timeout_send = timeout
        if timeout:
            with self.assertRaises(Exception): driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
            claim_path = next(self.root.rglob('*.claim.json'))
        else:
            result = driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
            claim_path = Path(result['action_claim_path'])
        claim = json.loads(claim_path.read_text())
        packet = claim_path.with_suffix('.packet.bin')
        native = claim_path.with_suffix('.native-result.json')
        unknown = claim_path.with_suffix('.unknown.json')
        saved = {'actor_id':7001,'recipient_id':RECIPIENT,'interaction_key':KEY,'round_nonce':3}
        before = write(self.root / 'synthetic-before-save.json', saved)
        after = write(self.root / 'synthetic-after-save.json', {**saved,'round_nonce':4})
        manifest = {'schema':'ck3-ordinary-interaction-consumption-manifest-v1',
            'claim_request_id':claim['request_id'],'action_identity':claim['action_identity'],
            'packet':ref(packet),'native_result':None if timeout else ref(native),
            'unknown':ref(unknown) if timeout else None,'before_artifact':ref(before),'after_artifact':ref(after),
            'independent_report':None}
        artifacts = {key:Path(value['path']).read_bytes() if value is not None else None for key,value in manifest.items()
                     if key in ('packet','native_result','unknown','before_artifact','after_artifact')}
        namespace = {}; exec(VERIFIER_SOURCE, namespace)
        facts = namespace['verify_consumption'](claim=claim,manifest=manifest,artifacts=artifacts)
        report = write(self.root / 'synthetic-independent-report.json', facts)
        manifest['independent_report'] = ref(report)
        manifest_path = write(self.root / 'synthetic-consumption-manifest.json', manifest)
        bundle = self.root / 'frozen-synthetic-verifier'; bundle.mkdir()
        source = bundle / 'verifier.py'; source.write_text(verifier_source, encoding='utf-8')
        index = write(bundle / 'INDEX.json', {'schema':'ck3-ordinary-interaction-consumption-verifier-bundle-v1',
            'verifier_id':'synthetic-save-verifier','entrypoint':'verifier.py:verify_consumption',
            'files':[{'path':'verifier.py','sha256':sha(source)}]})
        registry = write(self.root / 'ROOT-VERIFIERS.json', {'schema':'ck3-ordinary-interaction-root-verifier-registry-v1',
            'verifiers':{'synthetic-save-verifier':{'bundle_index':ref(index),'entrypoint':'verifier.py:verify_consumption'}}})
        host = OrdinaryClaimReleaseHost(registry, sha(registry))
        return driver, claim_path, manifest_path, host, source

    def release(self, host, claim, manifest):
        return host.release(claim, manifest, verifier_id='synthetic-save-verifier', operator_id='synthetic-ROOT', next_intent_id='synthetic-new-join2')

    def test_frozen_readback_permit_new_intent_preserves_old_claim_and_generations(self):
        driver, claim, manifest, host, source = self.fixture()
        oldbytes = claim.read_bytes()
        permit = self.release(host, claim, manifest)
        driver.frame.update(revision=2,native_revision=8,snapshot_id='synthetic-independent-next')
        driver.frame['diagnostics']['connection_generation'] = 3
        result = driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=2)
        newclaim = json.loads(Path(result['action_claim_path']).read_text())
        consumption = json.loads(permit.with_suffix('.consumed.json').read_text())
        self.assertEqual(newclaim['claim_ordinal'],1)
        self.assertEqual(consumption['old_connection_generation'],2)
        self.assertEqual(consumption['new_connection_generation'],3)
        self.assertNotEqual(newclaim['request_id'],json.loads(oldbytes)['request_id'])
        self.assertEqual(claim.read_bytes(),oldbytes)
        self.assertFalse(consumption['business_acceptance_credit'])
        self.assertEqual(result['status'],'pending')

    def test_timeout_native_receipt_null_unknown_is_real_host_evidence(self):
        driver, claim, manifest, host, source = self.fixture(timeout=True)
        value = json.loads(manifest.read_text())
        self.assertIsNone(value['native_result'])
        self.assertIsNotNone(value['unknown'])
        self.assertTrue(self.release(host,claim,manifest).is_file())
        self.assertFalse(claim.with_suffix('.native-result.json').exists())

    def test_missing_timeout_unknown_is_rejected(self):
        driver, claim, manifest, host, source = self.fixture(timeout=True)
        value = json.loads(manifest.read_text()); value['unknown'] = None; write(manifest,value)
        with self.assertRaises(ValueError): self.release(host,claim,manifest)

    def test_supplied_bool_verifier_is_not_consumption_facts(self):
        driver, claim, manifest, host, source = self.fixture(verifier_source='def verify_consumption(**kwargs): return True\n')
        with self.assertRaises(ValueError): self.release(host,claim,manifest)

    def test_wrong_full_id_or_key_manifest_never_releases(self):
        driver, claim, manifest, host, source = self.fixture()
        original = json.loads(manifest.read_text())
        for key,value in (('interaction_key',KEY.upper()),('recipient_id',RECIPIENT ^ 0x01000000)):
            value_manifest = deepcopy(original); value_manifest['action_identity'][key] = value; write(manifest,value_manifest)
            with self.subTest(key=key), self.assertRaises(ValueError): self.release(host,claim,manifest)

    def test_wrong_packet_sha_rejected(self):
        driver, claim, manifest, host, source = self.fixture()
        value = json.loads(manifest.read_text()); value['packet']['sha256'] = '0'*64; write(manifest,value)
        with self.assertRaises(ValueError): self.release(host,claim,manifest)

    def test_untrusted_id_and_changed_frozen_source_rejected(self):
        driver, claim, manifest, host, source = self.fixture()
        with self.assertRaises(ValueError): host.release(claim,manifest,verifier_id='caller-lambda',operator_id='ROOT',next_intent_id='new')
        source.write_text('def verify_consumption(**kwargs): return True\n')
        with self.assertRaises(ValueError): self.release(host,claim,manifest)

    def test_repeat_release_and_repeat_permit_consumption_refuse(self):
        driver, claim, manifest, host, source = self.fixture()
        permit = self.release(host,claim,manifest)
        with self.assertRaises(FileExistsError): self.release(host,claim,manifest)
        binding = c.interaction_binding(driver.frame,1)
        from xar_autoplayer.bridge.ordinary_interaction_host_release import consume_next_intent_permit
        consume_next_intent_permit(claim,json.loads(claim.read_text())['action_identity'],binding,'synthetic-next-request')
        with self.assertRaises(FileExistsError): consume_next_intent_permit(claim,json.loads(claim.read_text())['action_identity'],binding,'synthetic-another-request')

    def test_ack_or_same_nonce_cannot_be_independent_consumption(self):
        driver, claim, manifest, host, source = self.fixture()
        value = json.loads(manifest.read_text())
        after = Path(value['after_artifact']['path']); saved = json.loads(after.read_text()); saved['round_nonce'] = 3
        write(after,saved); value['after_artifact'] = ref(after); write(manifest,value)
        with self.assertRaises(ValueError): self.release(host,claim,manifest)

    def test_crash_after_permit_consumed_never_restores_it(self):
        driver, claim, manifest, host, source = self.fixture()
        permit = self.release(host,claim,manifest)
        binding = c.interaction_binding(driver.frame,1)
        from xar_autoplayer.bridge.ordinary_interaction_host_release import consume_next_intent_permit
        consume_next_intent_permit(claim,json.loads(claim.read_text())['action_identity'],binding,'synthetic-crashed-request')
        with self.assertRaises(ValueError): c.create_once_claim(claim.parent,binding,KEY,RECIPIENT,'synthetic-never-resend',
            host_provenance=driver._ordinary_interaction_host_provenance)
        self.assertTrue(permit.with_suffix('.consumed.json').exists())

    def test_concurrent_new_intents_can_consume_only_one_permit(self):
        driver, claim, manifest, host, source = self.fixture()
        self.release(host,claim,manifest)
        binding=c.interaction_binding(driver.frame,1)
        def attempt(index):
            try:
                return c.create_once_claim(claim.parent,binding,KEY,RECIPIENT,f'synthetic-concurrent-{index}',
                    host_provenance=driver._ordinary_interaction_host_provenance)
            except (ValueError,FileExistsError): return None
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes=list(executor.map(attempt,range(2)))
        self.assertEqual(sum(value is not None for value in outcomes),1)
        self.assertEqual(len(list(claim.parent.glob('*.claim.json'))),2)

    def test_removing_process_provenance_cannot_bypass_an_unknown_claim(self):
        driver, claim, manifest, host, source = self.fixture(timeout=True)
        binding=c.interaction_binding(driver.frame,1)
        with self.assertRaises(ValueError): c.create_once_claim(claim.parent,binding,KEY,RECIPIENT,'synthetic-API-switch',host_provenance=None)

    def test_episode_change_does_not_unlock_same_live_process_pair(self):
        driver, claim, manifest, host, source = self.fixture(timeout=True)
        driver.frame.update(episode_run_id='synthetic-new-episode',revision=2,native_revision=8,snapshot_id='synthetic-new-episode-frame')
        binding=c.interaction_binding(driver.frame,2)
        with self.assertRaises(ValueError): c.create_once_claim(claim.parent,binding,KEY,RECIPIENT,'synthetic-episode-resend',
            host_provenance=driver._ordinary_interaction_host_provenance)
        self.assertEqual(len(list(claim.parent.glob('*.claim.json'))),1)

if __name__ == '__main__': unittest.main()
