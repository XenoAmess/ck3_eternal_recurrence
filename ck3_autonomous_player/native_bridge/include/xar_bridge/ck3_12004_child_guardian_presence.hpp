#pragma once

#include "xar_bridge/ck3_12004_child_relation_peer_identities.hpp"

namespace xar::ck3_12004 {

// Existential projection of the named guardian descriptor over the current
// child's generic peer materials. This is not Character.HasGuardian, a GUI
// guardian collection, a directed guardian identity, or educator eligibility.
struct ChildGuardianMaterialPresence12004V1 {
  std::uint32_t child_character_id{0xFFFFFFFFU};
  std::optional<std::uintptr_t> child_address;
  bool available{};
  bool identity_round_trip{};
  bool inventory_join_complete{};
  bool sample_stable{};
  std::optional<bool> named_material_present;
  std::optional<std::uint32_t> matched_peer_full_id;
  std::optional<std::uintptr_t> matched_peer_character_address;
  bool witness_identity_available{};
  ChildRelationCharacterIdentityStatus12004V1 witness_identity_status{
      ChildRelationCharacterIdentityStatus12004V1::unavailable};
  std::string_view basis;
  std::string_view unavailable_reason{"child_guardian_material_unavailable"};
};

namespace child_guardian_presence_detail {

inline void Unavailable(ChildGuardianMaterialPresence12004V1 &output,
                        std::string_view reason) noexcept {
  output.available = false;
  output.named_material_present.reset();
  output.matched_peer_full_id.reset();
  output.matched_peer_character_address.reset();
  output.witness_identity_available = false;
  output.witness_identity_status =
      ChildRelationCharacterIdentityStatus12004V1::unavailable;
  output.basis = {};
  output.unavailable_reason = reason;
}

inline void Finish(guardian_relation_observation_detail::Reader &read,
                   ChildGuardianMaterialPresence12004V1 &output) noexcept {
  output.sample_stable = read.Stable();
  if (!output.sample_stable) {
    output.identity_round_trip = false;
    output.inventory_join_complete = false;
    Unavailable(output, "child_guardian_material_sample_changed");
  }
}

} // namespace child_guardian_presence_detail

// Consume 26's owning carrier within the same guarded paused-query shell and
// reader budget that produced it. This leaf rechecks its reached source cells;
// it does not independently enumerate or resolve character storage. The caller
// must retain the query's outer frame bookends. No native getter is invoked.
// False means this complete generic inventory has no matching named material;
// it cannot unlock an education fallback or establish a null guardian identity.
inline ChildGuardianMaterialPresence12004V1
ReadCurrentChildGuardianMaterialPresence12004V1(
    const GuardianFactoryReadEnvironment12004V1 &environment,
    const GuardianFactoryDiscoveryMetadata12004V1 &metadata,
    const CurrentChildRelationPeerIdentities12004V1 &peers) noexcept {
  using guardian_relation_observation_detail::Reader;
  using guardian_relation_observation_detail::Relation;
  using namespace child_guardian_presence_detail;
  ChildGuardianMaterialPresence12004V1 output{};
  output.child_character_id = peers.child_character_id;
  output.child_address = peers.child_address;
  if (environment.module_base == 0 || environment.read_memory == nullptr ||
      metadata.module_base != environment.module_base ||
      !peers.available || !peers.inventory_complete ||
      !peers.identity_round_trip || !peers.sample_stable ||
      peers.child_character_id == 0xFFFFFFFFU ||
      !peers.child_address || !peers.peer_extension_address) {
    Unavailable(output, "child_peer_carrier_unavailable");
    return output;
  }
  const GuardianFactoryTypedMetadata12004V1 *factory{};
  for (const auto &candidate : metadata.factories) {
    if (candidate.lookup.key != "has_relation_guardian") continue;
    if (factory != nullptr) {
      Unavailable(output, "guardian_factory_key_ambiguous");
      return output;
    }
    factory = &candidate;
  }
  if (factory == nullptr) {
    Unavailable(output, "guardian_factory_key_unavailable");
    return output;
  }
  try {
    Reader read(environment, metadata.image_size);
    std::uint32_t observed_id{};
    std::uintptr_t extension{};
    if (!read.At(*peers.child_address, 0x18, observed_id) ||
        observed_id != peers.child_character_id ||
        !read.At(*peers.child_address, 0x1B0, extension) ||
        extension != *peers.peer_extension_address) {
      Unavailable(output, "child_peer_carrier_changed");
      Finish(read, output);
      return output;
    }
    output.identity_round_trip = true;
    std::uintptr_t begin{};
    std::int32_t count{};
    if (extension == 0) {
      if (!peers.rows.empty()) {
        Unavailable(output, "child_peer_carrier_domain_unavailable");
        Finish(read, output);
        return output;
      }
    } else if (!peers.peer_count_raw ||
               !read.At(extension, 0x14, count) ||
               count != *peers.peer_count_raw || count < 0 ||
               static_cast<std::size_t>(count) != peers.rows.size()) {
      Unavailable(output, "child_peer_carrier_count_changed");
      Finish(read, output);
      return output;
    } else if (count != 0 &&
               (!peers.peer_data_address ||
                !read.At(extension, 8, begin) ||
                begin != *peers.peer_data_address ||
                !read.Extent(begin, count, 16))) {
      Unavailable(output, "child_peer_carrier_array_changed");
      Finish(read, output);
      return output;
    }

    // Revalidate the already-owned records, preserving every full DWORD key
    // and raw material QWORD. No inferred target list or age/death filter.
    for (std::size_t index = 0; index < peers.rows.size(); ++index) {
      const auto cursor = begin + static_cast<std::uintptr_t>(index) * 16U;
      std::uint32_t key{};
      std::uintptr_t material{};
      if (!read.At(cursor, 0, key) || !read.At(cursor, 8, material) ||
          key != peers.rows[index].peer_character_id ||
          material != peers.rows[index].material_address) {
        Unavailable(output, "child_peer_carrier_record_changed");
        Finish(read, output);
        return output;
      }
    }
    output.inventory_join_complete = true;

    for (const auto &peer : peers.rows) {
      // A null lookup value is a known missing material, not an unreadable
      // relation header and not a known-null guardian character.
      if (peer.material_address == 0) continue;
      GuardianCurrentFamilyRelationRow12004V1 relation{};
      Relation(read, *factory, peer.material_address, relation);
      if (!relation.available || !relation.raw_value.has_value()) {
        Unavailable(output, relation.unavailable_reason);
        Finish(read, output);
        return output;
      }
      if (!*relation.raw_value) continue;
      output.named_material_present = true;
      output.matched_peer_full_id = peer.peer_character_id;
      output.basis = relation.basis;
      // A known-null full-ID lookup is an observed peer identity result from
      // the same carrier sample, never a known-null guardian or unreadable cell.
      output.witness_identity_status = peer.identity_status;
      if (peer.identity_available && peer.character_address &&
          peer.character_tag_raw) {
        std::uint32_t peer_id{}, tag{};
        if (read.At(*peer.character_address, 0x18, peer_id) &&
            read.At(*peer.character_address, 0x1C, tag) &&
            peer_id == peer.peer_character_id &&
            tag == *peer.character_tag_raw && tag == 0x43686172U) {
          output.witness_identity_available = true;
          output.witness_identity_status =
              ChildRelationCharacterIdentityStatus12004V1::resolved;
          output.matched_peer_character_address = peer.character_address;
        } else {
          output.witness_identity_status =
              ChildRelationCharacterIdentityStatus12004V1::unavailable;
        }
      } else if (peer.identity_status ==
                 ChildRelationCharacterIdentityStatus12004V1::resolved) {
        output.witness_identity_status =
            ChildRelationCharacterIdentityStatus12004V1::unavailable;
      }
      output.available = true;
      output.unavailable_reason = {};
      Finish(read, output);
      return output;
    }
    output.available = true;
    output.named_material_present = false;
    output.basis = peers.rows.empty() ? "generic_inventory_empty" :
                                       "named_materials_exhausted";
    output.unavailable_reason = {};
    Finish(read, output);
    return output;
  } catch (...) {
    output.identity_round_trip = false;
    output.inventory_join_complete = false;
    output.sample_stable = false;
    Unavailable(output, "child_guardian_material_exception");
    return output;
  }
}

} // namespace xar::ck3_12004
