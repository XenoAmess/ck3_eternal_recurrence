#include "xar_bridge/character_interaction_preview_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_11906 {
namespace {

using Failure = game::CharacterInteractionPreviewFailureV1;
using Result = game::ReadCharacterInteractionPreviewResultV1;
using Status = game::CharacterInteractionPreviewStatusV1;

static_assert(sizeof(void *) == 8,
              "character interaction preview is x64-only");

constexpr std::size_t kContextSize = 0x338;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterDeathDataOffset = 0x1C8;
constexpr std::size_t kDefinitionRuntimeOrdinalOffset = 0x10;
constexpr std::size_t kDefinitionHashOffset = 0x14;
constexpr std::size_t kDefinitionCanonicalKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 15;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::size_t kMaximumStableKeyBytes = 127;

constexpr std::array<std::string_view, 5> kAllowlistedKeys{
    "gift_interaction", "recruit_guest_interaction",
    "invite_to_court_interaction", "offer_vassalization_interaction",
    "demand_payment_interaction"};

constexpr std::array<std::string_view,
                     game::kCharacterInteractionPreviewCostCountV1>
    kCostKeys{"gold",        "prestige",         "piety",
              "renown",      "influence",        "herd",
              "treasury",    "treasury_or_gold", "merit",
              "barter_goods"};

struct NativeSample {
  game::CharacterInteractionPreviewDefinitionV1 definition{};
  game::CharacterInteractionPreviewRolesV1 roles{};
  bool can_send = false;
  game::CharacterInteractionPreviewCostsV1 costs{};
  game::CharacterInteractionPreviewAcceptanceV1 acceptance{};

  friend bool operator==(const NativeSample &, const NativeSample &) = default;
};

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidSnapshotId(std::string_view value) noexcept {
  if (value.empty() ||
      value.size() >= game::kCharacterInteractionPreviewSnapshotIdCapacityV1) {
    return false;
  }
  return std::all_of(value.begin(), value.end(), [](char character) {
    return (character >= 'a' && character <= 'z') ||
           (character >= 'A' && character <= 'Z') ||
           (character >= '0' && character <= '9') || character == '_' ||
           character == '-' || character == '.';
  });
}

bool ValidStableKey(std::string_view value) noexcept {
  if (value.empty() || value.size() > kMaximumStableKeyBytes) return false;
  return std::all_of(value.begin(), value.end(), [](char character) {
    return (character >= 'a' && character <= 'z') ||
           (character >= '0' && character <= '9') || character == '_';
  });
}

bool Allowlisted(std::string_view value) noexcept {
  return std::find(kAllowlistedKeys.begin(), kAllowlistedKeys.end(), value) !=
         kAllowlistedKeys.end();
}

bool CallbacksComplete(const CharacterInteractionPreviewAccessV1 &access) {
  return access.capture_frame != nullptr && access.is_main_thread != nullptr &&
         access.read_memory != nullptr &&
         access.invoke_stable_hash != nullptr &&
         access.invoke_database_getter != nullptr &&
         access.invoke_definition_lookup != nullptr &&
         access.invoke_construct != nullptr && access.invoke_refresh != nullptr &&
         access.invoke_finalize != nullptr && access.invoke_can_send != nullptr &&
         access.invoke_costs != nullptr &&
         access.invoke_acceptance != nullptr &&
         access.invoke_destroy != nullptr;
}

bool EnvironmentComplete(
    const CharacterInteractionPreviewEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCharacterInteractionPreviewExecutableSha256V1 ||
      environment.character_storage_slot == 0 ||
      environment.database_getter == 0 || environment.stable_key_hash == 0 ||
      environment.definition_lookup == 0 ||
      environment.construct_context == 0 || environment.refresh_context == 0 ||
      environment.finalize_context == 0 || environment.can_send == 0 ||
      environment.cost_evaluator == 0 ||
      environment.auto_accept_evaluator == 0 ||
      environment.intermediary_raw == 0 || environment.recipient_raw == 0 ||
      environment.outer_final == 0 || environment.destroy_context == 0) {
    return false;
  }
  if (environment.offline_fixture) return true;
  if (environment.module_base == 0) return false;
  const auto base = environment.module_base;
  return environment.character_storage_slot ==
             base + kCharacterInteractionPreviewCharacterStorageSlotRvaV1 &&
         environment.database_getter ==
             base + kCharacterInteractionPreviewDatabaseGetterRvaV1 &&
         environment.stable_key_hash ==
             base + kCharacterInteractionPreviewStableKeyHashRvaV1 &&
         environment.definition_lookup ==
             base + kCharacterInteractionPreviewDefinitionLookupRvaV1 &&
         environment.construct_context ==
             base + kCharacterInteractionPreviewConstructContextRvaV1 &&
         environment.refresh_context ==
             base + kCharacterInteractionPreviewRefreshContextRvaV1 &&
         environment.finalize_context ==
             base + kCharacterInteractionPreviewFinalizeContextRvaV1 &&
         environment.can_send ==
             base + kCharacterInteractionPreviewCanSendRvaV1 &&
         environment.cost_evaluator ==
             base + kCharacterInteractionPreviewCostEvaluatorRvaV1 &&
         environment.auto_accept_evaluator ==
             base + kCharacterInteractionPreviewAutoAcceptEvaluatorRvaV1 &&
         environment.intermediary_raw ==
             base + kCharacterInteractionPreviewIntermediaryRawRvaV1 &&
         environment.recipient_raw ==
             base + kCharacterInteractionPreviewRecipientRawRvaV1 &&
         environment.outer_final ==
             base + kCharacterInteractionPreviewOuterFinalRvaV1 &&
         environment.destroy_context ==
             base + kCharacterInteractionPreviewDestroyContextRvaV1;
}

