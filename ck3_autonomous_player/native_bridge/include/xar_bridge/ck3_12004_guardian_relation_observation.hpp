#pragma once

#include "xar_bridge/ck3_12004_guardian_factory_metadata.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

// An owning value for the existing query's explicit played -> first-heir pair.
// This projects the source-closed lower relation primitives; it does not create
// a scripted trigger receiver or invoke its parsed-expression evaluator.
struct GuardianCurrentFamilyRelationRow12004V1 {
  bool available{};
  std::optional<bool> raw_value;
  std::string_view basis;
  std::string_view unavailable_reason{"pair_unavailable"};
  bool descriptor_reached{};
  std::optional<std::uint64_t> descriptor_raw;
  std::optional<std::uintptr_t> peer_address;
  std::optional<std::int32_t> peer_count_raw;
  std::optional<std::int32_t> relation_count_raw;
};

struct GuardianCurrentFamilyRelations12004V1 {
  std::uint32_t root_character_id{0xFFFFFFFFU};
  std::uint32_t target_character_id{0xFFFFFFFFU};
  std::optional<std::uintptr_t> root_address;
  std::optional<std::uintptr_t> target_address;
  std::optional<std::uint32_t> target_tag_raw;
  std::optional<std::uintptr_t> root_death_data_raw;
  std::optional<std::uintptr_t> target_death_data_raw;
  bool identity_round_trip{};
  bool sample_stable{};
  bool ready{};
  std::array<GuardianCurrentFamilyRelationRow12004V1, 2> rows{};
};

namespace guardian_relation_observation_detail {

struct Cell {
  std::uintptr_t address{};
  std::uint64_t bits{};
  std::size_t size{};
};

// Bookend only the exact scalar cells reached by this pair, including branch
// selectors. No character enumeration, borrowed-object copy or native call.
class Reader {
public:
  Reader(const GuardianFactoryReadEnvironment12004V1 &environment,
         std::uintptr_t image_size) : environment_(environment), image_size_(image_size) {}

  template <class Value>
  bool At(std::uintptr_t base, std::uintptr_t offset, Value &value) {
    static_assert(sizeof(Value) <= sizeof(std::uint64_t));
    constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
    if (base == 0 || offset > maximum - base ||
        sizeof(Value) - 1U > maximum - (base + offset)) return false;
    const auto address = base + offset;
    if (!environment_.read_memory(environment_.read_context, address, &value,
                                  sizeof(Value))) return false;
    Cell cell{address, 0, sizeof(Value)};
    std::memcpy(&cell.bits, &value, sizeof(Value));
    cells_.push_back(cell);
    return true;
  }

  template <class Value>
  bool Rva(std::uintptr_t rva, Value &value) {
    if (rva > image_size_ || sizeof(Value) > image_size_ - rva) return false;
    return At(environment_.module_base, rva, value);
  }

  bool Extent(std::uintptr_t begin, std::int32_t count,
              std::uintptr_t stride) const noexcept {
    if (count < 0) return false;
    if (count == 0) return true;
    constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
    return begin != 0 && static_cast<std::uintptr_t>(count) <=
        (maximum - begin) / stride;
  }

  bool Stable() const noexcept {
    for (const auto &cell : cells_) {
      std::uint64_t bits{};
      if (!environment_.read_memory(environment_.read_context, cell.address,
                                    &bits, cell.size) || bits != cell.bits)
        return false;
    }
    return true;
  }

private:
  const GuardianFactoryReadEnvironment12004V1 &environment_;
  std::uintptr_t image_size_{};
  std::vector<Cell> cells_;
};

inline void Unavailable(GuardianCurrentFamilyRelations12004V1 &output,
                        std::string_view reason) noexcept {
  output.ready = false;
  for (auto &row : output.rows) {
    row.available = false;
    row.raw_value.reset();
    row.basis = {};
    row.unavailable_reason = reason;
  }
}

inline void Known(GuardianCurrentFamilyRelationRow12004V1 &row, bool value,
                  std::string_view basis) noexcept {
  row.available = true;
  row.raw_value = value;
  row.basis = basis;
  row.unavailable_reason = {};
}

inline void KnownFalse(GuardianCurrentFamilyRelations12004V1 &output,
                       std::string_view basis) noexcept {
  for (auto &row : output.rows) Known(row, false, basis);
}

// Same actual .4 storage/full-generation pointer selection as the existing
// family resolver. An unresolved query identity is unavailable; no fallback
// sentinel is substituted as a current played/first-heir character.
inline bool Character(Reader &read, std::uintptr_t storage, std::uint32_t id,
                       std::uintptr_t &character) {
  if (id == 0xFFFFFFFFU) return false;
  std::int32_t capacity{};
  std::uintptr_t slots{};
  if (!read.At(storage, 0x2C, capacity) || capacity <= 0 ||
      !read.At(storage, 0x20, slots)) return false;
  const auto index = id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !read.At(slots, static_cast<std::uintptr_t>(index) * 16U + 8U,
               character) || character == 0) return false;
  std::uint32_t observed_id{};
  return read.At(character, 0x18, observed_id) && observed_id == id;
}

