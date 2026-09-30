#include "xar_bridge/h2743_stock_predicate_reader_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar::game;
using State = H2743StockPredicateStateV1;
using Failure = H2743StockPredicateFailureV1;
using Result = H2743StockPredicateResultV1;

int checks = 0;
int failures = 0;
void Check(bool condition, const char *expression, int line) {
  ++checks;
  if (!condition) {
    ++failures;
    std::fprintf(stderr, "CHECK failed at line %d: %s\n", line, expression);
  }
}
#define CHECK(expression) Check(static_cast<bool>(expression), #expression, __LINE__)

bool Is(const H2743StockPredicateValueV1 &value, State state,
        Failure failure = Failure::none) {
  return value.state == state && value.failure == failure;
}
bool AllUnknown(const Result &result, Failure failure) {
  return Is(result.short_truce, State::unavailable, failure) &&
         Is(result.long_truce, State::unavailable, failure) &&
         Is(result.border_raid_pair, State::unavailable, failure);
}

// Every object, table, array and phase is a complete contiguous fake region.
// Reads must fit one whole region; absent bytes never become implicit zeros.
struct Fixture {
  static constexpr std::uintptr_t module = 0x140000000ULL;
  static constexpr std::uint32_t attacker_id = 0x01000001U;
  static constexpr std::uint32_t defender_id = 0x02000002U;
  static constexpr std::uint32_t war_id = 0x03000003U;
  static constexpr std::uint32_t raid_war_id = 0x04000004U;
  static constexpr std::uint32_t struggle_id = 0x05000005U;
  static constexpr std::int32_t short_id = 100;
  static constexpr std::int32_t long_id = 200;
  static constexpr std::uint32_t border_hash = 0x229B01D7U;
  static constexpr std::string_view short_name =
      "truces_by_involved_or_interlopers_within_region_shorter";
  static constexpr std::string_view long_name =
      "truces_by_involved_or_interlopers_within_region_longer";
  static constexpr std::string_view border_name = "fp2_border_raid";

  struct Region {
    std::uintptr_t address;
    std::vector<std::uint8_t> bytes;
  };
  std::vector<Region> regions;
  std::uintptr_t next_address = 0x200000000ULL;
  std::uintptr_t attacker = 0, defender = 0, war = 0, raid_war = 0;
  std::uintptr_t attacker_cache = 0, defender_cache = 0;
  std::uintptr_t struggle = 0, phase = 0;
  std::uintptr_t cb_owner = 0, cb_buckets = 0, cb_definition = 0;
  std::uintptr_t alternate_attacker_rows = 0;
  H2743StockPredicateStampV1 expected{
      defender_id, war_id, 12345, 17, 19, true, true};
  std::size_t reads = 0, lookups = 0, hashes = 0, stamps = 0;
  bool short_available = true, long_available = true;
  bool return_missing_as_success = false;
  std::size_t change_stamp_at = 0, change_raw_at = 0;

  void AddRegion(std::uintptr_t address, std::size_t size) {
    regions.push_back({address, std::vector<std::uint8_t>(size, 0)});
  }
  std::uintptr_t Allocate(std::size_t size) {
    const auto address = next_address;
    next_address += (size + 0xFFFU) & ~std::uintptr_t{0xFFFU};
    AddRegion(address, size);
    return address;
  }
  bool WriteBytes(std::uintptr_t address, const void *bytes,
                  std::size_t size) noexcept {
    for (auto &region : regions) {
      if (address < region.address)
        continue;
      const auto offset = address - region.address;
      if (offset <= region.bytes.size() &&
          size <= region.bytes.size() - offset) {
        std::memcpy(region.bytes.data() + offset, bytes, size);
        return true;
      }
    }
    return false;
  }
  template <typename T> void Put(std::uintptr_t address, const T &value) {
    if (!WriteBytes(address, &value, sizeof(value))) {
      std::fprintf(stderr, "Fixture write outside region\n");
      std::abort();
    }
  }
  std::uintptr_t IdArray(std::uintptr_t header,
                         std::initializer_list<std::uint32_t> ids) {
    const auto data = ids.size() == 0 ? 0 : Allocate(ids.size() * 4);
    std::size_t index = 0;
    for (const auto id : ids)
      Put(data + index++ * 4, id);
    Put(header, static_cast<std::uintptr_t>(data));
    Put(header + 8, static_cast<std::int32_t>(ids.size()));
    Put(header + 0xC, static_cast<std::int32_t>(ids.size()));
    Put(header + 0x10, std::uintptr_t{0});
    return data;
  }
  void Storage(std::uintptr_t slot_rva,
               std::initializer_list<std::pair<std::uint32_t,
                                               std::uintptr_t>> objects) {
    const auto storage = Allocate(0x40);
    const auto table = Allocate(8 * 16);
    Put(module + slot_rva, storage);
    Put(storage + 0x20, table);
    Put(storage + 0x2C, std::uint32_t{8});
    for (const auto &entry : objects)
      Put(table + (entry.first & 0xFFFFFFU) * 16 + 8, entry.second);
  }
  void DefinitionName(std::string_view name) {
    if (name.size() > 15)
      std::abort();
    char bytes[16]{};
    std::memcpy(bytes, name.data(), name.size());
    Put(cb_definition + 0x18, bytes);
    Put(cb_definition + 0x28, static_cast<std::uint64_t>(name.size()));
    Put(cb_definition + 0x30, std::uint64_t{15});
  }
  void Shared(std::initializer_list<std::uint32_t> parameters) {
    IdArray(attacker_cache + 0x168, {struggle_id});
    IdArray(defender_cache + 0x180, {struggle_id});
    // Exercise the last of sixteen phase arrays, not just the first block.
    IdArray(phase + 0x78 + 3 * 0xB30 + 0xAF8, parameters);
    alternate_attacker_rows = Allocate(sizeof(struggle_id));
    Put(alternate_attacker_rows, struggle_id);
  }
  void BorderWar() { IdArray(attacker_cache + 0x318, {raid_war_id}); }

