"""Synthetic images/fake input only; never imports or touches a real desktop."""
from pathlib import Path
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

from PIL import Image
import numpy as np

REPO = Path(os.environ.get('CK3_TEMPLATE_TEST_REPO', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(REPO/'tools'))
import ck3_mod_acceptance_gui_template as matcher
import desktop_coordinate_map as coords
spec = importlib.util.spec_from_file_location('template_candidate', Path(__file__).with_name('ck3_mod_acceptance_template_click.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class FakeDesktop:
    def __init__(self, before, after):
        self.image, self.after, self.clicks = before, after, []
    def size(self): return self.image.size
    def screenshot(self, path=None):
        image=self.image.copy()
        if path is not None: image.save(path)
        return image
    def click(self, x, y, button='left'):
        self.clicks.append([x,y,button])
        self.image=self.after


class TemplateClickTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.pixels=np.random.default_rng(174).integers(0,256,(320,480,3),dtype=np.uint8)
        self.before=Image.fromarray(self.pixels)
        self.source=self.root/'reviewed.png';self.before.save(self.source)
        self.after_pixels=self.pixels.copy()
        self.after_pixels[170:210,300:380]=np.random.default_rng(9).integers(0,256,(40,80,3),dtype=np.uint8)
        self.after=Image.fromarray(self.after_pixels)
        self.payload={'target':{'crop_ltrb':[300,170,380,210],'point_offset':[40,20]},
                      'layout':[{'crop_ltrb':[60,40,160,85]}]}
        self.state={'foreground_pid':777,'foreground_hwnd':123,'focus_hwnd':123}
        self.desktop=FakeDesktop(self.before,self.after)
    def run_action(self, guard=None):
        with mock.patch.object(coords,'foreground_state',return_value=self.state),mock.patch.object(helper.time,'sleep'),mock.patch.object(coords,'mouse_button_state',return_value={'left':False,'right':False}):
            return helper.execute(source=helper.pin(self.source),payload=self.payload,output=self.root/'action',
                desktop=self.desktop,guard=guard or (lambda:dict(self.state)),coords=coords,matcher=matcher,
                expected_hwnd=123,reviewer='/root/synthetic',run_id='synthetic-run',
                pid=777,create_time=1000,original_deadline=time.time()+1000)
    def result(self): return json.loads((self.root/'action/result.json').read_bytes())
    def test_old_reviewed_template_fresh_capture_and_canonical_transition(self):
        os.utime(self.source,(time.time()-10000,time.time()-10000))
        result=self.run_action()
        self.assertEqual(self.desktop.clicks,[[340,190,'left']])
        self.assertTrue(result['post_image_captured'])
        self.assertFalse(result['post_template_observations'][0]['matched_uniquely'])
        self.assertFalse(result['human_review_claimed'])
        self.assertFalse(result['business_pass'])
        receipt=json.loads((self.root/'action/mapped-click-after.png.json').read_bytes())
        self.assertLess(receipt['source_age_before']['age_seconds'],60)
        self.assertEqual(receipt['source_age_before']['maximum_seconds'],60)
    def test_target_and_anchor_can_move_together_without_old_coordinates(self):
        shifted=np.random.default_rng(99).integers(0,256,(320,480,3),dtype=np.uint8)
        shifted[50:95,75:175]=self.pixels[40:85,60:160]
        shifted[180:220,315:395]=self.pixels[170:210,300:380]
        after=shifted.copy();after[180:220,315:395]=self.after_pixels[170:210,300:380]
        self.desktop=FakeDesktop(Image.fromarray(shifted),Image.fromarray(after))
        result=self.run_action()
        self.assertEqual(self.desktop.clicks,[[355,200,'left']])
        self.assertTrue(result['post_image_captured'])
    def test_ambiguous_target_refuses_before_input(self):
        changed=self.pixels.copy();changed[230:270,200:280]=changed[170:210,300:380]
        self.desktop.image=Image.fromarray(changed)
        with self.assertRaisesRegex(RuntimeError,'target is absent, ambiguous'):self.run_action()
        self.assertEqual(self.desktop.clicks,[])
        self.assertFalse(self.result()['click_completed'])
    def test_relative_layout_change_refuses_before_input(self):
        changed=self.pixels.copy();changed[40:85,60:160]=self.pixels[100:145,60:160]
        changed[50:95,75:175]=self.pixels[40:85,60:160]
        self.desktop.image=Image.fromarray(changed)
        with self.assertRaisesRegex(RuntimeError,'relative layout'):self.run_action()
        self.assertEqual(self.desktop.clicks,[])
    def test_changed_target_pixels_refuse_even_if_high_correlation(self):
        changed=self.pixels.copy();changed[175,305]=[0,0,0]
        self.desktop.image=Image.fromarray(changed)
        with self.assertRaisesRegex(RuntimeError,'quantization tolerance'):self.run_action()
        self.assertEqual(self.desktop.clicks,[])
    def test_r50_three_one_level_channels_only_pass_with_original_geometry_and_uniqueness(self):
        # R50: 64x31 = 1984 pixels; these exact three RGB channel changes
        # were the sole difference. Keep a portable random surrounding scene.
        pixels=self.pixels.copy()
        changes=((10,2,2,37),(0,17,1,35),(18,29,1,38))
        for x,y,channel,value in changes:pixels[170+y,300+x,channel]=value
        Image.fromarray(pixels).save(self.source)
        self.payload['target']={'crop_ltrb':[300,170,364,201],'point_offset':[32,15]}
        original_root=self.root
        for name,error in (('one_level',None),('two_levels','quantization tolerance'),
                           ('relative_position','relative layout'),('ambiguous','target is absent, ambiguous')):
            with self.subTest(name=name):
                self.root=original_root/name;self.root.mkdir()
                changed=pixels.copy()
                for x,y,channel,_ in changes:changed[170+y,300+x,channel]-=1
                if name=='two_levels':changed[172,310,2]-=1
                if name=='relative_position':
                    patch=changed[170:201,300:364].copy()
                    changed[170:201,300:364]=self.after_pixels[170:201,300:364]
                    changed[180:211,315:379]=patch
                if name=='ambiguous':changed[230:261,200:264]=changed[170:201,300:364]
                after=changed.copy();after[170:201,300:364]=self.after_pixels[170:201,300:364]
                self.desktop=FakeDesktop(Image.fromarray(changed),Image.fromarray(after))
                if error:
                    with self.assertRaisesRegex(RuntimeError,error):self.run_action()
                    self.assertEqual(self.desktop.clicks,[])
                    self.assertFalse(self.result()['click_completed'])
                else:
                    result=self.run_action()
                    self.assertEqual(self.desktop.clicks,[[332,185,'left']])
                    match=json.loads((self.root/'action/target-before.match.json').read_bytes())
                    self.assertFalse(match['pixels_exact'])
                    self.assertTrue(match['pixels_within_quantization_tolerance'])
                    self.assertEqual(match['pixel_quantization_tolerance'],1)
                    self.assertEqual(match['pixel_maximum_channel_difference'],1)
                    self.assertEqual(match['pixel_channel_difference_counts'],{'0':5949,'1':3})
                    self.assertEqual(match['pixel_changed_channel_count'],3)
                    self.assertEqual(match['pixel_changed_pixel_count'],3)
                    self.assertFalse(result['business_pass'])
                    self.assertFalse(result['human_review_claimed'])
                    receipt=json.loads((self.root/'action/mapped-click-after.png.json').read_bytes())
                    self.assertEqual(receipt['source_age_before']['maximum_seconds'],60)
                    self.assertEqual(result['reserve_seconds'],90)

    def test_changed_focus_refuses_before_input(self):
        count=[0]
        def guard():
            count[0]+=1
            return {**self.state,'focus_hwnd':0 if count[0]>=3 else 123}
        with self.assertRaisesRegex(RuntimeError,'HWND/focus'):self.run_action(guard)
        self.assertEqual(self.desktop.clicks,[])
    def test_desktop_size_change_refuses_before_input(self):
        self.desktop.image=Image.new('RGB',(481,320))
        with self.assertRaisesRegex(RuntimeError,'dimensions'):self.run_action()
        self.assertEqual(self.desktop.clicks,[])
    def test_unchanged_actual_after_pixels_do_not_infer_success_or_replay(self):
        self.desktop.after=self.before
        self.run_action()
        self.assertEqual(len(self.desktop.clicks),1)
        self.assertTrue(self.result()['click_completed'])
        self.assertTrue(self.result()['post_template_observations'][0]['matched_uniquely'])
        self.assertFalse(self.result()['business_pass'])
        with self.assertRaisesRegex(RuntimeError,'already consumed'):self.run_action()
        self.assertEqual(len(self.desktop.clicks),1)


if __name__=='__main__':unittest.main()
