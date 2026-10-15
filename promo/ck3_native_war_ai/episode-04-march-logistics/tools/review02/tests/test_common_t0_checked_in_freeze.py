"""The checked-in operational template pins Git LF bytes, not archive CRLF bytes."""
import hashlib,json,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[6]

class CheckedInCommonT0Freeze(unittest.TestCase):
    def test_template_pins_actual_checked_in_source_projection(self):
        template=REPO/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/common_t0_control.manifest.template.json'
        pin=json.loads(template.read_text(encoding='utf-8'))['common_t0_freeze']
        source=(REPO/pin['path']).resolve()
        self.assertTrue(source.is_relative_to(REPO))
        raw=source.read_bytes()
        # .gitattributes uses eol=lf. Do not normalize/hash an archive receipt in
        # place: archive exact bytes and this source projection are distinct pins.
        self.assertNotIn(b'\r',raw)
        self.assertEqual((pin['bytes'],pin['sha256']),(len(raw),hashlib.sha256(raw).hexdigest()))
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),
            (13320,'1d3593d906b8117934a8bb5cae6a1d3c6c280272c87476867f63e5e816362a5c'))
        frozen=json.loads(raw)
        self.assertEqual(frozen['T0']['save']['sha256'],'9ab3b0d05bdc1a0c4ef2d81a9dc27cec3f66e9af2871b5cac11776ddc6ddb784')
        self.assertEqual((frozen['T0']['date_raw'],frozen['T0']['actor'],frozen['T0']['U']),(53145048,31254,18))
        self.assertFalse(frozen['existing_treatment']['common_T0_seed_loaded_as_input'])

if __name__=='__main__':unittest.main()