// Literal 2949A80 positive-count lower_bound, unsigned full-DWORD key. The
// source's negative-count path is outside this projection's finite domain;
// it is neither clamped to zero nor reported as a missing peer.
inline bool Peer(Reader &read, std::uintptr_t extension, std::uint32_t target,
                 std::uintptr_t &peer, std::optional<std::int32_t> &count_raw) {
  std::int32_t count{};
  if (!read.At(extension, 0x14, count)) return false;
  count_raw = count;
  if (count == 0) { peer = 0; return true; }
  std::uintptr_t begin{};
  if (!read.At(extension, 8, begin) || !read.Extent(begin, count, 16)) return false;
  auto cursor = begin;
  auto remaining = static_cast<std::uint64_t>(count);
  const auto end = begin + static_cast<std::uintptr_t>(count) * 16U;
  while (remaining != 0) {
    const auto half = remaining >> 1U;
    const auto midpoint = cursor + static_cast<std::uintptr_t>(half) * 16U;
    std::uint32_t key{};
    if (!read.At(midpoint, 0, key)) return false;
    if (key < target)
      cursor += static_cast<std::uintptr_t>(remaining - half) * 16U;
    remaining = half;
  }
  if (cursor == end) { peer = 0; return true; }
  std::uint32_t key{};
  if (!read.At(cursor, 0, key)) return false;
  if (target < key) { peer = 0; return true; }
  // Preserve the literal source comparison; do not add an equality fallback.
  return read.At(cursor, 8, peer);
}

// Literal mode-zero25942B0: raw-bit equality, followed by tagged16B rows.
// The tag2 and fallback bits receive no additional pointee/role interpretation.
inline bool Match(Reader &read, std::uintptr_t entry, std::uint64_t wanted,
                  bool &matched, std::string_view &basis) {
  std::uintptr_t stored{};
  if (!read.At(entry, 0, stored)) return false;
  if (static_cast<std::uint64_t>(stored) == wanted) {
    matched = true;
    basis = "entry_raw_equal";
    return true;
  }
  std::uintptr_t begin{};
  std::int32_t count{};
  if (!read.At(stored, 0x220, begin) || !read.At(stored, 0x22C, count) ||
      !read.Extent(begin, count, 16)) return false;
  if (count == 0) { matched = false; return true; }
  // The source reads fallback on every nonempty list, including tag2-only
  // rows; preserve that reached input rather than inventing a narrower gate.
  std::uint64_t fallback{};
  if (!read.Rva(0x5D1EBF8, fallback)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto cursor = begin + static_cast<std::uintptr_t>(index) * 16U;
    std::uint8_t tag{};
    if (!read.At(cursor, 0x0C, tag)) return false;
    auto selected = fallback;
    if (tag == 2 && !read.At(cursor, 0, selected)) return false;
    if (selected == wanted) {
      matched = true;
      basis = tag == 2 ? "tag2_row_raw_equal" : "fallback_raw_equal";
      return true;
    }
  }
  matched = false;
  return true;
}

