#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using Failure = game::PlayerLifestyleSnapshotFailureV1;
using CandidateStatus = game::PlayerLifestyleCandidateCollectionStatusV1;
using CandidateFailure = game::PlayerLifestyleCandidateCollectionFailureV1;
using Presence = game::PlayerLifestyleFocusPresenceV1;
using Result = game::ReadPlayerLifestyleSnapshotResultV1;
using Snapshot = game::PlayerLifestyleSnapshotV1;
using State = game::PlayerLifestyleStateV1;

static_assert(sizeof(void *) == 8,
              "player lifestyle snapshot is x64-only");

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ParseCanonicalNativeSnapshotId(std::string_view value,
                                    std::uint64_t &revision) noexcept {
  constexpr std::string_view prefix = "native:";
  if (!value.starts_with(prefix)) return false;

  const auto digits = value.substr(prefix.size());
  if (digits.empty() || digits.front() < '1' || digits.front() > '9') {
    return false;
  }
  std::uint64_t parsed = 0;
  for (const char character : digits) {
    if (character < '0' || character > '9') return false;
    const auto digit = static_cast<std::uint64_t>(character - '0');
    if (parsed > (std::numeric_limits<std::uint64_t>::max() - digit) / 10) {
      return false;
    }
    parsed = parsed * 10 + digit;
  }
  revision = parsed;
  return true;
}

bool ValidSnapshotId(std::string_view value) noexcept {
  if (value.empty() ||
      value.size() >= game::kPlayerLifestyleSnapshotIdCapacityV1) {
    return false;
  }
  std::uint64_t native_revision = 0;
  if (ParseCanonicalNativeSnapshotId(value, native_revision)) return true;

  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= 'A' && character <= 'Z') ||
          (character >= '0' && character <= '9') || character == '_' ||
          character == '-' || character == '.')) {
      return false;
    }
  }
  return true;
}

