#include "xar_bridge/family_heir_betrothal_materializer_12004.hpp"
#include "xar_bridge/family_child_default_materializer_12004.hpp"
#include "xar_bridge/family_child_matrilineal_materializer_12004.hpp"
#include "xar_bridge/ck3_12002_family_query_abi.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <limits>
#include <utility>

namespace xar::bridge {
namespace {

using Status = FamilyRulerMaterializeStatus12004;

template <typename T>
bool ReadAt(const FamilyOutgoingStorageAccess12004 &access,
            std::uintptr_t base, std::size_t offset, T &out) noexcept {
  if (access.read_memory == nullptr) return false;
  constexpr auto top = (std::numeric_limits<std::uintptr_t>::max)();
  if (base == 0 || offset > top - base) return false;
  const auto address = base + offset;
  if (sizeof(T) - 1 > top - address) return false;
  return access.read_memory(access.context, address, &out, sizeof(T));
}

struct CharacterHeader {
  std::uintptr_t storage = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  friend bool operator==(const CharacterHeader &, const CharacterHeader &) = default;
};

struct CharacterEvidence {
  std::uintptr_t object = 0;
  std::uint32_t full_id = 0;
  std::uint8_t selector = 0;
  friend bool operator==(const CharacterEvidence &, const CharacterEvidence &) = default;
};

struct PairObservation {
  CharacterHeader header{};
  std::array<CharacterEvidence, 2> characters{};
  friend bool operator==(const PairObservation &, const PairObservation &) = default;
};

bool ReadHeader(const ck3_12002::CoreBindings &core,
                const FamilyOutgoingStorageAccess12004 &access,
                CharacterHeader &header) noexcept {
  return ReadAt(access, reinterpret_cast<std::uintptr_t>(core.character_storage_slot),
                0, header.storage) &&
      ReadAt(access, header.storage, 0x20, header.slots) &&
      ReadAt(access, header.storage, 0x2C, header.capacity);
}

bool ReadCharacter(const FamilyOutgoingStorageAccess12004 &access,
                   const CharacterHeader &header, std::uint32_t id,
                   CharacterEvidence &evidence) noexcept {
  const auto index = id & 0x00FFFFFFU;
  if (header.slots == 0 || header.capacity <= 0 || header.capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(header.capacity)) return false;
  const auto slot_offset = static_cast<std::size_t>(index) * 0x10U + 8U;
  return ReadAt(access, header.slots, slot_offset, evidence.object) &&
      ReadAt(access, evidence.object, 0x18, evidence.full_id) &&
      ReadAt(access, evidence.object,
             ck3_12002::family_query_abi::kAdultSelectorOffset,
             evidence.selector);
}

Status ReadPairObservation(const ck3_12002::CoreBindings &core,
                           const FamilyOutgoingStorageAccess12004 &access,
                           const std::array<std::uint32_t, 2> &ids,
                           PairObservation &output) noexcept {
  PairObservation copy{};
  if (!ReadHeader(core, access, copy.header)) return Status::unavailable;
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (!ReadCharacter(access, copy.header, ids[i], copy.characters[i]) ||
        copy.characters[i].full_id != ids[i] || copy.characters[i].selector > 1)
      return Status::unavailable;
  }
  CharacterHeader repeated_header{};
  if (!ReadHeader(core, access, repeated_header)) return Status::unavailable;
  if (repeated_header != copy.header) return Status::changed;
  for (std::size_t i = 0; i < ids.size(); ++i) {
    CharacterEvidence repeated{};
    if (!ReadCharacter(access, repeated_header, ids[i], repeated))
      return Status::unavailable;
    if (repeated != copy.characters[i]) return Status::changed;
  }
  if (!ReadHeader(core, access, repeated_header)) return Status::unavailable;
  if (repeated_header != copy.header) return Status::changed;
  output = copy;
  return Status::complete;
}

bool ValidRequest(const FamilyMarriageOutgoingRequestV2 &request) noexcept {
  if (request.scope != FamilyMarriageOutgoingScopeV2::action_preparation ||
      (request.route != FamilyMarriageOutgoingRouteV2::first_heir &&
       request.route != FamilyMarriageOutgoingRouteV2::fulfill_betrothal) ||
      request.actor == 0 || request.actor == UINT32_MAX ||
      request.subject == 0 || request.subject > 0x7FFFFFFFU ||
      request.candidate == 0 || request.candidate > 0x7FFFFFFFU ||
      !request.expected_recipient || request.sender ||
      request.request_matrilineal_option || request.require_matrilineal_option_off)
    return false;
  return *request.expected_recipient > 0 &&
      *request.expected_recipient <= 0x7FFFFFFFU &&
      request.actor != request.subject && request.actor != request.candidate &&
      request.subject != request.candidate;
}

} // namespace

