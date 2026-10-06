#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_county_conversion.hpp"
#include "xar_bridge/ck3_12004_county_conversion_abi.hpp"
#include "xar_bridge/ck3_12004_county_conversion_task_action_v1.hpp"
#include "xar_bridge/ck3_12003_county_conversion_task_action_mailbox.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

namespace c = xar::ck3_12004;
namespace r = c::religion::clergy;
namespace q = c::religion::county_conversion;
namespace abi = q::abi;
namespace action = q::action;
namespace envelope = xar::ck3_12002;
namespace pump_api = xar::ck3_11906;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T>
void Put(Buffer &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
template <typename T> T Load(const void *b, std::size_t at) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(b) + at, sizeof(result));
  return result;
}
template <typename Buffer>
void Key(Buffer &b, std::size_t at, std::string_view key) {
  Put(b, at, key.data()); Put(b, at + 0x10, std::uint64_t{key.size()});
  Put(b, at + 0x18, std::uint64_t{key.size() > 15 ? key.size() : 31});
}

struct Fixture {
  static constexpr std::int32_t owner_id = 29829;
  static constexpr std::int32_t incumbent_id = 56513;
  static constexpr std::int32_t other_holder_id = 47;
  static constexpr std::int32_t task_id = 7162;
  static constexpr std::array<std::int32_t, 3> title_ids{
      1537, 2173, 1982};
  static constexpr std::array<std::int32_t, 3> province_ids{3, 1, 2};
  static constexpr std::array<std::uint32_t, 3> rite_ids{153, 0, 0x83000003};
  static constexpr std::array<std::int64_t, 3> rates{500000, 125000, 350000};
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> characters{}, tasks{}, titles{};
  std::vector<std::byte> character_slots = std::vector<std::byte>(56514 * 0x10);
  std::vector<std::byte> task_slots = std::vector<std::byte>(7163 * 0x10);
  std::vector<std::byte> title_slots = std::vector<std::byte>(2174 * 0x10);
  Bytes<0x1D8> owner{}, incumbent{}, other_holder{};
  Bytes<0x240> landed{};
  Bytes<0x68> task{}, rr_type{}, conversion_type{};
  Bytes<0x60> position{};
  std::array<std::int32_t, 1> task_ids{task_id};
  std::array<Bytes<0x860>, 3> provinces{};
  std::array<Bytes<0x390>, 3> counties{};
  std::array<Bytes<0x130>, 3> title_objects{};
  std::array<Bytes<0x4C0>, 3> rites{};
  std::array<void *, 3> target_pointers{};
  Bytes<0x100> map{};
  std::array<void *, 4> province_pointers{};
  std::array<Bytes<0x20>, 4> province_entries{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = characters.data(), *tasks_ptr = tasks.data();
  void *titles_ptr = titles.data(), *database_ptr = conversion_type.data(), *fallback_ptr = nullptr;
  bool shown_value = true, valid_value = true, empty_targets = false;
  int rejected_ordinal = -1, rate_failure_ordinal = -1, rite_failure_ordinal = -1;
  bool bad_arguments = false;
  int shown_calls = 0, valid_calls = 0, producer_calls = 0, target_calls = 0;
  int candidate_rate_calls = 0, current_rate_calls = 0, rite_calls = 0;
  int allocations = 0, releases = 0;

  Fixture() {
    Put(state, c::kGameStateDateOffset, std::int32_t{53230008}); Put(state, c::kGameStateSpeedOffset, std::int32_t{2});
    Put(state, c::kGameStateDataOffset, data.data());
    Put(jomini, c::kJominiPlayersOffset, players.data()); jomini[c::kJominiPausedOffset] = std::byte{1};
    Put(players, c::kPlayersLocalPlayerIdOffset, std::int32_t{7}); Put(player, c::kPlayerIdOffset, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + c::kPlayerManagerEntriesOffset, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + c::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry, c::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7}); Put(entry, c::kPlayerEntryCharacterIdOffset, owner_id);
    Put(characters, c::kCharacterStorageSlotsOffset, character_slots.data()); Put(characters, c::kCharacterStorageCapacityOffset, std::int32_t{56514});
    Put(character_slots, static_cast<std::size_t>(owner_id) * 0x10 + 8, owner.data()); Put(owner, c::kCharacterFullIdOffset, owner_id);
    Put(character_slots, static_cast<std::size_t>(incumbent_id) * 0x10 + 8, incumbent.data()); Put(incumbent, c::kCharacterFullIdOffset, incumbent_id);
    Put(character_slots, static_cast<std::size_t>(other_holder_id) * 0x10 + 8, other_holder.data()); Put(other_holder, c::kCharacterFullIdOffset, other_holder_id);
    Put(owner, abi::kCharacterRiteOffset, std::uint32_t{152});
    Put(incumbent, abi::kCharacterRiteOffset, std::uint32_t{152});
    Put(owner, abi::kCharacterLandedOffset, landed.data());
    Put(landed, abi::kLandedTaskIdsOffset, task_ids.data());
    Put(landed, abi::kLandedTaskCountOffset, std::int32_t{1});
    Put(tasks, abi::kStorageEntriesOffset, task_slots.data()); Put(tasks, abi::kStorageCapacityOffset, std::int32_t{7163});
    Put(task_slots, static_cast<std::size_t>(task_id) * 0x10 + 8, task.data()); Put(task, abi::kTaskFullIdOffset, task_id);
    Put(task, abi::kTaskTypeOffset, rr_type.data()); Put(task, abi::kTaskOwnerOffset, owner_id);
    Put(task, abi::kTaskIncumbentOffset, incumbent_id);
    Put(task, abi::kTaskPercentageOffset, std::int64_t{8750000}); Put(task, abi::kTaskScopeTagOffset, std::uint32_t{0});
    Put(task, abi::kTaskScopeProvinceOffset, std::int32_t{-1});
    Key(rr_type, abi::kDefinitionKeyOffset, "task_religious_relations");
    Key(conversion_type, abi::kDefinitionKeyOffset, q::kTaskKey);
    Put(rr_type, abi::kTaskTypePositionOffset, position.data()); Put(conversion_type, abi::kTaskTypePositionOffset, position.data());
    Put(rr_type, abi::kTaskTypeKindOffset, std::int32_t{0}); Put(conversion_type, abi::kTaskTypeKindOffset, std::int32_t{1});
    Put(rr_type, abi::kTaskTypeProgressKindOffset, std::int32_t{0}); Put(conversion_type, abi::kTaskTypeProgressKindOffset, std::int32_t{1});
    // Position identity is proven through the native fixed-key task lookup.
    // No raw Position key field is constructed or read.
    Put(titles, abi::kStorageEntriesOffset, title_slots.data()); Put(titles, abi::kStorageCapacityOffset, std::int32_t{2174});
    for (std::size_t i = 0; i < 3; ++i) {
      Put(provinces[i], abi::kProvinceIdOffset, province_ids[i]);
      Put(provinces[i], abi::kProvinceTagOffset, std::uint32_t{0x50726F76});
      Put(provinces[i], abi::kProvinceCountyOffset, counties[i].data());
      Put(counties[i], abi::kCountyTitleIdOffset, title_ids[i]); Put(counties[i], abi::kCountyRiteOffset, rite_ids[i]);
      Put(title_objects[i], abi::kTitleFullIdOffset, title_ids[i]);
      Put(title_objects[i], abi::kTitleHolderOffset, i == 1 ? owner_id : other_holder_id);
      const auto index = static_cast<std::uint32_t>(title_ids[i]) & 0xFFFFFFU;
      Put(title_slots, static_cast<std::size_t>(index) * 0x10 + 8, title_objects[i].data());
      Put(rites[i], abi::kReligionFullIdOffset, rite_ids[i]); target_pointers[i] = provinces[i].data();
      province_pointers[static_cast<std::size_t>(province_ids[i])] = provinces[i].data();
    }
    Put(data, abi::kMapProvinceArrayOffset, province_pointers.data()); Put(data, abi::kMapProvinceCountOffset, std::int32_t{4});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
bool Read(void *, const void *address, void *out, std::size_t size) noexcept {
  if (f->rite_failure_ordinal >= 0 && address == f->counties[static_cast<std::size_t>(f->rite_failure_ordinal)].data() + abi::kCountyRiteOffset)
    return false;
  std::memcpy(out, address, size); return true;
}
bool PositionPredicate(void *, std::int32_t) { return true; }
bool ReassignPredicate(void *, void *) { return false; }
bool FirePredicate(void *, void *, void *, std::uint32_t, void *) { return false; }
void *CourtOwner(void *) { return f->owner.data(); }
const void *PositionTaskLookup(const void *owner, const std::string *key) {
  if (owner != f->owner.data() || !key || *key != "councillor_court_chaplain")
    f->bad_arguments = true;
  return f->task.data();
}
std::int32_t Hash(void *, const char *key, std::uint32_t) {
  if (std::string_view{key} != q::kTaskKey) f->bad_arguments = true;
  return 0x123456;
}
const void *Lookup(const void *database, std::int32_t hash) {
  if (database != f->database_ptr || hash != 0x123456) f->bad_arguments = true;
  return f->conversion_type.data();
}
bool Shown(const void *type, const void *scopes) {
  ++f->shown_calls;
  if (type != f->conversion_type.data() ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id) f->bad_arguments = true;
  return f->shown_value;
}
bool Valid(const void *type, const void *scopes, void *breakdown) {
  ++f->valid_calls;
  if (type != f->conversion_type.data() || breakdown != nullptr ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id) f->bad_arguments = true;
  return f->valid_value;
}
int Ordinal(const void *province) {
  for (int i = 0; i < 3; ++i)
    if (province == f->provinces[static_cast<std::size_t>(i)].data()) return i;
  f->bad_arguments = true; return -1;
}
bool TargetValid(const void *type, const void *incumbent, const void *province, void *breakdown) {
  ++f->target_calls;
  if (type != f->conversion_type.data() || breakdown != nullptr ||
      incumbent != f->incumbent.data()) f->bad_arguments = true;
  return Ordinal(province) != f->rejected_ordinal;
}
void Initialize(void *allocator, std::uintptr_t *address, std::int32_t *capacity) {
  ++f->allocations; *address = reinterpret_cast<std::uintptr_t>(allocator) + 8; *capacity = 64;
}
void Produce(const void *incumbent, const void *type, bool expand_court,
             q::NativeVector *out, bool first_only) {
  ++f->producer_calls;
  if (type != f->conversion_type.data() || expand_court || first_only ||
      incumbent != f->incumbent.data()) f->bad_arguments = true;
  out->data_address = reinterpret_cast<std::uintptr_t>(f->target_pointers.data());
  out->capacity = 3; out->count = f->empty_targets ? 0 : 3;
}
void Release(void *, void *address, std::size_t size) {
  ++f->releases;
  if (address != f->target_pointers.data() || size != sizeof(std::uintptr_t)) f->bad_arguments = true;
}
std::int64_t *MonthlyRate(const void *type, std::int64_t *out, const void *scopes,
                        void *breakdown, bool frozen) {
  if (type != f->conversion_type.data() || breakdown != nullptr ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id) f->bad_arguments = true;
  if (scopes == f->task.data() + abi::kTaskScopesOffset) {
    ++f->current_rate_calls;
    if (!frozen) f->bad_arguments = true;
    *out = 777000; return out;
  }
  ++f->candidate_rate_calls;
  if (frozen || Load<std::uint32_t>(scopes, 8) != 8U) f->bad_arguments = true;
  const auto id = Load<std::int32_t>(scopes, 0x10);
  for (int i = 0; i < 3; ++i) {
    if (id != Fixture::province_ids[static_cast<std::size_t>(i)]) continue;
    if (i == f->rate_failure_ordinal) return nullptr;
    *out = Fixture::rates[static_cast<std::size_t>(i)]; return out;
  }
  f->bad_arguments = true; return nullptr;
}
const void *CountyRite(const void *county) {
  ++f->rite_calls;
  for (std::size_t i = 0; i < 3; ++i)
    if (county == f->counties[i].data()) return f->rites[i].data();
  f->bad_arguments = true; return nullptr;
}
q::Environment Bind(Fixture &fixture) {
  f = &fixture;
  q::Environment e = q::BindCountyConversionImage12004(0x140000000ULL, c::kExecutableSha256);
  // Bind actual .4 address calculation, then explicitly replace every reached
  // image/function input with caller-owned offline synthetic objects.
  e.module_base = 0;
  e.exact_build_admitted = true; e.offline_fixture = true;
  e.executable_sha256 = c::kExecutableSha256;
  e.clergy.module_base = 0; e.clergy.enabled = true; e.clergy.offline_fixture = true;
  e.clergy.executable_sha256 = c::kExecutableSha256;
  e.clergy.core = {true, &f->state_ptr, &f->jomini_ptr, &f->characters_ptr, &Player};
  e.clergy.task_storage_slot = &f->tasks_ptr; e.clergy.read_memory = &Read;
  e.clergy.position_lookup = &PositionTaskLookup;
  // Synthetic native predicate callbacks support the actual .4 clergy reader.
  e.clergy.valid_position = &PositionPredicate;
  e.clergy.valid_character = &PositionPredicate;
  e.clergy.can_reassign = &ReassignPredicate; e.clergy.can_fire = &FirePredicate;
  e.clergy.court_owner = &CourtOwner;
  e.allocator.module_base = 0; e.allocator.exact_build_admitted = true;
  e.allocator.offline_fixture_function_overrides = true;
  e.allocator.admitted_executable_sha256 = c::kExecutableSha256;
  e.allocator.initialize_vector = &Initialize; e.allocator.release_allocation = &Release;
  e.game_state_slot = &f->state_ptr; e.title_storage_slot = &f->titles_ptr;
  e.title_fallback_slot = &f->fallback_ptr;
  e.task_type_database_slot = &f->database_ptr; e.task_type_fallback_slot = &f->fallback_ptr;
  e.hash_key = &Hash; e.lookup_type = &Lookup; e.shown = &Shown; e.valid = &Valid;
  e.target_valid = &TargetValid; e.produce_targets = &Produce;
  e.monthly_rate = &MonthlyRate; e.county_rite = &CountyRite;
  return e;
}

int checks = 0;
void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}

struct WholeFixture : Fixture {
  Bytes<0x4C0> owner_rite{};
  Bytes<0x10> owner_faith{};
  std::array<Bytes<0x10>, 3> county_faiths{};
  bool final_value = false;
  int readonly_final_calls = 0, action_final_calls = 0;
  int clone_calls = 0, queue_calls = 0, destroy_calls = 0;
  std::array<std::uintptr_t, 9> primary{};
  std::array<std::uintptr_t, 2> secondary{};
  action::ChangeCouncilTaskCommand queued{};

