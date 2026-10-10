#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_clergy_appointment.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"
#include "clergy_mode0_current_query_wire_12004.hpp"

#include <windows.h>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace {
namespace old = xar::ck3_12002;
namespace actual = xar::ck3_12004;
namespace clergy = actual::religion::clergy;
namespace api = xar::ck3_11906;
namespace game = xar::game;
constexpr std::int32_t owner_id = 0x01000005;
constexpr std::int32_t candidate_id = 0x02000010;
constexpr std::int32_t incumbent_id = 0x03000020;
constexpr std::int32_t task_id = 0x04000007;
constexpr std::int32_t date_input = 53290200;
constexpr std::uint64_t public_input = 37, native_input = 91, epoch_input = 901;
unsigned checks = 0;
void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
  ++checks;
}
template<std::size_t N> using Bytes = std::array<std::byte,N>;
template<class Buffer,class T> void Put(Buffer &buffer, std::size_t offset, T value) {
  if (offset > buffer.size() || sizeof(T) > buffer.size() - offset)
    throw std::runtime_error("03e fixture write out of owned bounds");
  std::memcpy(buffer.data()+offset, &value, sizeof(value));
}
struct Fixture {
  DWORD owner_thread = GetCurrentThreadId();
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void*,1> entries{entry.data()};
  Bytes<0x30> character_storage{}, task_storage{};
  Bytes<64 * 0x10> character_slots{};
  Bytes<16 * 0x10> task_slots{};
  Bytes<0x1D8> owner{},candidate{},incumbent{};
  Bytes<0x240> landed{};
  Bytes<0x80> task{},type{};
  Bytes<0x2400> position{};
  std::array<std::int32_t,1> task_ids{task_id};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *character_pointer = character_storage.data(), *task_pointer = task_storage.data();
  unsigned fire_calls = 0, predicate_calls = 0, memory_reads = 0;
  bool callback_arguments_match = true;
  Fixture() {
    Put(state,actual::kGameStateDateOffset,date_input);
    Put(state,actual::kGameStateSpeedOffset,std::int32_t{2});
    Put(state,actual::kGameStateDataOffset,data.data());
    Put(jomini,actual::kJominiPlayersOffset,players.data());
    jomini[actual::kJominiPausedOffset]=std::byte{1};
    Put(players,actual::kPlayersLocalPlayerIdOffset,std::int32_t{7});
    Put(player,actual::kPlayerIdOffset,std::int32_t{7});
    Put(data,actual::kPlayerCharacterManagerOffset+actual::kPlayerManagerEntriesOffset,entries.data());
    Put(data,actual::kPlayerCharacterManagerOffset+actual::kPlayerManagerCountOffset,std::int32_t{1});
    Put(entry,actual::kPlayerEntryLocalPlayerIdOffset,std::int32_t{7});
    Put(entry,actual::kPlayerEntryCharacterIdOffset,owner_id);
    Put(character_storage,actual::kCharacterStorageSlotsOffset,character_slots.data());
    Put(character_storage,actual::kCharacterStorageCapacityOffset,std::int32_t{64});
    Put(character_slots,5U*0x10U+8U,owner.data());
    Put(character_slots,16U*0x10U+8U,candidate.data());
    Put(character_slots,32U*0x10U+8U,incumbent.data());
    Put(owner,actual::kCharacterFullIdOffset,owner_id);
    Put(candidate,actual::kCharacterFullIdOffset,candidate_id);
    Put(incumbent,actual::kCharacterFullIdOffset,incumbent_id);
    Put(owner,clergy::kCharacterRiteOffset,std::uint32_t{0});
    Put(candidate,clergy::kCharacterRiteOffset,std::uint32_t{0});
    Put(owner,clergy::kLandedOffset,landed.data());
    Put(landed,clergy::kTaskIdsOffset,task_ids.data());
    Put(landed,clergy::kTaskCountOffset,std::int32_t{1});
    Put(task_storage,0x20,task_slots.data());
    Put(task_storage,0x2C,std::int32_t{16});
    Put(task_slots,7U*0x10U+8U,task.data());
    Put(task,clergy::kTaskIdentityOffset,task_id);
    Put(task,clergy::kTaskTypeOffset,type.data());
    Put(task,clergy::kTaskOwnerOffset,owner_id);
    Put(task,clergy::kTaskIncumbentOffset,incumbent_id);
    Put(task,0x30,std::uint32_t{static_cast<std::uint32_t>(incumbent_id)});
    Put(type,clergy::kTypePositionOffset,position.data());
    // This newly reached Initial branch makes20g demand09 exactly once.
    // Current original snapshot identity is missing, so09 must return unknown.
    position[0x2374]=std::byte{0};
    Put(position,0x1E38+0x4C,std::uint32_t{1});
  }
  bool Copy(const void *address,void *out,std::size_t size) noexcept {
    ++memory_reads;
    const auto at=reinterpret_cast<std::uintptr_t>(address);
    const bool task_slot=at==reinterpret_cast<std::uintptr_t>(&task_pointer) && size<=sizeof(task_pointer);
    const auto inside=[&](const auto &buffer) {
      const auto first=reinterpret_cast<std::uintptr_t>(buffer.data());
      const auto byte_count=buffer.size()*sizeof(buffer[0]);
      return at>=first && at-first<=byte_count && size<=byte_count-(at-first);
    };
    if (!address || !out || !(task_slot||inside(state)||inside(jomini)||inside(players)||inside(player)||inside(data)||
        inside(entry)||inside(entries)||inside(character_storage)||inside(task_storage)||inside(character_slots)||
        inside(task_slots)||inside(owner)||inside(candidate)||inside(incumbent)||inside(landed)||inside(task)||
        inside(type)||inside(position)||inside(task_ids))) return false;
    std::memcpy(out,address,size); return true;
  }
};
Fixture *active=nullptr;
void *Player(void*) { return active->player.data(); }
void *CourtOwner(void *candidate) {
  active->callback_arguments_match &= candidate==active->candidate.data();
  return active->owner.data();
}
const void *PositionTask(const void *owner,const std::string *key) {
  active->callback_arguments_match &= owner==active->owner.data() && key && *key==clergy::kPositionKey;
  return active->task.data();
}
bool ValidPosition(void *position,std::int32_t owner) {
  ++active->predicate_calls;
  active->callback_arguments_match &= position==active->position.data() && owner==owner_id;
  return true;
}
bool ValidCharacter(void *position,std::int32_t candidate) {
  ++active->predicate_calls;
  active->callback_arguments_match &= position==active->position.data() && candidate==candidate_id;
  return true;
}
bool CanReassign(void *task,void *tooltip) {
  ++active->predicate_calls;
  active->callback_arguments_match &= task==active->task.data() && !tooltip;
  return false;
}
bool CanFire(void *owner,void *incumbent,void *task,std::uint32_t mode,void *tooltip) {
  ++active->fire_calls;
  active->callback_arguments_match &= owner==active->owner.data() && incumbent==active->incumbent.data() &&
      task==active->task.data() && mode==0U && !tooltip && GetCurrentThreadId()==active->owner_thread;
  return true;
}
bool Read(void *context,const void *address,void *out,std::size_t size) noexcept {
  return static_cast<Fixture*>(context)->Copy(address,out,size);
}
actual::CoreBindings Core(Fixture &f) {
  return {true,&f.state_pointer,&f.jomini_pointer,&f.character_pointer,&Player};
}
clergy::Bindings Bind(Fixture &f) {
  clergy::Bindings b{}; b.enabled=true; b.offline_fixture=true;
  b.module_base=0; b.executable_sha256=actual::kExecutableSha256;
  b.core=Core(f); b.task_storage_slot=&f.task_pointer;
  b.position_lookup=&PositionTask; b.valid_position=&ValidPosition; b.valid_character=&ValidCharacter;
  b.can_reassign=&CanReassign; b.can_fire=&CanFire; b.court_owner=&CourtOwner;
  b.read_context=&f; b.read_memory=&Read; return b;
}
void *tls_context=nullptr;
void *__fastcall Tls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized=1;
  std::uintptr_t unused_rng=0;
  Pump(Fixture &f,api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20]=std::byte{1}; tls_context=tls.data();
    mailbox.global_rng_wrapper_slot=reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot=reinterpret_cast<std::uintptr_t>(&f.jomini_pointer);
    mailbox.game_state_slot=reinterpret_cast<std::uintptr_t>(&f.state_pointer);
    mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter=&Tls; mailbox.executor_submission_enabled=true;
    mailbox.permitted_executor_clergy12002=&old::ExecutePlayerClergyAppointmentMailbox12002;
    mailbox.iat_hook_installed=true; mailbox.state=api::MainThreadQueryMailboxStateV1::idle;
    mailbox.pump_epochs=epoch_input-3;
    for (unsigned n=0;n<2;++n)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());
  }
  ~Pump() { tls_context=nullptr; }
};
void Write(const std::filesystem::path &path,const std::string &text) {
  std::ofstream out(path,std::ios::binary); out<<text;
  if (!out) throw std::runtime_error("03e cannot write actual new fixture bytes");
}
}