FamilyRulerMaterializeStatus12004 MaterializeFamilyHeirBetrothalContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const FamilyMarriageOutgoingRequestV2 &request,
    FamilyHeirBetrothalPreparedCopy12004 &output) noexcept {
  output = {};
  if (!ValidRequest(request)) return Status::invalid_request;
  if (!bindings.enabled || !bindings.core.enabled ||
      bindings.redirect_roles == nullptr || bindings.construct_all_roles == nullptr ||
      bindings.refresh == nullptr || bindings.finalize == nullptr ||
      bindings.validate == nullptr || bindings.destroy == nullptr ||
      access.memory.read_memory == nullptr || access.read_boolean_option == nullptr ||
      access.matrilineal_option_id_slot == 0 || access.grand_wedding_option_id_slot == 0)
    return Status::unavailable;

  alignas(8) std::array<std::byte, 0x338> storage{};
  void *context = storage.data();
  bool owns_context = false;
  FamilyHeirBetrothalPreparedCopy12004 prepared{};
  Status status = Status::unavailable;
  try {
    status = [&]() -> Status {
      std::uintptr_t database = 0;
      std::uintptr_t definition = 0;
      if (!ReadAt(access.memory,
                  reinterpret_cast<std::uintptr_t>(bindings.interaction_database_slot),
                  0, database) ||
          !ReadAt(access.memory, database,
                  ck3_12002::kMarriageArrangeMarriageInteractionOffset, definition) ||
          definition == 0) return Status::unavailable;
      auto actor = std::bit_cast<std::int32_t>(request.actor);
      auto recipient = std::bit_cast<std::int32_t>(request.candidate);
      auto subject = std::bit_cast<std::int32_t>(request.subject);
      auto candidate = std::bit_cast<std::int32_t>(request.candidate);
      std::int32_t intermediary = -1;
      std::int32_t added_role = -1;
      bindings.redirect_roles(reinterpret_cast<void *>(definition), &actor, &recipient,
          &subject, &candidate, &intermediary, &added_role);
      if (std::bit_cast<std::uint32_t>(actor) != request.actor ||
          std::bit_cast<std::uint32_t>(subject) != request.subject ||
          std::bit_cast<std::uint32_t>(candidate) != request.candidate ||
          std::bit_cast<std::uint32_t>(recipient) != *request.expected_recipient)
        return Status::unavailable;
      const auto returned = bindings.construct_all_roles(context,
          reinterpret_cast<void *>(definition), actor, recipient, subject,
          candidate, intermediary, nullptr);
      owns_context = true;
      if (returned != context) return Status::unavailable;
      bindings.refresh(context, true);
      bindings.finalize(context);
      const std::array<std::uint32_t, 2> ids{request.subject, request.candidate};
      PairObservation before{};
      auto observed = ReadPairObservation(bindings.core, access.memory, ids, before);
      if (observed != Status::complete) return observed;
      observed = CopyFamilyRulerPreparedContext12004(bindings, access, context,
                                                     definition, prepared.materialized);
      if (observed != Status::complete) return observed;
      const std::array<std::uint32_t, 5> expected_roles{request.actor,
          *request.expected_recipient, request.subject, request.candidate,
          std::bit_cast<std::uint32_t>(intermediary)};
      if (prepared.materialized.roles != expected_roles) return Status::changed;
      PairObservation after{};
      observed = ReadPairObservation(bindings.core, access.memory, ids, after);
      if (observed != Status::complete) return observed;
      if (before != after) return Status::changed;
      const auto first = before.characters[0].selector;
      const auto second = before.characters[1].selector;
      prepared.effective_matrilineal_if_accepted = first == second
          ? first != 0 : prepared.materialized.matrilineal;
      return Status::complete;
    }();
  } catch (...) {
    status = Status::unavailable;
  }
  if (owns_context) {
    owns_context = false;
    try {
      bindings.destroy(context);
    } catch (...) {
      status = Status::unavailable;
    }
  }
  if (status == Status::complete) output = std::move(prepared);
  return status;
}

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
FamilyRulerMaterializeStatus12004 MaterializeFamilyChildMatrilinealContext12004(
    const ck3_12002::FamilyBindings &family,
    const FamilyRulerContextAccess12004 &access,
    const FamilyMarriageOutgoingRequestV2 &request,
    FamilyChildMatrilinealPreparedCopy12004 &output) noexcept {
  output = {};
  if (request.scope != FamilyMarriageOutgoingScopeV2::action_preparation ||
      request.route != FamilyMarriageOutgoingRouteV2::child_matrilineal ||
      request.actor == 0 || request.actor == UINT32_MAX ||
      request.subject == 0 || request.subject > 0x7FFFFFFFU ||
      request.candidate == 0 || request.candidate > 0x7FFFFFFFU ||
      !request.expected_recipient || *request.expected_recipient == 0 ||
      *request.expected_recipient > 0x7FFFFFFFU ||
      request.sender ||
      !request.request_matrilineal_option ||
      request.require_matrilineal_option_off ||
      request.actor == request.subject ||
      request.actor == request.candidate ||
      request.subject == request.candidate)
    return Status::invalid_request;

  if (!family.enabled || !family.context.enabled || !family.context.core.enabled ||
      family.context.redirect_roles == nullptr || family.context.construct_all_roles == nullptr ||
      family.context.refresh == nullptr || family.context.finalize == nullptr ||
      family.context.validate == nullptr || family.context.destroy == nullptr ||
      family.set_boolean_option == nullptr || family.read_boolean_option == nullptr ||
      family.matrilineal_option == nullptr || family.grand_wedding_option == nullptr ||
      access.memory.read_memory == nullptr || access.read_boolean_option == nullptr ||
      access.matrilineal_option_id_slot == 0 || access.grand_wedding_option_id_slot == 0)
    return Status::unavailable;

  if (access.read_boolean_option != family.read_boolean_option ||
      access.matrilineal_option_id_slot != reinterpret_cast<std::uintptr_t>(family.matrilineal_option) ||
      access.grand_wedding_option_id_slot != reinterpret_cast<std::uintptr_t>(family.grand_wedding_option))
    return Status::unavailable;

  alignas(8) std::array<std::byte, 0x338> storage{};
  void *context = storage.data();
  bool owns_context = false;
  FamilyHeirBetrothalPreparedCopy12004 prepared{};
  Status status = Status::unavailable;

  try {
    status = [&]() -> Status {
      std::uintptr_t database = 0;
      std::uintptr_t definition = 0;
      if (!ReadAt(access.memory,
                  reinterpret_cast<std::uintptr_t>(family.context.interaction_database_slot),
                  0, database) ||
          !ReadAt(access.memory, database,
                  ck3_12002::kMarriageArrangeMarriageInteractionOffset, definition) ||
          definition == 0) return Status::unavailable;

      std::uint32_t matrilineal_id_before = 0;
      if (!ReadAt(access.memory, access.matrilineal_option_id_slot, 0, matrilineal_id_before))
        return Status::unavailable;

      auto actor = std::bit_cast<std::int32_t>(request.actor);
      auto recipient = std::bit_cast<std::int32_t>(request.candidate);
      auto subject = std::bit_cast<std::int32_t>(request.subject);
      auto candidate = std::bit_cast<std::int32_t>(request.candidate);
      std::int32_t intermediary = -1;
      std::int32_t added_role = -1;

      family.context.redirect_roles(reinterpret_cast<void *>(definition), &actor, &recipient,
          &subject, &candidate, &intermediary, &added_role);

      if (std::bit_cast<std::uint32_t>(actor) != request.actor ||
          std::bit_cast<std::uint32_t>(subject) != request.subject ||
          std::bit_cast<std::uint32_t>(candidate) != request.candidate ||
          std::bit_cast<std::uint32_t>(recipient) != *request.expected_recipient)
        return Status::unavailable;

      const auto returned = family.context.construct_all_roles(context,
          reinterpret_cast<void *>(definition), actor, recipient, subject,
          candidate, intermediary, nullptr);
      owns_context = true;
      if (returned != context) return Status::unavailable;

      family.context.refresh(context, true);
      family.context.finalize(context);

      family.set_boolean_option(context, matrilineal_id_before, true);
      family.context.refresh(context, true);
      family.context.finalize(context);

      const std::array<std::uint32_t, 2> ids{request.subject, request.candidate};
      PairObservation before{};
      auto observed = ReadPairObservation(family.context.core, access.memory, ids, before);
      if (observed != Status::complete) return observed;

      observed = CopyFamilyRulerPreparedContext12004(family.context, access, context,
                                                     definition, prepared.materialized);
      if (observed != Status::complete) return observed;

      const std::array<std::uint32_t, 5> expected_roles{request.actor,
          *request.expected_recipient, request.subject, request.candidate,
          std::bit_cast<std::uint32_t>(intermediary)};
      if (prepared.materialized.roles != expected_roles) return Status::changed;

      if (!prepared.materialized.matrilineal) return Status::unavailable;

      PairObservation after{};
      observed = ReadPairObservation(family.context.core, access.memory, ids, after);
      if (observed != Status::complete) return observed;
      if (before != after) return Status::changed;

      std::uint32_t matrilineal_id_after = 0;
      if (!ReadAt(access.memory, access.matrilineal_option_id_slot, 0, matrilineal_id_after))
        return Status::unavailable;
      if (matrilineal_id_after != matrilineal_id_before) return Status::changed;

      const auto first = before.characters[0].selector;
      const auto second = before.characters[1].selector;
      prepared.effective_matrilineal_if_accepted = first == second
          ? first != 0 : prepared.materialized.matrilineal;

      return Status::complete;
    }();
  } catch (...) {
    status = Status::unavailable;
  }

  if (owns_context) {
    owns_context = false;
    try {
      family.context.destroy(context);
    } catch (...) {
      status = Status::unavailable;
    }
  }

  if (status == Status::complete) output = std::move(prepared);
  return status;
}
#endif

