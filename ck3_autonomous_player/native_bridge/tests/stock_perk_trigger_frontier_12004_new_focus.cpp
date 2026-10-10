#include "xar_bridge/ck3_12004_stock_perk_legality.hpp"

#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

// New source-join cases only. All memory and native callback results belong to
// this fixture; this does not observe CK3 or execute a native game callback.
namespace {
namespace life = xar::ck3_12004::lifestyle;
constexpr std::uintptr_t kModule = 0x180000000ULL;
constexpr std::uint32_t kFullId = 0x01000001U;
constexpr char kTarget[] = "cutting_corners_perk";
constexpr char kLifestyle[] = "stewardship_lifestyle";

struct Fixture {
  std::array<std::byte, 0x60> database{};
  std::array<std::uintptr_t, 1> definitions{};
  std::array<std::byte, 0x458> perk{};
  std::array<std::byte, 0x40> lifestyle{};
  std::array<std::byte, 0x1D8> character{};
  std::array<std::byte, 0x30> registry{};
  std::array<std::uintptr_t, 4> registry_rows{};
  life::StockPerkLegalityFrameV1 frame{};
  std::uint32_t validations = 0;
  std::uint32_t live_command_reads = 0;
  std::uint32_t metadata_reads = 0;
  bool hide_slot60 = false, reject_after_validator = false;
  std::uint32_t receiver_reads = 0, slot58_reads = 0, slot60_reads = 0, slotc8_reads = 0;
  bool hide_registry = false;
  bool change_source_sequence = false;
  bool command_operands_match = true;

  template<class T, std::size_t N>
  static void Put(std::array<std::byte, N> &storage, std::size_t offset, T value) {
    std::memcpy(storage.data() + offset, &value, sizeof(value));
  }

