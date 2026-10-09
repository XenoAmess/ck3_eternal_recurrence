#include "xar_bridge/ck3_12004_guardian_factory_lookup.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string_view>
#include <vector>

namespace {

using Environment = xar::ck3_12004::GuardianFactoryReadEnvironment12004V1;
using Metadata = xar::ck3_12004::ExistingGuardianFactoryMetadata12004V1;
using Status = xar::ck3_12004::ExistingGuardianFactoryStatusV1;
using Failure = xar::ck3_12004::GuardianFactoryLookupFailureV1;
using Result = std::array<Metadata, 2>;

constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uintptr_t kPool = 0x210000000ULL;
constexpr std::uintptr_t kRegistry = 0x210001000ULL;
constexpr std::uintptr_t kNames = 0x210002000ULL;
constexpr std::uintptr_t kFactories = 0x210003000ULL;
constexpr std::uintptr_t kGuardianKey = 0x210004000ULL;
constexpr std::uintptr_t kWardKey = 0x210005000ULL;
constexpr std::uintptr_t kCollisionKey = 0x210006000ULL;
constexpr std::uintptr_t kGuardianRecord = 0x210007000ULL;
constexpr std::uintptr_t kWardRecord = 0x210008000ULL;
// Synthetic metadata values only; no actual guardian vtable or descriptor has
// been captured. Sharing this value does not imply sharing a relation kind.
constexpr std::uintptr_t kSharedVtable = kModule + 0x10000;
constexpr std::uintptr_t kGuardianDescriptor = kModule + 0x20000;
constexpr std::uintptr_t kWardDescriptor = kModule + 0x20020;

constexpr std::uint32_t kGuardianId = 41;
constexpr std::uint32_t kWardId = 73;
constexpr std::string_view kGuardian = "has_relation_guardian";
constexpr std::string_view kWard = "has_relation_ward";
constexpr std::string_view kStoredGuardian = "HaS_ReLaTiOn_GuArDiAn";
constexpr std::string_view kStoredWard = "HAS_RELATION_WARD";
constexpr std::string_view kCollision = "has_relation_guardiav";

// Independently supplied actual-algorithm results. The fixture never calls
// the reader's hash helpers to construct its expected table positions.
constexpr std::uint32_t kGuardianNameHash = 0xB158555E;
constexpr std::uint32_t kWardNameHash = 0x48FA066B;
constexpr std::uint32_t kCollisionNameHash = 0xB95861F6;
constexpr std::uint32_t kGuardianIdHash = 0x825390AC;
constexpr std::uint32_t kWardIdHash = 0x71BBEA4C;
constexpr std::int32_t kMask = 7;
constexpr std::uintptr_t kGuardianNameSlot = kNames + 7 * 48;
constexpr std::uintptr_t kWardNameSlot = kNames + 3 * 48;
constexpr std::uintptr_t kGuardianFactorySlot = kFactories + 4 * 24;
constexpr std::uintptr_t kWardFactorySlot = kFactories + 5 * 24;

class SparseMemory {
 public:
  void Add(std::uintptr_t address, std::size_t size) {
    regions_.push_back({address, std::vector<std::uint8_t>(size)});
  }

  void Remove(std::uintptr_t address) {
    regions_.erase(
        std::remove_if(regions_.begin(), regions_.end(),
                       [address](const Region &region) {
                         return region.address == address;
                       }),
        regions_.end());
  }

  template <class Value>
  void Put(std::uintptr_t address, const Value &value) {
    PutBytes(address, &value, sizeof(value));
  }

  void PutBytes(std::uintptr_t address, const void *bytes, std::size_t size) {
    for (auto &region : regions_) {
      if (Contains(region, address, size)) {
        std::memcpy(region.bytes.data() + (address - region.address), bytes,
                    size);
        return;
      }
    }
    std::fputs("fixture storage address missing\n", stderr);
    std::abort();
  }

  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    const auto &memory = *static_cast<const SparseMemory *>(context);
    for (const auto &region : memory.regions_) {
      if (Contains(region, address, size)) {
        std::memcpy(output,
                    region.bytes.data() + (address - region.address), size);
        return true;
      }
    }
    return false;
  }

 private:
  struct Region {
    std::uintptr_t address;
    std::vector<std::uint8_t> bytes;
  };

  static bool Contains(const Region &region, std::uintptr_t address,
                       std::size_t size) noexcept {
    if (address < region.address) return false;
    const auto offset = address - region.address;
    return offset <= region.bytes.size() &&
           size <= region.bytes.size() - offset;
  }

  std::vector<Region> regions_;
};

struct Fixture {
  SparseMemory memory;