bool ValidStableKey(const game::PlayerLifestyleStableKeyV1 &value) noexcept {
  if (value.size == 0 ||
      value.size >= game::kPlayerLifestyleStableKeyCapacityV1 ||
      value.bytes[value.size] != '\0') {
    return false;
  }
  const auto view = PlayerLifestyleStableKeyViewV1(value);
  if (view.size() != value.size) return false;
  for (const char character : view) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool EmptyStableKey(const game::PlayerLifestyleStableKeyV1 &value) noexcept {
  return value.size == 0 && value.bytes[0] == '\0';
}

template <std::size_t Capacity>
bool UniqueKeys(
    const std::array<game::PlayerLifestyleStableKeyV1, Capacity> &values,
    std::uint32_t count) noexcept {
  for (std::uint32_t left = 0; left < count; ++left) {
    for (std::uint32_t right = left + 1; right < count; ++right) {
      if (values[left] == values[right]) return false;
    }
  }
  return true;
}

template <std::size_t Capacity>
bool UniqueCandidateKeys(
    const std::array<game::PlayerLifestyleLegalCandidateV1, Capacity> &values,
    std::uint32_t count) noexcept {
  for (std::uint32_t left = 0; left < count; ++left) {
    for (std::uint32_t right = left + 1; right < count; ++right) {
      if (values[left].key == values[right].key) return false;
    }
  }
  return true;
}

Failure ValidateCandidateCollection(
    CandidateStatus status, CandidateFailure reason, std::uint32_t count,
    const game::PlayerLifestyleLegalCandidateV1 *values,
    std::size_t capacity, bool focus) noexcept {
  const auto invalid = focus ? Failure::legal_focus_collection_invalid
                             : Failure::legal_perk_collection_invalid;
  if (status == CandidateStatus::unavailable) {
    return reason != CandidateFailure::none && count == 0
        ? Failure::none
        : invalid;
  }
  if (status != CandidateStatus::available ||
      reason != CandidateFailure::none || count > capacity) {
    return invalid;
  }
  for (std::uint32_t index = 0; index < count; ++index) {
    if (!ValidStableKey(values[index].key) ||
        !ValidStableKey(values[index].lifestyle_key)) {
      return Failure::stable_key_invalid;
    }
  }
  return Failure::none;
}

Failure ValidateState(const State &state) noexcept {
  if (state.current_focus_presence == Presence::unknown) {
    return Failure::current_focus_invariant_failed;
  }
  if (state.current_focus_presence == Presence::absent) {
    if (!EmptyStableKey(state.current_focus_key) ||
        !EmptyStableKey(state.current_lifestyle_key) ||
        state.current_lifestyle_progress_present) {
      return Failure::current_focus_invariant_failed;
    }
  } else {
    if (!ValidStableKey(state.current_focus_key) ||
        !ValidStableKey(state.current_lifestyle_key) ||
        !state.current_lifestyle_progress_present ||
        state.current_lifestyle_progress.lifestyle_key !=
            state.current_lifestyle_key) {
      return Failure::current_focus_invariant_failed;
    }
    const auto &progress = state.current_lifestyle_progress;
    const auto level_raw =
        static_cast<std::int64_t>(progress.xp_per_level) *
        kPlayerLifestyleFixedPointScaleV1;
    if (progress.xp_total_raw < 0 || progress.xp_within_level_raw < 0 ||
        progress.xp_per_level <= 0 || level_raw <= 0 ||
        progress.xp_within_level_raw >= level_raw ||
        progress.unspent_perk_points < 0 || progress.used_perk_points < 0) {
      return Failure::lifestyle_progress_invalid;
    }
  }

  if (state.owned_perk_count >
      game::kPlayerLifestyleMaximumOwnedPerksV1) {
    return Failure::owned_perk_collection_invalid;
  }
  for (std::uint32_t index = 0; index < state.owned_perk_count; ++index) {
    if (!ValidStableKey(state.owned_perk_keys[index])) {
      return Failure::stable_key_invalid;
    }
  }
  if (!UniqueKeys(state.owned_perk_keys, state.owned_perk_count)) {
    return Failure::duplicate_stable_key;
  }

  auto candidate_failure = ValidateCandidateCollection(
      state.legal_focus_candidate_status,
      state.legal_focus_candidate_unavailable_reason,
      state.legal_focus_candidate_count,
      state.legal_focus_candidates.data(),
      state.legal_focus_candidates.size(), true);
  if (candidate_failure != Failure::none) return candidate_failure;
  candidate_failure = ValidateCandidateCollection(
      state.legal_perk_candidate_status,
      state.legal_perk_candidate_unavailable_reason,
      state.legal_perk_candidate_count,
      state.legal_perk_candidates.data(),
      state.legal_perk_candidates.size(), false);
  if (candidate_failure != Failure::none) return candidate_failure;

  if (!UniqueCandidateKeys(state.legal_focus_candidates,
                           state.legal_focus_candidate_count) ||
      !UniqueCandidateKeys(state.legal_perk_candidates,
                           state.legal_perk_candidate_count)) {
    return Failure::duplicate_stable_key;
  }
  for (std::uint32_t candidate = 0;
       candidate < state.legal_perk_candidate_count; ++candidate) {
    for (std::uint32_t owned = 0; owned < state.owned_perk_count; ++owned) {
      if (state.legal_perk_candidates[candidate].key ==
          state.owned_perk_keys[owned]) {
        return Failure::legal_perk_collection_invalid;
      }
    }
  }
  return Failure::none;
}

bool ValidRequest(const PlayerLifestyleSnapshotRequestV1 &request) noexcept {
  if (!ValidSnapshotId(request.expected_snapshot_id) ||
      request.expected_public_revision == 0 ||
      request.expected_native_revision == 0 ||
      request.expected_player_character_id == -1) {
    return false;
  }

  if (request.expected_snapshot_id.starts_with("native:")) {
    std::uint64_t parsed_native_revision = 0;
    return ParseCanonicalNativeSnapshotId(request.expected_snapshot_id,
                                          parsed_native_revision) &&
        parsed_native_revision == request.expected_native_revision;
  }
  return true;
}

Failure ValidateInitialFrame(
    const PlayerLifestyleSnapshotFrameV1 &frame,
    const PlayerLifestyleSnapshotRequestV1 &request) noexcept {
  if (FixedString(frame.snapshot_id) != request.expected_snapshot_id) {
    return Failure::snapshot_identity_mismatch;
  }
  if (frame.public_revision != request.expected_public_revision ||
      frame.native_revision != request.expected_native_revision) {
    return Failure::revision_drift;
  }
  if (frame.date_raw != request.expected_date_raw) {
    return Failure::date_drift;
  }
  if (!frame.paused) return Failure::not_paused;
  if (!frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive || frame.played_character_id == -1 ||
      frame.played_character == 0 ||
      !frame.played_character_identity_round_trip ||
      frame.played_character_id != request.expected_player_character_id) {
    return Failure::player_unavailable;
  }
  return Failure::none;
}

Failure ClassifyFrameDrift(const PlayerLifestyleSnapshotFrameV1 &before,
                           const PlayerLifestyleSnapshotFrameV1 &after) noexcept {
  if (FixedString(before.snapshot_id) != FixedString(after.snapshot_id)) {
    return Failure::snapshot_identity_mismatch;
  }
  if (before.public_revision != after.public_revision ||
      before.native_revision != after.native_revision ||
      before.proof_epoch != after.proof_epoch) {
    return Failure::revision_drift;
  }
  if (before.date_raw != after.date_raw) return Failure::date_drift;
  if (!after.paused) return Failure::not_paused;
  if (before.map_ready != after.map_ready ||
      before.has_played_character != after.has_played_character ||
      before.played_character_alive != after.played_character_alive ||
      before.played_character_id != after.played_character_id ||
      before.played_character != after.played_character ||
      before.played_character_identity_round_trip !=
          after.played_character_identity_round_trip) {
    return Failure::player_unavailable;
  }
  return Failure::none;
}

bool ReadPointer(const PlayerLifestyleSnapshotAccessV1 &access,
                 std::uintptr_t address, std::uintptr_t &output) noexcept {
  output = 0;
  return access.read_memory != nullptr &&
      access.read_memory(access.context, address, &output, sizeof(output));
}

Failure ReadNativeSource(
    const PlayerLifestyleSnapshotEnvironmentV1 &environment,
    const PlayerLifestyleSnapshotAccessV1 &access,
    const PlayerLifestyleSnapshotFrameV1 &frame,
    PlayerLifestyleSourceSampleV1 &output) noexcept {
  output = {};
  if (access.read_memory == nullptr || environment.current_focus == nullptr ||
      environment.current_lifestyle == nullptr ||
      environment.unspent_perk_points == nullptr ||
      environment.used_perk_points == nullptr ||
      environment.lifestyle_xp == nullptr ||
      environment.unlocked_perks == nullptr ||
      environment.focus_fallback_slot_address == 0) {
    return Failure::native_bindings_unavailable;
  }

  output.player_character_id = frame.played_character_id;
  output.player_identity_round_trip =
      frame.played_character_identity_round_trip;
  auto &state = output.state;
  state.legal_focus_candidate_status = CandidateStatus::unavailable;
  state.legal_focus_candidate_unavailable_reason =
      CandidateFailure::lifestyle_window_unavailable;
  state.legal_perk_candidate_status = CandidateStatus::unavailable;
  state.legal_perk_candidate_unavailable_reason =
      CandidateFailure::lifestyle_window_unavailable;

  void *const character = reinterpret_cast<void *>(frame.played_character);
  void *const focus = environment.current_focus(character);
  if (focus == nullptr) return Failure::current_focus_getter_failed;
  std::uintptr_t fallback_focus = 0;
  if (!ReadPointer(access, environment.focus_fallback_slot_address,
                   fallback_focus)) return Failure::focus_fallback_read_failed;
  if (reinterpret_cast<std::uintptr_t>(focus) == fallback_focus) {
    state.current_focus_presence = Presence::absent;
  } else {
    state.current_focus_presence = Presence::present;
    if (!ReadPlayerLifestyleMsvcStableKeyV1(
            access.context, access.read_memory,
            reinterpret_cast<std::uintptr_t>(focus) +
                kPlayerLifestyleDatabaseStableKeyOffsetV1,
            state.current_focus_key)) {
      return Failure::current_focus_key_read_failed;
    }
    void *const lifestyle = environment.current_lifestyle(character);
    if (lifestyle == nullptr) {
      return Failure::current_lifestyle_getter_failed;
    }
    if (!ReadPlayerLifestyleMsvcStableKeyV1(
            access.context, access.read_memory,
            reinterpret_cast<std::uintptr_t>(lifestyle) +
                kPlayerLifestyleDatabaseStableKeyOffsetV1,
            state.current_lifestyle_key)) {
      return Failure::current_lifestyle_key_read_failed;
    }
    std::uintptr_t focus_lifestyle = 0;
    if (!ReadPointer(access, reinterpret_cast<std::uintptr_t>(focus) +
                                 kPlayerLifestyleFocusLifestyleOffsetV1,
                     focus_lifestyle) ||
        focus_lifestyle != reinterpret_cast<std::uintptr_t>(lifestyle)) {
      return Failure::focus_lifestyle_binding_failed;
    }

    auto &progress = state.current_lifestyle_progress;
    state.current_lifestyle_progress_present = true;
    progress.lifestyle_key = state.current_lifestyle_key;
    std::int64_t total = 0;
    std::int64_t within = 0;
    if (environment.lifestyle_xp(character, &total, lifestyle, false) ==
            nullptr ||
        environment.lifestyle_xp(character, &within, lifestyle, true) ==
            nullptr) {
      return Failure::lifestyle_xp_read_failed;
    }
    if (!access.read_memory(
            access.context,
            reinterpret_cast<std::uintptr_t>(lifestyle) +
                kPlayerLifestyleXpPerLevelOffsetV1,
            &progress.xp_per_level, sizeof(progress.xp_per_level))) {
      return Failure::lifestyle_xp_level_read_failed;
    }
    progress.xp_total_raw = total;
    progress.xp_within_level_raw = within;
    progress.unspent_perk_points =
        environment.unspent_perk_points(character, lifestyle);
    progress.used_perk_points =
        environment.used_perk_points(character, lifestyle);
  }

  const auto span = reinterpret_cast<std::uintptr_t>(
      environment.unlocked_perks(character));
  if (span == 0) return Failure::owned_perk_span_getter_failed;
  std::uintptr_t data = 0;
  std::int32_t count = 0;
  if (!ReadPointer(access, span, data) ||
      !access.read_memory(access.context,
                          span + kPlayerLifestyleUnlockedPerksCountOffsetV1,
                          &count, sizeof(count)) ||
      count < 0 ||
      count > static_cast<std::int32_t>(
                  game::kPlayerLifestyleMaximumOwnedPerksV1) ||
      (count > 0 && data == 0)) {
    return Failure::owned_perk_span_layout_invalid;
  }
  state.owned_perk_count = static_cast<std::uint32_t>(count);
  for (std::uint32_t index = 0; index < state.owned_perk_count; ++index) {
    std::uintptr_t perk = 0;
    const auto row_address = data +
        static_cast<std::uintptr_t>(index) * sizeof(std::uintptr_t);
    if (row_address < data || !ReadPointer(access, row_address, perk) ||
        perk == 0 ||
        !ReadPlayerLifestyleMsvcStableKeyV1(
            access.context, access.read_memory,
            perk + kPlayerLifestyleCharacterPerkStableKeyOffsetV1,
            state.owned_perk_keys[index])) {
      return Failure::owned_perk_key_read_failed;
    }
  }
  return Failure::none;
}

void ClearUnavailable(Snapshot &output, Failure reason) noexcept {
  output = {};
  output.status = game::PlayerLifestyleSnapshotStatusV1::unavailable;
  output.unavailable_reason = reason;
}

template <std::size_t Capacity>
void SortKeys(std::array<game::PlayerLifestyleStableKeyV1, Capacity> &values,
              std::uint32_t count) {
  std::sort(values.begin(), values.begin() + count,
            [](const auto &left, const auto &right) {
              return PlayerLifestyleStableKeyViewV1(left) <
                  PlayerLifestyleStableKeyViewV1(right);
            });
}

template <std::size_t Capacity>
void SortCandidates(
    std::array<game::PlayerLifestyleLegalCandidateV1, Capacity> &values,
    std::uint32_t count) {
  std::sort(values.begin(), values.begin() + count,
            [](const auto &left, const auto &right) {
              return PlayerLifestyleStableKeyViewV1(left.key) <
                  PlayerLifestyleStableKeyViewV1(right.key);
            });
}

void Publish(const PlayerLifestyleSnapshotFrameV1 &frame,
             const PlayerLifestyleSourceSampleV1 &sample,
             Snapshot &output) {
  output = {};
  output.status = game::PlayerLifestyleSnapshotStatusV1::available;
  output.unavailable_reason = Failure::none;
  output.snapshot_id = frame.snapshot_id;
  output.public_revision = frame.public_revision;
  output.native_revision = frame.native_revision;
  output.proof_epoch = frame.proof_epoch;
  output.date_raw = frame.date_raw;
  output.player_character_id = sample.player_character_id;
  output.state = sample.state;
  SortKeys(output.state.owned_perk_keys, output.state.owned_perk_count);
  SortCandidates(output.state.legal_focus_candidates,
                 output.state.legal_focus_candidate_count);
  SortCandidates(output.state.legal_perk_candidates,
                 output.state.legal_perk_candidate_count);
  output.readiness.current_focus_ready = true;
  output.readiness.lifestyle_progress_ready =
      output.state.current_focus_presence == Presence::absent ||
      output.state.current_lifestyle_progress_present;
  output.readiness.owned_perks_ready = true;
  output.readiness.legal_focus_candidates_ready =
      output.state.legal_focus_candidate_status == CandidateStatus::available;
  output.readiness.legal_perk_candidates_ready =
      output.state.legal_perk_candidate_status == CandidateStatus::available;
  output.readiness.same_frame_ready = true;
}

void AppendEscaped(std::string &output, std::string_view value) {
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20) {
        static constexpr char hex[] = "0123456789ABCDEF";
        output += "\\u00";
        output.push_back(hex[(character >> 4) & 0xF]);
        output.push_back(hex[character & 0xF]);
      } else {
        output.push_back(static_cast<char>(character));
      }
    }
  }
  output.push_back('"');
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