  static bool Read(void *opaque, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    ++self.reads;
    if (output == nullptr || size == 0)
      return false;
    for (const auto &region : self.regions) {
      if (address < region.address)
        continue;
      const auto offset = address - region.address;
      if (offset <= region.bytes.size() &&
          size <= region.bytes.size() - offset) {
        std::memcpy(output, region.bytes.data() + offset, size);
        return true;
      }
    }
    return false;
  }
  static bool Lookup(void *opaque, std::string_view name,
                     std::int32_t &output) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    ++self.lookups;
    if (name == short_name) {
      output = self.short_available ? short_id : 12;
      return self.short_available || self.return_missing_as_success;
    }
    if (name == long_name) {
      output = self.long_available ? long_id : 12;
      return self.long_available || self.return_missing_as_success;
    }
    output = -1;
    return false;
  }
  static bool Hash(void *opaque, std::string_view name,
                   std::uint32_t &output) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    ++self.hashes;
    output = name == border_name ? border_hash : 0;
    return name == border_name;
  }
  static bool Stamp(void *opaque,
                    H2743StockPredicateStampV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    ++self.stamps;
    output = self.expected;
    if (self.stamps == self.change_stamp_at)
      ++output.date_raw;
    if (self.stamps == self.change_raw_at &&
        !self.WriteBytes(self.attacker_cache + 0x168,
                         &self.alternate_attacker_rows,
                         sizeof(self.alternate_attacker_rows)))
      return false;
    return true;
  }
  H2743StockPredicateBindingsV1 Bindings() {
    H2743StockPredicateBindingsV1 bindings{};
    bindings.opaque = this;
    bindings.module_base = module;
    bindings.enabled = true;
    bindings.exact_build_verified = true;
    bindings.application_main_verified = true;
    bindings.read_bytes = &Read;
    bindings.lookup_identifier = &Lookup;
    bindings.hash_name = &Hash;
    bindings.read_stamp = &Stamp;
    return bindings;
  }
  Result ReadProduction() {
    return ReadH2743StockPredicatesV1(Bindings(), expected);
  }

  Fixture() {
    AddRegion(module + 0x5700000, 0x10000);
    attacker = Allocate(0x400);
    defender = Allocate(0x400);
    attacker_cache = Allocate(0x400);
    defender_cache = Allocate(0x400);
    war = Allocate(0x400);
    raid_war = Allocate(0x400);
    struggle = Allocate(0x500);
    phase = Allocate(0x3000);
    // Covers CB table metadata plus actual lock +EB8 and mode +EF8.
    cb_owner = Allocate(0x1000);
    cb_buckets = Allocate(5 * 24);
    cb_definition = Allocate(0x80);
    Storage(0x570C130, {{attacker_id, attacker}, {defender_id, defender}});
    Storage(0x570C740, {{war_id, war}, {raid_war_id, raid_war}});
    Storage(0x570CC78, {{struggle_id, struggle}});
    Put(attacker + 0x18, attacker_id);
    Put(defender + 0x18, defender_id);
    Put(attacker + 0x1B8, attacker_cache);
    Put(defender + 0x1B8, defender_cache);
    Put(attacker + 0x1C8, std::uint64_t{0});
    Put(defender + 0x1C8, std::uint64_t{0});
    for (const auto header : {attacker_cache + 0x168,
                             attacker_cache + 0x180,
                             defender_cache + 0x168,
                             defender_cache + 0x180,
                             attacker_cache + 0x318})
      IdArray(header, {});
    Put(war + 8, war_id);
    Put(raid_war + 8, raid_war_id);
    for (const auto object : {war, raid_war}) {
      Put(object + 0x288, attacker_id);
      Put(object + 0x28C, defender_id);
      Put(object + 0x100, cb_definition);
    }
    Put(struggle + 8, struggle_id);
    Put(struggle + 0x4C0, phase);
    Put(module + 0x570BE58, cb_owner);
    Put(cb_owner + 0x198, cb_buckets);
    Put(cb_owner + 0x1A4, std::int32_t{3});
    Put(cb_owner + 0x1A8, std::uint8_t{0});
    Put(cb_owner + 0xEB8, std::uint32_t{0});
    Put(cb_owner + 0xEF8, std::uint8_t{0});
    const auto bucket = cb_buckets + (border_hash & 3U) * 24;
    Put(bucket + 4, std::uint8_t{1});
    Put(bucket + 8, border_hash);
    Put(bucket + 16, cb_definition);
    Put(cb_definition, module + 0x44197A0);
    Put(cb_definition + 0x14, border_hash);
    DefinitionName(border_name);
  }
};
} // namespace

