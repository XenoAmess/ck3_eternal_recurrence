#include "xar_bridge/h2743_stock_predicate_reader_v1.hpp"

#include <algorithm>
#include <array>
#include <limits>
#include <utility>
#include <vector>

namespace xar::game {
namespace {
using State = H2743StockPredicateStateV1;
using Failure = H2743StockPredicateFailureV1;
using Value = H2743StockPredicateValueV1;
constexpr std::uintptr_t kCharacterStorage = 0x570C130;
constexpr std::uintptr_t kWarStorage = 0x570C740;
constexpr std::uintptr_t kStruggleStorage = 0x570CC78;
constexpr std::uintptr_t kCbOwnerSlot = 0x570BE58;
constexpr std::uintptr_t kCbVtable = 0x44197A0;
constexpr std::uint32_t kBorderRaidHash = 0x229B01D7;
constexpr std::string_view kBorderRaidName = "fp2_border_raid";
constexpr std::string_view kShortName =
    "truces_by_involved_or_interlopers_within_region_shorter";
constexpr std::string_view kLongName =
    "truces_by_involved_or_interlopers_within_region_longer";
constexpr std::size_t kMaxStruggles = 128;
constexpr std::size_t kMaxWars = 1024;
constexpr std::size_t kMaxPhaseParameterRows = 1024;
constexpr std::size_t kMaxCbBuckets = 16384;

Value Unknown(Failure failure) { return {State::unavailable, failure}; }
Value Observed(bool value) {
  return {value ? State::observed_native_true : State::observed_native_false,
          Failure::none};
}
H2743StockPredicateResultV1 AllUnknown(Failure failure) {
  H2743StockPredicateResultV1 out{};
  out.short_truce = out.long_truce = out.border_raid_pair = Unknown(failure);
  return out;
}

struct ReadRecord {
  std::uintptr_t address = 0;
  std::vector<std::uint8_t> bytes;
  friend bool operator==(const ReadRecord &, const ReadRecord &) = default;
};

class Reader {
public:
  explicit Reader(const H2743StockPredicateBindingsV1 &bindings)
      : b(bindings) {}

  bool Bytes(std::uintptr_t address, void *out, std::size_t size) {
    constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
    if (address < 0x10000 || size == 0 || address > maximum - size ||
        !b.read_bytes(b.opaque, address, out, size)) {
      return false;
    }
    const auto *bytes = static_cast<const std::uint8_t *>(out);
    journal.push_back({address, {bytes, bytes + size}});
    return true;
  }
  template <typename T> bool Read(std::uintptr_t address, T &out) {
    return Bytes(address, &out, sizeof(out));
  }

  bool Resolve(std::uintptr_t slot_rva, std::uint32_t id,
               std::uintptr_t identity_offset, std::uintptr_t &out) {
    std::uintptr_t storage = 0, table = 0;
    std::uint32_t capacity = 0, actual = 0;
    const auto index = id & 0xFFFFFFU; // Index only; identity compares full ID.
    if (id == 0xFFFFFFFFU ||
        !Read(b.module_base + slot_rva, storage) || storage == 0 ||
        !Read(storage + 0x20, table) || table == 0 ||
        !Read(storage + 0x2C, capacity) || index >= capacity ||
        !Read(table + static_cast<std::uintptr_t>(index) * 16 + 8, out) ||
        out == 0 || !Read(out + identity_offset, actual) || actual != id) {
      return false;
    }
    return true;
  }

  Failure IdArray(std::uintptr_t header, std::size_t limit,
                  std::vector<std::uint32_t> &out) {
    std::uintptr_t data = 0;
    std::int32_t count = 0;
    // Stock getter proves data/count. Capacity is not a proven phase ABI gate.
    if (!Read(header, data) || !Read(header + 0x0C, count)) {
      return Failure::read_failed;
    }
    if (count < 0 || static_cast<std::size_t>(count) > limit) {
      return Failure::bounded_extent_exceeded;
    }
    if (count == 0) {
      out.clear();
      return Failure::none;
    }
    if (data == 0) {
      return Failure::cache_unavailable;
    }
    out.resize(static_cast<std::size_t>(count));
    return Bytes(data, out.data(), out.size() * sizeof(out[0]))
               ? Failure::none
               : Failure::read_failed;
  }

