"""Source-backed callback+8 observations cannot imply named semantics or action."""
from copy import deepcopy
import unittest
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import SOURCE_12004,SOURCE_INDIRECT_12004
from xar_autoplayer.bridge.gui_window_tree_contract import normalize_gui_window_tree_v1


class GuiCallbackIndirectTarget12004Tests(unittest.TestCase):
    def raw(self, upgraded=True, wrapper=True):
        callback={"index":0,"callback_vtable_rva":0x4965D98,
                  "callback_slot2_rva":0x3AA30E0 if wrapper else 0x9CC100}
        if upgraded and wrapper:
            callback["indirect_target_3aa30e0"]={"native_target_8_rva":0xABC100,"receiver_f0_present":True}
        return {"step":"inspect-gui-window-tree-v1","accepted":True,"status":"available",
                "scope_root_name":"military_view","root_available":True,"truncated":False,"widget_count":1,
                "callback_binding_source_12004":dict(SOURCE_INDIRECT_12004 if upgraded else SOURCE_12004),
                "widgets":[{"runtime_name":"military_view","child_path":"","depth":0,"child_count":0,
                    "vtable_rva":0x4965910,"effective_visible":False,"enabled":True,
                    "standard_click_binding_12004":{"button_base_slot13":True,"group":"fallback","callbacks":[callback]}}]}

    def target(self, raw):return raw["widgets"][0]["standard_click_binding_12004"]["callbacks"][0]

    def test_source_pinned_indirect_target_is_preserved_without_business_credit(self):
        value=normalize_gui_window_tree_v1(self.raw(),"military")
        self.assertEqual(self.target(value)["indirect_target_3aa30e0"]["native_target_8_rva"],0xABC100)
        self.assertFalse(value["click_action_available"])
        self.assertFalse(value["callback_method_name_available"])

    def test_null_receiver_presence_is_observed_without_inventing_character(self):
        raw=self.raw();self.target(raw)["indirect_target_3aa30e0"]["receiver_f0_present"]=False
        self.assertIs(self.target(normalize_gui_window_tree_v1(raw,"military"))["indirect_target_3aa30e0"]["receiver_f0_present"],False)

    def test_non_thunk_retains_only_original_target(self):
        value=normalize_gui_window_tree_v1(self.raw(wrapper=False),"military")
        self.assertNotIn("indirect_target_3aa30e0",self.target(value))

    def test_original_source_profile_still_reads_original_published_leaf(self):
        value=normalize_gui_window_tree_v1(self.raw(upgraded=False),"military")
        self.assertNotIn("indirect_target_3aa30e0",self.target(value))

    def test_new_profile_requires_thunk_payload(self):
        raw=self.raw();self.target(raw).pop("indirect_target_3aa30e0")
        with self.assertRaises(ValueError):normalize_gui_window_tree_v1(raw,"military")

    def test_old_profile_cannot_assert_new_source_operands(self):
        raw=self.raw();raw["callback_binding_source_12004"]=dict(SOURCE_12004)
        with self.assertRaises(ValueError):normalize_gui_window_tree_v1(raw,"military")

    def test_modified_entry_pin_or_rva_is_rejected(self):
        for key,value in (("indirect_target_thunk_rva",0x3AA30E1),("indirect_target_thunk_bytes_sha256","0"*64)):
            raw=self.raw();raw["callback_binding_source_12004"][key]=value
            with self.assertRaises(ValueError):normalize_gui_window_tree_v1(raw,"military")

    def test_invalid_target_or_receiver_type_is_rejected(self):
        for key,value in (("native_target_8_rva",0),("native_target_8_rva",0x61C5000),
                          ("native_target_8_rva",True),("receiver_f0_present",1)):
            raw=self.raw();self.target(raw)["indirect_target_3aa30e0"][key]=value
            with self.assertRaises(ValueError):normalize_gui_window_tree_v1(raw,"military")

    def test_other_handler_cannot_borrow_thunk_layout(self):
        raw=self.raw();self.target(raw)["callback_slot2_rva"]=0x9CC100
        with self.assertRaises(ValueError):normalize_gui_window_tree_v1(raw,"military")

    def test_payload_cannot_claim_method_name_or_receiver_pointer(self):
        for key,value in (("method_name","MilitaryView.OnMilitaryReinforcementClick"),("receiver_pointer",0x12345678)):
            raw=self.raw();self.target(raw)["indirect_target_3aa30e0"][key]=value
            with self.assertRaises(ValueError):normalize_gui_window_tree_v1(raw,"military")
