#include "xar_bridge/army_actual_monthfirst_cleanup_12004.hpp"
#include "xar_bridge/army_actual_monthfirst_cleanup_12004_serializer.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <stdexcept>
#include <string>
#include <unordered_map>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kImage=0x140000000ULL;
constexpr std::uintptr_t kPrimary=0x100000U,kBuffer=0x200000U,kVtable=0x300000U,
    kFallback=0x500000U,kGameState=0x900000U,kRoster=0xA00000U;
constexpr std::uintptr_t kRawRax=0xFEDCBA9876543210ULL;
constexpr std::uint32_t kRegiId=0xA1000011U,kOtherRegi=0xB2000012U;
constexpr std::uint64_t kObservedAfterDate=0x887766550000002AULL;

void Require(bool condition,const char *message) {
  if(!condition)throw std::runtime_error(message);
}
struct Fixture {
  std::unordered_map<std::uintptr_t,std::uint8_t> bytes;
  std::size_t reads=0,child_original_calls=0,parent_original_calls=0;
  bool wrong_caller=false,overbound=false;
  ArmyActualMonthfirstCleanupRecord12004 child;
  ArmyActualMonthfirstCleanupBindings12004 binding;
  template<class T> void Put(std::uintptr_t address,const T &value) {
    const auto *source=reinterpret_cast<const std::uint8_t *>(&value);
    for(std::size_t i=0;i<sizeof(T);++i)bytes[address+i]=source[i];
  }
  static bool Read(void *context,std::uintptr_t address,void *destination,std::size_t count) noexcept {
    auto &f=*static_cast<Fixture *>(context);++f.reads;
    auto *output=static_cast<std::uint8_t *>(destination);
    for(std::size_t i=0;i<count;++i){
      const auto found=f.bytes.find(address+i);if(found==f.bytes.end())return false;
      output[i]=found->second;
    }
    return true;
  }
  void Setup() {
    binding=BindArmyActualMonthfirstCleanup12004(kImage,kExecutableSha256);
    binding.read_context=this;binding.read=&Read;
    Put(kGameState+8,std::uint64_t{0x1122334400000007ULL});
    Put(kGameState+0xC0,std::uint8_t{0}); // Parent entry precedes saved flag.
    Put(kPrimary+0x50,kRoster);Put(kPrimary+0x5C,std::int32_t{2});
    Put(kRoster,std::uint32_t{0xCC000033U});Put(kRoster+4,std::uint32_t{0xDD000033U});
    Put(kPrimary+0x468,kBuffer);Put(kPrimary+0x474,std::int32_t{2});
    Put(kBuffer,kVtable);Put(kBuffer+16,kVtable);
    Put(kVtable,std::uintptr_t{0xDEADBEEFU}); // Observed unknown callback target.
    Put(kBuffer+8,kRegiId);Put(kBuffer+0xC,std::int32_t{0});
    Put(kBuffer+16+8,kOtherRegi);Put(kBuffer+16+0xC,std::int32_t{0});
    Put(kImage+0x5D1EB68U,std::uintptr_t{0});
    Put(kImage+0x5D1EB58U,kFallback);
    Put(kFallback+0x10,std::uint32_t{0xEF000099U});
    Put(kFallback+0x14,std::uint32_t{0x52656769U});
    Put(kFallback+0x18+0x1C,std::uint64_t{0x1234567800000003ULL});
  }
};
Fixture *g_fixture=nullptr;

std::uintptr_t __fastcall OriginalCleanup(void *primary,const void *date) {
  auto &f=*g_fixture;++f.child_original_calls;
  Require(reinterpret_cast<std::uintptr_t>(primary)==kPrimary &&
          reinterpret_cast<std::uintptr_t>(date)==kGameState+8,"original gets original arguments");
  if(!f.wrong_caller && !f.overbound) {
    f.Put(kPrimary+0x474,std::int32_t{1});
    f.Put(kBuffer+8,kOtherRegi);
    f.Put(kFallback+0x18+0x1C,kObservedAfterDate);
  }
  return kRawRax;
}
std::uintptr_t __fastcall OriginalPostParent(void *secondary) {
  auto &f=*g_fixture;++f.parent_original_calls;
  Require(reinterpret_cast<std::uintptr_t>(secondary)==kPrimary+8,"parent original receives secondary");
  f.Put(kGameState+0xC0,std::uint8_t{2});
  const auto before_reads=f.reads;
  f.child=InvokeArmyActualMonthfirstCleanup12004(f.binding,&OriginalCleanup,
      reinterpret_cast<void *>(kPrimary),reinterpret_cast<const void *>(kGameState+8),
      f.wrong_caller ? std::uintptr_t{0x2A9A673U} : kArmyActualMonthfirstCleanupReturnRva12004);
  if(f.wrong_caller)Require(f.reads==before_reads,"wrong literal return PC forwards without raw capture");
  return f.child.raw_return_bits.value_or(0);
}