  Failure CharacterState(std::uint32_t id, std::uintptr_t &state) {
    std::uintptr_t character = 0;
    std::uint64_t dirty = 1;
    if (!Resolve(kCharacterStorage, id, 0x18, character)) {
      return Failure::stale_identity;
    }
    if (!Read(character + 0x1B8, state) ||
        !Read(character + 0x1C8, dirty)) {
      return Failure::read_failed;
    }
    return state != 0 && dirty == 0 ? Failure::none
                                   : Failure::cache_unavailable;
  }

  Failure Struggles(std::uintptr_t state, std::vector<std::uint32_t> &out) {
    std::vector<std::uint32_t> involved, interlopers;
    auto failure = IdArray(state + 0x168, kMaxStruggles, involved);
    if (failure != Failure::none) {
      return failure;
    }
    failure = IdArray(state + 0x180, kMaxStruggles, interlopers);
    if (failure != Failure::none) {
      return failure;
    }
    out = std::move(involved);
    out.insert(out.end(), interlopers.begin(), interlopers.end());
    // Stock mode2 emits full uint32 IDs into kind0x21/subtype0 tokens. The
    // original equality compares kind/subtype/full qword, never masked IDs.
    for (const auto id : out) {
      std::uintptr_t struggle = 0;
      if (!Resolve(kStruggleStorage, id, 8, struggle)) {
        return Failure::stale_identity;
      }
    }
    return Failure::none;
  }

  Failure PhaseParameters(std::uint32_t id,
                          std::vector<std::int32_t> &parameters) {
    std::uintptr_t struggle = 0, phase = 0;
    if (!Resolve(kStruggleStorage, id, 8, struggle)) {
      return Failure::stale_identity;
    }
    if (!Read(struggle + 0x4C0, phase) || phase == 0) {
      return Failure::phase_unavailable;
    }
    // Exact 0x2D05950 scans all four blocks and all four sorted arrays.
    constexpr std::array<std::uintptr_t, 4> headers{0xAB0, 0xAC8, 0xAE0,
                                                 0xAF8};
    for (std::uintptr_t block = 0; block != 4; ++block) {
      for (const auto offset : headers) {
        std::vector<std::uint32_t> ids;
        const auto failure = IdArray(phase + 0x78 + block * 0xB30 + offset,
                                     kMaxPhaseParameterRows, ids);
        if (failure != Failure::none) {
          return failure;
        }
        std::vector<std::int32_t> sorted;
        sorted.reserve(ids.size());
        for (const auto value : ids) {
          if (value > static_cast<std::uint32_t>(
                          std::numeric_limits<std::int32_t>::max())) {
            return Failure::phase_unavailable;
          }
          sorted.push_back(static_cast<std::int32_t>(value));
        }
        if (!std::is_sorted(sorted.begin(), sorted.end())) {
          return Failure::phase_unavailable;
        }
        parameters.insert(parameters.end(), sorted.begin(), sorted.end());
      }
    }
    return Failure::none;
  }

  bool DefinitionName(std::uintptr_t definition, std::string_view expected) {
    std::uint64_t length = 0, capacity = 0;
    std::uintptr_t data = definition + 0x18;
    if (!Read(definition + 0x28, length) ||
        !Read(definition + 0x30, capacity) || length != expected.size() ||
        capacity < length || capacity > 4096) {
      return false;
    }
    if (capacity >= 16 && (!Read(definition + 0x18, data) || data == 0)) {
      return false;
    }
    std::vector<char> bytes(expected.size() + 1);
    return Bytes(data, bytes.data(), bytes.size()) && bytes.back() == '\0' &&
           std::equal(expected.begin(), expected.end(), bytes.begin());
  }

