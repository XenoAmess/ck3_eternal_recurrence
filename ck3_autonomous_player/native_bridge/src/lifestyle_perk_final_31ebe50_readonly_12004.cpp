#include "xar_bridge/lifestyle_perk_final_31ebe50_readonly_12004.hpp"
#include "xar_bridge/construction_collection_predicate_a11cc0_12004.hpp"
#include "xar_bridge/lifestyle_owned_perk_collection_2919340_12004.hpp"
#include "xar_bridge/lifestyle_character_scope_12004.hpp"
#include "xar_bridge/lifestyle_perk_truth_producer_12004.hpp"

#include <limits>

namespace xar::ck3_12004::lifestyle {
namespace {
static_assert(sizeof(std::uintptr_t) == 8, "Actual12004 Perk pointers require x64");
// The existing M5 current collector retains at most512 owned Perk pointers.
// This selected-definition reader uses the same finite occurrence ceiling;
// exceeding it is unavailable, never a native false result.
constexpr std::size_t kM5PointerOccurrenceBound = 512U;

template <typename T>
bool ReadField(const LifestylePerkReadonlyAccess12004 &access,
               std::uintptr_t object, std::uintptr_t offset, T &value) noexcept {
  if (access.read_memory == nullptr || object == 0 ||
      offset > std::numeric_limits<std::uintptr_t>::max() - object)
    return false;
  try {
    return access.read_memory(access.read_context, object + offset,
                              &value, sizeof(value));
  } catch (...) {
    return false;
  }
}

bool ReadMembershipMemory(void *opaque, const void *address, void *out,
                          std::size_t size) {
  const auto &access = *static_cast<const LifestylePerkReadonlyAccess12004 *>(opaque);
  return access.read_memory != nullptr && access.read_memory(
      access.read_context, reinterpret_cast<std::uintptr_t>(address), out, size);
}

std::optional<bool> ReadMembership(const LifestylePerkReadonlyAccess12004 &access,
                                  std::uintptr_t collection,
                                  std::uintptr_t actual_key) noexcept {
  using namespace construction_owner_mode3;
  // Reuse27's source-closed full-QWORD reader. Only first_pointer is an input
  // to its equality model. No admitted M4 paused frame or natural event is
  // manufactured: the unused copied frame fields stay zero.
  RawReceiverAccessV1 raw{const_cast<LifestylePerkReadonlyAccess12004 *>(&access),
                          &ReadMembershipMemory, access.module_base, true};
  ContextPredicateInputsV1 inputs{};
  inputs.first_pointer = actual_key;
  return ReadConstructionCollectionPredicateA11CC0V1(
      raw, inputs, collection, actual_key, kM5PointerOccurrenceBound).value;
}

LifestylePerkReadonlyPredicate12004 Unknown(const char *reason) {
  return {{}, reason};
}
} // namespace

LifestylePerkReadonlyPredicate12004 ReadLifestylePerkFinal31EBE5012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t selected_perk, std::uintptr_t resolved_character,
    std::uintptr_t diagnostic_writer_identity,
    LifestylePerkTruthProducer37998D0Result12004 *reached_truth_observation) noexcept {
  if (reached_truth_observation != nullptr)
    *reached_truth_observation = {};
  if (diagnostic_writer_identity != 0)
    return Unknown("nonnull_diagnostic_writer_path_not_projected");

  const auto initial = ReadLifestyleOwnedPerkCollection291934012004(
      access, resolved_character);
  if (!initial.returned_collection_identity)
    return Unknown("initial_owned_perk_collection_unavailable");
  const auto already_owned = ReadMembership(
      access, *initial.returned_collection_identity, selected_perk);
  if (!already_owned)
    return Unknown("initial_owned_perk_membership_unavailable");
  if (*already_owned)
    return {false, ""};

  std::uintptr_t prerequisite_buffer = 0;
  std::int32_t prerequisite_count = 0;
  if (!ReadField(access, selected_perk, 0x448U, prerequisite_buffer) ||
      !ReadField(access, selected_perk, 0x454U, prerequisite_count))
    return Unknown("prerequisite_header_unreadable");
  if (prerequisite_count < 0)
    return Unknown("negative_prerequisite_count");
  const auto occurrences = static_cast<std::size_t>(prerequisite_count);
  if (occurrences > kM5PointerOccurrenceBound)
    return Unknown("prerequisite_occurrence_bound_exceeded");
  for (std::size_t index = 0; index < occurrences; ++index) {
    std::uintptr_t required_perk = 0;
    if (!ReadField(access, prerequisite_buffer,
                   static_cast<std::uintptr_t>(index) * 8U, required_perk))
      return Unknown("prerequisite_pointer_unreadable");
    // Every native iteration calls2919340 again; preserve fresh demand.
    const auto current = ReadLifestyleOwnedPerkCollection291934012004(
        access, resolved_character);
    if (!current.returned_collection_identity)
      return Unknown("prerequisite_owned_perk_collection_unavailable");
    const auto owned = ReadMembership(
        access, *current.returned_collection_identity, required_perk);
    if (!owned)
      return Unknown("prerequisite_owned_perk_membership_unavailable");
    if (!*owned)
      return {false, ""};
  }

  LifestyleCharacterScope12004 context;
  if (!ProjectLifestyleCharacterScope9D78D012004(
          access, resolved_character, context))
    return Unknown("character_scope_source_projection_unavailable");
  const auto truth = ReadLifestylePerkTruthProducer37998D012004(
      access, selected_perk, context, access.current_query_source_frame);
  // A copied child-frame scope address is trace identity for this temporary
  // software projection only; callers must not dereference it after return.
  if (reached_truth_observation != nullptr)
    *reached_truth_observation = truth;
  if (!truth.value || !truth.source_projected_returned_raw_u8) {
    return {{}, truth.unavailable_reason.empty()
        ? "reached_perk_truth_output_unavailable" : truth.unavailable_reason};
  }
  // Actual31EC060 TESTAL canonicalizes any nonzero source-returned byte.
  return {*truth.source_projected_returned_raw_u8 != 0, ""};
}
} // namespace xar::ck3_12004::lifestyle