FamilyRulerMaterializeStatus12004 MaterializeFamilyChildDefaultContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const FamilyMarriageOutgoingRequestV2 &request,
    FamilyChildDefaultPreparedCopy12004 &output) noexcept {
  output = {};
  if (request.scope != FamilyMarriageOutgoingScopeV2::action_preparation ||
      request.route != FamilyMarriageOutgoingRouteV2::child_default ||
      request.actor == 0 || request.actor == UINT32_MAX ||
      request.subject == 0 || request.subject > 0x7FFFFFFFU ||
      request.candidate == 0 || request.candidate > 0x7FFFFFFFU ||
      !request.expected_recipient || *request.expected_recipient == 0 ||
      *request.expected_recipient > 0x7FFFFFFFU ||
      request.sender ||
      request.request_matrilineal_option ||
      !request.require_matrilineal_option_off ||
      request.actor == request.subject ||
      request.actor == request.candidate ||
      request.subject == request.candidate)
    return Status::invalid_request;

  if (!bindings.enabled || !bindings.core.enabled ||
      bindings.redirect_roles == nullptr || bindings.construct_all_roles == nullptr ||
      bindings.refresh == nullptr || bindings.finalize == nullptr ||
      bindings.validate == nullptr || bindings.destroy == nullptr ||
      access.memory.read_memory == nullptr || access.read_boolean_option == nullptr ||
      access.matrilineal_option_id_slot == 0 || access.grand_wedding_option_id_slot == 0)
    return Status::unavailable;

  alignas(8) std::array<std::byte, 0x338> storage{};
  void *context = storage.data();
  bool owns_context = false;
  FamilyHeirBetrothalPreparedCopy12004 prepared{};
  Status status = Status::unavailable;

  try {
    status = [&]() -> Status {
      std::uintptr_t database = 0;
      std::uintptr_t definition = 0;
      if (!ReadAt(access.memory,
                  reinterpret_cast<std::uintptr_t>(bindings.interaction_database_slot),
                  0, database) ||
          !ReadAt(access.memory, database,
                  ck3_12002::kMarriageArrangeMarriageInteractionOffset, definition) ||
          definition == 0) return Status::unavailable;

      auto actor = std::bit_cast<std::int32_t>(request.actor);
      auto recipient = std::bit_cast<std::int32_t>(request.candidate);
      auto subject = std::bit_cast<std::int32_t>(request.subject);
      auto candidate = std::bit_cast<std::int32_t>(request.candidate);
      std::int32_t intermediary = -1;
      std::int32_t added_role = -1;

      bindings.redirect_roles(reinterpret_cast<void *>(definition), &actor, &recipient,
          &subject, &candidate, &intermediary, &added_role);

      if (std::bit_cast<std::uint32_t>(actor) != request.actor ||
          std::bit_cast<std::uint32_t>(subject) != request.subject ||
          std::bit_cast<std::uint32_t>(candidate) != request.candidate ||
          std::bit_cast<std::uint32_t>(recipient) != *request.expected_recipient)
        return Status::unavailable;

      const auto returned = bindings.construct_all_roles(context,
          reinterpret_cast<void *>(definition), actor, recipient, subject,
          candidate, intermediary, nullptr);
      owns_context = true;
      if (returned != context) return Status::unavailable;

      bindings.refresh(context, true);
      bindings.finalize(context);

      const std::array<std::uint32_t, 2> ids{request.subject, request.candidate};
      PairObservation before{};
      auto observed = ReadPairObservation(bindings.core, access.memory, ids, before);
      if (observed != Status::complete) return observed;

      observed = CopyFamilyRulerPreparedContext12004(bindings, access, context,
                                                     definition, prepared.materialized);
      if (observed != Status::complete) return observed;

      const std::array<std::uint32_t, 5> expected_roles{request.actor,
          *request.expected_recipient, request.subject, request.candidate,
          std::bit_cast<std::uint32_t>(intermediary)};
      if (prepared.materialized.roles != expected_roles) return Status::changed;

      PairObservation after{};
      observed = ReadPairObservation(bindings.core, access.memory, ids, after);
      if (observed != Status::complete) return observed;
      if (before != after) return Status::changed;

      const auto first = before.characters[0].selector;
      const auto second = before.characters[1].selector;
      prepared.effective_matrilineal_if_accepted = first == second
          ? first != 0 : prepared.materialized.matrilineal;

      return Status::complete;
    }();
  } catch (...) {
    status = Status::unavailable;
  }

  if (owns_context) {
    owns_context = false;
    try {
      bindings.destroy(context);
    } catch (...) {
      status = Status::unavailable;
    }
  }

  if (status == Status::complete) output = std::move(prepared);
  return status;
}

} // namespace xar::bridge
