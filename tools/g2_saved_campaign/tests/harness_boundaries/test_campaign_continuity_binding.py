from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from tools.g2_saved_campaign.campaign_continuity_binding import bind_campaign_continuity


def official_game_binding(launch):
    return {key: launch[key] for key in ("pid", "creation_date")}


class CampaignBinding(unittest.TestCase):
    def fixture(self, folder):
        campaign=Path(folder)/'clean-campaign';runtime=campaign/'runtime'
        previous=Path(folder)/'other-campaign/ROOT-CONTINUITY-WINDOW.json'
        feeder=SimpleNamespace(N=runtime,Q=runtime/'p8-queue',CONTINUITY_WINDOW=previous)
        launch={'pid':13,'creation_date':'fixture-generation-a'}
        ledger={'game_binding':official_game_binding(launch),'window_id':1,'manual_repair_count':0}
        return feeder,dict(campaign_root=campaign,runtime_root=runtime,sdk_prefix='p8',launch=launch,
            ledger_state=ledger,first_control_sequence=17,validate_first_control=lambda seq:None,
            game_binding=official_game_binding)

    def test_corrects_foreign_ledger_without_touching_window_or_counters(self):
        with TemporaryDirectory() as folder:
            feeder,args=self.fixture(folder);before=deepcopy(args['ledger_state'])
            result=bind_campaign_continuity(feeder,**args)
            self.assertEqual(result,Path(args['campaign_root']).resolve()/'ROOT-CONTINUITY-WINDOW.json')
            self.assertEqual(feeder.CONTINUITY_WINDOW,result)
            self.assertEqual(args['ledger_state'],before)
            self.assertFalse(result.exists())

    def test_missing_first_full_rejects_before_binding_and_never_marks_a_window_failed(self):
        with TemporaryDirectory() as folder:
            feeder,args=self.fixture(folder);old_path=feeder.CONTINUITY_WINDOW
            def missing(seq):raise FileNotFoundError('first FULL is absent')
            args['validate_first_control']=missing
            with self.assertRaises(FileNotFoundError):bind_campaign_continuity(feeder,**args)
            self.assertEqual(feeder.CONTINUITY_WINDOW,old_path)
            self.assertEqual(args['ledger_state']['manual_repair_count'],0)

    def test_wrong_game_pid_or_birth_keeps_identity_guards(self):
        with TemporaryDirectory() as folder:
            for key,value in [('pid',14),('creation_date','fixture-generation-b')]:
                feeder,args=self.fixture(folder);old_path=feeder.CONTINUITY_WINDOW
                args['launch'][key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):bind_campaign_continuity(feeder,**args)
                self.assertEqual(feeder.CONTINUITY_WINDOW,old_path)

    def test_different_campaign_runtime_or_queue_rejects(self):
        with TemporaryDirectory() as folder:
            for change in ['campaign','runtime','queue']:
                feeder,args=self.fixture(folder)
                if change=='campaign':args['campaign_root']=Path(folder)
                elif change=='runtime':feeder.N=Path(folder)/'old-runtime'
                else:feeder.Q=Path(folder)/'old-queue'
                with self.subTest(change=change),self.assertRaises(ValueError):bind_campaign_continuity(feeder,**args)


if __name__=='__main__':unittest.main()