ArmyNaturalPhaseRecord12004 Parent(Fixture &f) {
  g_fixture=&f;
  ArmyNaturalPhaseBindings12004 phase;
  phase.read_context=&f;phase.read=&Fixture::Read;
  phase.game_state_identity=kGameState;
  phase.next_event=&NextArmyNaturalPhaseEvent12004;
  return InvokeArmyNaturalPhaseScope12004(phase,&OriginalPostParent,
      reinterpret_cast<void *>(kPrimary+8),ArmyNaturalPhaseKind12004::post_date,
      std::uintptr_t{0x777777U});
}
} // namespace

// One fragment in33b's sole connectedphasecompound. No old43 algorithm cases.
void RunArmyMonthfirstCleanupNaturalFocus12004() {
  ClearArmyActualMonthfirstCleanupJournalFixture12004();
  Fixture actual;actual.Setup();
  const auto parent=Parent(actual);
  const auto &r=actual.child;
  Require(actual.parent_original_calls==std::size_t{1} && actual.child_original_calls==std::size_t{1} &&
          parent.raw_return_bits==kRawRax && r.raw_return_bits==kRawRax,"one original each and opaque RAX passthrough");
  Require(r.source_call_admitted && r.saved_mask02_admitted_by_literal_call==true &&
          r.phase.entry_c0_raw==std::uint8_t{0} && !r.phase.saved_c0_raw,
          "literal arrival proves masked admission without parent entry C0 substitution");
  Require(r.same_clock_thread_order==true &&
          r.phase.entry_event.clock_identity==parent.scope.entry_event.clock_identity &&
          r.phase.entry_event.sequence==parent.scope.entry_event.sequence,
          "actual active parent token and13 sharedclock ordering");
  Require(r.before.complete && r.after.complete &&
          r.before.live_count_raw_i32==std::int32_t{2} && r.after.live_count_raw_i32==std::int32_t{1} &&
          r.after.copied_physical_extent==std::size_t{2} && r.after.physical_slots.size()==std::size_t{2},
          "actual returned live count retains copied original physical backing");
  Require(r.before.physical_slots[0].slot0_matches_known_mode0_source==false &&
          r.after.physical_slots[0].date_1c_raw64==kObservedAfterDate &&
          r.after.physical_slots[0].requested_regi_full_id==kOtherRegi,
          "unknown callback target still produces actual returned copies, no predicted sentinel");
  auto owned=ReadArmyActualMonthfirstCleanupJournal12004();
  Require(owned.events.size()==std::size_t{1} && !owned.observer_installed,
          "fixture history distinct from actual installed status");
  std::string json;AppendArmyActualMonthfirstCleanupObservations12004(json,owned);
  const auto reads_after_copy=actual.reads;
  actual.Put(kFallback+0x18+0x1C,std::uint64_t{0});
  std::string same_json;AppendArmyActualMonthfirstCleanupObservations12004(same_json,owned);
  Require(json==same_json && actual.reads==reads_after_copy,"serializer owns snapshots, never rereads native bytes");
  Require(json.find("\"conditional_predictor_executed\":false")!=std::string::npos &&
          json.find("\"saved_c0_raw\":null")!=std::string::npos,"wire preserves literal source and unknown full saved C0");

  Fixture wrong;wrong.Setup();wrong.wrong_caller=true;
  (void)Parent(wrong);
  Require(wrong.child_original_calls==std::size_t{1} && !wrong.child.source_call_admitted &&
          wrong.child.raw_return_bits==kRawRax,"wrong callsite transparent original once");
  owned=ReadArmyActualMonthfirstCleanupJournal12004();
  Require(owned.events.size()==std::size_t{1} && owned.unattributed_invocations==std::uint64_t{1},
          "unsupported call never creates admitted natural history");

  Fixture partial;partial.Setup();partial.overbound=true;
  partial.Put(kPrimary+0x474,std::int32_t{257});
  (void)Parent(partial);
  Require(partial.child_original_calls==std::size_t{1} && partial.child.original_returned &&
          !partial.child.before.complete && partial.child.before.truncated &&
          partial.child.before.live_count_raw_i32==std::int32_t{257} &&
          partial.child.before.physical_slots.empty(),"overbound capture is partial257, not fake empty; original still once");
  ArmyActualMonthfirstCleanupDetourState12004 state;
  ArmyActualMonthfirstCleanupInstallEnvironment12004 environment;
  environment.bindings=actual.binding;
  Require(!InstallArmyActualMonthfirstCleanup12004(state,environment,"wrong-build") &&
          (state.failure_flags.load()&cleanup_install_exact_build)!=0,"install exact build gate before target read");
  Require(!InstallArmyActualMonthfirstCleanup12004(state,environment,kExecutableSha256) &&
          (state.failure_flags.load()&cleanup_install_quiescence)!=0,"install cold quiescence gate before target read");
  g_fixture=nullptr;
}
