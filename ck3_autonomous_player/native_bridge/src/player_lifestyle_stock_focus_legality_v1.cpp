#include "xar_bridge/player_lifestyle_stock_focus_legality_v1.hpp"
#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"

#include <array>
#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

// Exact ck3.exe 1.19.0.6: CharacterLifestyleWindow refresh at 0x132CE0A
// loads this definition database, then iterates its +0xF20 pointer span.
constexpr std::uintptr_t kFocusDatabaseGlobalRva = 0x570BDE8;
constexpr std::uintptr_t kFocusValidatorRva = 0x25DF570;
constexpr std::uintptr_t kValidatorPointerSlotRva = 0x4323C10;
constexpr std::uintptr_t kFocusPrimaryVtableRva = 0x4323BE0;
constexpr std::uintptr_t kFocusSecondaryVtableRva = 0x4323BB0;
constexpr std::uintptr_t kPlayedCharacterIdGlobalRva = 0x4FE7EE0;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kDatabaseSpanOffset = 0xF20;
constexpr std::size_t kStableKeyOffset = 0x18;
constexpr std::size_t kFocusLifestyleOffset = 0x880;
constexpr std::size_t kMaximumRows = game::kPlayerLifestyleWindowMaximumFocusesV1;

using Status = StockFocusLegalityStatusV1;
using StableKey = game::PlayerLifestyleWindowStableKeyV1;

struct RawSpan {
  std::uintptr_t data = 0;
  std::int32_t capacity = -1;
  std::int32_t count = -1;

  friend bool operator==(const RawSpan &, const RawSpan &) = default;
};
static_assert(sizeof(void *) == 8);
static_assert(sizeof(RawSpan) == 0x10);

struct FocusCommand {
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
  std::uint32_t current_player_id = 0xFFFFFFFFU;
  std::uint32_t padding_34 = 0;
};
static_assert(sizeof(FocusCommand) == 0x38);
static_assert(offsetof(FocusCommand, secondary_vtable) == 0x18);
static_assert(offsetof(FocusCommand, played_character_id) == 0x20);
static_assert(offsetof(FocusCommand, definition) == 0x28);
static_assert(offsetof(FocusCommand, current_player_id) == 0x30);