void AppendKey(std::string &output,
               const game::PlayerLifestyleStableKeyV1 &value) {
  AppendEscaped(output, PlayerLifestyleStableKeyViewV1(value));
}

template <std::size_t Capacity>
void AppendKeyArray(
    std::string &output,
    const std::array<game::PlayerLifestyleStableKeyV1, Capacity> &values,
    std::uint32_t count) {
  output.push_back('[');
  for (std::uint32_t index = 0; index < count; ++index) {
    if (index != 0) output.push_back(',');
    AppendKey(output, values[index]);
  }
  output.push_back(']');
}

template <std::size_t Capacity>
void AppendCandidateCollection(
    std::string &output, CandidateStatus status, CandidateFailure reason,
    const std::array<game::PlayerLifestyleLegalCandidateV1, Capacity> &values,
    std::uint32_t count) {
  output += "{\"status\":";
  AppendEscaped(output,
                status == CandidateStatus::available ? "available"
                                                     : "unavailable");
  if (status == CandidateStatus::unavailable) {
    output += ",\"reason\":";
    AppendEscaped(output, PlayerLifestyleCandidateCollectionFailureKeyV1(
                              reason));
  }
  output += ",\"items\":[";
  for (std::uint32_t index = 0; index < count; ++index) {
    if (index != 0) output.push_back(',');
    output += "{\"key\":";
    AppendKey(output, values[index].key);
    output += ",\"lifestyle_key\":";
    AppendKey(output, values[index].lifestyle_key);
    output.push_back('}');
  }
  output += "]}";
}

} // namespace