  Failure BorderDefinition(std::uintptr_t &definition) {
    std::uint32_t hash = 0;
    std::uintptr_t owner = 0, buckets = 0;
    std::int32_t mask = -1;
    std::uint8_t overflow = 0;
    std::uint32_t lock_state = 1;
    std::uint8_t lock_mode = 1;
    if (b.hash_name == nullptr ||
        !b.hash_name(b.opaque, kBorderRaidName, hash) ||
        hash != kBorderRaidHash ||
        !Read(b.module_base + kCbOwnerSlot, owner) || owner == 0 ||
        !Read(owner + 0xEB8, lock_state) || lock_state != 0 ||
        !Read(owner + 0xEF8, lock_mode) || lock_mode != 0 ||
        !Read(owner + 0x198, buckets) || buckets == 0 ||
        !Read(owner + 0x1A4, mask) || mask < 0 ||
        !Read(owner + 0x1A8, overflow)) {
      return Failure::definition_unavailable;
    }
    const auto rows = static_cast<std::size_t>(mask) + overflow + 2;
    if (rows > kMaxCbBuckets || rows < 2) {
      return Failure::bounded_extent_exceeded;
    }
    std::vector<std::uint8_t> table(rows * 24);
    if (!Bytes(buckets, table.data(), table.size())) {
      return Failure::read_failed;
    }
    std::size_t index = hash & static_cast<std::uint32_t>(mask);
    std::uint16_t distance = 1;
    for (;;) {
      if (index >= rows || distance >= 255) {
        return Failure::definition_unavailable;
      }
      const auto *row = table.data() + index * 24;
      const auto state = row[4];
      if (state == 0xFF || state < distance) {
        return Failure::definition_unavailable;
      }
      std::uint32_t row_hash = 0;
      std::copy_n(row + 8, sizeof(row_hash),
                  reinterpret_cast<std::uint8_t *>(&row_hash));
      if (row_hash == hash) {
        std::copy_n(row + 16, sizeof(definition),
                    reinterpret_cast<std::uint8_t *>(&definition));
        std::uintptr_t vtable = 0;
        std::uint32_t definition_hash = 0;
        if (definition == 0 || !Read(definition, vtable) ||
            vtable != b.module_base + kCbVtable ||
            !Read(definition + 0x14, definition_hash) ||
            definition_hash != hash ||
            !DefinitionName(definition, kBorderRaidName)) {
          return Failure::definition_unavailable;
        }
        // 0x2024E40 proves bit0 is the writer and +2 counts readers when
        // mode==0. This reader never acquires that lock: conservatively admit
        // only the supported mode and a quiescent word before and after raw
        // table/name reads. Any occupied/changed mode stays unavailable.
        if (!Read(owner + 0xEB8, lock_state) || lock_state != 0 ||
            !Read(owner + 0xEF8, lock_mode) || lock_mode != 0) {
          return Failure::definition_unavailable;
        }
        return Failure::none;
      }
      ++index; // Native Robin Hood probe does not wrap through mask.
      ++distance;
    }
  }

