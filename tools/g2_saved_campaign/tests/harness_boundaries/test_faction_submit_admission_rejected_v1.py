from copy import deepcopy
import unittest
from tools.g2_saved_campaign.faction_submit_admission_rejected_v1 import classify_faction_submit_admission_rejected_v1 as qualify

ERROR='Error executing tool ck3_auto_turn: private-submit-faction-gift-member-v1 failed: private_faction_action_or_pending_binding_invalid'

def failed(message=ERROR,sequence=17):
    return {'request':{'tool':'ck3_auto_turn','arguments':{},'sequence':sequence},
            'result':{'is_error':True,'result_type':'complete','structured_content':None,
                      'content':[{'type':'text','text':message}]}}

class SubmitAdmission(unittest.TestCase):
    def test_completed_presubmit_reject_is_not_a_read_query_or_gift_success(self):
        for sequence in (1,17,1001):
            result=qualify(failed(sequence=sequence))
            self.assertEqual(result['original_operation_kind'],'business_submit_attempt')
            self.assertFalse(result['native_business_executor_entered'])
            self.assertFalse(result['native_mailbox_submission_occurred'])
            self.assertTrue(result['python_submission_started_ledger_may_exist'])
            self.assertTrue(result['faction_pending_ledger_must_be_preserved'])
            self.assertFalse(result['gift_success_claimed'])
            self.assertFalse(result['original_action_replay_allowed'])

    def test_mailbox_timeout_receipt_other_command_and_unknown_do_not_qualify(self):
        for message in [ERROR+' extra',ERROR.replace('private_faction_action_or_pending_binding_invalid','private_faction_application_main_unavailable'),
            ERROR.replace('private_faction_action_or_pending_binding_invalid','timeout_executor_running'),
            ERROR.replace('private_faction_action_or_pending_binding_invalid','private_faction_pending_receipt_invalid'),
            ERROR.replace('private-submit-faction-gift-member-v1','private-query-faction-gift-receipt-v1')]:
            with self.subTest(message=message):self.assertIsNone(qualify(failed(message)))
        for key,value in [('is_error',False),('result_type','pending'),('structured_content',{})]:
            row=failed();row['result'][key]=value
            with self.subTest(key=key):self.assertIsNone(qualify(row))
        row=failed();row['client_error']='timeout';self.assertIsNone(qualify(row))
        row=failed();row['request']['tool']='ck3_execute_step';self.assertIsNone(qualify(row))
        row=failed();row['request']['arguments']={'retry':True};self.assertIsNone(qualify(row))
        row=failed(sequence=True);self.assertIsNone(qualify(row))
        row=failed();row['result']['content'].append({'type':'text','text':'unknown'});self.assertIsNone(qualify(row))

if __name__=='__main__':unittest.main()
