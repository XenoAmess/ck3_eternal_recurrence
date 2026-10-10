// Actual 1.20.0.4 bindings: finite LIFE proof manifest; software DTO semantics retained.
#include "xar_bridge/ck3_12004_stock_perk_legality.hpp"
#include "xar_bridge/lifestyle_perk_predicate_288b1b0_12004.hpp"
#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <string_view>
#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif
namespace xar::ck3_12004::lifestyle {
namespace {
constexpr std::uintptr_t kDatabaseGetterRva = 0x8FCD40;
constexpr std::uintptr_t kPerkValidatorRva = 0x288AE00;
constexpr std::uintptr_t kValidatorPointerSlotRva = 0x4760A30;
constexpr std::uintptr_t kPerkPrimaryVtableRva = 0x4760A00;
constexpr std::uintptr_t kPerkSecondaryVtableRva = 0x47609D0;
constexpr std::uintptr_t kPlayedCharacterIdGlobalRva = 0x54DBC00;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kDatabaseSpanOffset = 0x50;
constexpr std::size_t kStableKeyOffset = 0x18;
constexpr std::size_t kPerkLifestyleOffset = 0x440;
constexpr std::size_t kMaximumRows = 512;
using Status = StockPerkLegalityStatusV1;
using StableKey = game::PlayerLifestyleWindowStableKeyV1;
struct RawSpan {
  std::uintptr_t data = 0;
  std::int32_t capacity = -1;
  std::int32_t count = -1;
  friend bool operator==(const RawSpan &, const RawSpan &) = default;
};
static_assert(sizeof(RawSpan) == 0x10);
struct PerkCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t state_byte = 0;
  std::array<std::uint8_t, 3> padding_09{};
  std::uint32_t state_0c = 0;
  std::uint32_t state_10 = 0;
  std::uint32_t state_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::uint32_t padding_24 = 0;
  std::uintptr_t definition = 0;
};
static_assert(sizeof(void *) == 8);
static_assert(sizeof(PerkCommand) == 0x30);
static_assert(offsetof(PerkCommand, secondary_vtable) == 0x18);
static_assert(offsetof(PerkCommand, played_character_id) == 0x20);
static_assert(offsetof(PerkCommand, definition) == 0x28);
struct Sample {
  StockPerkLegalityFrameV1 frame{};
  StockPerkLegalityPlayerStateV1 player_state{};
  std::uintptr_t database = 0;
  RawSpan span{};
  std::array<std::uintptr_t, kMaximumRows> definition_members{};
  std::uintptr_t target_definition = 0;
  StableKey target_key{};
  StableKey target_lifestyle_key{};
  bool native_legal = false;
  std::optional<StockPerkLegalitySourcePacketV1> source_packet{};
  friend bool operator==(const Sample &a, const Sample &b) {
    return a.frame == b.frame && a.player_state == b.player_state &&
        a.database == b.database && a.span == b.span &&
        a.definition_members == b.definition_members &&
        a.target_definition == b.target_definition &&
        a.target_key == b.target_key &&
        a.target_lifestyle_key == b.target_lifestyle_key &&
        a.native_legal == b.native_legal;
  }
};
bool CheckedAdd(std::uintptr_t base, std::size_t offset,
                std::uintptr_t &output) noexcept {
  if (base == 0 || offset >
                       std::numeric_limits<std::uintptr_t>::max() - base) {
    return false;
  }
  output = base + offset;
  return true;
}
bool Read(const StockPerkLegalityAccessV1 &access, std::uintptr_t address,
          void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr && address != 0 && output != nullptr &&
         size != 0 && access.read_memory(access.context, address, output, size);
}
template <typename T>
bool ReadAt(const StockPerkLegalityAccessV1 &access, std::uintptr_t owner,
            std::size_t offset, T &output) noexcept {
  std::uintptr_t address = 0;
  return CheckedAdd(owner, offset, address) &&
         Read(access, address, &output, sizeof(output));
}
bool StableKeyValid(const StableKey &key) noexcept {
  if (key.size == 0 || key.size >= key.bytes.size()) return false;
  for (std::uint16_t index = 0; index < key.size; ++index) {
    const auto c = key.bytes[index];
    if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_')) {
      return false;
    }
  }
  return true;
}
std::string_view View(const StableKey &key) noexcept {
  return StableKeyValid(key) ? std::string_view(key.bytes.data(), key.size)
                             : std::string_view{};
}
std::string_view TargetLifestyle(std::string_view target_key) noexcept {
  if (target_key == kDiplomacyThoughtfulPerkV1)
    return kDiplomacyThoughtfulLifestyleV1;
  if (target_key == kMartialServeTheCrownPerkV1)
    return kMartialPerkLifestyleV1;
  return kStockPerkLegalityLifestyleV1;
}
bool ReadStableKey(const StockPerkLegalityAccessV1 &access,
                   std::uintptr_t owner, StableKey &output) noexcept {
  output = {};
  std::uintptr_t native_string = 0;
  if (!CheckedAdd(owner, kStableKeyOffset, native_string)) return false;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadAt(access, native_string, 0x10, size) ||
      !ReadAt(access, native_string, 0x18, capacity) || size == 0 ||
      size > capacity || size >= output.bytes.size()) {
    return false;
  }
  std::uintptr_t bytes = native_string;
  if (capacity > 15 &&
      (!ReadAt(access, native_string, 0, bytes) || bytes == 0)) {
    return false;
  }
  if (!Read(access, bytes, output.bytes.data(), static_cast<std::size_t>(size))) {
    return false;
  }
  output.size = static_cast<std::uint16_t>(size);
  return StableKeyValid(output);
}
bool FrameValid(const StockPerkLegalityFrameV1 &frame) noexcept {
  return frame.episode_run_id[0] != 0 && frame.snapshot_id[0] != 0 &&
         frame.public_revision != 0 && frame.native_revision != 0 &&
         frame.proof_epoch != 0 &&
         frame.date_raw > 0 && frame.paused && frame.map_ready &&
         frame.played_character_alive && frame.storage_round_trip &&
         frame.played_character != 0 && frame.played_character_id != 0 &&
         frame.played_character_id != 0xFFFFFFFFU;
}
bool EnvironmentValid(const StockPerkLegalityEnvironmentV1 &env) noexcept {
  if (!env.exact_build_admitted ||
      env.admitted_exe_sha256 != kStockPerkLegalityExeSha256V1 ||
      env.module_base == 0 || env.get_character_perk_database == nullptr ||
      env.validate_perk_command == nullptr) {
    return false;
  }
  if (env.offline_fixture) return true;
  return reinterpret_cast<std::uintptr_t>(env.get_character_perk_database) ==
             env.module_base + kDatabaseGetterRva &&
         reinterpret_cast<std::uintptr_t>(env.validate_perk_command) ==
             env.module_base + kPerkValidatorRva;
}
bool GetDatabase(const StockPerkLegalityEnvironmentV1 &env,
                 std::uintptr_t &output) noexcept {
  output = 0;
#if defined(_MSC_VER)
  __try {
    output = reinterpret_cast<std::uintptr_t>(
        env.get_character_perk_database());
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = 0;
  }
#else
  output = reinterpret_cast<std::uintptr_t>(
      env.get_character_perk_database());
#endif
  return output != 0;
}
bool Validate(const StockPerkLegalityEnvironmentV1 &env,
              PerkCommand &command, bool &native_legal) noexcept {
  native_legal = false;
#if defined(_MSC_VER)
  __try {
    native_legal = env.validate_perk_command(&command, nullptr);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  native_legal = env.validate_perk_command(&command, nullptr);
#endif
  return true;
}
bool ReadPredicateSourceMemory(void *opaque, std::uintptr_t address,
                               void *output, std::size_t size) {
  const auto *access = static_cast<const StockPerkLegalityAccessV1 *>(opaque);
  return access != nullptr && Read(*access, address, output, size);
}

std::string_view FixedSnapshotIdentity(const StockPerkLegalityFrameV1 &frame) {
  const auto end = std::find(frame.snapshot_id.begin(), frame.snapshot_id.end(), '\0');
  if (end == frame.snapshot_id.end()) return {};
  return {frame.snapshot_id.data(), static_cast<std::size_t>(end - frame.snapshot_id.begin())};
}

StockPerkLegalitySourcePacketV1 CapturePredicateSource(
    const StockPerkLegalityEnvironmentV1 &env,
    const StockPerkLegalityAccessV1 &access,
    const StockPerkLegalityFrameV1 &frame,
    std::string_view target_key, std::uintptr_t command_identity) noexcept {
  StockPerkLegalitySourcePacketV1 out{};
  out.target_key.assign(target_key);
  auto &copied = out.read_frame;
  copied.executable_sha256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
  copied.module_base = env.module_base;
  copied.snapshot_identity.assign(FixedSnapshotIdentity(frame));
  copied.public_revision = frame.public_revision;
  copied.native_revision = frame.native_revision;
  copied.proof_epoch = frame.proof_epoch;
  copied.date_raw = frame.date_raw;
  copied.played_character_id = frame.played_character_id;
  copied.caller_domain = "stock_perk_legality_12004";
  StockPerkLegalityFrameV1 before{};
  const bool frame_before = access.capture_frame(access.context, before) &&
                            before == frame;
  StockPerkLegalitySourceQueryMetadataV1 metadata_before{};
  const bool metadata_observed = access.capture_source_query_metadata != nullptr &&
      access.capture_source_query_metadata(access.context, metadata_before);
  if (metadata_observed) {
    copied.frame_identity = metadata_before.frame_identity;
    copied.query_sequence = metadata_before.query_sequence;
    copied.mailbox_before_accepted = metadata_before.mailbox_before_accepted;
    copied.mailbox_after_accepted = metadata_before.mailbox_after_accepted;
    copied.module_image_size = metadata_before.module_image_size;
    copied.module_time_date_stamp = metadata_before.module_time_date_stamp;
  }
  copied.caller_snapshot_confirmed = frame_before && metadata_observed &&
                                     metadata_before.caller_snapshot_confirmed;
  if (access.capture_source_tls_array != nullptr) {
    std::uintptr_t tls_array = 0;
    if (access.capture_source_tls_array(access.context, tls_array) && tls_array != 0)
      out.current_thread_tls_array_identity = tls_array;
  }
  ::xar::ck3_12004::SourceReadFrame12004 source_frame{};
  source_frame.executable_sha256 = copied.executable_sha256;
  source_frame.module_base = copied.module_base;
  source_frame.snapshot_identity = copied.snapshot_identity;
  source_frame.frame_identity = copied.frame_identity.value_or(0);
  source_frame.query_sequence = copied.query_sequence.value_or(0);
  source_frame.native_revision = copied.native_revision;
  source_frame.proof_epoch = copied.proof_epoch;
  source_frame.date_raw = copied.date_raw;
  source_frame.caller_domain = copied.caller_domain;
  source_frame.caller_snapshot_confirmed = copied.caller_snapshot_confirmed;
  LifestylePerkReadonlyAccess12004 source_access{};
  source_access.module_base = env.module_base;
  source_access.read_context = const_cast<StockPerkLegalityAccessV1 *>(&access);
  source_access.read_memory = &ReadPredicateSourceMemory;
  source_access.current_thread_tls_array_identity = out.current_thread_tls_array_identity;
  source_access.current_query_source_frame = copied.caller_snapshot_confirmed
      ? &source_frame : nullptr;
  const auto source = ReadLifestylePerkPredicate288B1B012004(source_access, command_identity);
  const auto &i = source.inputs;
  out.inputs = {i.command_identity, i.registry_identity,
      i.requested_full_character_id_u32, i.registry_capacity_u32,
      i.indexed_character_identity, i.indexed_character_full_id_u32,
      i.used_fallback, i.selected_character_identity,
      i.selected_character_magic_u32, i.selected_character_full_id_u32,
      i.selected_character_field_1d0_u64, i.selected_perk_identity,
      i.selected_perk_magic_u32, i.prefix_admitted, i.unavailable_reason};
  if (source.tail.has_value())
    out.tail = StockPerkLegalitySourceTailV1{source.tail->value,
                                          source.tail->unavailable_reason};
  out.value = source.value;
  out.unavailable_reason = source.unavailable_reason;
  if (source.truth_trace.has_value()) {
    const auto &t = *source.truth_trace;
    out.truth_trace = StockPerkLegalitySourceTruthTraceV1{
        t.selected_perk_identity, t.compiled_trigger_receiver_identity,
        t.context_root_word, t.context_full_id_payload, t.evaluation_flag_raw_u8,
        t.trigger_vtable_raw, t.root_kind_getter_slot58_raw,
        t.root_mask_getter_slot60_raw, t.final_evaluator_slotc8_raw,
        t.source_projected_returned_raw_u8, t.value,
        t.context_projection_available, t.copied_frame_ready, t.input_leaf_ready,
        t.child_source_value_ready, t.native_callback_executed,
        t.actual_trigger_evaluation_observed, t.unavailable_reason};
  }
  StockPerkLegalityFrameV1 after{};
  StockPerkLegalitySourceQueryMetadataV1 metadata_after{};
  const bool frame_after = access.capture_frame(access.context, after) &&
                           after == frame;
  const bool metadata_after_observed = access.capture_source_query_metadata != nullptr &&
      access.capture_source_query_metadata(access.context, metadata_after);
  const bool metadata_stable = !metadata_observed ||
      (metadata_after_observed && metadata_after == metadata_before);
  if (!frame_before || !frame_after || !metadata_stable) {
    copied.caller_snapshot_confirmed = false;
    out.value.reset();
    if (out.tail.has_value()) out.tail->value.reset();
    if (out.truth_trace.has_value()) {
      out.truth_trace->value.reset();
      out.truth_trace->source_projected_returned_raw_u8.reset();
      out.truth_trace->copied_frame_ready = false;
    }
    out.unavailable_reason = "stock_perk_predicate_source_frame_changed";
  }
  return out;
}

bool SamePredicateSource(StockPerkLegalitySourcePacketV1 first,
                         StockPerkLegalitySourcePacketV1 second) noexcept {
  // Each command pointer refers to a distinct live local invocation, not a
  // reusable object identity. Compare its copied actual operands instead.
  first.inputs.command_identity = second.inputs.command_identity = 0;
  first.native_can_select_before.reset();
  first.native_can_select_after.reset();
  second.native_can_select_before.reset();
  second.native_can_select_after.reset();
  return first == second;
}
Status ReadOne(const StockPerkLegalityEnvironmentV1 &env,
               const StockPerkLegalityAccessV1 &access,
               std::string_view target_key, Sample &sample) noexcept {
  sample = {};
  if (!access.capture_frame(access.context, sample.frame) ||
      !FrameValid(sample.frame)) {
    return Status::unavailable_frame;
  }
  std::uint32_t global_player_id = 0xFFFFFFFFU;
  std::uint32_t character_id = 0xFFFFFFFFU;
  if (!Read(access, env.module_base + kPlayedCharacterIdGlobalRva,
            &global_player_id, sizeof(global_player_id)) ||
      !ReadAt(access, sample.frame.played_character,
              kCharacterIdentityOffset, character_id) ||
      global_player_id != sample.frame.played_character_id ||
      character_id != sample.frame.played_character_id) {
    return Status::unavailable_player;
  }
  if (!GetDatabase(env, sample.database) ||
      !ReadAt(access, sample.database, kDatabaseSpanOffset, sample.span) ||
      sample.span.count <= 0 || sample.span.capacity < 0 ||
      sample.span.count > static_cast<std::int32_t>(kMaximumRows) ||
      sample.span.count > sample.span.capacity || sample.span.data == 0) {
    return Status::unavailable_database;
  }
  std::uint32_t target_matches = 0;
  for (std::int32_t index = 0; index < sample.span.count; ++index) {
    std::uintptr_t row = 0;
    StableKey key{};
    const bool address_ready =
        CheckedAdd(sample.span.data,
                   static_cast<std::size_t>(index) * sizeof(std::uintptr_t),
                   row);
    const bool pointer_read =
        address_ready && Read(access, row, &sample.definition_members[index],
                              sizeof(std::uintptr_t));
    const bool key_read =
        pointer_read && sample.definition_members[index] != 0 &&
        ReadStableKey(access, sample.definition_members[index], key);
    if (!key_read) {
      return Status::unavailable_database;
    }
    if (View(key) == target_key) {
      ++target_matches;
      sample.target_definition = sample.definition_members[index];
      sample.target_key = key;
    }
  }
  if (target_matches != 1 || sample.target_definition == 0) {
    return Status::unavailable_candidate;
  }
  std::uintptr_t lifestyle = 0;
  if (!ReadAt(access, sample.target_definition, kPerkLifestyleOffset,
              lifestyle) ||
      lifestyle == 0 ||
      !ReadStableKey(access, lifestyle, sample.target_lifestyle_key) ||
      View(sample.target_lifestyle_key) != TargetLifestyle(target_key)) {
    return Status::unavailable_candidate;
  }
  const bool state_observed =
      access.read_target_player_state != nullptr
          ? access.read_target_player_state(access.context, sample.frame,
                                            lifestyle, target_key,
                                            sample.player_state)
          : target_key == kStockPerkLegalityTargetV1 &&
                access.read_player_state != nullptr &&
                access.read_player_state(access.context, sample.frame,
                                         lifestyle, sample.player_state);
  if (!state_observed ||
      !StableKeyValid(sample.player_state.target_lifestyle_key) ||
      View(sample.player_state.target_lifestyle_key) !=
          TargetLifestyle(target_key) ||
      sample.player_state.target_xp_total_raw < 0 ||
      sample.player_state.target_xp_within_level_raw < 0 ||
      sample.player_state.target_xp_per_level <= 0 ||
      sample.player_state.target_xp_per_level >
          std::numeric_limits<std::int64_t>::max() /
              kPlayerLifestyleFixedPointScaleV1 ||
      sample.player_state.target_xp_within_level_raw >=
          static_cast<std::int64_t>(sample.player_state.target_xp_per_level) *
              kPlayerLifestyleFixedPointScaleV1 ||
      sample.player_state.unspent_perk_points < 0 ||
      sample.player_state.used_perk_points < 0 ||
      !sample.player_state.owned_perk_state_known) {
    return Status::unavailable_state;
  }
  std::uintptr_t slot_target = 0;
  if (!Read(access, env.module_base + kValidatorPointerSlotRva,
            &slot_target, sizeof(slot_target)) ||
      slot_target != env.module_base + kPerkValidatorRva) {
    return Status::unavailable_validator;
  }
  PerkCommand command{};
  command.primary_vtable = env.module_base + kPerkPrimaryVtableRva;
  command.secondary_vtable = env.module_base + kPerkSecondaryVtableRva;
  command.played_character_id = sample.frame.played_character_id;
  command.definition = sample.target_definition;
  sample.source_packet = CapturePredicateSource(env, access, sample.frame,
      target_key, reinterpret_cast<std::uintptr_t>(&command));
  if (!Validate(env, command, sample.native_legal)) {
    return Status::unavailable_validator;
  }
  return sample.native_legal ? Status::observed_native_legal
                             : Status::observed_native_illegal;
}
} // namespace
StockPerkLegalityEnvironmentV1 BindStockPerkLegalityEnvironment12004V1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_exe_sha256) noexcept {
  StockPerkLegalityEnvironmentV1 output{};
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_exe_sha256 = admitted_exe_sha256;
  output.module_base = module_base;
  if (!exact_build_admitted || module_base == 0 ||
      admitted_exe_sha256 != kStockPerkLegalityExeSha256V1) {
    return output;
  }
  output.get_character_perk_database =
      reinterpret_cast<StockPerkGetDatabaseV1>(module_base +
                                                kDatabaseGetterRva);
  output.validate_perk_command =
      reinterpret_cast<StockPerkValidateCommandV1>(module_base +
                                                    kPerkValidatorRva);
  return output;
}
StockPerkLegalityResultV1 ReadStockPerkLegality12004V1(
    const StockPerkLegalityEnvironmentV1 &env,
    const StockPerkLegalityAccessV1 &access) noexcept {
  return ReadStockPerkLegality12004V1(env, access, kStockPerkLegalityTargetV1);
}
StockPerkLegalityResultV1 ReadStockPerkLegality12004V1(
    const StockPerkLegalityEnvironmentV1 &env,
    const StockPerkLegalityAccessV1 &access,
    std::string_view target_key) noexcept {
  StockPerkLegalityResultV1 out{};
  if (target_key != kStockPerkLegalityTargetV1 &&
      target_key != kStockPerkLegalityFollowupTargetV1 &&
      target_key != kStockPerkLegalityNextTargetV1 &&
      target_key != kStockPerkLegalityCollectTaxesTargetV1 &&
      target_key != kDiplomacyThoughtfulPerkV1 &&
      target_key != kMartialServeTheCrownPerkV1) {
    out.status = Status::unavailable_candidate;
    return out;
  }
  if (!EnvironmentValid(env)) {
    out.status = Status::unavailable_exact_build;
    return out;
  }
  if (access.is_application_main_thread == nullptr ||
      access.capture_frame == nullptr || access.read_memory == nullptr ||
      (access.read_player_state == nullptr &&
       access.read_target_player_state == nullptr) ||
      (target_key != kStockPerkLegalityTargetV1 &&
       access.read_target_player_state == nullptr) ||
      !access.is_application_main_thread(access.context)) {
    out.status = Status::unavailable_binding;
    return out;
  }
  Sample first{};
  const auto first_status = ReadOne(env, access, target_key, first);
  if (first.source_packet.has_value()) {
    out.source_packet = first.source_packet;
    if (first_status == Status::observed_native_legal ||
        first_status == Status::observed_native_illegal)
      out.source_packet->native_can_select_before = first.native_legal;
  }
  if (first_status != Status::observed_native_illegal &&
      first_status != Status::observed_native_legal) {
    out.status = first_status;
    return out;
  }
  Sample second{};
  const auto second_status = ReadOne(env, access, target_key, second);
  if (out.source_packet.has_value() &&
      (second_status == Status::observed_native_legal ||
       second_status == Status::observed_native_illegal))
    out.source_packet->native_can_select_after = second.native_legal;
  if (second_status != Status::observed_native_illegal &&
      second_status != Status::observed_native_legal) {
    out.status = second_status;
    return out;
  }
  StockPerkLegalityFrameV1 final_frame{};
  if (!access.capture_frame(access.context, final_frame) ||
      !FrameValid(final_frame) || first != second ||
      final_frame != first.frame) {
    out.status = Status::unavailable_drift;
    return out;
  }
  const bool state_agrees =
      View(first.player_state.target_lifestyle_key) ==
          TargetLifestyle(target_key) &&
      first.player_state.unspent_perk_points > 0 &&
      !first.player_state.target_perk_owned;
  if (first.native_legal && !state_agrees) {
    out.status = Status::unavailable_state;
    return out;
  }
  out.status = first.native_legal ? Status::observed_native_legal
                                  : Status::observed_native_illegal;
  out.frame = first.frame;
  out.target_key = first.target_key;
  out.lifestyle_key = first.target_lifestyle_key;
  out.observed_unspent_points =
      first.player_state.unspent_perk_points;
  out.observed_used_points = first.player_state.used_perk_points;
  out.observed_target_xp_total_raw =
      first.player_state.target_xp_total_raw;
  out.observed_target_xp_within_level_raw =
      first.player_state.target_xp_within_level_raw;
  out.observed_target_xp_per_level =
      first.player_state.target_xp_per_level;
  out.observed_target_owned = first.player_state.target_perk_owned;
  out.scanned_database_rows = first.span.count;
  out.validator_invoked_twice = true;
  out.target_definition = first.target_definition;
  if (out.source_packet.has_value()) {
    auto &packet = *out.source_packet;
    packet.repeated_source_match = second.source_packet.has_value() &&
        SamePredicateSource(*first.source_packet, *second.source_packet);
    if (!packet.repeated_source_match) {
      packet.read_frame.caller_snapshot_confirmed = false;
      packet.value.reset();
      if (packet.tail.has_value()) packet.tail->value.reset();
      if (packet.truth_trace.has_value()) {
        packet.truth_trace->value.reset();
        packet.truth_trace->source_projected_returned_raw_u8.reset();
        packet.truth_trace->copied_frame_ready = false;
      }
      packet.unavailable_reason = "stock_perk_predicate_source_changed";
    }
  }
  return out;
}
std::string_view StockPerkLegalityStatusKey12004V1(Status status) noexcept {
  switch (status) {
  case Status::unavailable_exact_build: return "unavailable_exact_build";
  case Status::unavailable_binding: return "unavailable_binding";
  case Status::unavailable_frame: return "unavailable_frame";
  case Status::unavailable_player: return "unavailable_player";
  case Status::unavailable_database: return "unavailable_database";
  case Status::unavailable_candidate: return "unavailable_candidate";
  case Status::unavailable_state: return "unavailable_state";
  case Status::unavailable_validator: return "unavailable_validator";
  case Status::unavailable_drift: return "unavailable_drift";
  case Status::observed_native_illegal: return "observed_native_illegal";
  case Status::observed_native_legal: return "observed_native_legal";
  }
  return "unavailable_binding";
}
namespace {
void SourceJsonString(std::string &out, std::string_view value) {
  out += '"';
  static constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) {
      out += "\\u00";
      out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  out += '"';
}
template<class T>
void SourceJsonOptional(std::string &out, const std::optional<T> &value) {
  out += value.has_value() ? std::to_string(*value) : "null";
}
void SourceJsonOptional(std::string &out, const std::optional<bool> &value) {
  out += !value.has_value() ? "null" : *value ? "true" : "false";
}
}
std::string SerializeStockPerkLegalitySourcePacket12004V1(
    const std::optional<StockPerkLegalitySourcePacketV1> &packet) {
  if (!packet.has_value()) return "null";
  const auto &p = *packet;
  const auto &f = p.read_frame;
  std::string out = "{\"schema\":\"lifestyle_perk_predicate_source_12004_v1\",\"read_only\":true,\"target_key\":";
  SourceJsonString(out, p.target_key);
  out += ",\"read_frame\":{\"executable_sha256\":";
  SourceJsonString(out, f.executable_sha256);
  out += ",\"module_base\":" + std::to_string(f.module_base);
  out += ",\"snapshot_identity\":"; SourceJsonString(out, f.snapshot_identity);
  out += ",\"frame_identity\":"; SourceJsonOptional(out, f.frame_identity);
  out += ",\"query_sequence\":"; SourceJsonOptional(out, f.query_sequence);
  out += ",\"mailbox_before_accepted\":"; SourceJsonOptional(out, f.mailbox_before_accepted);
  out += ",\"mailbox_after_accepted\":"; SourceJsonOptional(out, f.mailbox_after_accepted);
  out += ",\"module_image_size\":"; SourceJsonOptional(out, f.module_image_size);
  out += ",\"module_time_date_stamp\":"; SourceJsonOptional(out, f.module_time_date_stamp);
  out += ",\"public_revision\":" + std::to_string(f.public_revision);
  out += ",\"native_revision\":" + std::to_string(f.native_revision);
  out += ",\"proof_epoch\":" + std::to_string(f.proof_epoch);
  out += ",\"date_raw\":" + std::to_string(f.date_raw);
  out += ",\"played_character_id\":" + std::to_string(f.played_character_id);
  out += ",\"caller_domain\":"; SourceJsonString(out, f.caller_domain);
  out += ",\"caller_snapshot_confirmed\":";
  out += f.caller_snapshot_confirmed ? "true" : "false";
  out += "},\"current_thread_tls_array_identity\":";
  SourceJsonOptional(out, p.current_thread_tls_array_identity);
  out += ",\"inputs\":{\"command_identity\":" + std::to_string(p.inputs.command_identity);
#define XAR_PERK_SOURCE_OPTIONAL(name) out += ",\"" #name "\":"; SourceJsonOptional(out, p.inputs.name)
  XAR_PERK_SOURCE_OPTIONAL(registry_identity);
  XAR_PERK_SOURCE_OPTIONAL(requested_full_character_id_u32);
  XAR_PERK_SOURCE_OPTIONAL(registry_capacity_u32);
  XAR_PERK_SOURCE_OPTIONAL(indexed_character_identity);
  XAR_PERK_SOURCE_OPTIONAL(indexed_character_full_id_u32);
  XAR_PERK_SOURCE_OPTIONAL(used_fallback);
  XAR_PERK_SOURCE_OPTIONAL(selected_character_identity);
  XAR_PERK_SOURCE_OPTIONAL(selected_character_magic_u32);
  XAR_PERK_SOURCE_OPTIONAL(selected_character_full_id_u32);
  XAR_PERK_SOURCE_OPTIONAL(selected_character_field_1d0_u64);
  XAR_PERK_SOURCE_OPTIONAL(selected_perk_identity);
  XAR_PERK_SOURCE_OPTIONAL(selected_perk_magic_u32);
  XAR_PERK_SOURCE_OPTIONAL(prefix_admitted);
#undef XAR_PERK_SOURCE_OPTIONAL
  out += ",\"unavailable_reason\":"; SourceJsonString(out, p.inputs.unavailable_reason);
  out += "},\"tail\":";
  if (!p.tail.has_value()) out += "null";
  else {
    out += "{\"value\":"; SourceJsonOptional(out, p.tail->value);
    out += ",\"unavailable_reason\":"; SourceJsonString(out, p.tail->unavailable_reason);
    out += '}';
  }
  out += ",\"truth_trace\":";
  if (!p.truth_trace.has_value()) out += "null";
  else {
    const auto &t = *p.truth_trace;
    out += "{\"selected_perk_identity\":" + std::to_string(t.selected_perk_identity);
#define XAR_PERK_TRACE_OPTIONAL(name) out += ",\"" #name "\":"; SourceJsonOptional(out, t.name)
    XAR_PERK_TRACE_OPTIONAL(compiled_trigger_receiver_identity);
    XAR_PERK_TRACE_OPTIONAL(context_root_word);
    XAR_PERK_TRACE_OPTIONAL(context_full_id_payload);
    XAR_PERK_TRACE_OPTIONAL(evaluation_flag_raw_u8);
    XAR_PERK_TRACE_OPTIONAL(trigger_vtable_raw);
    XAR_PERK_TRACE_OPTIONAL(root_kind_getter_slot58_raw);
    XAR_PERK_TRACE_OPTIONAL(root_mask_getter_slot60_raw);
    XAR_PERK_TRACE_OPTIONAL(final_evaluator_slotc8_raw);
    XAR_PERK_TRACE_OPTIONAL(source_projected_returned_raw_u8);
    XAR_PERK_TRACE_OPTIONAL(value);
#undef XAR_PERK_TRACE_OPTIONAL
#define XAR_PERK_TRACE_BOOL(name) out += ",\"" #name "\":"; out += t.name ? "true" : "false"
    XAR_PERK_TRACE_BOOL(context_projection_available);
    XAR_PERK_TRACE_BOOL(copied_frame_ready);
    XAR_PERK_TRACE_BOOL(input_leaf_ready);
    XAR_PERK_TRACE_BOOL(child_source_value_ready);
    XAR_PERK_TRACE_BOOL(native_callback_executed);
    XAR_PERK_TRACE_BOOL(actual_trigger_evaluation_observed);
#undef XAR_PERK_TRACE_BOOL
    out += ",\"unavailable_reason\":"; SourceJsonString(out, t.unavailable_reason);
    out += '}';
  }
  out += ",\"value\":"; SourceJsonOptional(out, p.value);
  out += ",\"unavailable_reason\":"; SourceJsonString(out, p.unavailable_reason);
  out += ",\"native_can_select_before\":"; SourceJsonOptional(out, p.native_can_select_before);
  out += ",\"native_can_select_after\":"; SourceJsonOptional(out, p.native_can_select_after);
  out += ",\"repeated_source_match\":";
  out += p.repeated_source_match ? "true" : "false";
  out += '}';
  return out;
}
} // namespace xar::ck3_12004::lifestyle