bool AssignPlayerLifestyleStableKeyV1(
    std::string_view value, game::PlayerLifestyleStableKeyV1 &output) noexcept {
  output = {};
  if (value.empty() ||
      value.size() >= game::kPlayerLifestyleStableKeyCapacityV1) {
    return false;
  }
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  output.size = static_cast<std::uint16_t>(value.size());
  std::memcpy(output.bytes.data(), value.data(), value.size());
  output.bytes[value.size()] = '\0';
  return true;
}

std::string_view PlayerLifestyleStableKeyViewV1(
    const game::PlayerLifestyleStableKeyV1 &value) noexcept {
  if (value.size >= game::kPlayerLifestyleStableKeyCapacityV1 ||
      value.bytes[value.size] != '\0') {
    return {};
  }
  return {value.bytes.data(), value.size};
}

bool ReadPlayerLifestyleMsvcStableKeyV1(
    void *context, ReadPlayerLifestyleMemoryV1 read_memory,
    std::uintptr_t native_string_address,
    game::PlayerLifestyleStableKeyV1 &output) noexcept {
  output = {};
  if (read_memory == nullptr || native_string_address == 0) return false;
  std::array<std::uint8_t, 32> header{};
  if (!read_memory(context, native_string_address, header.data(),
                   header.size())) {
    return false;
  }
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  std::memcpy(&size, header.data() + 0x10, sizeof(size));
  std::memcpy(&capacity, header.data() + 0x18, sizeof(capacity));
  if (size == 0 || size >= game::kPlayerLifestyleStableKeyCapacityV1 ||
      capacity < size) {
    return false;
  }
  std::array<char, game::kPlayerLifestyleStableKeyCapacityV1> bytes{};
  if (capacity < 16) {
    std::memcpy(bytes.data(), header.data(), static_cast<std::size_t>(size));
  } else {
    std::uintptr_t data = 0;
    std::memcpy(&data, header.data(), sizeof(data));
    if (data == 0 || !read_memory(context, data, bytes.data(),
                                  static_cast<std::size_t>(size))) {
      return false;
    }
  }
  return AssignPlayerLifestyleStableKeyV1(
      {bytes.data(), static_cast<std::size_t>(size)}, output);
}

