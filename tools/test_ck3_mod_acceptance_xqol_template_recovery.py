"""Portable fake controller checks; no desktop, CK3, or live business claims."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SOURCE=Path(__file__).with_name('ck3_mod_acceptance_cases')/'xqol_ui.py'
spec=importlib.util.spec_from_file_location('xqol_ui_template_recovery',SOURCE)
ui=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)
MESSAGE='Current stable layout anchor exceeds quantization tolerance or is ambiguous; no input'


class TemplatePreinputRecoveryTests(unittest.TestCase):
    def fixture(self,root):
        c=ui.Controller.__new__(ui.Controller)
        c.out=root;c.handle=None;c.seq=0;c.stage=0;c.records={};c.gaps=[]
        c.client=SimpleNamespace(focus_retained_process=mock.Mock())
        c.stages=['slider-anchor'];c.frozen={'run_id':'synthetic-run'};c.deadline=1000
        c.remaining=mock.Mock(return_value=1000)
        c.typed=mock.Mock();c.publish=mock.Mock();c.source_guard=mock.Mock();c.guard=mock.Mock()
        c.finish=mock.Mock(return_value={'gui_contract_qualified':False})
        c.mouse=mock.Mock(side_effect=RuntimeError(MESSAGE))
        source=root/'reviewed-source';source.write_bytes(b'synthetic reviewed source, not pixels')
        req={'action':'template-click','source':ui.pin(source),
             'target':{'crop_ltrb':[20,20,40,40],'point_offset':[10,10]},
             'layout':[{'crop_ltrb':[50,50,70,70]}]}
        (root/'requests').mkdir()
        ui.write(root/'requests/request-0000.json',req)
        ui.write(root/'requests/request-0001.json',{'action':'finish'})
        output=root/'action-0000-template-click';output.mkdir()
        match={'matched_uniquely':True,'pixel_geometry_equal':True,
               'pixel_quantization_tolerance':1,'pixels_within_quantization_tolerance':True,
               'pixel_maximum_channel_difference':0}
        ui.write(output/'target-before.match.json',match)
        match.update(pixels_within_quantization_tolerance=False,pixel_maximum_channel_difference=21)
        ui.write(output/'layout-before-0.match.json',match)
        result={'status':'REJECTED_NO_REPLAY','no_replay':True,
                'click_attempted':False,'click_completed':False,'post_image_captured':False,
                'error':'RuntimeError: '+MESSAGE,'run_id':'synthetic-run',
                'reviewed_original':req['source'],
                'request_payload':{key:req[key] for key in ('target','layout')},
                'business_pass':False,'human_review_claimed':False,
                'evidence':[ui.pin(output/'target-before.match.json'),ui.pin(output/'layout-before-0.match.json')]}
        ui.write(output/'result.json',result)
        return c,output,result

    def test_unique_pixel_rejection_advances_without_replay_or_business(self):
        with tempfile.TemporaryDirectory() as directory:
            c,output,result=self.fixture(Path(directory));original=(output/'result.json').read_bytes()
            value=c.run()
            self.assertEqual(c.seq,1);self.assertEqual(c.stage,0);self.assertEqual(c.records,{})
            c.mouse.assert_called_once();c.guard.assert_called_once_with()
            self.assertEqual(c.publish.call_count,2)
            c.typed.assert_called_once_with('snapshot',{},'initial-current-native-frame')
            c.client.focus_retained_process.assert_called_once_with(checkpoint_name='ui-entry-foreground',reserve_seconds=90)
            self.assertEqual((output/'result.json').read_bytes(),original)
            complete=ui.read(c.out/'action-0000.complete.json')
            self.assertEqual(complete['template_preinput_rejected'],ui.pin(output/'result.json'))
            self.assertTrue(complete['no_replay']);self.assertTrue(complete['fresh_root_review_required'])
            self.assertTrue(complete['input_ACK_is_not_business_pass'])
            self.assertFalse(value['gui_contract_qualified'])
            self.assertFalse((c.out/'controller-error-preserved.json').exists())

    def test_input_attempt_or_ambiguous_match_still_aborts(self):
        for invalid in ('input-attempted','ambiguous'):
            with self.subTest(invalid=invalid),tempfile.TemporaryDirectory() as directory:
                c,output,result=self.fixture(Path(directory))
                if invalid=='input-attempted':
                    result['click_attempted']=True
                else:
                    p=output/'layout-before-0.match.json';row=ui.read(p);row['matched_uniquely']=False
                    p.write_text(json.dumps(row),encoding='utf-8')
                    result['evidence'][-1]=ui.pin(p)
                (output/'result.json').write_text(json.dumps(result),encoding='utf-8')
                with self.assertRaisesRegex(RuntimeError,'quantization tolerance'):c.run()
                self.assertEqual(c.seq,0);self.assertEqual(c.stage,0)
                self.assertEqual(c.publish.call_count,1);c.guard.assert_not_called()
                self.assertFalse((c.out/'action-0000.complete.json').exists())
                self.assertTrue((c.out/'controller-error-preserved.json').exists())

    def test_original_guard_failure_aborts_without_sequence_advance(self):
        with tempfile.TemporaryDirectory() as directory:
            c,output,result=self.fixture(Path(directory));original=(output/'result.json').read_bytes()
            c.guard.side_effect=RuntimeError('Original keeper no longer owns screen')
            with self.assertRaisesRegex(RuntimeError,'Original keeper no longer owns screen'):c.run()
            self.assertEqual(c.seq,0);self.assertEqual(c.stage,0);self.assertEqual(c.records,{})
            c.mouse.assert_called_once();self.assertEqual(c.publish.call_count,1)
            self.assertEqual((output/'result.json').read_bytes(),original)
            self.assertFalse((c.out/'action-0000.complete.json').exists())
            self.assertTrue((c.out/'controller-error-preserved.json').exists())


    def template_mouse(self,c,req,execute):
        c.gui=object();c.coords=object();c.hwnd=42;c.pid=99;c.ctime=123
        c.operator_reviewer='/root/synthetic'
        with mock.patch.dict(sys.modules,{
            'ck3_mod_acceptance_gui_template':SimpleNamespace(),
            'ck3_mod_acceptance_template_click':SimpleNamespace(execute=execute)}):
            return ui.Controller.mouse(c,req,'action-0000')

    def test_default_template_source_remains_current_request_source(self):
        with tempfile.TemporaryDirectory() as directory:
            c,output,result=self.fixture(Path(directory))
            req=ui.read(c.out/'requests/request-0000.json');execute=mock.Mock()
            self.template_mouse(c,req,execute)
            self.assertEqual(execute.call_args.kwargs['source'],req['source'])
            self.assertEqual(execute.call_args.kwargs['pid'],c.pid)
            self.assertEqual(execute.call_args.kwargs['run_id'],c.frozen['run_id'])
            c.typed.assert_called_once_with('snapshot',{},'action-0000-independent-native-after')
            self.assertEqual(c.stage,0);self.assertEqual(c.records,{})

    def test_explicit_same_live_template_and_rejection_bind_old_source(self):
        with tempfile.TemporaryDirectory() as directory:
            c,output,result=self.fixture(Path(directory))
            request=c.out/'requests/request-0000.json';req=ui.read(request)
            old=c.out/'scene-older.png';old.write_bytes(b'older personally reviewed synthetic source')
            req['reviewed_template_source']=ui.pin(old)
            result['reviewed_original']=req['reviewed_template_source']
            request.write_text(json.dumps(req),encoding='utf-8')
            (output/'result.json').write_text(json.dumps(result),encoding='utf-8')
            original=(output/'result.json').read_bytes();execute=mock.Mock()
            self.template_mouse(c,req,execute)
            self.assertEqual(execute.call_args.kwargs['source'],ui.pin(old))
            self.assertNotEqual(execute.call_args.kwargs['source'],req['source'])
            foreign=dict(req,reviewed_template_source=dict(req['reviewed_template_source'],path=str(c.out/'other-live/scene-0000.png')))
            with self.assertRaisesRegex(RuntimeError,'same live controller'):
                self.template_mouse(c,foreign,execute)
            execute.assert_called_once()
            c.run()
            self.assertEqual(c.seq,1);self.assertEqual(c.stage,0);self.assertEqual(c.records,{})
            self.assertEqual((output/'result.json').read_bytes(),original)
            self.assertEqual(ui.read(c.out/'action-0000.complete.json')['template_preinput_rejected'],ui.pin(output/'result.json'))


if __name__=='__main__':unittest.main()