template <typename Value>
bool ReadValue(const CharacterInteractionPreviewAccessV1 &access,
               std::uintptr_t address, Value &output) noexcept {
  return address != 0 &&
         access.read_memory(access.context, address, &output, sizeof(output));
}

bool CheckedAdd(std::uintptr_t base, std::size_t offset,
                std::uintptr_t &output) noexcept {
  if (base == 0 ||
      offset > std::numeric_limits<std::uintptr_t>::max() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

bool ReadNativeStableKey(const CharacterInteractionPreviewAccessV1 &access,
                         std::uintptr_t native_string,
                         std::string &output) noexcept {
  output.clear();
  std::size_t size = 0;
  std::size_t capacity = 0;
  std::uintptr_t size_address = 0;
  std::uintptr_t capacity_address = 0;
  if (!CheckedAdd(native_string, kMsvcStringSizeOffset, size_address) ||
      !CheckedAdd(native_string, kMsvcStringCapacityOffset, capacity_address) ||
      !ReadValue(access, size_address, size) ||
      !ReadValue(access, capacity_address, capacity) || size == 0 ||
      size > capacity || size > kMaximumStableKeyBytes) {
    return false;
  }
  std::uintptr_t bytes = native_string;
  if (capacity > kMsvcStringInlineCapacity &&
      (!ReadValue(access, native_string, bytes) || bytes == 0)) {
    return false;
  }
  try {
    output.resize(size);
  } catch (...) {
    output.clear();
    return false;
  }
  if (!access.read_memory(access.context, bytes, output.data(), size) ||
      !ValidStableKey(output)) {
    output.clear();
    return false;
  }
  return true;
}

Failure ValidateInitialFrame(
    const CharacterInteractionPreviewFrameV1 &frame,
    const CharacterInteractionPreviewRequestV1 &request) noexcept {
  if (FixedString(frame.snapshot_id) != request.expected_snapshot_id) {
    return Failure::snapshot_identity_mismatch;
  }
  if (frame.public_revision != request.expected_public_revision ||
      frame.native_revision != request.expected_native_revision) {
    return Failure::revision_drift;
  }
  if (frame.date_raw != request.expected_date_raw) return Failure::date_drift;
  if (!frame.paused) return Failure::not_paused;
  if (!frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive ||
      frame.played_character_id != request.actor_character_id) {
    return Failure::player_unavailable;
  }
  return Failure::none;
}

Failure ClassifyFrameDrift(const CharacterInteractionPreviewFrameV1 &before,
                           const CharacterInteractionPreviewFrameV1 &after) {
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
      before.played_character_id != after.played_character_id) {
    return Failure::player_unavailable;
  }
  return Failure::none;
}

bool ReadDefinition(
    const CharacterInteractionPreviewEnvironmentV1 &environment,
    const CharacterInteractionPreviewAccessV1 &access,
    std::string_view requested_key, void *&definition,
    game::CharacterInteractionPreviewDefinitionV1 &identity,
    Failure &failure) noexcept {
  std::int32_t signed_hash = 0;
  void *database = nullptr;
  if (!access.invoke_database_getter(access.context,
                                     environment.database_getter, database) ||
      database == nullptr ||
      !access.invoke_stable_hash(access.context, environment.stable_key_hash,
                                 database, requested_key, signed_hash) ||
      !access.invoke_definition_lookup(access.context,
                                       environment.definition_lookup, database,
                                       signed_hash, definition) ||
      definition == nullptr) {
    failure = Failure::definition_lookup_failed;
    return false;
  }
  const auto base = reinterpret_cast<std::uintptr_t>(definition);
  std::uint32_t stored_hash = 0;
  std::uintptr_t ordinal_address = 0;
  std::uintptr_t hash_address = 0;
  std::uintptr_t key_address = 0;
  if (!CheckedAdd(base, kDefinitionRuntimeOrdinalOffset, ordinal_address) ||
      !CheckedAdd(base, kDefinitionHashOffset, hash_address) ||
      !CheckedAdd(base, kDefinitionCanonicalKeyOffset, key_address) ||
      !ReadValue(access, ordinal_address, identity.runtime_ordinal) ||
      !ReadValue(access, hash_address, stored_hash) ||
      !ReadNativeStableKey(access, key_address, identity.canonical_key) ||
      identity.runtime_ordinal < 0 ||
      stored_hash != static_cast<std::uint32_t>(signed_hash) ||
      identity.canonical_key != requested_key) {
    identity = {};
    failure = Failure::definition_identity_mismatch;
    return false;
  }
  identity.deterministic_key_hash = stored_hash;
  return true;
}

bool ResolveCharacter(
    const CharacterInteractionPreviewEnvironmentV1 &environment,
    const CharacterInteractionPreviewAccessV1 &access,
    std::int32_t full_id, Failure lookup_failure, void *&character,
    Failure &failure) noexcept {
  std::uintptr_t storage = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  std::uintptr_t slots_address = 0;
  std::uintptr_t capacity_address = 0;
  if (!ReadValue(access, environment.character_storage_slot, storage) ||
      storage == 0 ||
      !CheckedAdd(storage, kStorageSlotsOffset, slots_address) ||
      !CheckedAdd(storage, kStorageCapacityOffset, capacity_address) ||
      !ReadValue(access, slots_address, slots) || slots == 0 ||
      !ReadValue(access, capacity_address, capacity) || capacity <= 0 ||
      capacity > kMaximumComponentSlots) {
    failure = lookup_failure;
    return false;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    failure = lookup_failure;
    return false;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kStorageSlotStride +
                           kStorageSlotObjectOffset;
  std::uintptr_t slot_address = 0;
  std::uintptr_t object = 0;
  std::uintptr_t identity_address = 0;
  std::int32_t observed_id = -1;
  if (!CheckedAdd(slots, slot_offset, slot_address) ||
      !ReadValue(access, slot_address, object) || object == 0 ||
      !CheckedAdd(object, kCharacterIdentityOffset, identity_address) ||
      !ReadValue(access, identity_address, observed_id)) {
    failure = lookup_failure;
    return false;
  }
  if (observed_id != full_id) {
    failure = Failure::character_identity_mismatch;
    return false;
  }
  std::uintptr_t death_address = 0;
  std::uintptr_t death_data = 0;
  if (!CheckedAdd(object, kCharacterDeathDataOffset, death_address) ||
      !ReadValue(access, death_address, death_data)) {
    failure = lookup_failure;
    return false;
  }
  if (death_data != 0) {
    failure = Failure::character_not_alive;
    return false;
  }
  character = reinterpret_cast<void *>(object);
  return true;
}

bool ValidAcceptance(
    const game::CharacterInteractionPreviewAcceptanceV1 &value) noexcept {
  using Kind = game::CharacterInteractionAcceptanceKindV1;
  if (!value.intermediary_raw_present && value.intermediary_raw != 0) {
    return false;
  }
  if (!value.recipient_raw_present && value.recipient_raw != 0) return false;
  if (!value.final_status_present && value.final_status_raw != -1) return false;
  if (!value.would_accept_now_present && value.would_accept_now) return false;
  switch (value.kind) {
  case Kind::auto_accept:
    return value.auto_accept && !value.intermediary_present &&
           !value.intermediary_raw_present && !value.recipient_raw_present &&
           !value.final_status_present && value.would_accept_now_present &&
           value.would_accept_now;
  case Kind::ai_final:
    return value.recipient_is_ai && !value.auto_accept &&
           value.recipient_raw_present && value.final_status_present &&
           value.final_status_raw >= 0 && value.final_status_raw <= 2 &&
           value.would_accept_now_present &&
           value.would_accept_now == (value.final_status_raw != 2) &&
           value.intermediary_present == value.intermediary_raw_present;
  case Kind::human_pending:
    return !value.recipient_is_ai && !value.auto_accept &&
           !value.intermediary_present && !value.intermediary_raw_present &&
           !value.recipient_raw_present && !value.final_status_present &&
           !value.would_accept_now_present;
  case Kind::unavailable:
    return false;
  }
  return false;
}

bool ReadNativeSample(
    const CharacterInteractionPreviewEnvironmentV1 &environment,
    const CharacterInteractionPreviewAccessV1 &access,
    const CharacterInteractionPreviewRequestV1 &request, NativeSample &sample,
    Failure &failure) noexcept {
  void *definition = nullptr;
  if (!ReadDefinition(environment, access, request.interaction_key, definition,
                      sample.definition, failure)) {
    return false;
  }
  void *actor = nullptr;
  void *recipient = nullptr;
  if (!ResolveCharacter(environment, access, request.actor_character_id,
                        Failure::actor_lookup_failed, actor, failure) ||
      !ResolveCharacter(environment, access, request.recipient_character_id,
                        Failure::recipient_lookup_failed, recipient, failure)) {
    return false;
  }
  (void)actor;
  (void)recipient;
  sample.roles.actor_character_id = request.actor_character_id;
  sample.roles.recipient_character_id = request.recipient_character_id;

  alignas(16) std::array<std::byte, kContextSize> context_storage{};
  void *constructed = nullptr;
  const bool construction_invoked = access.invoke_construct(
      access.context, environment.construct_context, context_storage.data(),
      definition, request.actor_character_id, request.recipient_character_id,
      constructed);
  if (!construction_invoked || constructed != context_storage.data()) {
    if (constructed == context_storage.data() &&
        !access.invoke_destroy(access.context, environment.destroy_context,
                               constructed)) {
      failure = Failure::context_cleanup_failed;
    } else {
      failure = Failure::context_construction_failed;
    }
    return false;
  }

  auto destroy = [&]() noexcept {
    return access.invoke_destroy(access.context, environment.destroy_context,
                                 constructed);
  };
  if (!access.invoke_refresh(access.context, environment.refresh_context,
                             constructed)) {
    failure = destroy() ? Failure::context_refresh_failed
                        : Failure::context_cleanup_failed;
    return false;
  }
  if (!access.invoke_finalize(access.context, environment.finalize_context,
                              constructed)) {
    failure = destroy() ? Failure::context_finalize_failed
                        : Failure::context_cleanup_failed;
    return false;
  }
  if (!access.invoke_can_send(access.context, environment.can_send,
                              constructed, sample.can_send)) {
    failure = destroy() ? Failure::can_send_evaluation_failed
                        : Failure::context_cleanup_failed;
    return false;
  }
  if (!access.invoke_costs(access.context, environment.cost_evaluator,
                           constructed, sample.costs.raw)) {
    failure = destroy() ? Failure::cost_evaluation_failed
                        : Failure::context_cleanup_failed;
    return false;
  }
  if (!access.invoke_acceptance(
          access.context, environment.auto_accept_evaluator,
          environment.intermediary_raw, environment.recipient_raw,
          environment.outer_final, constructed, sample.acceptance)) {
    failure = destroy() ? Failure::acceptance_evaluation_failed
                        : Failure::context_cleanup_failed;
    return false;
  }
  if (!ValidAcceptance(sample.acceptance)) {
    failure = destroy() ? Failure::acceptance_invariant_failed
                        : Failure::context_cleanup_failed;
    return false;
  }
  if (!destroy()) {
    failure = Failure::context_cleanup_failed;
    return false;
  }
  return true;
}

void AppendEscaped(std::string &output, std::string_view value) {
  static constexpr char kHex[] = "0123456789ABCDEF";
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
      if (character < 0x20U) {
        output += "\\u00";
        output.push_back(kHex[(character >> 4U) & 0x0FU]);
        output.push_back(kHex[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
    }
  }
  output.push_back('"');
}

std::string_view AcceptanceKindKey(
    game::CharacterInteractionAcceptanceKindV1 value) noexcept {
  using Kind = game::CharacterInteractionAcceptanceKindV1;
  switch (value) {
  case Kind::auto_accept: return "auto_accept";
  case Kind::ai_final: return "ai_final";
  case Kind::human_pending: return "human_pending";
  case Kind::unavailable: return "unavailable";
  }
  return "unavailable";
}

} // namespace

CharacterInteractionPreviewEnvironmentV1
BindCharacterInteractionPreviewEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  CharacterInteractionPreviewEnvironmentV1 environment{};
  environment.exact_build_admitted = exact_build_admitted;
  environment.admitted_executable_sha256 = admitted_executable_sha256;
  environment.module_base = module_base;
  if (module_base == 0) return environment;
  environment.character_storage_slot =
      module_base + kCharacterInteractionPreviewCharacterStorageSlotRvaV1;
  environment.database_getter =
      module_base + kCharacterInteractionPreviewDatabaseGetterRvaV1;
  environment.stable_key_hash =
      module_base + kCharacterInteractionPreviewStableKeyHashRvaV1;
  environment.definition_lookup =
      module_base + kCharacterInteractionPreviewDefinitionLookupRvaV1;
  environment.construct_context =
      module_base + kCharacterInteractionPreviewConstructContextRvaV1;
  environment.refresh_context =
      module_base + kCharacterInteractionPreviewRefreshContextRvaV1;
  environment.finalize_context =
      module_base + kCharacterInteractionPreviewFinalizeContextRvaV1;
  environment.can_send =
      module_base + kCharacterInteractionPreviewCanSendRvaV1;
  environment.cost_evaluator =
      module_base + kCharacterInteractionPreviewCostEvaluatorRvaV1;
  environment.auto_accept_evaluator =
      module_base + kCharacterInteractionPreviewAutoAcceptEvaluatorRvaV1;
  environment.intermediary_raw =
      module_base + kCharacterInteractionPreviewIntermediaryRawRvaV1;
  environment.recipient_raw =
      module_base + kCharacterInteractionPreviewRecipientRawRvaV1;
  environment.outer_final =
      module_base + kCharacterInteractionPreviewOuterFinalRvaV1;
  environment.destroy_context =
      module_base + kCharacterInteractionPreviewDestroyContextRvaV1;
  return environment;
}

game::ReadCharacterInteractionPreviewResultV1 ReadCharacterInteractionPreviewV1(
    const CharacterInteractionPreviewEnvironmentV1 &environment,
    const CharacterInteractionPreviewAccessV1 &access,
    const CharacterInteractionPreviewRequestV1 &request,
    game::CharacterInteractionPreviewV1 &output) noexcept {
  output = {};
  auto fail = [&](Failure reason) {
    output = {};
    output.status = Status::unavailable;
    output.unavailable_reason = reason;
    return Result::unavailable;
  };

  if (!ValidSnapshotId(request.expected_snapshot_id) ||
      request.expected_public_revision == 0 ||
      request.expected_native_revision == 0 ||
      request.actor_character_id <= 0 || request.recipient_character_id <= 0 ||
      !ValidStableKey(request.interaction_key)) {
    return fail(Failure::invalid_request);
  }
  if (!Allowlisted(request.interaction_key)) {
    return fail(Failure::interaction_not_allowlisted);
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCharacterInteractionPreviewExecutableSha256V1) {
    return fail(Failure::exact_build_not_admitted);
  }
  if (!EnvironmentComplete(environment) || !CallbacksComplete(access)) {
    return fail(Failure::native_bindings_unavailable);
  }
  if (!access.is_main_thread(access.context)) {
    return fail(Failure::application_main_thread_required);
  }

  CharacterInteractionPreviewFrameV1 before{};
  if (!access.capture_frame(access.context, before)) {
    return fail(Failure::frame_capture_failed);
  }
  if (const auto frame_failure = ValidateInitialFrame(before, request);
      frame_failure != Failure::none) {
    return fail(frame_failure);
  }

  NativeSample first{};
  NativeSample second{};
  Failure native_failure = Failure::none;
  if (!ReadNativeSample(environment, access, request, first, native_failure) ||
      !ReadNativeSample(environment, access, request, second,
                        native_failure)) {
    return fail(native_failure);
  }
  if (first != second) return fail(Failure::native_sample_drift);

  CharacterInteractionPreviewFrameV1 after{};
  if (!access.capture_frame(access.context, after)) {
    return fail(Failure::frame_capture_failed);
  }
  if (const auto frame_failure = ClassifyFrameDrift(before, after);
      frame_failure != Failure::none) {
    return fail(frame_failure);
  }

  std::copy(request.expected_snapshot_id.begin(),
            request.expected_snapshot_id.end(), output.snapshot_id.begin());
  output.status = Status::available;
  output.unavailable_reason = Failure::none;
  output.public_revision = before.public_revision;
  output.native_revision = before.native_revision;
  output.proof_epoch = before.proof_epoch;
  output.date_raw = before.date_raw;
  output.definition = std::move(first.definition);
  output.roles = first.roles;
  output.can_send = first.can_send;
  output.costs = first.costs;
  output.acceptance = first.acceptance;
  output.readiness = {true, true, true, true, true, true, true, true};
  return Result::available;
}

std::string_view CharacterInteractionPreviewFailureKeyV1(
    game::CharacterInteractionPreviewFailureV1 reason) noexcept {
  using enum game::CharacterInteractionPreviewFailureV1;
  switch (reason) {
  case none: return "none";
  case invalid_request: return "invalid_request";
  case interaction_not_allowlisted: return "interaction_not_allowlisted";
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
  case definition_lookup_failed: return "definition_lookup_failed";
  case definition_identity_mismatch: return "definition_identity_mismatch";
  case actor_lookup_failed: return "actor_lookup_failed";
  case recipient_lookup_failed: return "recipient_lookup_failed";
  case character_identity_mismatch: return "character_identity_mismatch";
  case character_not_alive: return "character_not_alive";
  case context_construction_failed: return "context_construction_failed";
  case context_refresh_failed: return "context_refresh_failed";
  case context_finalize_failed: return "context_finalize_failed";
  case can_send_evaluation_failed: return "can_send_evaluation_failed";
  case cost_evaluation_failed: return "cost_evaluation_failed";
  case acceptance_evaluation_failed:
    return "acceptance_evaluation_failed";
  case acceptance_invariant_failed: return "acceptance_invariant_failed";
  case context_cleanup_failed: return "context_cleanup_failed";
  case native_sample_drift: return "native_sample_drift";
  }
  return "unknown";
}

std::string SerializeCharacterInteractionPreviewV1(
    const game::CharacterInteractionPreviewV1 &preview) {
  std::string output =
      "{\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"action_surface_present\":false";
  output += ",\"status\":\"";
  output += preview.status == Status::available ? "available" : "unavailable";
  output += '"';
  if (preview.status != Status::available) {
    output += ",\"unavailable_reason\":\"";
    output += CharacterInteractionPreviewFailureKeyV1(
        preview.unavailable_reason);
    output += "\"}";
    return output;
  }
  output += ",\"snapshot_id\":";
  AppendEscaped(output, FixedString(preview.snapshot_id));
  output += ",\"public_revision\":" +
            std::to_string(preview.public_revision);
  output += ",\"native_revision\":" +
            std::to_string(preview.native_revision);
  output += ",\"proof_epoch\":" + std::to_string(preview.proof_epoch);
  output += ",\"date_raw\":" + std::to_string(preview.date_raw);
  output += ",\"definition\":{\"canonical_key\":";
  AppendEscaped(output, preview.definition.canonical_key);
  output += ",\"deterministic_key_hash\":" +
            std::to_string(preview.definition.deterministic_key_hash);
  output += ",\"runtime_ordinal\":" +
            std::to_string(preview.definition.runtime_ordinal) + '}';
  output += ",\"payload_shape\":\"two_role_no_target_no_options\"";
  output += ",\"roles\":{\"actor_character_id\":" +
            std::to_string(preview.roles.actor_character_id);
  output += ",\"recipient_character_id\":" +
            std::to_string(preview.roles.recipient_character_id) + '}';
  output += ",\"can_send\":";
  output += preview.can_send ? "true" : "false";
  output += ",\"costs\":{\"raw_scale\":" +
            std::to_string(preview.costs.raw_scale) + ",\"payer_role\":"
            "\"actor\",\"application_timing\":\"on_send\",\"entries\":[";
  for (std::size_t index = 0; index < kCostKeys.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += "{\"resource_key\":";
    AppendEscaped(output, kCostKeys[index]);
    output += ",\"raw\":" + std::to_string(preview.costs.raw[index]) + '}';
  }
  output += "]}";
  const auto &acceptance = preview.acceptance;
  output += ",\"acceptance\":{\"kind\":";
  AppendEscaped(output, AcceptanceKindKey(acceptance.kind));
  output += ",\"recipient_is_ai\":";
  output += acceptance.recipient_is_ai ? "true" : "false";
  output += ",\"auto_accept\":";
  output += acceptance.auto_accept ? "true" : "false";
  output += ",\"intermediary_present\":";
  output += acceptance.intermediary_present ? "true" : "false";
  output += ",\"intermediary_raw\":";
  output += acceptance.intermediary_raw_present
                ? std::to_string(acceptance.intermediary_raw)
                : "null";
  output += ",\"recipient_raw\":";
  output += acceptance.recipient_raw_present
                ? std::to_string(acceptance.recipient_raw)
                : "null";
  output += ",\"raw_scale\":" +
            std::to_string(game::kCharacterInteractionPreviewRawScaleV1);
  output += ",\"outer_final_status_raw\":";
  output += acceptance.final_status_present
                ? std::to_string(acceptance.final_status_raw)
                : "null";
  output += ",\"would_accept_now\":";
  output += acceptance.would_accept_now_present
                ? (acceptance.would_accept_now ? "true" : "false")
                : "null";
  output += '}';
  const auto &ready = preview.readiness;
  output += ",\"readiness\":{\"definition_ready\":";
  output += ready.definition_ready ? "true" : "false";
  output += ",\"actor_ready\":";
  output += ready.actor_ready ? "true" : "false";
  output += ",\"recipient_ready\":";
  output += ready.recipient_ready ? "true" : "false";
  output += ",\"finalized_context_ready\":";
  output += ready.finalized_context_ready ? "true" : "false";
  output += ",\"can_send_ready\":";
  output += ready.can_send_ready ? "true" : "false";
  output += ",\"costs_ready\":";
  output += ready.costs_ready ? "true" : "false";
  output += ",\"acceptance_ready\":";
  output += ready.acceptance_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += ready.same_frame_ready ? "true" : "false";
  output += "}}";
  return output;
}

} // namespace xar::ck3_11906