int main(int argc,char **argv) {
  try {
    if (argc!=2 && argc!=3) throw std::runtime_error("03e requires output directory and optional exact resume");
    const bool resume=argc==3 && std::string(argv[2])=="resume-after-query-guards";
    if (argc==3 && !resume) throw std::runtime_error("03e unsupported resume");
    const auto Guard=[&](bool value,const char *reason) {
      if (!value) throw std::runtime_error(reason);
      if (!resume) ++checks;
    };
    const std::filesystem::path output(argv[1]);
    if (!std::filesystem::is_directory(output)) throw std::runtime_error("03e output directory must be pre-admitted");
    auto fixture=std::make_unique<Fixture>(); active=fixture.get();
    game::Ck3_12004AdapterBindings bindings{}; bindings.core=Core(*fixture);
    auto adapter=game::CreateCk3_12004AdapterFromBindings(std::move(bindings));
    Guard(adapter && adapter->enabled(),"03e actual production adapter from fresh owned input");
    game::Snapshot frame{};
    Guard(game::ReadCk3_12002TimelineCoreSnapshot(*adapter,frame) && frame.paused && frame.map_ready &&
        frame.played_character_alive && frame.played_character_id==owner_id,"03e source-derived core frame");
    api::MainThreadQueryMailboxV1 mailbox{}; Pump pump(*fixture,mailbox);
    old::PlayerClergyAppointmentMailboxContext12002 query{};
    const auto request="{\"candidate_character_id\":"+std::to_string(candidate_id)+
        ",\"expected_revision\":"+std::to_string(native_input)+",\"expected_public_revision\":"+std::to_string(public_input)+"}";
    Guard(old::ParsePlayerClergyAppointmentRequest12002(request,query.request),"03e original request parser");
    query.envelope.game=adapter.get(); query.envelope.mailbox=&mailbox;
    query.envelope.expected_snapshot=frame; query.envelope.expected_snapshot_revision=native_input;
    query.bindings12004=Bind(*fixture);
    std::atomic<bool> done=false;
    bool observed=false,drained=false; std::string original_wire,failure;
    std::thread worker([&] {
      observed=old::RunPlayerClergyAppointmentMailbox12002(query,"clergy-source-new-query-01",original_wire,failure);
      done.store(true,std::memory_order_release);
    });
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(6);
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now()<deadline) {
      if (mailbox.state.load(std::memory_order_acquire)==api::MainThreadQueryMailboxStateV1::queued)
        drained=api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    worker.join();
    Guard(observed && drained && failure.empty() && query.completed && query.envelope.frame_stable,
            "03e existing query enters and finishes once");
    Guard(mailbox.executed_requests==1U && mailbox.state==api::MainThreadQueryMailboxStateV1::idle,
            "03e one executor ticket completed and reclaimed");
    Write(output/"ACTUAL-ORIGINAL-CALLBACKS.json","{\"fire_calls\":"+std::to_string(fixture->fire_calls)+
        ",\"predicate_calls\":"+std::to_string(fixture->predicate_calls)+",\"arguments_match\":"+
        (fixture->callback_arguments_match?"true":"false")+",\"observation_available\":"+
        (query.observation.available?"true":"false")+",\"failure_enum\":"+
        std::to_string(static_cast<unsigned>(query.observation.failure))+"}");
    Require(fixture->fire_calls==1U && fixture->predicate_calls==3U && fixture->callback_arguments_match,
            "03e original aggregate CanFire once with unchanged arguments");
    Require(query.observation.available && query.observation.native_can_fire==true &&
        query.observation.native_can_reassign==false,"03e original aggregate stays independent");
    Require(query.mode0_source_capture.packet.has_value(),"03e same read creates independent packet");
    const auto &packet=*query.mode0_source_capture.packet;
    Require(packet.source_projected && !packet.source_ready && !packet.raw_al,
            "03e unavailable Initial input remains unavailable software AL");
    Require(packet.generic_trigger.software_adapter_invoked && packet.generic_trigger.scope_root_word==std::uint16_t{4} &&
        packet.generic_trigger.scope_full_id_payload==static_cast<std::uint64_t>(owner_id),
            "03e 20g reaches09 once with WORD4 and full owner payload");
    Require(!packet.source_read_frame.frame_identity && !packet.source_read_frame.snapshot_identity &&
        !packet.source_read_frame.ready && !packet.generic_trigger.copied_frame_ready &&
        !packet.generic_trigger.source_value_ready && !packet.generic_trigger.raw_al,
            "03e real original identity gap retains dynamic unknown");
    Require(query.mode0_source_capture.borrowed_frame==nullptr && packet.input_scope_confirmed,
            "03e final guards confirm scope and borrowed frame is cleared");
    const auto wire=old::SerializeActualClergyMode0QueryForNewCase12004(query,"clergy-source-new-query-01");
    Require(wire==original_wire,"03e new export retains full original production query bytes");
    Write(output/"ACTUAL-CLERGY-CURRENT-WIRE.json",wire);
    Write(output/"ACTUAL-QUERY-FRAME-RECEIPT.json",old::SerializeActualClergyQueryFrameReceiptForNewCase12004(query));
    Write(output/"NATIVE-SOFTWARE-CONTEXT-RESULT.json","{\"status\":\"GREEN\",\"checks\":"+std::to_string(checks)+
        ",\"owned_software_query_contexts\":1,\"original_CanFire_callback_invocations\":1,"
        "\"Game_queries\":0,\"native_getter_calls\":0,\"old62_or_M4_replays\":0}");
    std::cout<<"{\"status\":\"GREEN\",\"checks\":"<<checks<<",\"wire_bytes\":"<<wire.size()<<"}\n";
    active=nullptr; return 0;
  } catch (const std::exception &error) {
    std::cerr<<"03e RED: "<<error.what()<<'\n'; active=nullptr; return 1;
  }
}