  Fixture() {
    using namespace xar::ck3_12004;
    memory.Add(kModule + kGuardianNamePoolSlotRvaV1, 8);
    memory.Add(kModule + kGuardianTriggerRegistrySlotRvaV1, 8);
    memory.Add(kModule + kGuardianNameComparisonModeRvaV1, 4);
    memory.Put(kModule + kGuardianNamePoolSlotRvaV1, kPool);
    memory.Put(kModule + kGuardianTriggerRegistrySlotRvaV1, kRegistry);
    memory.Put(kModule + kGuardianNameComparisonModeRvaV1, std::int32_t{0});

    memory.Add(kPool, 0x40);
    memory.Add(kRegistry, 0x80);
    memory.Add(kNames, 11 * 48);
    memory.Add(kFactories, 11 * 24);
    memory.Put(kPool + 0x08 + 0x08, kNames);
    memory.Put(kPool + 0x08 + 0x14, kMask);
    memory.Put(kPool + 0x08 + 0x18, std::uint8_t{2});
    memory.Put(kRegistry + 0x48 + 0x08, kFactories);
    memory.Put(kRegistry + 0x48 + 0x14, kMask);

    // Both fixed names exceed the native 15-byte inline capacity.
    PutKey(kGuardianKey, kStoredGuardian);
    PutKey(kWardKey, kStoredWard);
    PutKey(kCollisionKey, kCollision);

    // Guardian hashes to bucket 6. The occupied equal-length key at bucket
    // 6 forces a failed byte comparison before the distance-2 hit at 7.
    // Changing the final 'n' to 'v' preserves the low three hash bits.
    PutName(kNames + 6 * 48, kCollisionNameHash, 1, kCollisionKey,
            kCollision.size(), 99);
    PutName(kGuardianNameSlot, kGuardianNameHash, 2, kGuardianKey,
            kStoredGuardian.size(), kGuardianId);
    PutName(kWardNameSlot, kWardNameHash, 1, kWardKey, kStoredWard.size(),
            kWardId);
    memory.Put(kNames + (kMask + 2 + 1) * 48 + 0x04, std::uint8_t{0xFF});

    // IDs 41 and 73 independently hash to bucket 4, exercising the next
    // 24-byte factory slot with distance 2.
    PutFactory(kGuardianFactorySlot, kGuardianIdHash, 1, kGuardianId,
               kGuardianRecord);
    PutFactory(kWardFactorySlot, kWardIdHash, 2, kWardId, kWardRecord);
    PutRecord(kGuardianRecord, kGuardianDescriptor, kGuardianId);
    PutRecord(kWardRecord, kWardDescriptor, kWardId);
  }

  Environment Bind(std::string_view sha = xar::ck3_12004::kExecutableSha256) {
    return xar::ck3_12004::BindGuardianFactoryReadEnvironment12004V1(
        kModule, sha, &memory, &SparseMemory::Read);
  }

  Result Read() {
    return xar::ck3_12004::ReadExistingGuardianTriggerFactories12004V1(Bind());
  }

 private:
  void PutKey(std::uintptr_t address, std::string_view key) {
    memory.Add(address, 32);
    memory.PutBytes(address, key.data(), key.size());
  }

  void PutName(std::uintptr_t slot, std::uint32_t hash, std::uint8_t distance,
               std::uintptr_t key, std::size_t length, std::uint32_t id) {
    memory.Put(slot, hash);
    memory.Put(slot + 0x04, distance);
    memory.Put(slot + 0x08, key);
    memory.Put(slot + 0x18, static_cast<std::int32_t>(length));
    memory.Put(slot + 0x20, std::uint64_t{31});
    memory.Put(slot + 0x28, id);
  }

  void PutFactory(std::uintptr_t slot, std::uint32_t hash,
                  std::uint8_t distance, std::uint32_t id,
                  std::uintptr_t record) {
    memory.Put(slot, hash);
    memory.Put(slot + 0x04, distance);
    memory.Put(slot + 0x08, id);
    memory.Put(slot + 0x10, record);
  }

  void PutRecord(std::uintptr_t address, std::uintptr_t descriptor,
                 std::uint32_t id) {
    memory.Add(address, 24);
    memory.Put(address, kSharedVtable);
    memory.Put(address + 0x08, descriptor);
    memory.Put(address + 0x10, id);
  }
};

bool Check(bool condition, const char *label) {
  if (!condition) std::fprintf(stderr, "SOURCE_FIXTURE_FAIL: %s\n", label);
  return condition;
}