  WholeFixture() {
    Put(owner_rite, abi::kReligionFullIdOffset, std::uint32_t{152});
    Put(owner_rite, abi::kRiteFaithOffset, std::uint32_t{0});
    Put(owner_faith, abi::kReligionFullIdOffset, std::uint32_t{0});
    constexpr std::array<std::uint32_t, 3> faith_ids{3, 0, 4};
    for (std::size_t i = 0; i < faith_ids.size(); ++i) {
      Put(rites[i], abi::kRiteFaithOffset, faith_ids[i]);
      Put(county_faiths[i], abi::kReligionFullIdOffset, faith_ids[i]);
    }
  }
  void ReligiousRelations() {
    Put(task, abi::kTaskTypeOffset, rr_type.data());
    Put(task, abi::kTaskScopeTagOffset, std::uint16_t{0});
    Put(task, abi::kTaskScopeProvinceOffset, std::int32_t{-1});
    task[abi::kTaskFrozenOffset] = std::byte{0};
  }
  void CurrentConversion() {
    Put(task, abi::kTaskTypeOffset, conversion_type.data());
    Put(task, abi::kTaskScopeTagOffset, std::uint16_t{8});
    Put(task, abi::kTaskScopeProvinceOffset, std::int32_t{1});
    task[abi::kTaskFrozenOffset] = std::byte{1};
  }
  void DeliverFixtureOnly() {
    // Explicit synthetic source mutation between independent transactions.
    // The production native Execute/apply function is not called or emulated.
    Put(task, abi::kTaskTypeOffset, queued.task_type);
    Put(task, abi::kTaskScopesOffset, queued.scopes);
    Put(task, abi::kTaskPercentageOffset, std::int64_t{0});
    task[abi::kTaskFrozenOffset] = std::byte{1};
  }
};
WholeFixture *whole = nullptr;
const void *CharacterRiteValue(const void *character) {
  if (character != whole->owner.data() && character != whole->incumbent.data())
    whole->bad_arguments = true;
  return whole->owner_rite.data();
}
const void *RiteFaithValue(const void *rite) {
  if (rite == whole->owner_rite.data()) return whole->owner_faith.data();
  for (std::size_t i = 0; i < 3; ++i)
    if (rite == whole->rites[i].data()) return whole->county_faiths[i].data();
  whole->bad_arguments = true; return nullptr;
}
const void *GovernmentValue(const void *owner) {
  if (owner != whole->owner.data()) whole->bad_arguments = true;
  return nullptr; // Actual no-government fallback observation in this fixture.
}
const void *TitleByKeyValue(const void *) {
  whole->bad_arguments = true; return nullptr;
}
const std::string *IdentifierNameValue(std::int32_t) {
  whole->bad_arguments = true; return nullptr;
}
std::int32_t CountyOpinionValue(const void *county) {
  constexpr std::array<std::int32_t, 3> values{-12, 0, 7};
  for (std::size_t i = 0; i < 3; ++i)
    if (county == whole->counties[i].data()) return values[i];
  whole->bad_arguments = true; return 0;
}
bool FinalValidator(const void *packet, void *tooltip) {
  if (tooltip || Load<std::int32_t>(packet, 0x20) != Fixture::task_id ||
      Load<const void *>(packet, 0x28) != whole->conversion_type.data() ||
      Load<std::int32_t>(packet, 0x30) != Fixture::incumbent_id ||
      Load<std::int32_t>(packet, 0x34) != Fixture::owner_id ||
      Load<std::uint16_t>(packet, 0x38) != 8)
    whole->bad_arguments = true;
  const auto primary = Load<std::uintptr_t>(packet, 0);
  if (primary == 0) {
    ++whole->readonly_final_calls;
  } else {
    ++whole->action_final_calls;
    const auto &command = *static_cast<const action::ChangeCouncilTaskCommand *>(packet);
    if (primary != reinterpret_cast<std::uintptr_t>(whole->primary.data()) ||
        command.secondary_vtable != reinterpret_cast<std::uintptr_t>(whole->secondary.data()) ||
        command.flags != 0 || command.padding != 0 ||
        command.scopes.province_id != 1 ||
        std::any_of(command.metadata.begin(), command.metadata.end(),
            [](std::byte value) { return value != std::byte{0}; }) ||
        std::any_of(command.scopes.reserved.begin(), command.scopes.reserved.end(),
            [](std::byte value) { return value != std::byte{0}; }) ||
        std::any_of(command.scopes.trailing.begin(), command.scopes.trailing.end(),
            [](std::byte value) { return value != std::byte{0}; }))
      whole->bad_arguments = true;
  }
  return whole->final_value;
}
void *DestroyFixtureCommand(void *command, std::uint32_t flags) {
  ++whole->destroy_calls;
  if (flags != 1) whole->bad_arguments = true;
  delete static_cast<action::ChangeCouncilTaskCommand *>(command);
  return nullptr;
}
void **CloneFixtureCommand(const void *command, void **storage) {
  ++whole->clone_calls;
  if (!storage || *storage) whole->bad_arguments = true;
  *storage = new action::ChangeCouncilTaskCommand(
      *static_cast<const action::ChangeCouncilTaskCommand *>(command));
  return storage;
}
bool QueueFixtureCommand(void *manager, void **command, std::uint32_t channel) {
  ++whole->queue_calls;
  if (manager != whole || !command || !*command || channel != 14)
    whole->bad_arguments = true;
  whole->queued = *static_cast<const action::ChangeCouncilTaskCommand *>(*command);
  // Retain ownership for the actual software SubmitCommandCopy residual delete.
  // Queue acceptance does not mutate the synthetic task source.
  return true;
}
q::Environment CountyEnvironment(WholeFixture &fixture) {
  whole = &fixture;
  auto environment = Bind(fixture);
  environment.value_inputs_enabled = true;
  environment.character_rite = &CharacterRiteValue;
  environment.rite_faith = &RiteFaithValue;
  environment.government = &GovernmentValue;
  environment.title_by_key = &TitleByKeyValue;
  environment.identifier_name = &IdentifierNameValue;
  environment.county_opinion = &CountyOpinionValue;
  environment.government_fallback_slot = &fixture.fallback_ptr;
  environment.task_dispatch_enabled = true;
  environment.final_task_validator = &FinalValidator;
  return environment;
}
action::Access ActionAccess(WholeFixture &fixture) {
  // Exercise actual .4 binder calculation, then supply explicit synthetic
  // callbacks/tables. No production image pointer is invoked in the fixture.
  auto access = action::BindCountyConversionTaskActionImage12004(
      0x140000000ULL, c::kExecutableSha256);
  access.county = CountyEnvironment(fixture);
  fixture.primary[0] = reinterpret_cast<std::uintptr_t>(&DestroyFixtureCommand);
  fixture.primary[8] = reinterpret_cast<std::uintptr_t>(&CloneFixtureCommand);
  access.primary_vtable = reinterpret_cast<std::uintptr_t>(fixture.primary.data());
  access.secondary_vtable = reinterpret_cast<std::uintptr_t>(fixture.secondary.data());
  access.commands.enabled = true;
  access.commands.command_manager = &fixture;
  access.commands.queue_owned_command = &QueueFixtureCommand;
  return access;
}

std::array<std::byte, 0x28> fixture_tls{};
void *__fastcall FixtureTls() noexcept { return fixture_tls.data(); }
struct SyntheticPump {
  std::uint8_t initialized = 1;
  void *unused_rng = nullptr;
  SyntheticPump(WholeFixture &fixture, pump_api::MainThreadQueryMailboxV1 &mailbox) {
    fixture_tls[0x20] = std::byte{1};
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_clergy12002 =
        &envelope::ExecutePlayerClergyAppointmentMailbox12002;
    mailbox.permitted_executor_county_conversion_task_action12003 =
        &envelope::ExecutePlayerCountyConversionTaskActionMailbox12003;
    mailbox.iat_hook_installed = true;
    mailbox.state = pump_api::MainThreadQueryMailboxStateV1::idle;
    for (int i = 0; i < 2; ++i)
      (void)pump_api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
};
template <typename Work>
void OwningRun(pump_api::MainThreadQueryMailboxV1 &mailbox, Work work) {
  std::atomic<bool> done{false};
  bool result = false;
  std::thread worker([&] { result = work(); done.store(true, std::memory_order_release); });
  bool drained = false;
  while (!done.load(std::memory_order_acquire)) {
    if (!drained && mailbox.state.load(std::memory_order_acquire) ==
            pump_api::MainThreadQueryMailboxStateV1::queued)
      drained = pump_api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    Sleep(0);
  }
  worker.join();
  Check(drained && result, "actual named mailbox submitted/drained/reclaimed");
  Check(mailbox.state == pump_api::MainThreadQueryMailboxStateV1::idle,
      "completed named mailbox returns idle");
}
constexpr std::array<const char *, 6> kFiles{
    "clergy-rr-county-dispatch-false.json", "clergy-current-county-conversion.json",
    "county-task-final-denied.json", "county-task-queued.json",
    "county-task-independent-pending.json", "county-task-independent-delivered.json"};
constexpr std::array<const char *, 6> kRequests{
    "g2-read-00000000000000000000000000004401",
    "g2-read-00000000000000000000000000004402",
    "county-task-00000000000000000000000000004403",
    "county-task-00000000000000000000000000004404",
    "county-task-00000000000000000000000000004405",
    "county-task-00000000000000000000000000004406"};
struct CaseFrame {
  std::uint64_t capture_epoch = 0;
  std::uint64_t mailbox_sequence = 0;
};
std::array<CaseFrame, 6> case_frames{};
void SaveWire(const std::filesystem::path &directory, std::size_t index,
              std::string_view wire, const envelope::QueryMailboxEnvelope &query) {
  Check(query.execution_stamp.pump_epoch > 0 &&
      query.execution_stamp.thread_id == GetCurrentThreadId() &&
      query.execution_stamp.date_raw == 53230008 && query.execution_stamp.paused &&
      query.frame_stable && query.ticket.sequence > 0,
      "actual owning stamp records synthetic frame and thread");
  case_frames[index] = {query.execution_stamp.pump_epoch, query.ticket.sequence};
  std::ofstream output(directory / kFiles[index], std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "write unchanged actual whole serializer bytes");
}
void ReadClergyWhole(WholeFixture &fixture, q::Environment environment,
    const xar::game::GameAdapter &adapter, pump_api::MainThreadQueryMailboxV1 &mailbox,
    const xar::game::Snapshot &frame, const std::filesystem::path &directory,
    std::size_t index) {
  envelope::PlayerClergyAppointmentMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame;
  query.envelope.expected_snapshot_revision = 9;
  query.envelope.snapshot_comparison = envelope::QuerySnapshotComparison12002::core_frame;
  const std::string payload = "{\"expected_revision\":9,\"expected_public_revision\":2,"
      "\"candidate_character_id\":56513}";
  Check(envelope::ParsePlayerClergyAppointmentRequest12002(payload, query.request),
      "existing clergy whole request parser");
  query.bindings12004 = environment.clergy;
  query.county_conversion_environment12004 = environment;
  std::string wire, failure;
  OwningRun(mailbox, [&] {
    return envelope::RunPlayerClergyAppointmentMailbox12002(
        query, kRequests[index], wire, failure);
  });
  Check(failure.empty() && query.completed && query.observation.available &&
      query.county_conversion_observation.has_value(),
      "actual clergy/base and county4 sibling complete in same query");
  const auto &county = *query.county_conversion_observation;
  Check(county.available && county.capture_epoch == query.observation.capture_epoch &&
      county.owner_character_id == Fixture::owner_id && county.active_task_id == Fixture::task_id &&
      county.candidates.size() == 3 && county.value_inputs &&
      county.value_inputs->available && county.task_dispatch && county.task_dispatch->available,
      "same frame actual county collection/value/dispatch outputs");
  Check(county.candidates[0].county_title_id == 1537 &&
      county.candidates[1].county_title_id == 1982 &&
      county.candidates[2].county_title_id == 2173 &&
      county.candidates[2].native_collection_ordinal == 1 &&
      county.candidates[2].county_rite_id == 0U &&
      county.value_inputs->candidates[2].county_faith_id == 0U &&
      county.value_inputs->candidates[2].current_popular_opinion == 0,
      "unsigned full title sort, native ordinal, legitimate zero identities/opinion");
  if (index == 0) {
    Check(county.current_task_key == "task_religious_relations" &&
        !county.current_target_province_id && !county.current_conversion_monthly_rate_raw &&
        std::all_of(county.task_dispatch->candidates.begin(),
            county.task_dispatch->candidates.end(),
            [](const auto &row) { return !row.native_final_can_dispatch; }),
        "RR current and independent observed false final dispatch");
  } else {
    Check(county.current_task_key == q::kTaskKey && county.current_target_province_id == 1 &&
        county.current_target_county_title_id == 2173 && county.current_target_county_rite_id == 0U &&
        county.current_percentage_progress_raw == 8750000 &&
        county.current_conversion_monthly_rate_raw == 777000 && county.current_task_frozen == true,
        "actual current target/progress/frozen/monthly fields remain separate");
  }
  Check(!fixture.bad_arguments, "native callback receivers and raw scopes are genuine fixture inputs");
  SaveWire(directory, index, wire, query.envelope);
}
void ActionWhole(WholeFixture &fixture, action::Access access,
    const xar::game::GameAdapter &adapter, pump_api::MainThreadQueryMailboxV1 &mailbox,
    const xar::game::Snapshot &frame,
    envelope::PlayerCountyConversionTaskActionMailboxState12003 &state,
    const std::filesystem::path &directory, std::size_t index) {
  envelope::PlayerCountyConversionTaskActionMailboxContext12003 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame;
  query.envelope.expected_snapshot_revision = 9;
  query.envelope.snapshot_comparison = envelope::QuerySnapshotComparison12002::core_frame;
  query.state = &state; query.request_id = kRequests[index]; query.access12004 = access;
  const bool submit = index < 4;
  query.mode = submit ? envelope::PlayerCountyConversionTaskActionMode12003::submit
                     : envelope::PlayerCountyConversionTaskActionMode12003::result;
  const std::string payload = submit
      ? "{\"expected_revision\":9,\"expected_snapshot_revision\":9,\"expected_public_revision\":2,"
        "\"expected_active_task_id\":7162,\"expected_incumbent_character_id\":56513,\"province_id\":1,"
        "\"replace_existing_task\":false,\"action_id\":\"county4-selected-assignment\"}"
      : "{\"expected_revision\":9,\"expected_snapshot_revision\":9,\"expected_public_revision\":2,"
        "\"submitted_request_id\":\"county-task-00000000000000000000000000004404\","
        "\"action_id\":\"county4-selected-assignment\"}";
  Check(envelope::ParsePlayerCountyConversionTaskActionRequest12003(payload, 9, query),
      "existing county action payload parser retains public intent and native frame");
  const auto step = submit ? envelope::kPlayerCountyConversionTaskSubmitStep12003
                          : envelope::kPlayerCountyConversionTaskResultStep12003;
  const auto final_before = fixture.action_final_calls;
  std::string wire, failure;
  OwningRun(mailbox, [&] {
    return envelope::RunPlayerCountyConversionTaskActionMailbox12003(
        query, step, kRequests[index], wire, failure);
  });
  Check(failure.empty() && query.complete, "actual whole action serializer after owning execution");
  if (index == 2) {
    Check(query.submission.status == action::SubmitStatus::not_submitted &&
        query.submission.failure == "county_task_native_final_denied" &&
        query.submission.native_final_can_dispatch == false &&
        !query.submission.native_submit_copy_called &&
        fixture.action_final_calls == final_before + 1 &&
        fixture.clone_calls == 0 && fixture.queue_calls == 0,
        "native false final input does not clone or queue");
  } else if (index == 3) {
    Check(query.submission.status == action::SubmitStatus::queued_verification_pending &&
        query.submission.request.expected_revision == 2 &&
        query.submission.native_final_can_dispatch == true &&
        query.submission.native_submit_copy_called && query.submission.target_county_title_id == 2173 &&
        fixture.clone_calls == 1 && fixture.queue_calls == 1 && fixture.destroy_calls == 1,
        "once submit uses actual4 reader/final and existing owning software clone/queue");
  } else {
    const auto &result = query.independent_result;
    Check(result.actual_task_id_unchanged == true && !result.county_conversion_completed,
        "task identity may remain unchanged and assignment does not mean conversion completion");
    if (index == 4) {
      Check(result.verification_pending && !result.task_assignment_material_observed &&
          result.actual_task_assignment_matches == false &&
          result.after.task_key == "task_religious_relations",
          "queue ACK does not change independent observed task");
    } else {
      Check(!result.verification_pending && result.task_assignment_material_observed &&
          result.actual_task_assignment_matches == true &&
          result.after.task_key == q::kTaskKey && result.after.target_scope_tag == 8 &&
          result.after.target_province_id == 1 && result.after.target_county_title_id == 2173 &&
          result.after.percentage_progress_raw == 0 &&
          result.after.capture_epoch > query.submission.capture_epoch,
          "later owning transaction reads explicitly delivered synthetic task material");
    }
  }
  Check(!fixture.bad_arguments && fixture.allocations == fixture.releases,
      "current collection allocation/release and action receivers preserved");
  SaveWire(directory, index, wire, query.envelope);
}
void WriteReceipt(const std::filesystem::path &directory) {
  std::ofstream out(directory / "county-native-whole-receipt.json", std::ios::binary);
  out << "{\"schema\":\"xar.ck3.county-conversion-native-whole-fixture12004/v1\","
      "\"status\":\"GREEN\",\"cases\":6,\"checks\":" << checks
      << ",\"whole_wire_files\":[";
  for (std::size_t i = 0; i < kFiles.size(); ++i) {
    if (i) out << ',';
    out << '"' << kFiles[i] << '"';
  }
  out << "],\"exact_build\":{\"game_version\":\"1.20.0.4\",\"steam_build\":25734779,"
      "\"executable_sha256\":\"" << c::kExecutableSha256
      << "\"},\"frame\":{\"public_revision\":2,\"native_revision\":9,\"date_raw\":53230008,"
      "\"owner_character_id\":29829,\"incumbent_character_id\":56513,\"active_task_id\":7162,"
      "\"paused\":true,\"map_ready\":true},\"case_frames\":[";
  for (std::size_t i = 0; i < kFiles.size(); ++i) {
    if (i) out << ',';
    out << "{\"file\":\"" << kFiles[i] << "\",\"capture_epoch\":"
        << case_frames[i].capture_epoch << ",\"mailbox_sequence\":"
        << case_frames[i].mailbox_sequence << '}';
  }
  out << "],\"provenance\":{\"native_memory\":\"fixture-synthetic\","
      "\"native_callbacks\":\"fixture-synthetic\",\"source_frame\":\"fixture-synthetic\","
      "\"public_revision\":\"fixture-synthetic\",\"capture_epoch\":\"fixture-synthetic\","
      "\"whole_wires\":\"compiled-production-serializer\",\"whole_wire_rows_repaired\":false,"
      "\"fixture_delivery\":\"After pending output, explicit fixture-only task memory delivery before final independent read. Production native apply not emulated or claimed.\","
      "\"live\":false},\"actual_named_mailbox\":true,\"actual_core12004_reader\":true,"
      "\"actual_clergy12004_reader\":true,\"actual_county12004_reader\":true,"
      "\"actual_action12004_reader\":true,\"native_apply_invoked\":false,"
      "\"old_cases\":0,\"production_stubs\":0,\"game\":0,\"sdk\":0,\"pipe\":0}\n";
  Check(static_cast<bool>(out), "write actual compiled assertion receipt");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 100;
  try {
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    WholeFixture fixture;
    auto environment = CountyEnvironment(fixture);
    xar::game::Ck3_12004AdapterBindings bindings{};
    bindings.core = environment.clergy.core;
    bindings.read_core_snapshot = &c::ReadCoreSnapshot;
    auto adapter = xar::game::CreateCk3_12004AdapterFromBindings(std::move(bindings));
    Check(adapter && adapter->enabled(), "actual4 adapter factory with explicit synthetic Core bindings");
    xar::game::Snapshot frame{};
    Check(xar::game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) &&
        frame.played_character_id == Fixture::owner_id && frame.date_raw == 53230008 &&
        frame.paused && frame.map_ready && frame.played_character_alive,
        "published synthetic context comes from actual4 current Core reader");
    pump_api::MainThreadQueryMailboxV1 mailbox{};
    SyntheticPump pump(fixture, mailbox);
    ReadClergyWhole(fixture, environment, *adapter, mailbox, frame, directory, 0);
    fixture.CurrentConversion(); fixture.final_value = true;
    ReadClergyWhole(fixture, environment, *adapter, mailbox, frame, directory, 1);
    fixture.ReligiousRelations(); fixture.final_value = false;
    auto access = ActionAccess(fixture);
    envelope::PlayerCountyConversionTaskActionMailboxState12003 state{};
    ActionWhole(fixture, access, *adapter, mailbox, frame, state, directory, 2);
    fixture.final_value = true;
    ActionWhole(fixture, access, *adapter, mailbox, frame, state, directory, 3);
    ActionWhole(fixture, access, *adapter, mailbox, frame, state, directory, 4);
    fixture.DeliverFixtureOnly();
    ActionWhole(fixture, access, *adapter, mailbox, frame, state, directory, 5);
    Check(fixture.clone_calls == 1 && fixture.queue_calls == 1 &&
        fixture.destroy_calls == 1 && !fixture.bad_arguments &&
        mailbox.executed_requests == 6, "six new named whole transactions, one queue submit only");
    WriteReceipt(directory);
    std::cout << "PASS cases=6 checks=" << checks
        << " actual4=true whole_native_packets=true production_stubs=0 live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