PlayerLifestyleSnapshotEnvironmentV1 BindPlayerLifestyleSnapshotEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  PlayerLifestyleSnapshotEnvironmentV1 output{};
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  output.module_base = module_base;
  if (!exact_build_admitted || module_base == 0 ||
      admitted_executable_sha256 !=
          kPlayerLifestyleSnapshotExecutableSha256V1) {
    return output;
  }
  output.current_focus =
      reinterpret_cast<PlayerLifestyleSnapshotEnvironmentV1::ObjectGetter>(
          module_base + kPlayerLifestyleCurrentFocusGetterRvaV1);
  output.current_lifestyle =
      reinterpret_cast<PlayerLifestyleSnapshotEnvironmentV1::ObjectGetter>(
          module_base + kPlayerLifestyleCurrentLifestyleGetterRvaV1);
  output.unspent_perk_points =
      reinterpret_cast<PlayerLifestyleSnapshotEnvironmentV1::Int32Getter>(
          module_base + kPlayerLifestylePerkPointsGetterRvaV1);
  output.used_perk_points =
      reinterpret_cast<PlayerLifestyleSnapshotEnvironmentV1::Int32Getter>(
          module_base + kPlayerLifestylePerkPointsUsedGetterRvaV1);
  output.lifestyle_xp =
      reinterpret_cast<PlayerLifestyleSnapshotEnvironmentV1::XpGetter>(
          module_base + kPlayerLifestyleXpGetterRvaV1);
  output.unlocked_perks =
      reinterpret_cast<PlayerLifestyleSnapshotEnvironmentV1::PerkSpanGetter>(
          module_base + kPlayerLifestyleOwnedPerksGetterRvaV1);
  output.focus_fallback_slot_address =
      module_base + kPlayerLifestyleFocusFallbackSlotRvaV1;
  return output;
}

