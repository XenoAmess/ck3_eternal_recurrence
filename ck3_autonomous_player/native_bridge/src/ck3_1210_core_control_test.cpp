#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <cstdlib>
#include "xar_bridge/main_thread_timeline_policy_v1.hpp"
#include <vector>
#include <windows.h>

namespace {
using namespace xar::game;
using namespace xar::ck3_1210;
constexpr std::array<std::string_view, 11> kCapabilities{kCoreFrameCapabilityV1,
    kCoreControlCapabilityV1,kApplicationExitCapabilityV1,"game.command.pause-map","game.command.resume-map",
    "game.command.set-speed-1","game.command.set-speed-2","game.command.set-speed-3",
    "game.command.set-speed-4","game.command.set-speed-5","game.command.save-checkpoint"};
const AdapterDescriptor kDescriptor{kAdapterId, kGameVersion,
    kExecutableSha256, "xar_checkpoint", kCapabilities};
class FixtureAdapter final : public GameAdapter {
public:
  explicit FixtureAdapter(const AdapterDescriptor &d) : descriptor_(d) {}
  const AdapterDescriptor &descriptor() const noexcept override {
    return descriptor_;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(xar::game::Snapshot &output) const noexcept override {
    output = {};
    return false;
  }
  xar::game::PauseSubmitResult
  submit_pause_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::PauseSubmitResult::unavailable;
  }
  xar::game::ResumeSubmitResult
  submit_resume_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::ResumeSubmitResult::unavailable;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  xar::game::SelectEventOptionResult
  submit_select_event_option(std::int32_t) const noexcept override {
    return xar::game::SelectEventOptionResult::unavailable;
  }
  xar::game::SaveCheckpointResult
  submit_save_checkpoint() const noexcept override {
    return {};
  }
  xar::game::ReplyPendingInteractionResult
  submit_reply_to_pending_interaction(
      xar::game::PendingInteractionReply) const noexcept override {
    return xar::game::ReplyPendingInteractionResult::unavailable;
  }
  xar::game::RaiseTroopsResult
  submit_raise_troops_default() const noexcept override {
    return xar::game::RaiseTroopsResult::unavailable;
  }
  xar::game::MoveArmyResult
  submit_move_army(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MoveArmyResult::unavailable;
  }
  xar::game::PreviewMoveArmyResult
  preview_move_army(std::int32_t, std::int32_t) const noexcept override {
    return {};
  }
  xar::game::DisbandArmyResult
  submit_disband_army(std::int32_t) const noexcept override {
    return xar::game::DisbandArmyResult::unavailable;
  }
  xar::game::SplitArmyHalfResult
  submit_split_army_half(std::int32_t) const noexcept override {
    return xar::game::SplitArmyHalfResult::unavailable;
  }
  xar::game::MergeArmiesResult
  submit_merge_armies(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MergeArmiesResult::unavailable;
  }
  xar::game::StartAssaultResult
  submit_start_assault(std::int32_t) const noexcept override {
    return xar::game::StartAssaultResult::unavailable;
  }
  xar::game::StopAssaultResult
  submit_stop_assault(std::int32_t) const noexcept override {
    return xar::game::StopAssaultResult::unavailable;
  }
  bool read_declarable_wars(
      std::vector<xar::game::DeclarableWarSnapshot> &output) const noexcept override {
    output.clear();
    return false;
  }
  xar::game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t, std::vector<xar::game::DeclarableWarSnapshot> &output)
      const noexcept override {
    output.clear();
    return xar::game::ReadDeclarableWarsResult::unavailable;
  }
  xar::game::DeclareWarResult submit_declare_war(
      const xar::game::DeclarableWarSnapshot &) const noexcept override {
    return xar::game::DeclareWarResult::unavailable;
  }
  xar::game::ReadArrangeMarriageChoicesResult
  read_arrange_marriage_choices(
      std::vector<xar::game::ArrangeMarriageChoice> &output,
      xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    output.clear();
    diagnostics = {};
    return xar::game::ReadArrangeMarriageChoicesResult::unavailable;
  }
  xar::game::ArrangeMarriageResult submit_arrange_marriage(
      const xar::game::ArrangeMarriageChoice &) const noexcept override {
    return xar::game::ArrangeMarriageResult::unavailable;
  }
  xar::game::EnforceDemandsResult
  submit_enforce_demands(std::int32_t) const noexcept override {
    return xar::game::EnforceDemandsResult::unavailable;
  }
  xar::game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<xar::game::ArmyStrengthSnapshot> &output) const noexcept override {
    output.clear();
    return xar::game::ReadArmyStrengthsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsResult
  read_combat_simulation_inputs(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsV3Result
  read_combat_simulation_inputs_v3(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsV3Snapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsV3Result::unavailable;
  }
  xar::game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t,
      xar::game::WarTerminationOptionsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationOptionsResult::unavailable;
  }
  xar::game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t,
      xar::game::WarTerminationTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationTermsResult::unavailable;
  }
  xar::game::ReadWarTerminationExitTermsResult
  read_war_termination_exit_terms(
      std::int32_t,
      xar::game::WarTerminationExitTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationExitTermsResult::unavailable;
  }
  xar::game::SurrenderWarResult
  submit_surrender_war(std::int32_t) const noexcept override {
    return xar::game::SurrenderWarResult::unavailable;
  }
  xar::game::OfferWhitePeaceResult
  submit_offer_white_peace(std::int32_t) const noexcept override {
    return xar::game::OfferWhitePeaceResult::unavailable;
  }
