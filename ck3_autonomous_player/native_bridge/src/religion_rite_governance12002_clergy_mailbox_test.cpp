#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion::clergy;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte,N>;
template <typename Buffer,typename T>
void Put(Buffer &b,std::size_t at,T value) {
  std::memcpy(b.data()+at,&value,sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *,1> entries{entry.data()};
  Bytes<0x30> characters{}, tasks{};
  Bytes<0xA0> character_slots{}, task_slots{};
  Bytes<0x1D8> owner{}, candidate{}, foreign_owner{};
  Bytes<0x240> landed{};
  Bytes<0x50> task{}, type{};
  Bytes<0x60> position{};
  std::array<std::int32_t,2> task_ids{task_id,task_id};
  void *state_ptr=state.data(), *jomini_ptr=jomini.data();
  void *characters_ptr=characters.data(), *tasks_ptr=tasks.data();
  static constexpr std::int32_t owner_id=0x03000004;
  static constexpr std::int32_t candidate_id=0x06000005;
  static constexpr std::int32_t foreign_owner_id=0x01000007;
  static constexpr std::int32_t task_id=0x02000006;
  int native_calls=0;
  bool position_value=true,character_value=true,reassign_value=true;
  bool foreign_context=false,drift=false,bad_arguments=false,deny_read=false;
  Fixture() {
    Put(state,8,std::int32_t{53175816}); Put(state,0x70,std::int32_t{2}); Put(state,0xA0,data.data());
    Put(jomini,0x18,players.data()); jomini[0x20]=std::byte{1};
    Put(players,0x1F0,std::int32_t{7}); Put(player,0x70,std::int32_t{7});
    Put(data,c::kPlayerCharacterManagerOffset+0x58,entries.data());
    Put(data,c::kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(entry,0xD8,std::int32_t{7}); Put(entry,0xB0,owner_id);
    Put(characters,0x20,character_slots.data()); Put(characters,0x2C,std::int32_t{10});
    Put(character_slots,4*0x10+8,owner.data()); Put(owner,0x18,owner_id);
    Put(character_slots,5*0x10+8,candidate.data()); Put(candidate,0x18,candidate_id);
    Put(character_slots,7*0x10+8,foreign_owner.data()); Put(foreign_owner,0x18,foreign_owner_id);
    Put(owner,r::kCharacterRiteOffset,std::uint32_t{0});
    Put(candidate,r::kCharacterRiteOffset,std::uint32_t{0});
    Put(owner,r::kLandedOffset,landed.data());
    Put(landed,r::kTaskIdsOffset,task_ids.data()); Put(landed,r::kTaskCountOffset,std::int32_t{1});
    Put(tasks,0x20,task_slots.data()); Put(tasks,0x2C,std::int32_t{10});
    Put(task_slots,6*0x10+8,task.data()); Put(task,r::kTaskIdentityOffset,task_id);
    Put(task,r::kTaskTypeOffset,type.data()); Put(task,r::kTaskOwnerOffset,owner_id);
    Put(task,r::kTaskIncumbentOffset,std::int32_t{-1});
    Put(type,r::kTypePositionOffset,position.data());
    Put(position,r::kPositionKeyOffset,r::kPositionKey.data());
    Put(position,r::kPositionKeyOffset+0x10,std::uint64_t{r::kPositionKey.size()});
    Put(position,r::kPositionKeyOffset+0x18,std::uint64_t{31});
  }
};
Fixture *f=nullptr;
void *Player(void *) { return f->player.data(); }
void *CourtOwner(void *candidate) {
  if (candidate!=f->candidate.data()) f->bad_arguments=true;
  return f->foreign_context ? f->foreign_owner.data() : f->owner.data();
}
bool ValidPosition(void *position,std::int32_t owner) {
  ++f->native_calls;
  if (position!=f->position.data() || owner!=Fixture::owner_id) f->bad_arguments=true;
  return f->position_value;
}
bool ValidCharacter(void *position,std::int32_t candidate) {
  ++f->native_calls;
  if (position!=f->position.data() || candidate!=Fixture::candidate_id) f->bad_arguments=true;
  return f->character_value;
}
bool CanReassign(void *task,void *tooltip) {
  ++f->native_calls;
  if (task!=f->task.data() || tooltip!=nullptr) f->bad_arguments=true;
  if (f->drift) Put(f->state,8,std::int32_t{53175817});
  return f->reassign_value;
}
bool Read(void *,const void *address,void *out,std::size_t size) noexcept {
  if (f->deny_read && address==f->owner.data()+r::kCharacterRiteOffset) return false;
  std::memcpy(out,address,size); return true;
}
r::Bindings Bind(Fixture &fixture) {
  f=&fixture;
  r::Bindings b{}; b.enabled=true; b.offline_fixture=true;
  b.executable_sha256=c::kExecutableSha256;
  b.core={true,&f->state_ptr,&f->jomini_ptr,&f->characters_ptr,&Player};
  b.task_storage_slot=&f->tasks_ptr;
  b.valid_position=&ValidPosition; b.valid_character=&ValidCharacter;
  b.can_reassign=&CanReassign; b.court_owner=&CourtOwner;
  b.read_memory=&Read; return b;
}
}

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

#if defined(XAR_CLERGY_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif

namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
int checks = 0;
void Check(bool condition,const char *message) {
  ++checks;
  if(!condition) throw std::runtime_error(message);
}
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "clergy-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    if (++reads > 1 && drift) ++out.date_raw;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;
  Pump(Fixture &fixture, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    // Existing primary offline fixture permit; central named clergy registration is separate.
    mailbox.permitted_executor = &c::ExecutePlayerClergyAppointmentMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};


bool Query(Fixture &fixture,FrameAdapter &adapter,const std::filesystem::path &directory,
           const char *filename,r::Observation &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture,mailbox);
  c::PlayerClergyAppointmentMailboxContext12002 query{};
  query.envelope.game=&adapter;
  query.envelope.mailbox=&mailbox;
  query.envelope.expected_snapshot=adapter.frame;
  query.envelope.expected_snapshot_revision=701;
  query.request.candidate_character_id=Fixture::candidate_id;
  query.bindings=Bind(fixture);
  adapter.reads=0;
  std::atomic<bool> done{false};
  bool result=false,drained=false;
  std::string serialized,failure;
  std::thread worker([&] {
    result=c::RunPlayerClergyAppointmentMailbox12002(query,"clergy\"worker-fixture",serialized,failure);
    done.store(true,std::memory_order_release);
  });
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(6);
  while(!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now()<deadline) {
    if(mailbox.state.load(std::memory_order_acquire)==api::MainThreadQueryMailboxStateV1::queued)
      drained=api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained,"actual queued executor drained on owner thread");
  Check(mailbox.state==api::MainThreadQueryMailboxStateV1::idle,"actual ticket reclaimed");
  observed=query.observation;
  Check(query.bindings.application_main_thread_id==GetCurrentThreadId(),"clergy native owner comes from actual stamp");
  if(result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(),"complete actual wrapper");
    Check(observed.capture_epoch==query.envelope.execution_stamp.pump_epoch && observed.capture_epoch!=701,"native epoch distinct from public revision");
    std::ofstream(directory/filename)<<serialized<<'\n';
  } else {
    Check(serialized.empty() && !failure.empty(),"unstable frame has no success JSON");
    std::ofstream(directory/"frame-changed-rejection.json")
      <<"{\"success_wire_emitted\":false,\"mailbox_reclaimed\":true,\"failure\":\""<<failure<<"\"}\n";
  }
  return result;
}
}

