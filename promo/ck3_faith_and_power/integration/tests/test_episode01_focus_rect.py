"""New focus boundaries only; no real media, font, encoder or provider."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from faith_power_promo import full_episode as common


class Episode01FocusTests(unittest.TestCase):
    def part(self):
        return {'kind':'diagram','image':{'path':'fixture.png','bytes':1,'sha256':'0'*64},
            'focus_rect':[10,20,50,30],'duration_seconds':3,'disclosure':'RULE DIAGRAM · NOT GAMEPLAY'}

    def header(self,size=(100,80),format='PNG'):
        result=MagicMock();result.__enter__.return_value=SimpleNamespace(size=size,format=format)
        return result

    def test_focus_rejects_raw_motion_and_noninteger_nonfinite_empty_rectangles(self):
        for kind in ['raw','mechanism-motion']:
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):common.focus_geometry({**self.part(),'kind':kind},Mock())
        cases=[None,[],[0,0,0,2],[0,0,2,0],[-1,0,2,2],[0,-1,2,2],
               [0,0,True,2],[False,0,2,2],[0,0,1.0,2],[0,0,float('nan'),2],
               [0,0,float('inf'),2],[0,0,2,2,2]]
        for rect in cases:
            with self.subTest(rect=rect):
                bound=Mock()
                with self.assertRaises(ValueError):common.focus_geometry({**self.part(),'focus_rect':rect},bound)
                bound.assert_not_called()

    def test_normal_geometry_uses_actual_png_header_and_rejects_outside_or_non_png(self):
        bound=Mock(return_value=Path('header-only.png'))
        with patch.object(common.Image,'open',return_value=self.header()) as opened:
            result=common.focus_geometry(self.part(),bound)
            opened.assert_called_once_with(Path('header-only.png'))
            self.assertEqual(result['source_geometry'],[100,80])
            self.assertTrue(result['source_geometry_checked'])
        for rect in [[99,0,2,1],[0,79,1,2],[0,0,101,80]]:
            with self.subTest(rect=rect),patch.object(common.Image,'open',return_value=self.header()):
                with self.assertRaisesRegex(ValueError,'outside'):
                    common.focus_geometry({**self.part(),'focus_rect':rect},bound)
        with patch.object(common.Image,'open',return_value=self.header(format='JPEG')):
            with self.assertRaisesRegex(ValueError,'PNG'):common.focus_geometry(self.part(),bound)

    def test_metadata_only_binds_without_opening_image_and_defers_geometry(self):
        bound=Mock(return_value=Path('stat-only.png'))
        with patch.object(common.Image,'open',side_effect=AssertionError('Metadata opened media')):
            result=common.focus_geometry(self.part(),bound,metadata_only=True)
        bound.assert_called_once_with(self.part()['image'])
        self.assertIsNone(result['source_geometry'])
        self.assertFalse(result['source_geometry_checked'])
        self.assertIn('deferred',result['verification'])

    def test_prepare_filter_crops_then_scales_and_pads_without_stretching(self):
        row={'id':'unit-focus','duration_seconds':3,'visual_parts':[self.part()]}
        with patch.object(common.Image,'open',return_value=self.header()):
            argv=common.visual_command('ffmpeg-not-executed',row,Path('not-created.mp4'),lambda r:Path(r['path']))
        graph=argv[argv.index('-filter_complex')+1]
        self.assertIn('crop=50:30:10:20,scale=2560:1120:force_original_aspect_ratio=decrease',graph)
        self.assertIn('pad=2560:1440:(ow-iw)/2:0',graph)
        self.assertEqual(argv[argv.index('-t')+1],'3.000000000')
        self.assertEqual(row['duration_seconds'],3)

    def test_cropped_graphic_keeps_provenance_but_uses_one_ass_class_label(self):
        part=self.part();label=part['disclosure']
        part['burned_in_disclosure']={'source_class':'diagram','text':label,
                                      'render_receipt':{'path':'receipt.json','bytes':0,'sha256':'1'*64}}
        receipt={'schema':'ck3-faith-power-result-source-diagram-v1','image':part['image'],'permanent_disclosure':label,
                 'rows':[{'provenance':'unchanged synthetic marker'}]}
        before=deepcopy(receipt)
        with patch.object(common,'read',return_value=receipt):
            self.assertFalse(common.validate_burned_in_disclosure(part,lambda ref:Path(ref['path'])))
        self.assertEqual(receipt,before)
        row={'id':'unit','zh':'规则。','en':'Rule.','duration_seconds':3,'speech_duration_seconds':2,'visual_parts':[part]}
        face=SimpleNamespace(getlength=lambda text:len(text)*10)
        with patch.object(common.ImageFont,'truetype',return_value=face):
            ass=common.subtitle(row,Path('unused.ttf'),'Unit Font')
        self.assertEqual(ass.count(label),1)
        self.assertIn('unit.source0',ass)

    def test_focus_viewport_stays_above_subtitles(self):
        with patch.object(common.Image,'open',return_value=self.header(size=(2560,1440))):
            graph=common.focus_filter({**self.part(),'focus_rect':[0,607,670,328]},lambda _:Path('unused.png'))
        self.assertIn('scale=2560:1120:',graph)
        self.assertIn('pad=2560:1440:(ow-iw)/2:0:',graph)
        self.assertLessEqual(328*min(2560/670,1120/328),1120)


if __name__=='__main__':unittest.main()