  Fixture() {
    const auto perk_address = reinterpret_cast<std::uintptr_t>(perk.data());
    const auto lifestyle_address = reinterpret_cast<std::uintptr_t>(lifestyle.data());
    const auto character_address = reinterpret_cast<std::uintptr_t>(character.data());
    definitions[0] = perk_address;
    Put(database, 0x50, reinterpret_cast<std::uintptr_t>(definitions.data()));
    Put(database, 0x58, std::int32_t{1});
    Put(database, 0x5C, std::int32_t{1});
    Put(perk, 0x18, reinterpret_cast<std::uintptr_t>(kTarget));
    Put(perk, 0x28, std::uint64_t{sizeof(kTarget) - 1});
    Put(perk, 0x30, std::uint64_t{sizeof(kTarget) - 1});
    Put(perk, 0x38, std::uint32_t{0x4744624FU});
    Put(perk, 0x440, lifestyle_address);
    Put(perk, 0x80, std::uintptr_t{kModule + 0x5000});
    Put(lifestyle, 0x18, reinterpret_cast<std::uintptr_t>(kLifestyle));
    Put(lifestyle, 0x28, std::uint64_t{sizeof(kLifestyle) - 1});
    Put(lifestyle, 0x30, std::uint64_t{sizeof(kLifestyle) - 1});
    Put(character, 0x18, kFullId);
    Put(character, 0x1C, std::uint32_t{0x43686172U});
    Put(character, 0x1D0, std::uint64_t{1});
    Put(registry, 0x20, reinterpret_cast<std::uintptr_t>(registry_rows.data()));
    Put(registry, 0x2C, std::uint32_t{2});
    registry_rows[3] = character_address;
    std::memcpy(frame.episode_run_id.data(), "owned_source_join_fixture", 26);
    std::memcpy(frame.snapshot_id.data(), "opaque:owned-memory:query", 25);
    frame.public_revision = 11;
    frame.native_revision = 23;
    frame.proof_epoch = 37;
    frame.date_raw = 12345;
    frame.played_character_id = kFullId;
    frame.played_character = character_address;
    frame.paused = frame.map_ready = frame.played_character_alive = true;
    frame.storage_round_trip = true;
  }
};

Fixture *active_fixture = nullptr;
std::string joined_wire;

bool CopyRange(std::uintptr_t address, void *output, std::size_t size,
               const void *storage, std::size_t storage_size) noexcept {
  const auto begin = reinterpret_cast<std::uintptr_t>(storage);
  if (address < begin || size > storage_size || address - begin > storage_size - size)
    return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool ReadOwnedMemory(void *opaque, std::uintptr_t address, void *output,
                     std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  if (!output || !size) return false;
  if (address == reinterpret_cast<std::uintptr_t>(f.perk.data()) + 0x80 && size == 8)
    ++f.receiver_reads;
  if (size == sizeof(std::uintptr_t) &&
      (address == kModule + 0x5058 || address == kModule + 0x5060 || address == kModule + 0x50C8)) {
    std::uintptr_t target = 0;
    if (address == kModule + 0x5058) { ++f.slot58_reads; target = kModule + 0x1000; }
    if (address == kModule + 0x5060) { ++f.slot60_reads; if (f.hide_slot60) return false; target = kModule + 0x2000; }
    if (address == kModule + 0x50C8) { ++f.slotc8_reads; target = kModule + 0x3000; }
    std::memcpy(output, &target, size);
    return true;
  }
  if (address == kModule + 0x54DBC00 && size == sizeof(std::uint32_t)) {
    std::memcpy(output, &f.frame.played_character_id, size);
    return true;
  }
  if (address == kModule + 0x4760A30 && size == sizeof(std::uintptr_t)) {
    const std::uintptr_t validator = kModule + 0x288AE00;
    std::memcpy(output, &validator, size);
    return true;
  }
  if (address == kModule + 0x5C67568 && size == sizeof(std::uintptr_t)) {
    if (f.hide_registry) return false;
    const auto registry = reinterpret_cast<std::uintptr_t>(f.registry.data());
    std::memcpy(output, &registry, size);
    return true;
  }
#define XAR_FIXTURE_RANGE(member) \
  if (CopyRange(address, output, size, f.member.data(), sizeof(f.member))) return true
  XAR_FIXTURE_RANGE(database);
  XAR_FIXTURE_RANGE(definitions);
  XAR_FIXTURE_RANGE(perk);
  XAR_FIXTURE_RANGE(lifestyle);
  XAR_FIXTURE_RANGE(character);
  XAR_FIXTURE_RANGE(registry);
  XAR_FIXTURE_RANGE(registry_rows);
#undef XAR_FIXTURE_RANGE
  if (CopyRange(address, output, size, kTarget, sizeof(kTarget)) ||
      CopyRange(address, output, size, kLifestyle, sizeof(kLifestyle))) return true;

  // The production source reader borrows ReadOne's actual live local command.
  // Admit only this thread's stack range; no arbitrary address is dereferenced.
  ULONG_PTR stack_low = 0, stack_high = 0;
  GetCurrentThreadStackLimits(&stack_low, &stack_high);
  if (address < stack_low || address > stack_high || size > stack_high - address)
    return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  ++f.live_command_reads;
  return true;
}

bool OnFixtureThread(void *) noexcept { return true; }
bool CaptureFrame(void *opaque, life::StockPerkLegalityFrameV1 &out) noexcept {
  out = static_cast<Fixture *>(opaque)->frame;
  return true;
}
bool CaptureMetadata(void *opaque,
                     life::StockPerkLegalitySourceQueryMetadataV1 &out) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  ++f.metadata_reads;
  if (f.reject_after_validator && f.validations != 0) return false;
  out = {};
  out.module_image_size = std::uint32_t{0x6000000};
  out.module_time_date_stamp = std::uint32_t{0x12345678};
  // Explicit fixture-shaped existing ticket. No numeric snapshot identity or
  // TLS array is invented from the revision, epoch, or opaque snapshot string.
  out.query_sequence = std::uint64_t{71} +
      (f.change_source_sequence && f.metadata_reads > 2 ? std::uint64_t{1} : std::uint64_t{0});
  out.mailbox_before_accepted = true;
  out.caller_snapshot_confirmed = true;
  return true;
}
bool ReadState(void *, const life::StockPerkLegalityFrameV1 &,
               std::uintptr_t, life::StockPerkLegalityPlayerStateV1 &out) noexcept {
  out = {};
  std::memcpy(out.target_lifestyle_key.bytes.data(), kLifestyle, sizeof(kLifestyle) - 1);
  out.target_lifestyle_key.size = static_cast<std::uint16_t>(sizeof(kLifestyle) - 1);
  out.target_xp_total_raw = 0;
  out.target_xp_within_level_raw = 0;
  out.target_xp_per_level = 1000;
  out.unspent_perk_points = 1;
  out.used_perk_points = 0;
  out.owned_perk_state_known = true;
  return true;
}
void *GetDatabase() { return active_fixture->database.data(); }
bool ValidateFixtureCommand(void *command, void *) {
  auto &f = *active_fixture;
  ++f.validations;
  std::uint32_t full_id = 0;
  std::uintptr_t definition = 0;
  std::memcpy(&full_id, static_cast<const std::byte *>(command) + 0x20, sizeof(full_id));
  std::memcpy(&definition, static_cast<const std::byte *>(command) + 0x28, sizeof(definition));
  f.command_operands_match = f.command_operands_match && full_id == kFullId &&
      definition == reinterpret_cast<std::uintptr_t>(f.perk.data());
  return false; // Independent original-parent observation in owned memory.
}

life::StockPerkLegalityResultV1 RunNewSourceQuery(Fixture &f) {
  active_fixture = &f;
  life::StockPerkLegalityEnvironmentV1 env{};
  env.exact_build_admitted = true;
  env.admitted_exe_sha256 = life::kStockPerkLegalityExeSha256V1;
  env.module_base = kModule;
  env.offline_fixture = true;
  env.get_character_perk_database = &GetDatabase;
  env.validate_perk_command = &ValidateFixtureCommand;
  life::StockPerkLegalityAccessV1 access{};
  access.context = &f;
  access.is_application_main_thread = &OnFixtureThread;
  access.capture_frame = &CaptureFrame;
  access.read_memory = &ReadOwnedMemory;
  access.read_player_state = &ReadState;
  access.capture_source_query_metadata = &CaptureMetadata;
  return life::ReadStockPerkLegality12004V1(env, access);
}


bool ParentObservationsPreserved(const Fixture &f, const life::StockPerkLegalityResultV1 &r) {
  return r.status == life::StockPerkLegalityStatusV1::observed_native_illegal &&
      r.validator_invoked_twice && f.validations == 2 && f.command_operands_match &&
      r.raw_targets_source && r.trigger_frontier_source &&
      r.raw_targets_source->native_before == std::optional<bool>{false} &&
      r.raw_targets_source->native_after == std::optional<bool>{false};
}
bool ReturnedOutputsAbsent(const life::StockPerkLegalityResultV1 &r) {
  if (!r.trigger_frontier_source) return false;
  const auto &p = *r.trigger_frontier_source;
  for (const auto *lane : {&p.descriptor_al, &p.root_kind_ax, &p.root_mask_qwords, &p.final_c8_al})
    if (lane->source_value_ready || lane->returned_raw_u8 || lane->returned_raw_u16 ||
        lane->returned_qword0 || lane->returned_qword1 || lane->natural_witness) return false;
  return true;
}
}