struct Sample {
  StockFocusLegalityFrameV1 frame{};
  std::uintptr_t database = 0;
  RawSpan span{};
  std::array<std::uintptr_t, kMaximumRows> members{};
  std::array<StableKey, kMaximumRows> keys{};
  std::uintptr_t target_definition = 0;
  StableKey target_key{};
  StableKey lifestyle_key{};
  StockFocusTargetProgressV1 target_progress{};
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

bool Read(const StockFocusLegalityAccessV1 &access, std::uintptr_t address,
          void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr && address != 0 && output != nullptr &&
         size != 0 && access.read_memory(access.context, address, output, size);
}

template <typename T>
bool ReadAt(const StockFocusLegalityAccessV1 &access, std::uintptr_t owner,
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

bool ReadStableKey(const StockFocusLegalityAccessV1 &access,
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

bool FrameValid(const StockFocusLegalityFrameV1 &frame) noexcept {
  return frame.episode_run_id[0] != 0 && frame.snapshot_id[0] != 0 &&
         frame.public_revision != 0 && frame.native_revision != 0 &&
         frame.proof_epoch != 0 && frame.date_raw > 0 && frame.paused &&
         frame.map_ready && frame.played_character_alive &&
         frame.storage_round_trip && frame.played_character != 0 &&
         frame.played_character_id != 0 &&
         frame.played_character_id != 0xFFFFFFFFU;
}

bool EnvironmentValid(const StockFocusLegalityEnvironmentV1 &env) noexcept {
  if (!env.exact_build_admitted ||
      env.admitted_exe_sha256 != kStockFocusLegalityExeSha256V1 ||
      env.module_base == 0 || env.validate_focus_command == nullptr) {
    return false;
  }
  return env.offline_fixture ||
         reinterpret_cast<std::uintptr_t>(env.validate_focus_command) ==
             env.module_base + kFocusValidatorRva;
}

bool Validate(const StockFocusLegalityEnvironmentV1 &env,
              FocusCommand &command, bool &native_legal) noexcept {
  native_legal = false;
#if defined(_MSC_VER)
  __try {
    native_legal = env.validate_focus_command(&command, nullptr);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  native_legal = env.validate_focus_command(&command, nullptr);
#endif
  return true;
}

bool ValidTargetProgress(const StockFocusTargetProgressV1 &progress) noexcept {
  if (!progress.available || progress.xp_total_raw < 0 ||
      progress.xp_within_level_raw < 0 || progress.xp_per_level <= 0 ||
      progress.unspent_perk_points < 0 || progress.used_perk_points < 0 ||
      progress.xp_per_level >
          std::numeric_limits<std::int64_t>::max() /
              kPlayerLifestyleFixedPointScaleV1) {
    return false;
  }
  return progress.xp_within_level_raw <
      static_cast<std::int64_t>(progress.xp_per_level) *
          kPlayerLifestyleFixedPointScaleV1;
}

Status ReadOne(const StockFocusLegalityEnvironmentV1 &env,
               const StockFocusLegalityAccessV1 &access, Sample &sample) noexcept {
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

  if (!Read(access, env.module_base + kFocusDatabaseGlobalRva,
            &sample.database, sizeof(sample.database)) ||
      sample.database == 0 ||
      !ReadAt(access, sample.database, kDatabaseSpanOffset, sample.span) ||
      sample.span.count <= 0 || sample.span.capacity < 0 ||
      sample.span.count > static_cast<std::int32_t>(kMaximumRows) ||
      sample.span.count > sample.span.capacity || sample.span.data == 0) {
    return Status::unavailable_database;
  }
  std::uint32_t target_matches = 0;
  for (std::int32_t index = 0; index < sample.span.count; ++index) {
    std::uintptr_t row = 0;
    if (!CheckedAdd(sample.span.data,
                    static_cast<std::size_t>(index) * sizeof(std::uintptr_t),
                    row) ||
        !Read(access, row, &sample.members[index], sizeof(std::uintptr_t)) ||
        sample.members[index] == 0 ||
        !ReadStableKey(access, sample.members[index], sample.keys[index])) {
      return Status::unavailable_database;
    }
    if (View(sample.keys[index]) == kStockFocusLegalityTargetV1) {
      ++target_matches;
      sample.target_definition = sample.members[index];
      sample.target_key = sample.keys[index];
    }
  }
  if (target_matches != 1 || sample.target_definition == 0) {
    return Status::unavailable_candidate;
  }
  std::uintptr_t lifestyle = 0;
  if (!ReadAt(access, sample.target_definition, kFocusLifestyleOffset,
              lifestyle) ||
      lifestyle == 0 ||
      !ReadStableKey(access, lifestyle, sample.lifestyle_key) ||
      View(sample.lifestyle_key) != kStockFocusLegalityLifestyleV1) {
    return Status::unavailable_candidate;
  }
  if (access.capture_target_progress != nullptr) {
    StockFocusTargetProgressV1 progress{};
    if (access.capture_target_progress(access.context, sample.frame,
                                       lifestyle, progress) &&
        ValidTargetProgress(progress)) {
      sample.target_progress = progress;
    }
  }
  std::uintptr_t slot_target = 0;
  if (!Read(access, env.module_base + kValidatorPointerSlotRva,
            &slot_target, sizeof(slot_target)) ||
      slot_target != env.module_base + kFocusValidatorRva) {
    return Status::unavailable_validator;
  }
  FocusCommand command{};
  command.primary_vtable = env.module_base + kFocusPrimaryVtableRva;
  command.secondary_vtable = env.module_base + kFocusSecondaryVtableRva;
  command.played_character_id = sample.frame.played_character_id;
  command.definition = sample.target_definition;
  command.current_player_id = sample.frame.played_character_id;
  if (!Validate(env, command, sample.native_legal)) {
    return Status::unavailable_validator;
  }
  return sample.native_legal ? Status::observed_native_legal
                             : Status::observed_native_illegal;
}

} // namespace

StockFocusLegalityEnvironmentV1 BindStockFocusLegalityEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_exe_sha256) noexcept {
  StockFocusLegalityEnvironmentV1 out{};
  out.exact_build_admitted = exact_build_admitted;
  out.admitted_exe_sha256 = admitted_exe_sha256;
  out.module_base = module_base;
  if (exact_build_admitted && module_base != 0 &&
      admitted_exe_sha256 == kStockFocusLegalityExeSha256V1) {
    out.validate_focus_command =
        reinterpret_cast<StockFocusValidateCommandV1>(module_base +
                                                       kFocusValidatorRva);
  }
  return out;
}

StockFocusLegalityResultV1 ReadStockFocusLegalityV1(
    const StockFocusLegalityEnvironmentV1 &env,
    const StockFocusLegalityAccessV1 &access) noexcept {
  StockFocusLegalityResultV1 out{};
  if (!EnvironmentValid(env)) {
    out.status = Status::unavailable_exact_build;
    return out;
  }
  if (access.is_application_main_thread == nullptr ||
      access.capture_frame == nullptr || access.read_memory == nullptr ||
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
  StockFocusLegalityFrameV1 final_frame{};
  if (!access.capture_frame(access.context, final_frame) ||
      !FrameValid(final_frame) || first != second ||
      final_frame != first.frame) {
    out.status = Status::unavailable_drift;
    return out;
  }
  out.status = first.native_legal ? Status::observed_native_legal
                                  : Status::observed_native_illegal;
  out.frame = first.frame;
  out.target_key = first.target_key;
  out.lifestyle_key = first.lifestyle_key;
  out.scanned_database_rows = first.span.count;
  out.validator_invoked_twice = true;
  out.target_progress = first.target_progress;
  out.target_definition = first.target_definition;
  return out;
}

std::string_view StockFocusLegalityStatusKeyV1(Status status) noexcept {
  switch (status) {
  case Status::unavailable_exact_build: return "unavailable_exact_build";
  case Status::unavailable_binding: return "unavailable_binding";
  case Status::unavailable_frame: return "unavailable_frame";
  case Status::unavailable_player: return "unavailable_player";
  case Status::unavailable_database: return "unavailable_database";
  case Status::unavailable_candidate: return "unavailable_candidate";
  case Status::unavailable_validator: return "unavailable_validator";
  case Status::unavailable_drift: return "unavailable_drift";
  case Status::observed_native_illegal: return "observed_native_illegal";
  case Status::observed_native_legal: return "observed_native_legal";
  }
  return "unavailable_binding";
}

} // namespace xar::ck3_11906
