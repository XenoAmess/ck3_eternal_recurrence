#include "xar_bridge/player_lifestyle_stock_perk_legality_v1.hpp"
#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"

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

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kDatabaseGetterRva = 0x88EC20;
constexpr std::uintptr_t kPerkValidatorRva = 0x25DFAF0;
constexpr std::uintptr_t kValidatorPointerSlotRva = 0x4323A80;
constexpr std::uintptr_t kPerkPrimaryVtableRva = 0x4323A50;
constexpr std::uintptr_t kPerkSecondaryVtableRva = 0x4323A20;
constexpr std::uintptr_t kPlayedCharacterIdGlobalRva = 0x4FE7EE0;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kDatabaseSpanOffset = 0x68;
constexpr std::size_t kStableKeyOffset = 0x18;
constexpr std::size_t kPerkLifestyleOffset = 0x468;
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

  friend bool operator==(const Sample &, const Sample &) = default;
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

Status ReadOne(const StockPerkLegalityEnvironmentV1 &env,
               const StockPerkLegalityAccessV1 &access, Sample &sample) noexcept {
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
    if (View(key) == kStockPerkLegalityTargetV1) {
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
      View(sample.target_lifestyle_key) != kStockPerkLegalityLifestyleV1) {
    return Status::unavailable_candidate;
  }
  if (!access.read_player_state(access.context, sample.frame, lifestyle,
                                sample.player_state) ||
      !StableKeyValid(sample.player_state.target_lifestyle_key) ||
      View(sample.player_state.target_lifestyle_key) !=
          kStockPerkLegalityLifestyleV1 ||
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
  if (!Validate(env, command, sample.native_legal)) {
    return Status::unavailable_validator;
  }
  return sample.native_legal ? Status::observed_native_legal
                             : Status::observed_native_illegal;
}

} // namespace

StockPerkLegalityEnvironmentV1 BindStockPerkLegalityEnvironmentV1(
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

StockPerkLegalityResultV1 ReadStockPerkLegalityV1(
    const StockPerkLegalityEnvironmentV1 &env,
    const StockPerkLegalityAccessV1 &access) noexcept {
  StockPerkLegalityResultV1 out{};
  if (!EnvironmentValid(env)) {
    out.status = Status::unavailable_exact_build;
    return out;
  }
  if (access.is_application_main_thread == nullptr ||
      access.capture_frame == nullptr || access.read_memory == nullptr ||
      access.read_player_state == nullptr ||
      !access.is_application_main_thread(access.context)) {
    out.status = Status::unavailable_binding;
    return out;
  }
  Sample first{};
  const auto first_status = ReadOne(env, access, first);
  if (first_status != Status::observed_native_illegal &&
      first_status != Status::observed_native_legal) {
    out.status = first_status;
    return out;
  }
  Sample second{};
  const auto second_status = ReadOne(env, access, second);
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
          kStockPerkLegalityLifestyleV1 &&
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
  return out;
}

std::string_view StockPerkLegalityStatusKeyV1(Status status) noexcept {
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

} // namespace xar::ck3_11906
