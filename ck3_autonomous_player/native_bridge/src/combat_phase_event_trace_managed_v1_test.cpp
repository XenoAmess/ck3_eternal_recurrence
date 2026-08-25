#include "xar_bridge/combat_phase_event_trace_managed_v1.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <string_view>

namespace {

using namespace xar::ck3_11906;

template <typename T, std::size_t Size>
void Store(std::array<std::byte, Size> &storage, std::size_t offset,
           T value) {
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <typename T>
void Store(void *storage, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(storage) + offset, &value,
              sizeof(value));
}

bool Fail(std::string_view reason) {
  std::cerr << reason << '\n';
  return false;
}

template <std::size_t Capacity>
struct ComponentStore {
  std::array<std::byte, 0x30> header{};
  std::array<std::array<std::byte, 0x10>, Capacity> rows{};
  void *root = header.data();

  ComponentStore() {
    Store(header, 0x20, reinterpret_cast<void *>(rows.data()));
    Store(header, 0x2C, static_cast<std::int32_t>(Capacity));
  }

  void Add(std::int32_t full_id, void *object) {
    const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
    Store(rows[index], 0x08, object);
  }

  void **Slot() { return &root; }
};

constexpr std::array<std::uint8_t, 15> kSchedulePrologue{
    0x4C, 0x89, 0x44, 0x24, 0x18, 0x48, 0x89, 0x54,
    0x24, 0x10, 0x53, 0x56, 0x57, 0x41, 0x55};
constexpr std::array<std::uint8_t, 15> kFirePrologue{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
    0x24, 0x10, 0x48, 0x89, 0x7C, 0x24, 0x18};
constexpr std::array<std::uint8_t, 5> kScheduleSide0Call{
    0xE8, 0xBC, 0xD1, 0xBC, 0xFF};
constexpr std::array<std::uint8_t, 5> kScheduleSide1Call{
    0xE8, 0xA4, 0xD1, 0xBC, 0xFF};
constexpr std::array<std::uint8_t, 5> kFireSide0Call{
    0xE8, 0xF9, 0x03, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 5> kFireSide1Call{
    0xE8, 0xF1, 0x03, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 5> kFireTailJump{
    0xE9, 0xAD, 0xF5, 0xFF, 0xFF};

struct DetourMemory {
  void *schedule_page = nullptr;
  void *fire_page = nullptr;
  std::uint32_t live_allocations = 0;

  ~DetourMemory() {
    if (schedule_page != nullptr) VirtualFree(schedule_page, 0, MEM_RELEASE);
    if (fire_page != nullptr) VirtualFree(fire_page, 0, MEM_RELEASE);
  }
};

void *FixtureAlloc(void *opaque, std::size_t size, DWORD type,
                   DWORD protection) noexcept {
  auto &memory = *static_cast<DetourMemory *>(opaque);
  void *const result = VirtualAlloc(nullptr, size, type, protection);
  if (result != nullptr) ++memory.live_allocations;
  return result;
}

bool FixtureFree(void *opaque, void *address, std::size_t size,
                 DWORD type) noexcept {
  auto &memory = *static_cast<DetourMemory *>(opaque);
  const bool freed = VirtualFree(address, size, type) != FALSE;
  if (freed && memory.live_allocations != 0) --memory.live_allocations;
  return freed;
}

bool FixtureProtect(void *, void *address, std::size_t size, DWORD desired,
                    DWORD &previous) noexcept {
  return VirtualProtect(address, size, desired, &previous) != FALSE;
}

bool FixtureFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

struct NativeFixture {
  static constexpr std::uintptr_t kModule = 0x0000000140000000ULL;
  static constexpr std::int32_t kCombatId = 0x01000001;
  static constexpr std::int32_t kBattleResultId = 0x01000002;
  static constexpr std::array<std::int32_t, 2> kArmyIds{11, 21};
  static constexpr std::array<std::int32_t, 2> kRegimentIds{31, 41};
  static constexpr std::array<std::int32_t, 2> kCharacterIds{51, 61};
  static constexpr std::int32_t kAccoladeId = 31;
  static constexpr std::int32_t kBeforeDate = 53'175'816;

  ComponentStore<64> combat_store{};
  ComponentStore<64> army_store{};
  ComponentStore<64> regiment_store{};
  ComponentStore<64> character_store{};
  ComponentStore<64> battle_store{};
  ComponentStore<64> accolade_store{};
  std::array<std::byte, 0x720> combat{};
  std::array<std::array<std::byte, 0x130>, 2> armies{};
  std::array<std::array<std::byte, 0x150>, 2> regiments{};
  std::array<std::array<std::byte, 0x1D0>, 2> characters{};
  std::array<std::array<std::byte, 0x100>, 2> character_links{};
  std::array<std::byte, 0x570> accolade_link{};
  std::array<std::byte, 0xB8> accolade{};
  std::array<std::array<std::byte, 0x60>, 2> knight_rows{};
  std::array<std::int32_t, 2> side_army_ids{kArmyIds};
  std::array<std::byte, 0x1B0> battle_result{};
  std::array<std::byte, 0x10> date_object{};
  std::array<std::byte, 0x18> rng_wrapper{};
  std::array<std::byte, 0x18> rng_state{};
  std::array<std::byte, 8> event_database{};
  std::array<std::byte, 8> battle_event_vtable{};
  std::array<std::int64_t, 3> thresholds{100'000, 500'000, 1'000'000};
  std::uintptr_t phase_database_slot = 0;
  std::uintptr_t date_slot = 0;
  std::uintptr_t rng_wrapper_slot = 0;
  std::uintptr_t threshold_data_slot = 0;
  std::int32_t threshold_count_slot = 3;
  std::array<std::uint32_t, 2> schedule_rng{700, 701};
  Bindings bindings{};
  CombatPhaseEventTracePlanEnvironmentV1 plan_environment{};

  DetourMemory detour_memory{};
  std::array<std::uint8_t, 5> schedule_side0_call{kScheduleSide0Call};
  std::array<std::uint8_t, 5> schedule_side1_call{kScheduleSide1Call};
  std::array<std::uint8_t, 5> fire_side0_call{kFireSide0Call};
  std::array<std::uint8_t, 5> fire_side1_call{kFireSide1Call};
  std::array<std::uint8_t, 5> fire_tail_jump{kFireTailJump};
  CombatPhaseEventTraceDetourEnvironmentV1 detour_environment{};

  NativeFixture() {
    const auto combat_pointer =
        reinterpret_cast<std::uintptr_t>(combat.data());
    const std::array<std::uintptr_t, 2> sides{
        combat_pointer + 0x20, combat_pointer + 0x368};
    Store(combat, 0x08, kCombatId);
    Store(combat, 0x6B0, std::int32_t{1});
    Store(combat, 0x6B4, std::int32_t{4});
    Store(combat, 0x6C8, std::int64_t{300'000});
    Store(combat, 0x6D0, std::int32_t{2});
    Store(combat, 0x6D4, std::int32_t{5});
    Store(combat, 0x6E0, std::int32_t{-1});
    Store(combat, 0x708, kBattleResultId);
    Store(combat, 0x710, std::int64_t{600'000});
    for (std::size_t index = 0; index < 2; ++index) {
      void *const side = reinterpret_cast<void *>(sides[index]);
      Store(side, 0x10,
            reinterpret_cast<std::uintptr_t>(&side_army_ids[index]));
      Store(side, 0x18, std::int32_t{1});
      Store(side, 0x1C, std::int32_t{1});
      Store(side, 0x40,
            reinterpret_cast<std::uintptr_t>(knight_rows[index].data()));
      Store(side, 0x48, std::int32_t{1});
      Store(side, 0x4C, std::int32_t{1});
      Store(side, 0x74, kCharacterIds[index]);
      Store(side, 0x98,
            std::int64_t{1'000'000 + static_cast<std::int64_t>(index)});
      Store(side, 0xA0,
            std::int64_t{500'000 + static_cast<std::int64_t>(index)});
      Store(side, 0xB8, combat_pointer);
      Store(side, 0xD8, std::uintptr_t{0});
      Store(side, 0xE0, std::int32_t{0});
      Store(side, 0xE4, std::int32_t{0});
      Store(side, 0xF0,
            reinterpret_cast<std::uintptr_t>(event_database.data()) + index);

      Store(armies[index], 0x10, kArmyIds[index]);
      Store(armies[index], 0x120, kCharacterIds[index]);
      Store(armies[index], 0x128, kCombatId);
      Store(knight_rows[index], 0x08, kRegimentIds[index]);
      Store(regiments[index], 0x10, kRegimentIds[index]);
      Store(regiments[index], 0x140, kArmyIds[index]);
      Store(regiments[index], 0x148, kCharacterIds[index]);
      Store(characters[index], 0x18, kCharacterIds[index]);
      Store(characters[index], 0xD8,
            std::int32_t{10 + static_cast<std::int32_t>(index)});
      Store(characters[index], 0xE4,
            std::int32_t{8 + static_cast<std::int32_t>(index)});
      Store(characters[index], 0xE8,
            std::int32_t{15 + static_cast<std::int32_t>(index)});
      Store(character_links[index], 0xF8, kRegimentIds[index]);
      Store(characters[index], 0x1B0,
            reinterpret_cast<std::uintptr_t>(
                character_links[index].data()));
      army_store.Add(kArmyIds[index], armies[index].data());
      regiment_store.Add(kRegimentIds[index], regiments[index].data());
      character_store.Add(kCharacterIds[index], characters[index].data());
    }
    Store(battle_result, 0x08, kBattleResultId);
    Store(battle_result, 0x188, std::uintptr_t{0});
    Store(battle_result, 0x190, std::int32_t{0});
    Store(battle_result, 0x194, std::int32_t{0});
    Store(date_object, 0x08, kBeforeDate);
    Store(rng_wrapper, 0x00,
          reinterpret_cast<std::uintptr_t>(rng_state.data()));
    Store(rng_state, 0x08, std::uint32_t{100});
    Store(rng_state, 0x0C, std::uint32_t{0x12345678});
    Store(rng_state, 0x10, std::uint32_t{GetCurrentThreadId()});
    Store(accolade_link, 0x568, kAccoladeId);
    Store(characters[0], 0x1A8,
          reinterpret_cast<std::uintptr_t>(accolade_link.data()));
    Store(accolade, 0x08, kAccoladeId);
    Store(accolade, 0x70, std::int32_t{901});
    Store(accolade, 0xB0, std::int64_t{600'000});
    phase_database_slot =
        reinterpret_cast<std::uintptr_t>(event_database.data());
    date_slot = reinterpret_cast<std::uintptr_t>(date_object.data());
    rng_wrapper_slot =
        reinterpret_cast<std::uintptr_t>(rng_wrapper.data());
    threshold_data_slot =
        reinterpret_cast<std::uintptr_t>(thresholds.data());
    combat_store.Add(kCombatId, combat.data());
    battle_store.Add(kBattleResultId, battle_result.data());
    accolade_store.Add(kAccoladeId, accolade.data());

    bindings.enabled = true;
    bindings.combat_storage_slot = combat_store.Slot();
    bindings.army_internal_storage_slot = army_store.Slot();
    bindings.regiment_storage_slot = regiment_store.Slot();
    bindings.character_storage_slot = character_store.Slot();

    plan_environment.exact_build_admitted = true;
    plan_environment.offline_fixture = true;
    plan_environment.module_base = kModule;
    plan_environment.phase_event_database_slot_override =
        reinterpret_cast<std::uintptr_t>(&phase_database_slot);
    plan_environment.current_date_slot_override =
        reinterpret_cast<std::uintptr_t>(&date_slot);
    plan_environment.global_rng_wrapper_slot_override =
        reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot);
    plan_environment.battle_result_storage_slot_override =
        battle_store.Slot();
    plan_environment.battle_result_fallback_override = this;
    plan_environment.accolade_storage_slot_override = accolade_store.Slot();
    plan_environment.accolade_fallback_override = this;
    plan_environment.battle_event_vtable_override =
        reinterpret_cast<std::uintptr_t>(battle_event_vtable.data());
    plan_environment.accolade_rank_threshold_data_slot_override =
        reinterpret_cast<std::uintptr_t>(&threshold_data_slot);
    plan_environment.accolade_rank_threshold_count_slot_override =
        reinterpret_cast<std::uintptr_t>(&threshold_count_slot);

    SYSTEM_INFO information{};
    GetSystemInfo(&information);
    const auto page_size = static_cast<std::size_t>(information.dwPageSize);
    detour_memory.schedule_page = VirtualAlloc(
        nullptr, page_size, MEM_RESERVE | MEM_COMMIT,
        PAGE_EXECUTE_READWRITE);
    detour_memory.fire_page = VirtualAlloc(
        nullptr, page_size, MEM_RESERVE | MEM_COMMIT,
        PAGE_EXECUTE_READWRITE);
    if (detour_memory.schedule_page != nullptr &&
        detour_memory.fire_page != nullptr) {
      std::memcpy(detour_memory.schedule_page, kSchedulePrologue.data(),
                  kSchedulePrologue.size());
      std::memcpy(detour_memory.fire_page, kFirePrologue.data(),
                  kFirePrologue.size());
      DWORD ignored = 0;
      (void)VirtualProtect(detour_memory.schedule_page, page_size,
                           PAGE_EXECUTE_READ, &ignored);
      (void)VirtualProtect(detour_memory.fire_page, page_size,
                           PAGE_EXECUTE_READ, &ignored);
    }
    detour_environment.exact_build_admitted = true;
    detour_environment.offline_fixture = true;
    detour_environment.module_base = kModule;
    detour_environment.schedule_target_override =
        reinterpret_cast<std::uintptr_t>(detour_memory.schedule_page);
    detour_environment.fire_target_override =
        reinterpret_cast<std::uintptr_t>(detour_memory.fire_page);
    detour_environment.schedule_side0_call_override =
        reinterpret_cast<std::uintptr_t>(schedule_side0_call.data());
    detour_environment.schedule_side1_call_override =
        reinterpret_cast<std::uintptr_t>(schedule_side1_call.data());
    detour_environment.fire_side0_call_override =
        reinterpret_cast<std::uintptr_t>(fire_side0_call.data());
    detour_environment.fire_side1_call_override =
        reinterpret_cast<std::uintptr_t>(fire_side1_call.data());
    detour_environment.fire_tail_jump_override =
        reinterpret_cast<std::uintptr_t>(fire_tail_jump.data());
    detour_environment.memory_context = &detour_memory;
    detour_environment.virtual_alloc_override = &FixtureAlloc;
    detour_environment.virtual_free_override = &FixtureFree;
    detour_environment.virtual_protect_override = &FixtureProtect;
    detour_environment.flush_instruction_cache_override = &FixtureFlush;
  }

  void SetNextDay() {
    Store(date_object, 0x08, kBeforeDate + 24);
  }

  void SetPhaseDay(std::int32_t value) {
    Store(combat, 0x6B4, value);
  }
};

MainThreadExecutionStampV1 Stamp(std::uint64_t epoch,
                                 std::int32_t date_raw) {
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 2;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 3;
  stamp.game_state = 4;
  stamp.date_raw = date_raw;
  stamp.paused = true;
  return stamp;
}

template <typename Context>
void PrepareMailbox(MainThreadQueryMailboxV1 &mailbox, Context &context,
                    MainThreadQueryExecutorV1 executor,
                    std::uint64_t sequence) {
  context.mailbox = &mailbox;
  context.ticket.sequence = sequence;
  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = executor;
  mailbox.executor_context = &context;
}

bool PlanBuilderClosesPointers() {
  NativeFixture fixture;
  CombatPhaseEventTraceCapturePlanV1 plan{};
  if (BuildCombatPhaseEventTraceCapturePlanV1(
          fixture.bindings, fixture.plan_environment,
          NativeFixture::kCombatId, 77, plan) !=
      BuildCombatPhaseEventTraceCapturePlanV1Result::built) {
    return Fail("capture plan did not build");
  }
  if (plan.combat_id != NativeFixture::kCombatId ||
      plan.army_count != 2 || plan.regiment_count != 2 ||
      plan.character_count != 2 || plan.accolade_count != 1 ||
      plan.armies[0].full_id != NativeFixture::kArmyIds[0] ||
      plan.regiments[1].full_id != NativeFixture::kRegimentIds[1] ||
      plan.characters[0].full_id != NativeFixture::kCharacterIds[0] ||
      plan.accolades[0].accolade_id != NativeFixture::kAccoladeId ||
      plan.accolades[0].acclaimed_knight_character_id !=
          NativeFixture::kCharacterIds[0] ||
      plan.accolade_rank_threshold_count != 3) {
    return Fail("capture plan contents mismatch");
  }
  fixture.threshold_count_slot = 65;
  if (BuildCombatPhaseEventTraceCapturePlanV1(
          fixture.bindings, fixture.plan_environment,
          NativeFixture::kCombatId, 78, plan) !=
      BuildCombatPhaseEventTraceCapturePlanV1Result::capacity_exceeded) {
    return Fail("oversize threshold vector was not rejected");
  }
  return true;
}

bool ManagedBeginFinishProducesBoundedDto() {
  constexpr std::uint64_t token = 9001;
  NativeFixture fixture;
  if (fixture.detour_memory.schedule_page == nullptr ||
      fixture.detour_memory.fire_page == nullptr) {
    return Fail("detour pages unavailable");
  }
  MainThreadQueryMailboxV1 mailbox{};
  auto session = std::make_unique<CombatPhaseEventTraceManagedSessionV1>();
  CombatPhaseEventTraceBeginContextV1 begin{};
  begin.session = session.get();
  begin.bindings = &fixture.bindings;
  begin.plan_environment = fixture.plan_environment;
  begin.detour_environment = fixture.detour_environment;
  begin.combat_id = NativeFixture::kCombatId;
  begin.managed_daily_sequence_token = token;
  begin.recoverable_checkpoint_created = true;
  PrepareMailbox(mailbox, begin, &ExecuteCombatPhaseEventTraceBeginV1, 1);
  if (!ExecuteCombatPhaseEventTraceBeginV1(
          &begin, Stamp(10, NativeFixture::kBeforeDate)) ||
      begin.completion != CombatPhaseEventTraceManagedCompletionV1::armed ||
      session->stage != CombatPhaseEventTraceManagedStageV1::
                            armed_waiting_for_one_day ||
      !IsCombatPhaseEventTraceRingV1Armed()) {
    return Fail("typed begin did not arm trace");
  }

  fixture.SetNextDay();
  void *const combat = fixture.combat.data();
  const auto side0 = reinterpret_cast<void *>(session->plan.sides[0]);
  const auto side1 = reinterpret_cast<void *>(session->plan.sides[1]);
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule, combat,
          side0, fixture.schedule_rng.data(),
          NativeFixture::kModule +
              kCombatPhaseEventScheduleSide0ReturnRva) ||
      !CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::after_side1_schedule, combat,
          side1, fixture.schedule_rng.data(),
          NativeFixture::kModule +
              kCombatPhaseEventScheduleSide1ReturnRva)) {
    return Fail("schedule boundaries failed");
  }
  fixture.SetPhaseDay(5);
  const std::array<CombatPhaseEventTraceBoundaryV1, 4> fire_boundaries{
      CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire,
      CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire,
      CombatPhaseEventTraceBoundaryV1::before_side1_phase_fire,
      CombatPhaseEventTraceBoundaryV1::after_side1_phase_fire};
  for (std::size_t index = 0; index < fire_boundaries.size(); ++index) {
    void *const side = index < 2 ? side0 : side1;
    const auto return_address =
        NativeFixture::kModule +
        (index < 2 ? kCombatPhaseEventFireSide0ReturnRva
                   : kCombatPhaseEventFireSide1ReturnRva);
    if (!CaptureCombatPhaseEventTraceBoundaryV1(
            fire_boundaries[index], combat, side, nullptr,
            return_address)) {
      return Fail("fire boundary failed");
    }
  }

  CombatPhaseEventTraceFinishContextV1 finish{};
  finish.session = session.get();
  finish.managed_daily_sequence_token = token;
  PrepareMailbox(mailbox, finish, &ExecuteCombatPhaseEventTraceFinishV1, 2);
  if (!ExecuteCombatPhaseEventTraceFinishV1(
          &finish, Stamp(11, NativeFixture::kBeforeDate + 24)) ||
      finish.completion != CombatPhaseEventTraceManagedCompletionV1::
                               bounded_trace_available ||
      session->stage != CombatPhaseEventTraceManagedStageV1::drained ||
      !session->exact_one_day_observed || !session->detours_uninstalled ||
      !session->drain.bounded_capture_complete ||
      session->drain.production_trace_ready ||
      fixture.detour_memory.live_allocations != 0 ||
      IsCombatPhaseEventTraceRingV1Armed()) {
    return Fail("typed finish did not drain/cleanup bounded trace");
  }
  const auto wire = SerializeCombatPhaseEventTraceManagedResultV1(*session);
  if (wire.empty() ||
      wire.find("\"recoverable_checkpoint_created\":true") ==
          std::string::npos ||
      wire.find("\"exact_one_day_observed\":true") == std::string::npos ||
      wire.find("\"record_count\":7") == std::string::npos ||
      wire.find("\"original_trace_ready\":false") == std::string::npos) {
    return Fail("managed DTO serialization mismatch");
  }
  return true;
}

bool AdmissionRequiresCheckpointAndMailbox() {
  NativeFixture fixture;
  auto session = std::make_unique<CombatPhaseEventTraceManagedSessionV1>();
  CombatPhaseEventTraceBeginContextV1 begin{};
  begin.session = session.get();
  begin.bindings = &fixture.bindings;
  begin.plan_environment = fixture.plan_environment;
  begin.detour_environment = fixture.detour_environment;
  begin.combat_id = NativeFixture::kCombatId;
  begin.managed_daily_sequence_token = 2;
  const auto stamp = Stamp(3, NativeFixture::kBeforeDate);
  if (ExecuteCombatPhaseEventTraceBeginV1(&begin, stamp) ||
      begin.completion != CombatPhaseEventTraceManagedCompletionV1::
                              infrastructure_rejected) {
    return Fail("direct begin invocation was not rejected");
  }

  MainThreadQueryMailboxV1 mailbox{};
  auto session2 = std::make_unique<CombatPhaseEventTraceManagedSessionV1>();
  CombatPhaseEventTraceBeginContextV1 no_checkpoint{};
  no_checkpoint.session = session2.get();
  no_checkpoint.bindings = &fixture.bindings;
  no_checkpoint.plan_environment = fixture.plan_environment;
  no_checkpoint.detour_environment = fixture.detour_environment;
  no_checkpoint.combat_id = NativeFixture::kCombatId;
  no_checkpoint.managed_daily_sequence_token = 3;
  PrepareMailbox(mailbox, no_checkpoint,
                 &ExecuteCombatPhaseEventTraceBeginV1, 7);
  if (!ExecuteCombatPhaseEventTraceBeginV1(&no_checkpoint, stamp) ||
      no_checkpoint.completion !=
          CombatPhaseEventTraceManagedCompletionV1::trace_unavailable ||
      session2->stage != CombatPhaseEventTraceManagedStageV1::failed ||
      fixture.detour_memory.live_allocations != 0) {
    return Fail("missing recoverable checkpoint did not fail closed");
  }
  return true;
}

} // namespace

int main() {
  if (!PlanBuilderClosesPointers() ||
      !ManagedBeginFinishProducesBoundedDto() ||
      !AdmissionRequiresCheckpointAndMailbox()) {
    return 1;
  }
  std::cout << "combat phase event managed v1 fixture passed\n";
  return 0;
}
