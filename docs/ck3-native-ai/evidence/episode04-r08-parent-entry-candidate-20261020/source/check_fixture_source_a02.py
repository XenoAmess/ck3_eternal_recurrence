import ast
import hashlib
import json
import os
from pathlib import Path
import unittest
import check_core_a04 as old
HERE=Path(__file__).resolve().parent

class CorrectedCoreChecks(old.CandidateTests):
 @classmethod
 def setUpClass(cls):
  p=HERE/'candidate-a04'
  cls.asm=(p/'parent_entry_opportunity_12004.asm').read_text()
  cls.cpp=(p/'parent_entry_opportunity_12004.cpp').read_text()
  cls.header=(p/'parent_entry_opportunity_12004.hpp').read_text()
 def test_real_player_slot_and_character_ID_are_independent(self):
  p=Path('C:/ck3-e04-resume-20261020-a01/r08-scene-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0223/case-output/r08-writer-control/watch/ADMISSION.actual.json')
  raw=p.read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'0f442d65fd587101b2cc070add82f23921c71d95ddbad293755cafad5eee1f81')
  b=json.loads(raw)['owner_binding'];self.assertEqual((b['local_player_id'],b['player_character_full_id']),(1,33388))
  self.assertIn('!a.local_player_id',self.cpp)
  self.assertNotIn('a.local_player_id!=a.full_id',self.cpp)

class FixtureSourceChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=HERE/'fixture-a02';cls.cpp=(cls.p/'cold_main.cpp').read_text();cls.asm=(cls.p/'fixture_call.asm').read_text();cls.core=(cls.p/'fixture_core.cpp').read_text()
 def test_actual_native_fixture_is_explicit_and_core_is_unmodified_input(self):
  cm=(self.p/'CMakeLists.txt').read_text()
  self.assertIn('add_executable(parent_entry_opportunity_cold',cm)
  self.assertIn('XAR_BUILD_PARENT_ENTRY_SYNTHETIC_COLD',cm)
  self.assertIn('#include "../candidate-a04/parent_entry_opportunity_12004.cpp"',self.core)
  self.assertIn('owner.local_player_id=1',self.core)
  self.assertIn('ParentFixtureAdmissionGuardTest()',self.cpp)
  for name in ('cold_main.cpp','fixture_core.cpp','fixture_call.asm','fixture_shared.hpp'):self.assertTrue((self.p/name).is_file())
 def test_return_and_real_body_are_measured_separately_from_prefix_flags(self):
  self.assertIn('f.rflags&0xcd5',self.cpp)
  self.assertNotIn('b.rflags',self.cpp)
  self.assertIn('ParentFixtureReturnedRax==0xd00dfeed11223344ULL',self.cpp)
  self.assertIn('ParentFixtureReturnedRsp==f.rsp+8',self.cpp)
  self.assertIn('ParentFixtureBodyCalls==1',self.cpp)
  self.assertIn('std::memcmp(b.xmm,ParentFixtureInputXmm',self.cpp)
  self.assertIn('ParentFixtureAfterCall',self.cpp)
  self.assertIn('  cld\n',self.asm) # caller must restore normal ABI DF before C++
 def test_real_OS_unwind_is_required_and_each_boundary_file_is_bounded(self):
  self.assertIn('RtlLookupFunctionEntry',self.cpp)
  self.assertIn('RtlVirtualUnwind(UNW_FLAG_NHANDLER',self.cpp)
  helper=(self.p/'prepare_unwind_cases.py').read_text();ast.parse(helper)
  self.assertIn("for key,kind in (('thunk','T'),('prefix','P'))",helper)
  self.assertIn('for ins in decoded:',helper)
  self.assertIn("raw[-4:].hex()=='ff642408'",helper)
  self.assertIn('reads<=16',helper)
  self.assertIn('full_EXE_hashes',helper)
 def test_foreign_and_stalled_unknowns_are_not_relabelled_native_install(self):
  self.assertIn('i<257',self.cpp)
  self.assertIn('!busy.foreign_count',self.cpp)
  self.assertIn('!overflow.foreign_count',self.cpp)
  self.assertIn('!pe::Uninstall(false)',self.cpp)
  self.assertIn('real_Install_Restore_qualified\\\":false',self.cpp)
  self.assertIn('full_native_qualification\\\":false',self.cpp)

 def test_unwind_input_rejects_duplicate_and_partial_case_sets(self):
  self.assertIn('visited.emplace(kind,offset).second',self.cpp)
  self.assertIn('seen_t==expected_t&&seen_p==expected_p',self.cpp)
  for nv in ('c.Rsi==0x5151','c.Rdi==0xd1d1','c.R12==0x1212','c.R13==0x1313','c.R15==0x1515'):self.assertIn(nv,self.cpp)
 def test_admission_guard_reaches_prefix_not_merely_first_identity_read(self):
  self.assertIn('Atomic(fixture_prefix_reads)==0',self.core)
  self.assertIn('InterlockedIncrement64(&fixture_prefix_reads)',self.core)
  self.assertIn('add_dependencies(parent_entry_opportunity_cold xar_parent_entry_opportunity_12004)',(self.p/'CMakeLists.txt').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