game::ReadPlayerLifestyleSnapshotResultV1 ReadPlayerLifestyleSnapshotV1(
    const PlayerLifestyleSnapshotEnvironmentV1 &environment,
    const PlayerLifestyleSnapshotAccessV1 &access,
    const PlayerLifestyleSnapshotRequestV1 &request,
    game::PlayerLifestyleSnapshotV1 &output) noexcept {
  ClearUnavailable(output, Failure::invalid_request);
  if (!ValidRequest(request)) return Result::unavailable;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kPlayerLifestyleSnapshotExecutableSha256V1) {
    ClearUnavailable(output, Failure::exact_build_not_admitted);
    return Result::unavailable;
  }
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      (environment.offline_fixture
           ? access.read_offline_fixture_source == nullptr ||
                 environment.module_base != 0
           : access.read_memory == nullptr || environment.module_base == 0 ||
                 environment.current_focus == nullptr ||
                 environment.current_lifestyle == nullptr ||
                 environment.unspent_perk_points == nullptr ||
                 environment.used_perk_points == nullptr ||
                 environment.lifestyle_xp == nullptr ||
                 environment.unlocked_perks == nullptr ||
                 environment.focus_fallback_slot_address == 0)) {
    ClearUnavailable(output, Failure::native_bindings_unavailable);
    return Result::unavailable;
  }
  if (!access.is_main_thread(access.context)) {
    ClearUnavailable(output, Failure::application_main_thread_required);
    return Result::unavailable;
  }

  try {
    PlayerLifestyleSnapshotFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      ClearUnavailable(output, Failure::frame_capture_failed);
      return Result::unavailable;
    }
    const auto initial_failure = ValidateInitialFrame(before, request);
    if (initial_failure != Failure::none) {
      ClearUnavailable(output, initial_failure);
      return Result::unavailable;
    }

    PlayerLifestyleSourceSampleV1 first{};
    PlayerLifestyleSourceSampleV1 second{};
    Failure source_failure = Failure::none;
    const auto read = [&](PlayerLifestyleSourceSampleV1 &sample) noexcept {
      if (environment.offline_fixture) {
        source_failure = access.read_offline_fixture_source(
                             access.context, before.played_character, sample)
                             ? Failure::none
                             : Failure::native_source_read_failed;
      } else {
        source_failure = ReadNativeSource(environment, access, before, sample);
      }
      return source_failure == Failure::none;
    };
    if (!read(first) || !read(second)) {
      ClearUnavailable(output, source_failure);
      return Result::unavailable;
    }
    if (first.player_character_id != before.played_character_id ||
        second.player_character_id != before.played_character_id ||
        !first.player_identity_round_trip ||
        !second.player_identity_round_trip) {
      ClearUnavailable(output, Failure::player_unavailable);
      return Result::unavailable;
    }
    const auto first_failure = ValidateState(first.state);
    const auto second_failure = ValidateState(second.state);
    if (first_failure != Failure::none) {
      ClearUnavailable(output, first_failure);
      return Result::unavailable;
    }
    if (second_failure != Failure::none) {
      ClearUnavailable(output, second_failure);
      return Result::unavailable;
    }
    if (first != second) {
      ClearUnavailable(output, Failure::native_sample_drift);
      return Result::unavailable;
    }

    PlayerLifestyleSnapshotFrameV1 after{};
    if (!access.capture_frame(access.context, after)) {
      ClearUnavailable(output, Failure::frame_capture_failed);
      return Result::unavailable;
    }
    const auto drift = ClassifyFrameDrift(before, after);
    if (drift != Failure::none) {
      ClearUnavailable(output, drift);
      return Result::unavailable;
    }
    Publish(before, first, output);
    return Result::available;
  } catch (...) {
    ClearUnavailable(output, Failure::native_source_read_failed);
    return Result::unavailable;
  }
}