bool Found(const Metadata &row, std::string_view key,
           std::string_view stored_key, std::uint32_t id,
           std::uintptr_t record, std::uintptr_t descriptor) {
  return row.key == key && row.status == Status::found &&
         row.failure == Failure::none && row.name_id == id &&
         row.map_name_id == id && row.record_name_id == id &&
         row.factory_address == record && row.vtable_address == kSharedVtable &&
         row.descriptor_address == descriptor &&
         row.matched_stored_key_size == stored_key.size() &&
         std::memcmp(row.matched_stored_key.data(), stored_key.data(),
                     stored_key.size()) == 0;
}

bool BothUnavailable(const Result &result, Failure failure) {
  return result[0].key == kGuardian && result[1].key == kWard &&
         result[0].status == Status::unavailable &&
         result[1].status == Status::unavailable &&
         result[0].failure == failure && result[1].failure == failure;
}

bool RunChecks() {
  {
    Fixture fixture;
    const auto rows = fixture.Read();
    if (!Check(Found(rows[0], kGuardian, kStoredGuardian, kGuardianId,
                     kGuardianRecord, kGuardianDescriptor) &&
                   Found(rows[1], kWard, kStoredWard, kWardId, kWardRecord,
                         kWardDescriptor),
               "ordered heap-key ASCII hits and both collision paths"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Put(kGuardianNameSlot + 0x04, std::uint8_t{1});
    const auto rows = fixture.Read();
    if (!Check(rows[0].status == Status::name_missing &&
                   rows[0].failure == Failure::none && !rows[0].name_id &&
                   rows[0].factory_address == 0 &&
                   Found(rows[1], kWard, kStoredWard, kWardId, kWardRecord,
                         kWardDescriptor),
               "name miss stops at probe greater than stored distance"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Put(kWardFactorySlot + 0x04, std::uint8_t{1});
    const auto rows = fixture.Read();
    if (!Check(rows[1].status == Status::factory_missing &&
                   rows[1].failure == Failure::none &&
                   rows[1].name_id == kWardId && !rows[1].map_name_id &&
                   !rows[1].record_name_id && rows[1].factory_address == 0 &&
                   Found(rows[0], kGuardian, kStoredGuardian, kGuardianId,
                         kGuardianRecord, kGuardianDescriptor),
               "factory miss retains name hit independently"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Remove(kWardRecord);
    const auto rows = fixture.Read();
    if (!Check(rows[1].status == Status::unavailable &&
                   rows[1].failure == Failure::factory_record_unreadable &&
                   rows[1].name_id == kWardId &&
                   rows[1].map_name_id == kWardId &&
                   Found(rows[0], kGuardian, kStoredGuardian, kGuardianId,
                         kGuardianRecord, kGuardianDescriptor),
               "unreadable factory record differs from factory missing"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Remove(kFactories);
    if (!Check(BothUnavailable(fixture.Read(), Failure::factory_map_unreadable),
               "unreadable factory table"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Remove(kNames);
    if (!Check(BothUnavailable(fixture.Read(), Failure::name_map_unreadable),
               "unreadable name table"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Remove(kGuardianKey);
    const auto rows = fixture.Read();
    if (!Check(rows[0].status == Status::unavailable &&
                   rows[0].failure == Failure::name_key_unreadable &&
                   Found(rows[1], kWard, kStoredWard, kWardId, kWardRecord,
                         kWardDescriptor),
               "unreadable heap key leaves the other name available"))
      return false;
  }
  {
    Fixture fixture;
    constexpr std::uint32_t raw_record_id = 0xAABBCCDD;
    fixture.memory.Put(kWardRecord + 0x10, raw_record_id);
    const auto rows = fixture.Read();
    if (!Check(rows[1].status == Status::found &&
                   rows[1].failure == Failure::none &&
                   rows[1].name_id == kWardId &&
                   rows[1].map_name_id == kWardId &&
                   rows[1].record_name_id == raw_record_id &&
                   rows[1].vtable_address == kSharedVtable &&
                   rows[1].descriptor_address == kWardDescriptor,
               "raw record ID and opaque descriptor are retained"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Put(
        kModule + xar::ck3_12004::kGuardianNameComparisonModeRvaV1,
        std::int32_t{1});
    if (!Check(BothUnavailable(fixture.Read(),
                               Failure::comparison_branch_unavailable),
               "nondefault comparison branch remains unavailable"))
      return false;
  }
  {
    Fixture fixture;
    const auto environment = fixture.Bind("fixture-unqualified-build");
    if (!Check(BothUnavailable(
                   xar::ck3_12004::ReadExistingGuardianTriggerFactories12004V1(
                       environment),
                   Failure::environment_unavailable),
               "environment binding checks the qualified build value"))
      return false;
  }
  return true;
}

} // namespace

int main() {
  if (!RunChecks()) return 1;
  std::puts("SOURCE_FIXTURE_PASS");
  return 0;
}
