#pragma once

#include "xar_bridge/ck3_12004_guardian_relation_observation.hpp"

namespace xar::ck3_12004 {

// Source-owned identities for the current child's generic full-ID peer map.
// Named relation matching remains the consumer's separate operation. These
// rows are not CharacterWindow.GetRelationsOfType or guardian target rows.
enum class ChildRelationCharacterIdentityStatus12004V1 {
  unavailable,
  resolved,
  known_null
};

struct ChildRelationPeerIdentityRow12004V1 {
  std::uint32_t peer_character_id{0xFFFFFFFFU};
  std::uintptr_t material_address{};
  std::optional<std::uintptr_t> character_address;
  std::optional<std::uint32_t> character_tag_raw;
  ChildRelationCharacterIdentityStatus12004V1 identity_status{
      ChildRelationCharacterIdentityStatus12004V1::unavailable};
  std::optional<std::uintptr_t> lookup_address;
  std::optional<std::uint32_t> observed_full_id;
  bool identity_available{};
  std::string_view unavailable_reason{"peer_identity_unavailable"};
};

struct CurrentChildRelationPeerIdentities12004V1 {
  std::uint32_t child_character_id{0xFFFFFFFFU};
  std::optional<std::uintptr_t> child_address;
  ChildRelationCharacterIdentityStatus12004V1 child_identity_status{
      ChildRelationCharacterIdentityStatus12004V1::unavailable};
  std::optional<std::uintptr_t> peer_extension_address;
  std::optional<std::uintptr_t> peer_data_address;
  std::optional<std::int32_t> peer_count_raw;
  bool available{};
  bool inventory_complete{};
  bool identities_complete{};
  bool identity_round_trip{};
  bool sample_stable{};
  std::string_view basis;
  std::string_view unavailable_reason{"child_peer_inventory_unavailable"};
  std::vector<ChildRelationPeerIdentityRow12004V1> rows;
};

namespace child_relation_peer_identities_detail {

struct Identity {
  ChildRelationCharacterIdentityStatus12004V1 status{
      ChildRelationCharacterIdentityStatus12004V1::unavailable};
  std::optional<std::uintptr_t> candidate;
  std::optional<std::uint32_t> observed_id;
  std::string_view reason{"character_identity_read_unavailable"};
};

// Same source storage/low24 slot/full32 generation comparison as the admitted
// Character selector, with read failure separated from observed lookup-null.
inline Identity CharacterIdentity(
    guardian_relation_observation_detail::Reader &read,
    std::uintptr_t storage, std::uint32_t id) {
  Identity output{};
  if (id == 0xFFFFFFFFU) {
    // No literal prelookup -1 absence branch is adopted for this carrier.
    output.reason = "full_id_domain_unavailable";
    return output;
  }
  if (storage == 0) {
    output.reason = "character_storage_domain_unavailable";
    return output;
  }
  std::uint32_t capacity{};
  if (!read.At(storage, 0x2C, capacity)) return output;
  const auto index = id & 0x00FFFFFFU;
  if (index >= capacity) {
    output.status = ChildRelationCharacterIdentityStatus12004V1::known_null;
    output.reason = "character_slot_out_of_range";
    return output;
  }
  std::uintptr_t slots{}, candidate{};
  if (!read.At(storage, 0x20, slots) ||
      !read.At(slots, static_cast<std::uintptr_t>(index) * 16U + 8U, candidate))
    return output;
  output.candidate = candidate;
  if (candidate == 0) {
    output.status = ChildRelationCharacterIdentityStatus12004V1::known_null;
    output.reason = "character_slot_null";
    return output;
  }
  std::uint32_t observed_id{};
  if (!read.At(candidate, 0x18, observed_id)) return output;
  output.observed_id = observed_id;
  if (observed_id != id) {
    output.status = ChildRelationCharacterIdentityStatus12004V1::known_null;
    output.reason = "character_full_generation_mismatch";
    return output;
  }
  output.status = ChildRelationCharacterIdentityStatus12004V1::resolved;
  output.reason = {};
  return output;
}

inline void Unavailable(CurrentChildRelationPeerIdentities12004V1 &output,
                        std::string_view reason) noexcept {
  output.available = false;
  output.inventory_complete = false;
  output.identities_complete = false;
  output.basis = {};
  output.unavailable_reason = reason;
  output.rows.clear();
}

inline void Finish(guardian_relation_observation_detail::Reader &read,
                   CurrentChildRelationPeerIdentities12004V1 &output) noexcept {
  output.sample_stable = read.Stable();
  if (!output.sample_stable) {
    output.identity_round_trip = false;
    output.child_identity_status = ChildRelationCharacterIdentityStatus12004V1::unavailable;
    output.child_address.reset();
    Unavailable(output, "child_peer_inventory_changed");
  }
}

} // namespace child_relation_peer_identities_detail

// Caller supplies the actual current descendant row's full generation ID.
// Reuse its existing paused query/frame shell. No player/heir/window subject
// substitution, parsed receiver construction, native call, or death/age filter.
inline CurrentChildRelationPeerIdentities12004V1
ReadCurrentChildRelationPeerIdentities12004V1(
    const GuardianFactoryReadEnvironment12004V1 &environment,
    const GuardianFactoryDiscoveryMetadata12004V1 &metadata,
    std::uint32_t child_character_id) noexcept {
  using guardian_relation_observation_detail::Reader;
  using namespace child_relation_peer_identities_detail;
  CurrentChildRelationPeerIdentities12004V1 output{};
  output.child_character_id = child_character_id;
  if (environment.module_base == 0 || environment.read_memory == nullptr ||
      metadata.module_base != environment.module_base) {
    Unavailable(output, "child_peer_environment_unavailable");
    return output;
  }
  try {
    Reader read(environment, metadata.image_size);
    std::uintptr_t storage{}, child{}, extension{};
    if (!read.Rva(kCharacterStorageSlotRva, storage)) {
      Unavailable(output, "current_child_full_id_unavailable");
      Finish(read, output);
      return output;
    }
    const auto child_identity = CharacterIdentity(read, storage, child_character_id);
    output.child_identity_status = child_identity.status;
    if (child_identity.status != ChildRelationCharacterIdentityStatus12004V1::resolved) {
      Unavailable(output, child_identity.reason);
      Finish(read, output);
      return output;
    }
    child = *child_identity.candidate;
    output.child_address = child;
    output.identity_round_trip = true;
    if (!read.At(child, 0x1B0, extension)) {
      Unavailable(output, "child_peer_extension_unreadable");
    } else {
      output.peer_extension_address = extension;
      if (extension == 0) {
        output.available = output.inventory_complete = output.identities_complete = true;
        output.basis = "generic_peer_extension_absent";
        output.unavailable_reason = {};
      } else {
        std::int32_t count{};
        std::uintptr_t begin{};
        if (!read.At(extension, 0x14, count)) {
          Unavailable(output, "child_peer_count_unreadable");
        } else {
          output.peer_count_raw = count;
          if (count == 0) {
            output.available = output.inventory_complete = output.identities_complete = true;
            output.basis = "generic_peer_entries_empty";
            output.unavailable_reason = {};
          } else if (count < 0) {
            Unavailable(output, "child_peer_array_domain_unavailable");
          } else if (!read.At(extension, 8, begin) || !read.Extent(begin, count, 16)) {
            Unavailable(output, "child_peer_array_unreadable");
          } else {
            output.peer_data_address = begin;
            output.identities_complete = true;
            bool copied = true;
            for (std::int32_t index = 0; index < count; ++index) {
              const auto cursor = begin + static_cast<std::uintptr_t>(index) * 16U;
              ChildRelationPeerIdentityRow12004V1 row{};
              if (!read.At(cursor, 0, row.peer_character_id) ||
                  !read.At(cursor, 8, row.material_address)) {
                Unavailable(output, "child_peer_record_unreadable");
                copied = false;
                break;
              }
              // Preserve raw inventory order and duplicate keys. Enumeration
              // does not add the lookup's ordered-domain assumptions as gates.
              const auto identity = CharacterIdentity(read, storage, row.peer_character_id);
              row.identity_status = identity.status;
              row.lookup_address = identity.candidate;
              row.observed_full_id = identity.observed_id;
              row.unavailable_reason = identity.reason;
              if (identity.status == ChildRelationCharacterIdentityStatus12004V1::resolved) {
                std::uint32_t tag{};
                if (!read.At(*identity.candidate, 0x1C, tag)) {
                  row.identity_status = ChildRelationCharacterIdentityStatus12004V1::unavailable;
                  row.unavailable_reason = "peer_character_tag_unreadable";
                } else {
                  row.character_tag_raw = tag;
                  if (tag == 0x43686172U) {
                    row.character_address = identity.candidate;
                    row.identity_available = true;
                    row.unavailable_reason = {};
                  } else {
                    row.identity_status = ChildRelationCharacterIdentityStatus12004V1::known_null;
                    row.unavailable_reason = "peer_character_type_rejected";
                  }
                }
              }
              if (row.identity_status == ChildRelationCharacterIdentityStatus12004V1::unavailable)
                output.identities_complete = false;
              output.rows.push_back(row);
            }
            if (copied) {
              output.available = output.inventory_complete = true;
              output.basis = "generic_full_id_peer_inventory";
              output.unavailable_reason = {};
            }
          }
        }
      }
    }
    Finish(read, output);
    return output;
  } catch (...) {
    output.identity_round_trip = false;
    output.sample_stable = false;
    Unavailable(output, "child_peer_inventory_exception");
    return output;
  }
}

} // namespace xar::ck3_12004