inline void Relation(Reader &read, const GuardianFactoryTypedMetadata12004V1 &factory,
                      std::uintptr_t peer,
                      GuardianCurrentFamilyRelationRow12004V1 &row) {
  std::uintptr_t begin{};
  std::int32_t count{};
  if (!read.At(peer, 0x20, begin) || !read.At(peer, 0x2C, count)) {
    row.unavailable_reason = "relation_header_unreadable";
    return;
  }
  row.relation_count_raw = count;
  if (!read.Extent(begin, count, 40)) {
    row.unavailable_reason = "relation_array_domain_unavailable";
    return;
  }
  if (count == 0) { Known(row, false, "relation_entries_empty"); return; }
  row.descriptor_reached = true;
  const auto &lookup = factory.lookup;
  if (lookup.status != ExistingGuardianFactoryStatusV1::found ||
      !lookup.name_id || !lookup.map_name_id || !lookup.record_name_id ||
      *lookup.name_id != *lookup.map_name_id ||
      !factory.factory_create_input_18_qword) {
    row.unavailable_reason = "named_factory_input_unavailable";
    return;
  }
  std::uint32_t record_id{};
  std::uint64_t wanted{};
  if (!read.At(lookup.factory_address, 0x10, record_id) ||
      record_id != *lookup.record_name_id ||
      !read.At(lookup.factory_address, 0x18, wanted) ||
      wanted != *factory.factory_create_input_18_qword) {
    row.unavailable_reason = "named_factory_input_changed";
    return;
  }
  row.descriptor_raw = wanted;
  for (std::int32_t index = 0; index < count; ++index) {
    bool matched{};
    std::string_view basis;
    if (!Match(read, begin + static_cast<std::uintptr_t>(index) * 40U,
               wanted, matched, basis)) {
      row.unavailable_reason = "relation_predicate_input_unavailable";
      return;
    }
    if (matched) { Known(row, true, basis); return; }
  }
  Known(row, false, "relation_entries_exhausted");
}

} // namespace guardian_relation_observation_detail

inline GuardianCurrentFamilyRelations12004V1
ReadGuardianCurrentFamilyRelations12004V1(
    const GuardianFactoryReadEnvironment12004V1 &environment,
    const GuardianFactoryDiscoveryMetadata12004V1 &metadata,
    std::int32_t played_character_id, std::int32_t heir_character_id) noexcept {
  using namespace guardian_relation_observation_detail;
  GuardianCurrentFamilyRelations12004V1 output{};
  output.root_character_id = std::bit_cast<std::uint32_t>(played_character_id);
  output.target_character_id = std::bit_cast<std::uint32_t>(heir_character_id);
  if (environment.module_base == 0 || environment.read_memory == nullptr ||
      metadata.module_base != environment.module_base) {
    Unavailable(output, "relation_environment_unavailable");
    return output;
  }
  try {
    Reader read(environment, metadata.image_size);
    std::uintptr_t storage{}, root{}, target{};
    if (!read.Rva(kCharacterStorageSlotRva, storage) ||
        !Character(read, storage, output.root_character_id, root) ||
        !Character(read, storage, output.target_character_id, target)) {
      Unavailable(output, "current_family_identity_unavailable");
      return output;
    }
    output.root_address = root;
    output.target_address = target;
    output.identity_round_trip = true;
    std::uint32_t target_tag{};
    std::uintptr_t death{}, extension{}, peer{};
    std::optional<std::int32_t> peer_count;
    if (!read.At(target, 0x1C, target_tag)) {
      Unavailable(output, "target_tag_unreadable");
    } else {
      output.target_tag_raw = target_tag;
      if (target_tag != 0x43686172U) {
        KnownFalse(output, "target_tag_rejected");
      } else if (!read.At(root, 0x1D0, death)) {
        Unavailable(output, "root_state_unreadable");
      } else {
        output.root_death_data_raw = death;
        if (death != 0) {
          KnownFalse(output, "root_state_rejected");
        } else if (!read.At(target, 0x1D0, death)) {
          Unavailable(output, "target_state_unreadable");
        } else {
          output.target_death_data_raw = death;
          if (death != 0) {
            KnownFalse(output, "target_state_rejected");
          } else if (!read.At(root, 0x1B0, extension)) {
            Unavailable(output, "root_peer_extension_unreadable");
          } else if (extension == 0) {
            KnownFalse(output, "root_peer_extension_absent");
          } else if (!Peer(read, extension, output.target_character_id,
                           peer, peer_count)) {
            for (auto &row : output.rows) row.peer_count_raw = peer_count;
            Unavailable(output, "peer_lookup_input_unavailable");
          } else {
            for (auto &row : output.rows) {
              row.peer_address = peer;
              row.peer_count_raw = peer_count;
            }
            if (peer == 0) {
              KnownFalse(output, "peer_absent");
            } else {
              for (std::size_t index = 0; index < output.rows.size(); ++index)
                Relation(read, metadata.factories[index], peer, output.rows[index]);
            }
          }
        }
      }
    }
    output.sample_stable = read.Stable();
    if (!output.sample_stable) {
      output.identity_round_trip = false;
      Unavailable(output, "relation_sample_changed");
      return output;
    }
    output.ready = output.identity_round_trip &&
        output.rows[0].available && output.rows[1].available;
    return output;
  } catch (...) {
    output.identity_round_trip = false;
    output.sample_stable = false;
    Unavailable(output, "relation_observation_exception");
    return output;
  }
}

} // namespace xar::ck3_12004