int main() {
  {
    Fixture f;
    const H2743StockPredicateBindingsV1 defaults{};
    CHECK(!defaults.enabled && defaults.read_bytes == nullptr &&
          defaults.lookup_identifier == nullptr && defaults.hash_name == nullptr &&
          defaults.read_stamp == nullptr);
    CHECK(AllUnknown(ReadH2743StockPredicatesV1(defaults, f.expected),
                     Failure::disabled));
    auto disabled = f.Bindings();
    disabled.enabled = false;
    const auto result = ReadH2743StockPredicatesV1(disabled, f.expected);
    CHECK(AllUnknown(result, Failure::disabled));
    CHECK(!result.double_sample_stable && !result.material_complete);
    CHECK(f.reads == 0 && f.lookups == 0 && f.hashes == 0 && f.stamps == 0);
  }
  {
    Fixture f;
    const auto result = f.ReadProduction();
    CHECK(Is(result.short_truce, State::observed_native_false));
    CHECK(Is(result.long_truce, State::observed_native_false));
    CHECK(Is(result.border_raid_pair, State::observed_native_false));
    CHECK(result.stamp == f.expected && result.attacker_id == Fixture::attacker_id &&
          result.defender_id == Fixture::defender_id);
    CHECK(result.double_sample_stable && !result.material_complete);
    CHECK(f.reads > 0 && f.lookups == 4 && f.hashes == 2 && f.stamps == 3);
  }
  {
    Fixture f;
    f.Shared({Fixture::short_id});
    const auto result = f.ReadProduction();
    CHECK(Is(result.short_truce, State::observed_native_true));
    CHECK(Is(result.long_truce, State::observed_native_false));
    CHECK(Is(result.border_raid_pair, State::observed_native_false));
    CHECK(result.double_sample_stable && !result.material_complete);
  }
  {
    Fixture f;
    f.Shared({Fixture::long_id});
    f.short_available = false;
    const auto result = f.ReadProduction();
    CHECK(Is(result.short_truce, State::unavailable,
             Failure::identifier_unavailable));
    CHECK(Is(result.long_truce, State::observed_native_true));
    CHECK(Is(result.border_raid_pair, State::observed_native_false));
    CHECK(result.double_sample_stable && !result.material_complete);
  }
  {
    Fixture f;
    f.short_available = false;
    f.return_missing_as_success = true;
    const auto result = f.ReadProduction();
    CHECK(Is(result.short_truce, State::unavailable,
             Failure::identifier_unavailable));
    CHECK(Is(result.long_truce, State::observed_native_false));
    CHECK(Is(result.border_raid_pair, State::observed_native_false));
  }
  {
    Fixture f;
    f.Put(f.attacker + 0x1C8, std::uint64_t{1});
    const auto result = f.ReadProduction();
    CHECK(AllUnknown(result, Failure::cache_unavailable));
    CHECK(result.double_sample_stable && !result.material_complete);
  }
  {
    Fixture f;
    f.BorderWar();
    f.Put(f.defender + 0x1C8, std::uint64_t{1});
    const auto result = f.ReadProduction();
    CHECK(Is(result.short_truce, State::unavailable, Failure::cache_unavailable));
    CHECK(Is(result.long_truce, State::unavailable, Failure::cache_unavailable));
    CHECK(Is(result.border_raid_pair, State::observed_native_true));
  }
  {
    Fixture f;
    // Same table slot, different generation: masking is not identity.
    f.Put(f.attacker + 0x18, Fixture::attacker_id ^ 0x01000000U);
    CHECK(AllUnknown(f.ReadProduction(), Failure::stale_identity));
  }
  {
    Fixture f;
    f.BorderWar();
    f.Put(f.defender + 0x18, Fixture::defender_id ^ 0x01000000U);
    CHECK(AllUnknown(f.ReadProduction(), Failure::stale_identity));
  }
  {
    Fixture f;
    f.Shared({Fixture::short_id});
    f.Put(f.struggle + 8, Fixture::struggle_id ^ 0x01000000U);
    const auto result = f.ReadProduction();
    CHECK(Is(result.short_truce, State::unavailable, Failure::stale_identity));
    CHECK(Is(result.long_truce, State::unavailable, Failure::stale_identity));
    CHECK(Is(result.border_raid_pair, State::observed_native_false));
  }
  {
    Fixture f;
    f.BorderWar();
    const auto result = f.ReadProduction();
    CHECK(Is(result.border_raid_pair, State::observed_native_true));
    CHECK(Is(result.short_truce, State::observed_native_false));
    CHECK(Is(result.long_truce, State::observed_native_false));
    CHECK(result.double_sample_stable && !result.material_complete);
  }
  {
    Fixture f;
    f.BorderWar();
    f.Put(f.raid_war + 0x288, Fixture::defender_id);
    f.Put(f.raid_war + 0x28C, Fixture::attacker_id);
    CHECK(Is(f.ReadProduction().border_raid_pair, State::observed_native_false));
  }
  {
    Fixture f;
    f.BorderWar();
    f.Put(f.raid_war + 0x100, f.cb_definition + 0x40);
    CHECK(Is(f.ReadProduction().border_raid_pair, State::observed_native_false));
  }
  {
    Fixture f;
    f.BorderWar();
    // A bucket hash collision cannot certify a different full definition name.
    f.DefinitionName("fp2_border_raix");
    const auto result = f.ReadProduction();
    CHECK(Is(result.border_raid_pair, State::unavailable,
             Failure::definition_unavailable));
    CHECK(Is(result.short_truce, State::observed_native_false));
    CHECK(Is(result.long_truce, State::observed_native_false));
  }
  {
    Fixture f;
    f.BorderWar();
    f.Put(f.cb_definition, Fixture::module + 0x44197A8);
    CHECK(Is(f.ReadProduction().border_raid_pair, State::unavailable,
             Failure::definition_unavailable));
  }
  {
    Fixture f;
    f.Put(f.cb_owner + 0xEB8, std::uint32_t{1});
    const auto result = f.ReadProduction();
    CHECK(Is(result.border_raid_pair, State::unavailable,
             Failure::definition_unavailable));
    CHECK(Is(result.short_truce, State::observed_native_false));
    CHECK(Is(result.long_truce, State::observed_native_false));
  }
  {
    Fixture f;
    f.Put(f.cb_owner + 0xEF8, std::uint8_t{1});
    const auto result = f.ReadProduction();
    CHECK(Is(result.border_raid_pair, State::unavailable,
             Failure::definition_unavailable));
    CHECK(Is(result.short_truce, State::observed_native_false));
    CHECK(Is(result.long_truce, State::observed_native_false));
  }
  {
    Fixture f;
    f.change_stamp_at = 2;
    const auto result = f.ReadProduction();
    CHECK(AllUnknown(result, Failure::unstable_sample));
    CHECK(!result.double_sample_stable && !result.material_complete);
  }
  {
    Fixture f;
    f.Shared({Fixture::short_id});
    f.change_raw_at = 2;
    // Alternate bytes contain the same full ID; booleans stay the same.
    // Different source address/headers must still invalidate the double sample.
    const auto result = f.ReadProduction();
    CHECK(AllUnknown(result, Failure::unstable_sample));
    CHECK(!result.double_sample_stable && !result.material_complete);
    CHECK(f.stamps == 3);
  }
  std::printf("h2743 stock predicate fixture: %d checks, %d failures\n",
              checks, failures);
  return failures == 0 ? 0 : 1;
}
