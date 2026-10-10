#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {

std::optional<std::uintptr_t> At(std::uintptr_t base,
                                 std::uintptr_t offset) noexcept {
  if (base == 0 || base > std::numeric_limits<std::uintptr_t>::max() - offset)
    return std::nullopt;
  return base + offset;
}

template <class T>
std::optional<T> Read(const PersonInstalledTransferBindings12004 &bindings,
                      std::optional<std::uintptr_t> address) noexcept {
  if (!bindings.read || !address)
    return std::nullopt;
  T value{};
  if (!bindings.read(bindings.read_context, *address, &value, sizeof(value)))
    return std::nullopt;
  return value;
}

std::optional<std::uint32_t> CharacterId(
    const PersonInstalledTransferBindings12004 &bindings,
    std::optional<std::uintptr_t> character) noexcept {
  return character ? Read<std::uint32_t>(bindings, At(*character, 0x18))
                   : std::nullopt;
}

PersonInstalledTransferSnapshot12004 Snapshot(
    const PersonInstalledTransferBindings12004 &bindings,
    std::uintptr_t model_a, std::uintptr_t model_b,
    std::optional<std::uintptr_t> immutable_owner,
    bool select_initial_b_owner) noexcept {
  PersonInstalledTransferSnapshot12004 result;
  result.model_a_owner_identity =
      Read<std::uintptr_t>(bindings, At(model_a, 0x8));
  result.model_b_owner_identity =
      Read<std::uintptr_t>(bindings, At(model_b, 0x8));
  result.model_a_owner_character_id =
      CharacterId(bindings, result.model_a_owner_identity);
  result.model_b_owner_character_id =
      CharacterId(bindings, result.model_b_owner_identity);
  if (select_initial_b_owner)
    immutable_owner = result.model_b_owner_identity;
  result.observed_owner_identity = immutable_owner;
  result.observed_owner_character_id = CharacterId(bindings, immutable_owner);
  if (!immutable_owner || *immutable_owner == 0)
    return result;
  result.carrier_identity =
      Read<std::uintptr_t>(bindings, At(*immutable_owner, 0x1B0));
  if (!result.carrier_identity)
    return result;
  if (*result.carrier_identity == 0) {
    // Native carrier absence is known null, not an unread Model slot.
    result.installed_model_identity = 0;
  } else {
    result.installed_model_identity =
        Read<std::uintptr_t>(bindings, At(*result.carrier_identity, 0x258));
  }
  if (!result.installed_model_identity)
    return result;
  result.installed_model_is_a =
      model_a != 0 && *result.installed_model_identity == model_a;
  result.installed_model_is_b =
      model_b != 0 && *result.installed_model_identity == model_b;
  if (*result.installed_model_identity == 0)
    return result;
  result.installed_model_owner_identity = Read<std::uintptr_t>(
      bindings, At(*result.installed_model_identity, 0x8));
  if (!result.installed_model_owner_identity)
    return result;
  result.installed_owner_matches_observed_owner =
      *result.installed_model_owner_identity == *immutable_owner;
  if (*result.installed_owner_matches_observed_owner)
    result.matching_installed_inline_context_identity =
        At(*result.installed_model_identity, 0x10);
  return result;
}

std::optional<bool> OwnerMatches(
    const PersonInstalledTransferPreparation12004 &preparation,
    const PersonInstalledTransferSnapshot12004 &snapshot) noexcept {
  if (!preparation.observed ||
      !preparation.preparation_owner_character_identity ||
      !preparation.preparation_owner_character_id ||
      !snapshot.observed_owner_identity ||
      !snapshot.observed_owner_character_id)
    return std::nullopt;
  return *preparation.preparation_owner_character_identity ==
             *snapshot.observed_owner_identity &&
         *preparation.preparation_owner_character_id ==
             *snapshot.observed_owner_character_id;
}

} // namespace

PersonInstalledTransferInvocation12004 InvokePersonInstalledTransferStage12004(
    const PersonInstalledTransferBindings12004 &bindings,
    PersonInstalledTransferOriginal12004 original,
    void *model_a, void *model_b, std::uintptr_t original_return_rva) noexcept {
  PersonInstalledTransferInvocation12004 result;
  auto &stage = result.stage;
  stage.original_return_rva = original_return_rva;
  if (!original) {
    stage.reason = "original_transfer_missing";
    return result;
  }
  if (original_return_rva != kPersonInstalledTransferCallerReturnRva12004) {
    result.raw_return_bits = original(model_a, model_b);
    stage.original_called = true;
    stage.original_returned = true;
    stage.reason = "different_native_transfer_caller";
    return result;
  }
  stage.observed = true;
  stage.model_a_identity = reinterpret_cast<std::uintptr_t>(model_a);
  stage.model_b_identity = reinterpret_cast<std::uintptr_t>(model_b);
  if (bindings.next_event)
    stage.before_event = bindings.next_event(bindings.event_context);
  stage.before = Snapshot(bindings, stage.model_a_identity,
                          stage.model_b_identity, std::nullopt, true);
  const auto owner = stage.before.observed_owner_identity;
  if (bindings.read_preparation && owner && *owner != 0 &&
      stage.before.observed_owner_character_id) {
    stage.preparation = bindings.read_preparation(
        bindings.preparation_context, *owner,
        *stage.before.observed_owner_character_id);
  }
  if (stage.preparation.observed &&
      stage.preparation.preparation_model_identity) {
    stage.preparation_model_is_b =
        stage.model_b_identity != 0 &&
        *stage.preparation.preparation_model_identity == stage.model_b_identity;
  }
  stage.preparation_owner_matches_before =
      OwnerMatches(stage.preparation, stage.before);

  result.raw_return_bits = original(model_a, model_b);
  stage.original_called = true;
  stage.original_returned = true;

  // The full native tail has returned to the wrapper; this observation does not
  // manufacture a generic-container postimage or a later Entry event.
  if (bindings.next_event)
    stage.completed_event = bindings.next_event(bindings.event_context);
  stage.after = Snapshot(bindings, stage.model_a_identity,
                         stage.model_b_identity, owner, false);
  stage.preparation_owner_matches_after =
      OwnerMatches(stage.preparation, stage.after);
  if (stage.before.observed_owner_character_id &&
      stage.after.observed_owner_character_id)
    stage.before_after_owner_generation_equal =
        *stage.before.observed_owner_character_id ==
        *stage.after.observed_owner_character_id;
  if (stage.before_event.clock_identity != 0 &&
      stage.completed_event.clock_identity != 0 &&
      stage.before_event.thread_id && stage.completed_event.thread_id) {
    stage.event_clock_and_thread_match =
        stage.before_event.clock_identity == stage.completed_event.clock_identity &&
        *stage.before_event.thread_id == *stage.completed_event.thread_id;
    if (*stage.event_clock_and_thread_match)
      stage.completion_ordered_after_begin =
          stage.completed_event.sequence > stage.before_event.sequence;
  }
  stage.reason = "original_paired_transfer_returned_identity_copy";
  return result;
}

} // namespace xar::ck3_12004