private:
  const AdapterDescriptor &descriptor_;
};
void *gPlayer = nullptr;
std::size_t gReads = 0;
CoreBindings gBindings{};
void *LocalPlayer(void *) { return gPlayer; }
template<class T, class Buffer>
void Store(Buffer &buffer, std::size_t at, T value) {
  std::memcpy(buffer.data() + at, &value, sizeof(value));
}
bool ReadPrefix(const GameAdapter &, Snapshot &snapshot) noexcept {
  ++gReads;
  CoreSnapshotPrefix core{};
  if (!ReadCoreSnapshot(gBindings, core)) return false;
  snapshot = {};
  snapshot.date_raw = core.clock.date_raw;
  snapshot.speed = core.clock.speed;
  snapshot.paused = core.clock.paused;
  snapshot.player_id = core.local_player_id;
  snapshot.map_ready = core.map_ready;
  snapshot.has_played_character = core.has_played_character;
  snapshot.played_character_id = core.played_character_id;
  snapshot.played_character_alive = core.played_character_alive;
  return true;
}
} // namespace
#define CHECK(expression) do { if (!(expression)) { std::cerr << #expression << std::endl; return 1; } } while (false)


namespace {
struct Clocks { std::uint64_t wall=1000,mono=1000; } clocks;
std::uint64_t Wall(void *) noexcept { return clocks.wall; }
std::uint64_t Mono(void *) noexcept { return clocks.mono; }
std::size_t clones=0,queues=0,deletes=0,object_size=0;
bool reject=false,expire_on_clone=false;
std::array<std::byte,0x40> observed_command{};
void *Destroy(void *p,std::uint32_t flags) {
  if (flags!=1) std::abort(); ++deletes; delete[] static_cast<std::byte *>(p); return nullptr;
}
void **Clone(const void *source,void **out) {
  ++clones; auto *copy=new std::byte[object_size];
  std::memcpy(copy,source,object_size); *out=copy;
  if (expire_on_clone) clocks.wall=3000;
  return out;
}
bool Queue(void *,void **owned,std::uint32_t flags) {
  if (flags!=7 || owned==nullptr || *owned==nullptr) std::abort();
  ++queues; std::memcpy(observed_command.data(),*owned,object_size);
  Destroy(*owned,1); *owned=nullptr; return !reject;
}
unsigned exit_calls=0;
void NativeApplicationQuit(void *app) { ++exit_calls; static_cast<unsigned char *>(app)[0x89]=1; }
std::string Payload() {
  return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"control-fixture","step":"set-speed-3","expected_revision":0,"core_control_deadline_unix_ms":2000,"core_clock_control":{"schema":"ck3_1210_core_clock_control_v1","game_version":"1.21.0","executable_sha256":")")+
      kExecutableSha256+R"(","adapter_id":"ck3-1.21.0-msvc-x64","backend":"ck3-1.21.0-native-headless-main-thread","date_raw":123456,"speed":5,"paused":true,"local_player_id":7,"map_ready":true,"has_played_character":true,"played_character_id":16777217,"played_character_alive":true},"arguments":{}})";
}
std::string Changed(std::string text,std::string_view from,std::string_view to) {
  const auto at=text.find(from); if (at==std::string::npos) std::abort();
  text.replace(at,from.size(),to); return text;
}
} // namespace
int main() {
  using namespace xar::ck3_1210;
  constexpr std::int32_t id = 0x01000001;
  std::array<std::byte, 0x74> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1E0> character{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x20> slots{};
  Store(state, 8, std::int32_t{123456}); Store(state, 0x70, std::int32_t{4});
  // State +A0 requires the complete fixture buffer, separate from clock span.
  std::vector<std::byte> complete_state(0xA8);
  std::memcpy(complete_state.data(), state.data(), state.size());
  Store(complete_state, 0xA0, data.data());
  Store(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
  Store(players, 0x1F0, std::int32_t{7}); Store(player, 0x70, std::int32_t{7});
  Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
  Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
  Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, id);
  Store(character, 0x18, id); Store(storage, 0x20, slots.data());
  Store(storage, 0x2C, std::int32_t{2}); Store(slots, 0x18, character.data());
  void *gs = complete_state.data(), *js = jomini.data(), *ss = storage.data();
  gPlayer = player.data(); gBindings = {true, &gs, &js, &ss, &LocalPlayer};

  CoreSnapshotPrefix actual{}; CHECK(ReadCoreSnapshot(gBindings,actual));
  xar::game::Snapshot copy{}; CHECK(ReadPrefix(FixtureAdapter(kDescriptor),copy));
  CHECK(gReads==1 && copy.played_character_id==id);
  CoreControlRequestV1 parsed{};
  auto raw=Payload(); CHECK(ParseCoreControlRequestV1(raw,parsed));
  raw.assign(12000,'x'); CHECK(parsed.step=="set-speed-3");
  CHECK(EqualCorePrefixV1(parsed.expected,actual));
  for (const auto &bad : {
      Changed(Payload(),"1.21.0\"","1.21.0.0\""),
      Changed(Payload(),"\"expected_revision\":0","\"expected_revision\":1"),
      Changed(Payload(),"\"speed\":5","\"speed\":5,\"speed\":5"),
      Changed(Payload(),"\"date_raw\":123456","\"date_raw\":123456.0"),
      Changed(Payload(),"\"date_raw\":123456","\"unknown\":0,\"date_raw\":123456"),
      Changed(Payload(),",\"core_control_deadline_unix_ms\":2000","")}) {
    CoreControlRequestV1 invalid{}; CHECK(!ParseCoreControlRequestV1(bad,invalid));
  }
  auto exit_payload=Changed(Changed(Changed(Payload(),"set-speed-3",kApplicationExitStepV1),
      "core_clock_control", "core_application_exit"),kCoreControlSchemaV1,kApplicationExitSchemaV1);
  CoreControlRequestV1 exit_request{};
  CHECK(ParseCoreControlRequestV1(exit_payload,exit_request));
  CHECK(exit_request.operation==CoreControlOperationV1::application_exit);
  CHECK(!ParseCoreControlRequestV1(Changed(Payload(),"set-speed-3",kApplicationExitStepV1),exit_request));
  CHECK(!ParseCoreControlRequestV1(Changed(exit_payload,kApplicationExitStepV1,"pause-map"),exit_request));
  CHECK(ParseCoreControlRequestV1(exit_payload,exit_request));
  FixtureAdapter adapter(kDescriptor);
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id=GetCurrentThreadId(); stamp.pump_epoch=1;
  stamp.tls_initialized=1; stamp.tls_main_thread_marker=1; stamp.tls_context=1;
  stamp.game_state=reinterpret_cast<std::uintptr_t>(gs);
  stamp.jomini_state=reinterpret_cast<std::uintptr_t>(js);
  stamp.date_raw=actual.clock.date_raw; stamp.paused=actual.clock.paused;
  std::array<std::uintptr_t,9> table{};
  table[0]=reinterpret_cast<std::uintptr_t>(&Destroy);
  table[8]=reinterpret_cast<std::uintptr_t>(&Clone);
  const auto vtable=reinterpret_cast<std::uintptr_t>(table.data());
  std::int32_t speed_count=5;
  CommandBindings commands{true,&queues,&Queue,vtable,1,vtable,1,vtable,1,&speed_count};
  CoreControlContextV1 context{};
  const auto reset=[&]() {
    context={}; clocks={}; clones=queues=deletes=0; reject=expire_on_clone=false;
    object_size=sizeof(TimeCommand);
    context.game=&adapter; context.core=gBindings; context.commands=commands;
    context.request=parsed; context.mailbox=&mailbox; context.ticket.sequence=1;
    context.wall_clock=&Wall; context.monotonic_clock=&Mono;
    mailbox.state.store(xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
    mailbox.owner_thread_id.store(stamp.thread_id); mailbox.owner_verified_pump_epochs.store(2);
    mailbox.failure_flags.store(0); mailbox.stop_requested.store(false);
    mailbox.published_sequence.store(1); mailbox.executor.store(&ExecuteCoreControlMailboxV1);
    mailbox.executor_context=&context; mailbox.iat_hook_installed.store(true);
    (void)xar::ck3_11906::RegisterMainThreadTimelineExecutorsV1(
        mailbox,&ExecuteCoreFrameMailboxV1,&ExecuteCoreControlMailboxV1);
    ArmCoreControlDeadlineV1(context);
  };
  reset(); CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::submitted && queues==1 && clones==1 && deletes==1);
  CHECK(context.result.effect_attempted);
  std::int32_t value=0; std::memcpy(&value,observed_command.data()+0x20,4); CHECK(value==2);
  const auto ack=SerializeCoreControlCommandResultV1("control-fixture",context.request.step,context.result);
  CHECK(ack.find("physical_save_confirmed\":false")!=std::string::npos);
  reset(); reject=true; CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::rejected && queues==1 && deletes==1);
  reset(); clocks.wall=3000; CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::expired && queues==0 && clones==0);
  reset(); expire_on_clone=true; CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::expired && queues==0 && clones==1 && deletes==1);
  CHECK(!context.result.effect_attempted);
  reset(); clocks.wall=500; clocks.mono=3000; CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::expired && queues==0);
  for (int field=0;field<8;++field) {
    reset(); auto &e=context.request.expected;
    if(field==0) ++e.clock.date_raw; if(field==1) --e.clock.speed;
    if(field==2) e.clock.paused=!e.clock.paused; if(field==3) ++e.local_player_id;
    if(field==4) e.map_ready=!e.map_ready; if(field==5) e.has_played_character=false;
    if(field==6) ++e.played_character_id; if(field==7) e.played_character_alive=false;
    CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
    CHECK(context.result.status==CoreControlStatusV1::stale && clones==0 && queues==0);
  }
  reset(); speed_count=2; CHECK(ExecuteCoreControlMailboxV1(&context,stamp)); CHECK(queues==0 && clones==0); speed_count=5;
  reset(); context.request.operation=CoreControlOperationV1::pause; context.request.step="pause-map";
  CHECK(ExecuteCoreControlMailboxV1(&context,stamp)); CHECK(context.result.status==CoreControlStatusV1::already_satisfied && clones==0);
  reset(); context.request.operation=CoreControlOperationV1::resume; context.request.step="resume-map";
  CHECK(ExecuteCoreControlMailboxV1(&context,stamp)); CHECK(context.result.status==CoreControlStatusV1::submitted && queues==1);
  CHECK(observed_command[8]==std::byte{8} && observed_command[0x24]==std::byte{});
  reset(); context.request.operation=CoreControlOperationV1::save; context.request.step="save-checkpoint";
  object_size=sizeof(AutoSaveCommand); CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::submitted && queues==1);
  CHECK(observed_command[8]==std::byte{0x20});
  CHECK(std::memcmp(observed_command.data()+0x20,kCheckpointSaveName,sizeof(kCheckpointSaveName))==0);
  CHECK(!BindCommandImage(0x140000000,"old-hash").enabled);
  std::array<unsigned char,0x100> app{};void *app_slot=app.data();
  const std::uintptr_t app_vtable=0x12340;std::memcpy(app.data(),&app_vtable,sizeof(app_vtable));
  ApplicationExitSessionV1 exit_session;
  const auto arm_exit=[&]() {
    context.request=exit_request;
    context.application_exit={true,&app_slot,&NativeApplicationQuit,app_vtable,app_vtable+8};
    context.application_exit_session=&exit_session;
  };
  reset();arm_exit();CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::exit_requested && exit_calls==1 &&
      context.result.effect_attempted && queues==0 && clones==0);
  CoreControlResultV1 consumed{};consumed.status=CoreControlStatusV1::exit_claim_consumed;
  const auto consumed_ack=SerializeCoreControlCommandResultV1("exit-consumed",kApplicationExitStepV1,consumed);
  CHECK(consumed_ack.find("accepted\":false")!=std::string::npos);
  const auto exit_ack=SerializeCoreControlCommandResultV1("exit-fixture",kApplicationExitStepV1,context.result);
  CHECK(exit_ack.find("normal_exit_confirmed\":false")!=std::string::npos);
  CHECK(exit_ack.find("dispatch_status\":\"requested")!=std::string::npos);
  reset();arm_exit();CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::exit_already_requested && exit_calls==1 && !context.result.effect_attempted);
  ApplicationExitSessionV1 expired_session;
  reset();arm_exit();context.application_exit_session=&expired_session;clocks.wall=3000;
  CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::expired && !expired_session.claimed.load() && exit_calls==1);
  // A real Partial with no actor/map still grants no gameplay command, but
  // the same owner-held application can request its own normal shutdown.
  ApplicationExitSessionV1 menu_session;app[0x89]=0;Store(player,0x70,std::int32_t{-1});
  CoreSnapshotPrefix menu{};CHECK(ReadCoreSnapshot(gBindings,menu));
  CHECK(!menu.map_ready && !menu.has_played_character);
  reset();arm_exit();context.request.expected=menu;context.application_exit_session=&menu_session;
  CHECK(ExecuteCoreControlMailboxV1(&context,stamp));
  CHECK(context.result.status==CoreControlStatusV1::exit_requested && exit_calls==2 && queues==0);
  Store(player,0x70,std::int32_t{7});
  std::cout<<exit_ack<<std::endl;
  std::cout<<ack<<std::endl;
  std::cout<<"PASS strict claim ownership/lifetime; all prefix fields; monotonic expiry; native clone/queue cleanup; speed count; save shape (NoGame)"<<std::endl;
  return 0;
}