std::string_view PlayerLifestyleSnapshotFailureKeyV1(
    game::PlayerLifestyleSnapshotFailureV1 reason) noexcept {
  using enum game::PlayerLifestyleSnapshotFailureV1;
  switch (reason) {
  case none: return "none";
  case invalid_request: return "invalid_request";
  case exact_build_not_admitted: return "exact_build_not_admitted";
  case native_bindings_unavailable: return "native_bindings_unavailable";
  case application_main_thread_required:
    return "application_main_thread_required";
  case frame_capture_failed: return "frame_capture_failed";
  case snapshot_identity_mismatch: return "snapshot_identity_mismatch";
  case revision_drift: return "revision_drift";
  case date_drift: return "date_drift";
  case not_paused: return "not_paused";
  case player_unavailable: return "player_unavailable";
  case native_source_read_failed: return "native_source_read_failed";
  case current_focus_getter_failed: return "current_focus_getter_failed";
  case focus_fallback_read_failed: return "focus_fallback_read_failed";
  case current_focus_key_read_failed: return "current_focus_key_read_failed";
  case current_lifestyle_getter_failed:
    return "current_lifestyle_getter_failed";
  case current_lifestyle_key_read_failed:
    return "current_lifestyle_key_read_failed";
  case focus_lifestyle_binding_failed:
    return "focus_lifestyle_binding_failed";
  case lifestyle_xp_read_failed: return "lifestyle_xp_read_failed";
  case lifestyle_xp_level_read_failed:
    return "lifestyle_xp_level_read_failed";
  case owned_perk_span_getter_failed:
    return "owned_perk_span_getter_failed";
  case owned_perk_span_layout_invalid:
    return "owned_perk_span_layout_invalid";
  case owned_perk_key_read_failed: return "owned_perk_key_read_failed";
  case stable_key_invalid: return "stable_key_invalid";
  case current_focus_invariant_failed:
    return "current_focus_invariant_failed";
  case lifestyle_progress_invalid: return "lifestyle_progress_invalid";
  case owned_perk_collection_invalid:
    return "owned_perk_collection_invalid";
  case legal_focus_collection_invalid:
    return "legal_focus_collection_invalid";
  case legal_perk_collection_invalid:
    return "legal_perk_collection_invalid";
  case duplicate_stable_key: return "duplicate_stable_key";
  case native_sample_drift: return "native_sample_drift";
  }
  return "unknown_failure";
}

std::string_view PlayerLifestyleCandidateCollectionFailureKeyV1(
    game::PlayerLifestyleCandidateCollectionFailureV1 reason) noexcept {
  using enum game::PlayerLifestyleCandidateCollectionFailureV1;
  switch (reason) {
  case none: return "none";
  case lifestyle_window_unavailable: return "lifestyle_window_unavailable";
  case native_enumerator_unavailable: return "native_enumerator_unavailable";
  case final_legality_evaluator_unavailable:
    return "final_legality_evaluator_unavailable";
  case source_read_failed: return "source_read_failed";
  }
  return "unknown_failure";
}

