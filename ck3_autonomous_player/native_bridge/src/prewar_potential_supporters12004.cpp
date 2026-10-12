#include "xar_bridge/prewar_potential_supporters12004.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_family_obligations_alliance.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>

namespace xar::ck3_12004 {
namespace {
// Actual network 1A23FF0..1A24F1F, retained in shared-span-cache and the
// complete WarEntryNetworkCollector1A24010 actual4 instruction/edge mapping.
constexpr std::uintptr_t kSubjectContractStorageSlotRva = 0x5D1EB88;
constexpr std::uintptr_t kSubjectContractFallbackSlotRva = 0x5D1EB40;
constexpr std::uintptr_t kConfederationStorageSlotRva = 0x5D1EB78;
constexpr std::uintptr_t kConfederationFallbackSlotRva = 0x5D1EB50;
constexpr std::size_t kCharacterLandOffset = 0x1C0;
constexpr std::size_t kLandSubjectContractsOffset = 0x248;
constexpr std::size_t kLandOwnContractOffset = 0x1C8;
constexpr std::size_t kCharacterConfederationComponentOffset = 0x1C8;
constexpr std::size_t kComponentConfederationIdOffset = 0x80;
constexpr std::size_t kConfederationMembersOffset = 0x18;
constexpr std::size_t kComponentIdentityOffset = 0x08;
constexpr std::size_t kContractSubjectOffset = 0x20;
constexpr std::size_t kContractSuzerainOffset = 0x28;
// Reuse actual4 character_house_resolution in the retained prisoner layout
// ledger. No House member-vector layout or new native membership getter.
constexpr std::size_t kCharacterHouseIdOffset = 0x158;
constexpr std::int32_t kMaximumSourceRows = 65'536;

template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}

void SetReason(PrewarPotentialSupporters12004 &output, std::string_view value,
               std::string_view *reason) noexcept {
  output.reason = value;
  if (reason != nullptr) *reason = value;
}

const void *ResolveComponent(void **storage_slot, void **fallback_slot,
                             std::int32_t full_id) noexcept {
  if (storage_slot == nullptr || fallback_slot == nullptr || full_id == -1)
    return nullptr;
  const void *const storage = *storage_slot;
  if (storage == nullptr) return nullptr;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const void *const component = Load<const void *>(
      slots, static_cast<std::size_t>(index) * 0x10 + 0x08);
  if (component == nullptr || component == *fallback_slot ||
      Load<std::int32_t>(component, kComponentIdentityOffset) != full_id)
    return nullptr;
  return component;
}

bool SourceIds(const void *container, std::int32_t &count,
               std::int32_t &visited, std::vector<std::int32_t> &ids) {
  const auto *data = Load<const std::int32_t *>(container, 0);
  count = Load<std::int32_t>(container, 0xC);
  // Only actual data/count/stride operands are consumed; no capacity inferred.
  if (count < 0 || count > kMaximumSourceRows || (count != 0 && data == nullptr))
    return false;
  for (std::int32_t index = 0; index < count; ++index) {
    ids.push_back(data[index]);
    ++visited;
  }
  return true;
}

void AddCandidate(PrewarPotentialSupporters12004 &output, std::int32_t id,
                  PrewarPotentialSupporterSource12004 source) {
  if (id != output.owner_character_id)
    output.candidates.push_back({id, static_cast<std::uint32_t>(source)});
}

bool AddCharacterId(const PrewarPotentialSupportersBindings12004 &bindings,
                    PrewarPotentialSupporters12004 &output, std::int32_t id,
                    PrewarPotentialSupporterSource12004 source) {
  if (id == -1) return true; // Observed native absent reference.
  const void *const character = ck3_12004::ResolveCoreCharacter(
      bindings.alliance.core, id);
  if (character == nullptr) {
    output.unresolved_character_ids.push_back(id);
    return false;
  }
  if (Load<const void *>(character, kCharacterDeathDataOffset) != nullptr) {
    output.dead_source_character_ids.push_back(id);
    return true;
  }
  AddCandidate(output, id, source);
  return true;
}

bool ContractEndpoint(const PrewarPotentialSupportersBindings12004 &bindings,
                      const void *contract, std::size_t offset,
                      PrewarPotentialSupporters12004 &output,
                      std::int32_t &id, bool &verified,
                      PrewarPotentialSupporterSource12004 source) {
  const void *const character = Load<const void *>(contract, offset);
  if (character == nullptr) {
    ++output.unresolved_contract_endpoint_count;
    return false;
  }
  id = Load<std::int32_t>(character, kCharacterFullIdOffset);
  if (id == -1 || ck3_12004::ResolveCoreCharacter(bindings.alliance.core, id) !=
                      character) {
    ++output.unresolved_contract_endpoint_count;
    if (id != -1) output.unresolved_character_ids.push_back(id);
    return false;
  }
  verified = true;
  if (Load<const void *>(character, kCharacterDeathDataOffset) != nullptr)
    output.dead_source_character_ids.push_back(id);
  else
    AddCandidate(output, id, source);
  return true;
}

bool ReadContract(const PrewarPotentialSupportersBindings12004 &bindings,
                  const void *contract, std::int32_t id,
                  std::uint32_t order, bool own,
                  PrewarPotentialSupporters12004 &output) {
  PrewarPotentialContract12004 row{};
  row.contract_id = id;
  row.source_native_order = order;
  row.is_owner_contract = own;
  row.identity_verified = contract != nullptr;
  if (contract == nullptr) {
    output.unresolved_contract_ids.push_back(id);
    output.contracts.push_back(row);
    return false;
  }
  const bool subject = ContractEndpoint(bindings, contract, kContractSubjectOffset,
      output, row.subject_character_id, row.subject_verified,
      PrewarPotentialSupporterSource12004::subject_contract_endpoint);
  const bool suzerain = ContractEndpoint(bindings, contract, kContractSuzerainOffset,
      output, row.suzerain_character_id, row.suzerain_verified,
      PrewarPotentialSupporterSource12004::suzerain_contract_endpoint);
  output.contracts.push_back(row);
  return subject && suzerain;
}

void ReadContractSources(const PrewarPotentialSupportersBindings12004 &bindings,
                         const void *owner,
                         PrewarPotentialSupporters12004 &output) {
  const auto *land = Load<const std::byte *>(owner, kCharacterLandOffset);
  output.land_component_present = land != nullptr;
  if (land == nullptr) {
    output.contract_source_count = 0;
    output.contract_source_complete = true;
    output.owner_contract_source_complete = true;
    return;
  }
  output.contract_source_complete = SourceIds(
      land + kLandSubjectContractsOffset, output.contract_source_count,
      output.contract_source_visited_count, output.source_contract_ids);
  for (std::size_t index = 0; index < output.source_contract_ids.size(); ++index) {
    const auto id = output.source_contract_ids[index];
    if (id == -1) continue;
    const void *const contract = ResolveComponent(
        bindings.subject_contract_storage_slot,
        bindings.subject_contract_fallback_slot, id);
    if (!ReadContract(bindings, contract, id, static_cast<std::uint32_t>(index),
                      false, output)) output.contract_source_complete = false;
  }
  const void *const own_contract = Load<const void *>(land, kLandOwnContractOffset);
  if (own_contract == *bindings.subject_contract_fallback_slot &&
      own_contract != nullptr) {
    output.owner_contract_source_complete = true;
    return;
  }
  if (own_contract == nullptr) return; // Missing operand is unknown, not empty.
  output.owner_contract_present = true;
  const auto id = Load<std::int32_t>(own_contract, kComponentIdentityOffset);
  const void *const resolved = ResolveComponent(
      bindings.subject_contract_storage_slot,
      bindings.subject_contract_fallback_slot, id);
  output.owner_contract_source_complete = ReadContract(bindings,
      resolved == own_contract ? resolved : nullptr, id, 0, true, output);
}

void ReadConfederationSource(
    const PrewarPotentialSupportersBindings12004 &bindings, const void *owner,
    PrewarPotentialSupporters12004 &output) {
  const void *const component = Load<const void *>(
      owner, kCharacterConfederationComponentOffset);
  if (component == nullptr) {
    output.confederation_source_count = 0;
    output.confederation_source_complete = true;
    return;
  }
  output.confederation_id = Load<std::int32_t>(
      component, kComponentConfederationIdOffset);
  if (output.confederation_id == -1) {
    output.confederation_source_count = 0;
    output.confederation_source_complete = true;
    return;
  }
  const auto *confederation = static_cast<const std::byte *>(ResolveComponent(
      bindings.confederation_storage_slot, bindings.confederation_fallback_slot,
      output.confederation_id));
  if (confederation == nullptr) return;
  output.confederation_source_complete = SourceIds(
      confederation + kConfederationMembersOffset,
      output.confederation_source_count, output.confederation_source_visited_count,
      output.source_confederation_character_ids);
  for (const auto id : output.source_confederation_character_ids)
    if (!AddCharacterId(bindings, output, id,
                        PrewarPotentialSupporterSource12004::confederation_member))
      output.confederation_source_complete = false;
}

void CensusWord(PrewarPotentialSupporters12004 &output, std::uint64_t word) noexcept {
  output.character_census_fingerprint_a ^= word;
  output.character_census_fingerprint_a *= 0x100000001B3ULL;
  auto mixed = output.character_census_fingerprint_b + word + 0x9E3779B97F4A7C15ULL;
  mixed = (mixed ^ (mixed >> 30)) * 0xBF58476D1CE4E5B9ULL;
  mixed = (mixed ^ (mixed >> 27)) * 0x94D049BB133111EBULL;
  output.character_census_fingerprint_b = mixed ^ (mixed >> 31);
}

void ReadSameHouseSource(const PrewarPotentialSupportersBindings12004 &bindings,
                         const void *owner,
                         PrewarPotentialSupporters12004 &output) {
  output.owner_house_id = Load<std::int32_t>(owner, kCharacterHouseIdOffset);
  output.owner_house_observed = true;
  if (output.owner_house_id == -1) {
    output.same_house_source_complete = true;
    return; // The native no-House sentinel is a known empty House source.
  }
  output.whole_character_scan_required = true;
  const void *const storage = *bindings.alliance.core.character_storage_slot;
  if (storage == nullptr) return;
  output.character_storage_capacity = Load<std::int32_t>(
      storage, kCharacterStorageCapacityOffset);
  const auto *slots = Load<const std::byte *>(storage, kCharacterStorageSlotsOffset);
  // A verified living owner requires an occupied character store. Zero is not
  // a legitimate empty census after this sample's owner admission.
  if (output.character_storage_capacity <= 0 ||
      output.character_storage_capacity > kPrewarPotentialMaximumCharacterSlots12004 ||
      (output.character_storage_capacity != 0 && slots == nullptr)) return;
  output.character_census_fingerprint_a = 0xCBF29CE484222325ULL;
  output.character_census_fingerprint_b = 0x6A09E667F3BCC909ULL;
  CensusWord(output, static_cast<std::uint32_t>(output.character_storage_capacity));
  for (std::int32_t index = 0; index < output.character_storage_capacity; ++index) {
    const void *const character = Load<const void *>(slots,
        static_cast<std::size_t>(index) * kCharacterStorageSlotStride +
        kCharacterStorageObjectOffset);
    ++output.character_storage_visited_count;
    CensusWord(output, static_cast<std::uint32_t>(index));
    CensusWord(output, reinterpret_cast<std::uintptr_t>(character));
    if (character == nullptr) continue;
    ++output.character_storage_non_null_count;
    const auto id = Load<std::int32_t>(character, kCharacterFullIdOffset);
    CensusWord(output, static_cast<std::uint32_t>(id));
    if (id == -1 ||
        (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
            static_cast<std::uint32_t>(index) ||
        ck3_12004::ResolveCoreCharacter(bindings.alliance.core, id) != character) {
      output.unresolved_character_slot_indices.push_back(
          static_cast<std::uint32_t>(index));
      if (id != -1) output.unresolved_character_ids.push_back(id);
      continue;
    }
    const void *const death = Load<const void *>(character, kCharacterDeathDataOffset);
    const auto house_id = Load<std::int32_t>(character, kCharacterHouseIdOffset);
    CensusWord(output, reinterpret_cast<std::uintptr_t>(death));
    CensusWord(output, static_cast<std::uint32_t>(house_id));
    if (character == owner && id == output.owner_character_id && death == nullptr &&
        house_id == output.owner_house_id) output.character_storage_owner_seen = true;
    if (death != nullptr) {
      ++output.character_storage_dead_count;
      continue;
    }
    if (house_id == output.owner_house_id)
      AddCandidate(output, id,
                   PrewarPotentialSupporterSource12004::same_house_living_character);
  }
  output.whole_character_scan_complete =
      output.character_storage_visited_count == output.character_storage_capacity &&
      output.unresolved_character_slot_indices.empty() &&
      output.character_storage_owner_seen;
  output.same_house_source_complete = output.whole_character_scan_complete;
}

template <typename T> void Unique(std::vector<T> &values) {
  std::sort(values.begin(), values.end());
  values.erase(std::unique(values.begin(), values.end()), values.end());
}

void Normalize(PrewarPotentialSupporters12004 &output) {
  Unique(output.unresolved_contract_ids);
  Unique(output.unresolved_character_ids);
  Unique(output.dead_source_character_ids);
  auto &rows = output.candidates;
  std::sort(rows.begin(), rows.end(), [](const auto &first, const auto &second) {
    return first.character_id < second.character_id;
  });
  std::size_t kept = 0;
  for (const auto row : rows) {
    if (kept != 0 && rows[kept - 1].character_id == row.character_id)
      rows[kept - 1].source_mask |= row.source_mask;
    else
      rows[kept++] = row;
  }
  rows.resize(kept);
}
} // namespace

PrewarPotentialSupportersBindings12004 BindPrewarPotentialSupportersImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  PrewarPotentialSupportersBindings12004 output{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return output;
  output.alliance = BindFamilyObligationsAllianceImage(image_base, executable_sha256);
  if (!output.alliance.enabled || !output.alliance.core.enabled) return output;
  output.subject_contract_storage_slot = reinterpret_cast<void **>(
      image_base + kSubjectContractStorageSlotRva);
  output.subject_contract_fallback_slot = reinterpret_cast<void **>(
      image_base + kSubjectContractFallbackSlotRva);
  output.confederation_storage_slot = reinterpret_cast<void **>(
      image_base + kConfederationStorageSlotRva);
  output.confederation_fallback_slot = reinterpret_cast<void **>(
      image_base + kConfederationFallbackSlotRva);
  output.enabled = true;
  return output;
}

bool ReadPrewarPotentialSupporters12004(
    const PrewarPotentialSupportersBindings12004 &bindings,
    const ck3_12002::CoreSnapshotPrefix &frame,
    std::int32_t owner_character_id, PrewarPotentialSupporters12004 &output,
    std::string_view *reason) noexcept {
  output = {};
  output.owner_character_id = owner_character_id;
  if (reason != nullptr) *reason = {};
  if (!bindings.enabled || !bindings.alliance.enabled ||
      !bindings.alliance.core.enabled ||
      bindings.alliance.core.character_storage_slot == nullptr ||
      bindings.alliance.is_allied == nullptr ||
      bindings.subject_contract_storage_slot == nullptr ||
      bindings.subject_contract_fallback_slot == nullptr ||
      bindings.confederation_storage_slot == nullptr ||
      bindings.confederation_fallback_slot == nullptr) {
    SetReason(output, "prewar_potential_supporters_binding_unavailable", reason);
    return false;
  }
  if (!frame.clock.paused || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive) {
    SetReason(output, "prewar_potential_supporters_paused_played_frame_required", reason);
    return false;
  }
  try {
    const void *const player = ck3_12004::ResolveCoreCharacter(
        bindings.alliance.core, frame.played_character_id);
    if (player == nullptr ||
        Load<const void *>(player, kCharacterDeathDataOffset) != nullptr) {
      SetReason(output, "prewar_potential_supporters_played_full_id_unavailable", reason);
      return false;
    }
    const void *const owner = ck3_12004::ResolveCoreCharacter(
        bindings.alliance.core, owner_character_id);
    if (owner == nullptr) {
      SetReason(output, "prewar_potential_supporters_owner_full_id_unavailable", reason);
      return false;
    }
    output.owner_verified = true;
    output.owner_alive = Load<const void *>(owner, kCharacterDeathDataOffset) == nullptr;
    if (!output.owner_alive) {
      SetReason(output, "prewar_potential_supporters_owner_not_alive", reason);
      return false;
    }
    output.current_allies_available = ReadPrewarOwnerAllies12004(
        bindings.alliance, frame, owner_character_id, output.current_allies);
    for (const auto &ally : output.current_allies.allies)
      AddCandidate(output, ally.character_id,
                   PrewarPotentialSupporterSource12004::current_bilateral_alliance);
    output.unresolved_character_ids.insert(output.unresolved_character_ids.end(),
        output.current_allies.unresolved_source_character_ids.begin(),
        output.current_allies.unresolved_source_character_ids.end());
    output.dead_source_character_ids.insert(output.dead_source_character_ids.end(),
        output.current_allies.dead_source_character_ids.begin(),
        output.current_allies.dead_source_character_ids.end());
    ReadContractSources(bindings, owner, output);
    ReadConfederationSource(bindings, owner, output);
    ReadSameHouseSource(bindings, owner, output);
    Normalize(output);
    output.covered_source_subset_complete = output.current_allies_available &&
        output.current_allies.collection_complete && output.contract_source_complete &&
        output.owner_contract_source_complete && output.confederation_source_complete &&
        output.same_house_source_complete && output.unresolved_contract_ids.empty() &&
        output.unresolved_contract_endpoint_count == 0 &&
        output.unresolved_character_ids.empty();
    if (!output.current_allies_available || !output.current_allies.collection_complete)
      SetReason(output, "prewar_potential_supporters_alliance_source_partial", reason);
    else if (!output.contract_source_complete || !output.owner_contract_source_complete)
      SetReason(output, "prewar_potential_supporters_contract_source_partial", reason);
    else if (!output.confederation_source_complete)
      SetReason(output, "prewar_potential_supporters_confederation_source_partial", reason);
    else if (!output.same_house_source_complete)
      SetReason(output, output.character_storage_capacity >
                            kPrewarPotentialMaximumCharacterSlots12004
          ? "prewar_potential_supporters_character_scan_capacity_exceeded"
          : "prewar_potential_supporters_same_house_source_partial", reason);
    else if (!output.unresolved_character_ids.empty())
      SetReason(output, "prewar_potential_supporters_character_source_partial", reason);
    return true;
  } catch (...) {
    output.covered_source_subset_complete = false;
    SetReason(output, "prewar_potential_supporters_native_capture_exception", reason);
    return false;
  }
}

} // namespace xar::ck3_12004