  const H2743StockPredicateBindingsV1 &b;
  std::vector<ReadRecord> journal;
};

struct Sample {
  H2743StockPredicateResultV1 result{};
  std::int32_t short_identifier = -1;
  std::int32_t long_identifier = -1;
  std::vector<ReadRecord> journal;
};

Sample Collect(const H2743StockPredicateBindingsV1 &bindings,
               const H2743StockPredicateStampV1 &expected) {
  Sample sample{};
  sample.result = AllUnknown(Failure::read_failed);
  sample.result.stamp = expected;
  Reader reader(bindings);
  std::uintptr_t war = 0;
  auto &out = sample.result;
  if (!reader.Resolve(kWarStorage, expected.war_id, 8, war) ||
      !reader.Read(war + 0x288, out.attacker_id) ||
      !reader.Read(war + 0x28C, out.defender_id) ||
      out.attacker_id == out.defender_id || expected.actor_id != out.defender_id) {
    out.short_truce = out.long_truce = out.border_raid_pair =
        Unknown(Failure::stale_identity);
    sample.journal = std::move(reader.journal);
    return sample;
  }
  std::uintptr_t attacker_state = 0, defender_state = 0;
  const auto attacker_failure =
      reader.CharacterState(out.attacker_id, attacker_state);
  auto failure = attacker_failure;
  const auto defender_failure =
      reader.CharacterState(out.defender_id, defender_state);
  if (failure == Failure::none && defender_failure == Failure::none) {
    std::vector<std::uint32_t> attacker, defender;
    failure = reader.Struggles(attacker_state, attacker);
    if (failure == Failure::none) {
      failure = reader.Struggles(defender_state, defender);
    }
    if (failure == Failure::none) {
      const bool short_bound = bindings.lookup_identifier != nullptr &&
          bindings.lookup_identifier(bindings.opaque, kShortName,
                                      sample.short_identifier) &&
          sample.short_identifier >= 0 && sample.short_identifier != 12;
      const bool long_bound = bindings.lookup_identifier != nullptr &&
          bindings.lookup_identifier(bindings.opaque, kLongName,
                                      sample.long_identifier) &&
          sample.long_identifier >= 0 && sample.long_identifier != 12;
      bool shorter = false, longer = false;
      for (const auto id : attacker) {
        if (std::find(defender.begin(), defender.end(), id) == defender.end()) {
          continue;
        }
        std::vector<std::int32_t> parameters;
        failure = reader.PhaseParameters(id, parameters);
        if (failure != Failure::none) {
          break;
        }
        shorter = shorter || (short_bound &&
            std::find(parameters.begin(), parameters.end(),
                      sample.short_identifier) != parameters.end());
        longer = longer || (long_bound &&
            std::find(parameters.begin(), parameters.end(),
                      sample.long_identifier) != parameters.end());
      }
      out.short_truce = failure == Failure::none
          ? (short_bound ? Observed(shorter)
                         : Unknown(Failure::identifier_unavailable))
          : Unknown(failure);
      out.long_truce = failure == Failure::none
          ? (long_bound ? Observed(longer)
                        : Unknown(Failure::identifier_unavailable))
          : Unknown(failure);
    } else {
      out.short_truce = out.long_truce = Unknown(failure);
    }
  } else {
    out.short_truce = out.long_truce = Unknown(
        failure != Failure::none ? failure : defender_failure);
  }

  // Independent branch: missing struggle bindings cannot turn border false.
  std::uintptr_t definition = 0;
  std::uintptr_t defender_character = 0;
  if (attacker_failure != Failure::none) {
    failure = attacker_failure;
  } else if (!reader.Resolve(kCharacterStorage, out.defender_id, 0x18,
                             defender_character)) {
    // Stock named defender scope uses the resolved complete Character ID,
    // including generation. A stale role must not become a raw-ID match.
    // Defender struggle cache availability is independent of this identity.
    failure = Failure::stale_identity;
  } else {
    failure = reader.BorderDefinition(definition);
  }
  if (failure == Failure::none) {
    std::vector<std::uint32_t> wars;
    failure = reader.IdArray(attacker_state + 0x318, kMaxWars, wars);
    bool matched = false;
    for (const auto id : wars) {
      if (failure != Failure::none) {
        break;
      }
      std::uintptr_t listed_war = 0, active_cb = 0;
      std::uint32_t attacker = 0, defender = 0;
      if (!reader.Resolve(kWarStorage, id, 8, listed_war) ||
          !reader.Read(listed_war + 0x288, attacker) ||
          !reader.Read(listed_war + 0x28C, defender) ||
          !reader.Read(listed_war + 0x100, active_cb) || active_cb == 0) {
        failure = Failure::stale_identity;
        break;
      }
      matched = matched || (attacker == out.attacker_id &&
                            defender == out.defender_id &&
                            active_cb == definition);
    }
    out.border_raid_pair = failure == Failure::none ? Observed(matched)
                                                   : Unknown(failure);
  } else {
    out.border_raid_pair = Unknown(failure);
  }
  sample.journal = std::move(reader.journal);
  return sample;
}

bool MatchingStamp(const H2743StockPredicateBindingsV1 &bindings,
                   const H2743StockPredicateStampV1 &expected) {
  H2743StockPredicateStampV1 actual{};
  return bindings.read_stamp(bindings.opaque, actual) && actual == expected;
}
} // namespace

H2743StockPredicateResultV1 ReadH2743StockPredicatesV1(
    const H2743StockPredicateBindingsV1 &bindings,
    const H2743StockPredicateStampV1 &expected) {
  if (!bindings.enabled) {
    return AllUnknown(Failure::disabled);
  }
  if (!bindings.exact_build_verified || !bindings.application_main_verified ||
      bindings.module_base == 0 || bindings.read_bytes == nullptr ||
      bindings.read_stamp == nullptr || expected.actor_id == 0 ||
      expected.war_id == 0 || expected.revision == 0 ||
      expected.native_revision == 0 || !expected.paused || !expected.living_map) {
    return AllUnknown(Failure::wrong_session);
  }
  try {
    if (!MatchingStamp(bindings, expected)) {
      return AllUnknown(Failure::unstable_sample);
    }
    auto first = Collect(bindings, expected);
    if (!MatchingStamp(bindings, expected)) {
      return AllUnknown(Failure::unstable_sample);
    }
    auto second = Collect(bindings, expected);
    if (!MatchingStamp(bindings, expected) || first.journal != second.journal ||
        first.short_identifier != second.short_identifier ||
        first.long_identifier != second.long_identifier ||
        first.result.attacker_id != second.result.attacker_id ||
        first.result.defender_id != second.result.defender_id ||
        first.result.short_truce != second.result.short_truce ||
        first.result.long_truce != second.result.long_truce ||
        first.result.border_raid_pair != second.result.border_raid_pair) {
      return AllUnknown(Failure::unstable_sample);
    }
    second.result.double_sample_stable = true;
    return second.result;
  } catch (...) {
    return AllUnknown(Failure::read_failed);
  }
}
} // namespace xar::game