std::string SerializePlayerLifestyleSnapshotV1(
    const game::PlayerLifestyleSnapshotV1 &snapshot) {
  std::string output;
  output.reserve(4'096);
  output += "{\"private_build\":true,\"advertised\":false,\"status\":";
  AppendEscaped(output,
                snapshot.status == game::PlayerLifestyleSnapshotStatusV1::
                                       available
                    ? "available"
                    : "unavailable");
  if (snapshot.status == game::PlayerLifestyleSnapshotStatusV1::unavailable) {
    output += ",\"unavailable_reason\":";
    AppendEscaped(output,
                  PlayerLifestyleSnapshotFailureKeyV1(
                      snapshot.unavailable_reason));
    output.push_back('}');
    return output;
  }

  output += ",\"snapshot_id\":";
  AppendEscaped(output, FixedString(snapshot.snapshot_id));
  output += ",\"public_revision\":" +
      std::to_string(snapshot.public_revision);
  output += ",\"native_revision\":" +
      std::to_string(snapshot.native_revision);
  output += ",\"proof_epoch\":" + std::to_string(snapshot.proof_epoch);
  output += ",\"date_raw\":" + std::to_string(snapshot.date_raw);
  output += ",\"player_character_id\":" +
      std::to_string(snapshot.player_character_id);
  output += ",\"current_focus\":{";
  output += "\"presence\":";
  AppendEscaped(output,
      snapshot.state.current_focus_presence == Presence::present
          ? "present" : "absent");
  if (snapshot.state.current_focus_presence == Presence::present) {
    output += ",\"key\":";
    AppendKey(output, snapshot.state.current_focus_key);
    output += ",\"lifestyle_key\":";
    AppendKey(output, snapshot.state.current_lifestyle_key);
  }
  output.push_back('}');

  output += ",\"current_lifestyle_progress\":";
  if (!snapshot.state.current_lifestyle_progress_present) {
    output += "{\"presence\":\"absent\"}";
  } else {
    const auto &progress = snapshot.state.current_lifestyle_progress;
    output += "{\"presence\":\"present\",\"lifestyle_key\":";
    AppendKey(output, progress.lifestyle_key);
    output += ",\"xp_total_raw\":" +
        std::to_string(progress.xp_total_raw);
    output += ",\"xp_within_level_raw\":" +
        std::to_string(progress.xp_within_level_raw);
    output += ",\"xp_per_level\":" +
        std::to_string(progress.xp_per_level);
    output += ",\"unspent_perk_points\":" +
        std::to_string(progress.unspent_perk_points);
    output += ",\"used_perk_points\":" +
        std::to_string(progress.used_perk_points) + "}";
  }

  output += ",\"owned_perk_keys\":";
  AppendKeyArray(output, snapshot.state.owned_perk_keys,
                 snapshot.state.owned_perk_count);
  output += ",\"legal_focus_candidates\":";
  AppendCandidateCollection(
      output, snapshot.state.legal_focus_candidate_status,
      snapshot.state.legal_focus_candidate_unavailable_reason,
      snapshot.state.legal_focus_candidates,
      snapshot.state.legal_focus_candidate_count);
  output += ",\"legal_perk_candidates\":";
  AppendCandidateCollection(
      output, snapshot.state.legal_perk_candidate_status,
      snapshot.state.legal_perk_candidate_unavailable_reason,
      snapshot.state.legal_perk_candidates,
      snapshot.state.legal_perk_candidate_count);

  output += ",\"readiness\":{\"current_focus_ready\":";
  AppendBool(output, snapshot.readiness.current_focus_ready);
  output += ",\"lifestyle_progress_ready\":";
  AppendBool(output, snapshot.readiness.lifestyle_progress_ready);
  output += ",\"owned_perks_ready\":";
  AppendBool(output, snapshot.readiness.owned_perks_ready);
  output += ",\"legal_focus_candidates_ready\":";
  AppendBool(output, snapshot.readiness.legal_focus_candidates_ready);
  output += ",\"legal_perk_candidates_ready\":";
  AppendBool(output, snapshot.readiness.legal_perk_candidates_ready);
  output += ",\"same_frame_ready\":";
  AppendBool(output, snapshot.readiness.same_frame_ready);
  output += "}}";
  return output;
}

} // namespace xar::ck3_11906