bool VerifyStockPerkTriggerFrontierCurrentQuery12004() {
  Fixture independent_targets;
  auto first = RunNewSourceQuery(independent_targets);
  if (!ParentObservationsPreserved(independent_targets, first) ||
      independent_targets.receiver_reads != 2 || independent_targets.slot58_reads != 2 ||
      independent_targets.slot60_reads != 2 || independent_targets.slotc8_reads != 2)
    return false;
  const auto &raw = *first.raw_targets_source;
  if (raw.capture_scope != "owned_memory_fixture" ||
      first.trigger_frontier_source->inputs.capture_scope != "owned_memory_fixture") return false;
  if (!first.source_packet || first.source_packet->inputs.prefix_admitted != std::optional<bool>{false} ||
      raw.selected_perk_identity != reinterpret_cast<std::uintptr_t>(independent_targets.perk.data()) ||
      raw.receiver_identity != std::optional<std::uintptr_t>{raw.selected_perk_identity + 0x80} ||
      raw.vtable_rva != std::optional<std::uintptr_t>{0x5000} ||
      raw.slot58_target_rva != std::optional<std::uintptr_t>{0x1000} ||
      raw.slot60_target_rva != std::optional<std::uintptr_t>{0x2000} ||
      raw.slotc8_target_rva != std::optional<std::uintptr_t>{0x3000} ||
      !raw.raw_slots_copied || !raw.caller_before_after_confirmed || !raw.repeated_raw_match ||
      raw.descriptor_provider || raw.source_context_root_word || raw.source_context_full_id_payload ||
      raw.context_is_source_projection || !ReturnedOutputsAbsent(first)) return false;
  // This pure finalizer models the successful fixture mailbox result. No
  // natural event/clock or game return witness is supplied by this operation.
  life::FinishStockPerkRawTargetsSourceMailbox12004V1(first, true);
  if (first.trigger_frontier_source->inputs.mailbox_after_accepted != std::optional<bool>{true}) return false;
  joined_wire = life::SerializeStockPerkRawTargetsSource12004V1(first);
  if (joined_wire.empty() || joined_wire == "null" || !ReturnedOutputsAbsent(first)) return false;

  Fixture partial_target;
  partial_target.hide_slot60 = true;
  auto partial = RunNewSourceQuery(partial_target);
  if (!ParentObservationsPreserved(partial_target, partial) ||
      partial.raw_targets_source->slot60_target_identity ||
      partial.raw_targets_source->slot60_unavailable_reason != "trigger_vtable_slot_unreadable" ||
      partial.raw_targets_source->slot58_target_rva != std::optional<std::uintptr_t>{0x1000} ||
      partial.raw_targets_source->slotc8_target_rva != std::optional<std::uintptr_t>{0x3000} ||
      partial.raw_targets_source->raw_slots_copied || !ReturnedOutputsAbsent(partial)) return false;

  Fixture after_guard_rejected;
  after_guard_rejected.reject_after_validator = true;
  auto rejected = RunNewSourceQuery(after_guard_rejected);
  if (!ParentObservationsPreserved(after_guard_rejected, rejected) ||
      rejected.raw_targets_source->caller_before_after_confirmed ||
      rejected.raw_targets_source->read_frame.caller_snapshot_confirmed ||
      rejected.trigger_frontier_source->copied_input_binding_ready ||
      !rejected.raw_targets_source->slot58_target_identity ||
      !rejected.raw_targets_source->slotc8_target_identity || !ReturnedOutputsAbsent(rejected)) return false;
  life::FinishStockPerkRawTargetsSourceMailbox12004V1(rejected, true);
  if (rejected.trigger_frontier_source->copied_input_binding_ready ||
      !rejected.raw_targets_source->slot58_target_identity || !ReturnedOutputsAbsent(rejected)) return false;
  active_fixture = nullptr;
  return true;
}

std::string_view StockPerkTriggerFrontierCurrentQueryWire12004() { return joined_wire; }