int main(int argc,char **argv) {
  try {
    Check(argc==2,"output directory argument");
    const std::filesystem::path dir(argv[1]);
    Fixture q; FrameAdapter adapter;
    adapter.frame.paused=adapter.frame.map_ready=true;
    adapter.frame.has_played_character=adapter.frame.played_character_alive=true;
    adapter.frame.played_character_id=Fixture::owner_id;
    adapter.frame.date_raw=53175816;
    r::Observation out{};
    Check(Query(q,adapter,dir,"vacant-valid.json",out) && out.available &&
          out.position_present && out.native_valid_position==true && out.native_valid_character==true &&
          out.native_can_reassign==true && !out.incumbent_character_id &&
          out.owner_rite_id==0U && !q.bad_arguments,"actual candidate and native predicates through owning mailbox");
    Put(q.task,r::kTaskIncumbentOffset,Fixture::candidate_id); q.reassign_value=false;
    Check(Query(q,adapter,dir,"incumbent-reassign-denied.json",out) && out.available &&
          out.candidate_is_incumbent && out.native_valid_character==true && out.native_can_reassign==false,
          "actual final denial remains an observed query");
    q.reassign_value=true; q.character_value=false;
    Put(q.candidate,r::kCharacterRiteOffset,std::uint32_t{0x83000003});
    Check(Query(q,adapter,dir,"candidate-native-denied.json",out) && out.available &&
          out.native_valid_character==false && out.candidate_rite_id==0x83000003U,
          "candidate-specific native final and complete Rite reference");
    q.character_value=true; q.foreign_context=true;
    Check(Query(q,adapter,dir,"foreign-context.json",out) && out.available &&
          out.candidate_matches_owner_context==false && out.native_valid_character==true,
          "foreign context stays distinct from compiled root predicate");
    q.foreign_context=false; Put(q.landed,r::kTaskCountOffset,std::int32_t{0});
    Check(Query(q,adapter,dir,"position-absent.json",out) && out.available && !out.position_present &&
          !out.native_can_reassign && !out.native_valid_character,"actual position absence has no invented gates");
    Put(q.landed,r::kTaskCountOffset,std::int32_t{1});
    Put(q.candidate,0x18,Fixture::candidate_id+0x01000000);
    Check(Query(q,adapter,dir,"candidate-unavailable.json",out) && !out.available &&
          out.failure==r::Failure::candidate_unavailable && out.candidate_character_id==Fixture::candidate_id &&
          out.owner_character_id==Fixture::owner_id,"actual invalid full candidate returns typed unavailable with actual player frame");
    Put(q.candidate,0x18,Fixture::candidate_id); q.deny_read=true;
    Check(Query(q,adapter,dir,"context-unavailable.json",out) && !out.available &&
          out.failure==r::Failure::candidate_context_unavailable && !out.native_valid_character,
          "failed actual context does not become native false");
    q.deny_read=false; adapter.drift=true;
    Check(!Query(q,adapter,dir,"frame-changed.json",out),"actual full owner snapshot post-read drift");
    adapter.drift=false;
    c::PlayerClergyAppointmentRequest12002 request{};
    Check(!c::ParsePlayerClergyAppointmentRequest12002("{}",request),"required explicit candidate");
    Check(!c::ParsePlayerClergyAppointmentRequest12002("{\"candidate_character_id\":0}",request),"not an empty candidate");
    Check(c::ParsePlayerClergyAppointmentRequest12002("{\"candidate_character_id\":100663301}",request) &&
          request.candidate_character_id==Fixture::candidate_id && request.expected_revision==0,"actual full candidate without optional revision");
    Check(c::ParsePlayerClergyAppointmentRequest12002("{\"candidate_character_id\":100663301,\"expected_revision\":701}",request) &&
          request.expected_revision==701,"revision alias");
    Check(c::ParsePlayerClergyAppointmentRequest12002("{\"candidate_character_id\":100663301,\"expected_snapshot_revision\":701,\"expected_revision\":701}",request),"matching revision aliases");
    Check(!c::ParsePlayerClergyAppointmentRequest12002("{\"candidate_character_id\":100663301,\"expected_snapshot_revision\":701,\"expected_revision\":702}",request),"conflicting revision aliases");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire,failure;
    Check(!c::HandlePlayerClergyAppointmentPrivate12002(adapter,mailbox,adapter.frame,701,
          c::kPlayerClergyAppointmentPrivateStep12002,"{\"candidate_character_id\":100663301,\"expected_revision\":702}","stale",wire,failure) &&
          wire.empty() && failure=="player_clergy_appointment_current_frame_unavailable" && mailbox.next_sequence==0,
          "real handler rejects stale public frame before native queue");
    Check(!c::HandlePlayerClergyAppointmentPrivate12002(adapter,mailbox,adapter.frame,701,
          c::kPlayerClergyAppointmentPrivateStep12002,"{}","empty",wire,failure) &&
          failure=="player_clergy_appointment_request_invalid" && mailbox.next_sequence==0,"real handler has no empty-candidate fallback");
    Check(c::IsPlayerClergyAppointmentPrivateStep12002(c::kPlayerClergyAppointmentPrivateStep12002) &&
          !c::IsPlayerClergyAppointmentPrivateStep12002("query-player-clergy-appointment-v1-other"),"exact clergy selector");
    std::cout<<"PASS checks="<<checks<<" actual_worker_owner_pipeline=true actual_provider=true actual_wrapper=true live=false\n";
    return 0;
  } catch(const std::exception &error) { std::cerr<<"FAIL "<<error.what()<<'\n'; return 1; }
}
