#include "xar_bridge/guardian_factory_discovery_job_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace {

using Environment = xar::ck3_12004::GuardianFactoryReadEnvironment12004V1;
using TypedMetadata = xar::ck3_12004::GuardianFactoryTypedMetadata12004V1;
using Status = xar::ck3_12004::ExistingGuardianFactoryStatusV1;
using Failure = xar::ck3_12004::GuardianFactoryLookupFailureV1;

constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uintptr_t kImageSize = 0x6000000;
constexpr std::uintptr_t kPool = 0x210000000ULL;
constexpr std::uintptr_t kRegistry = 0x210001000ULL;
constexpr std::uintptr_t kNames = 0x210002000ULL;
constexpr std::uintptr_t kFactories = 0x210003000ULL;
constexpr std::uintptr_t kGuardianKey = 0x210004000ULL;
constexpr std::uintptr_t kWardKey = 0x210005000ULL;
constexpr std::uintptr_t kCollisionKey = 0x210006000ULL;
constexpr std::uintptr_t kGuardianRecord = 0x210007000ULL;
constexpr std::uintptr_t kWardRecord = 0x210008000ULL;

// Every vtable, slot, descriptor, COL and type name below is synthetic fixture
// metadata. No value supplies an actual guardian factory or evaluator ABI.
constexpr std::uintptr_t kVtable = kModule + 0x10000;
constexpr std::array<std::uintptr_t, 4> kVirtualSlots{
    kModule + 0x11000, kModule + 0x11020,
    kModule + 0x11040, kModule + 0x11060};
constexpr std::uintptr_t kGuardianDescriptor = kModule + 0x20000;
constexpr std::uintptr_t kWardDescriptor = kModule + 0x20020;
constexpr std::uintptr_t kCol = kModule + 0x30000;
constexpr std::uintptr_t kTypeDescriptor = kModule + 0x40000;
constexpr std::array<std::uint32_t, 6> kColFields{
    1, 0, 0, 0x40000, 0x45000, 0x30000};
constexpr std::string_view kTypeName = ".?AVFixtureGuardianFactory@@";

constexpr std::uint32_t kGuardianId = 41;
constexpr std::uint32_t kWardId = 73;
constexpr std::string_view kGuardian = "has_relation_guardian";
constexpr std::string_view kWard = "has_relation_ward";
constexpr std::string_view kStoredGuardian = "HaS_ReLaTiOn_GuArDiAn";
constexpr std::string_view kStoredWard = "HAS_RELATION_WARD";
constexpr std::string_view kCollision = "has_relation_guardiav";
constexpr std::uintptr_t kGuardianNameSlot = kNames + 7 * 48;
constexpr std::uintptr_t kWardNameSlot = kNames + 3 * 48;
constexpr std::uintptr_t kGuardianFactorySlot = kFactories + 4 * 24;
constexpr std::uintptr_t kWardFactorySlot = kFactories + 5 * 24;

class SparseMemory {
 public:
  std::size_t total_reads{};
  std::uintptr_t change_address{};
  std::uint32_t change_value{};
  std::size_t change_read{};
  std::size_t change_seen{};
  std::array<std::size_t, 2> dword_reads{};
  std::array<std::size_t, 2> qword_reads{};
  std::array<bool, 2> fail_dword{};
  std::array<bool, 2> fail_qword{};
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
    auto &memory = *static_cast<SparseMemory *>(context);
    ++memory.total_reads;
    if (address == memory.change_address && size == sizeof(std::uint32_t) &&
        ++memory.change_seen == memory.change_read)
      memory.Put(address, memory.change_value);
    constexpr std::array<std::uintptr_t, 2> records{kGuardianRecord, kWardRecord};
    for (std::size_t index = 0; index < records.size(); ++index) {
      if (address == records[index] + 0x10 && size == sizeof(std::uint32_t)) {
        ++memory.dword_reads[index];
        if (memory.fail_dword[index]) return false;
      }
      if (address == records[index] + 0x18 && size == sizeof(std::uint64_t)) {
        ++memory.qword_reads[index];
        if (memory.fail_qword[index]) {
          const std::uint64_t partial = 0xAAAAAAAAAAAAAAAAULL;
          std::memcpy(output, &partial, sizeof(partial));
          return false;
        }
      }
    }
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
    memory.Put(kPool + 0x10, kNames);
    memory.Put(kPool + 0x1C, std::int32_t{7});
    memory.Put(kPool + 0x20, std::uint8_t{2});
    memory.Put(kRegistry + 0x50, kFactories);
    memory.Put(kRegistry + 0x5C, std::int32_t{7});
    PutKey(kGuardianKey, kStoredGuardian);
    PutKey(kWardKey, kStoredWard);
    PutKey(kCollisionKey, kCollision);

    // Reuse the qualified sparse table layout, without replaying its ten
    // original lookup-only groups. Hash constants are independently supplied.
    PutName(kNames + 6 * 48, 0xB95861F6, 1, kCollisionKey,
            kCollision.size(), 99);
    PutName(kGuardianNameSlot, 0xB158555E, 2, kGuardianKey,
            kStoredGuardian.size(), kGuardianId);
    PutName(kWardNameSlot, 0x48FA066B, 1, kWardKey, kStoredWard.size(), kWardId);
    memory.Put(kNames + 10 * 48 + 0x04, std::uint8_t{0xFF});
    PutFactory(kGuardianFactorySlot, 0x825390AC, 1, kGuardianId,
               kGuardianRecord);
    PutFactory(kWardFactorySlot, 0x71BBEA4C, 2, kWardId, kWardRecord);
    PutRecord(kGuardianRecord, kGuardianDescriptor, kGuardianId);
    PutRecord(kWardRecord, kWardDescriptor, kWardId);

    // Separate blocks allow one virtual slot to be unreadable independently.
    memory.Add(kVtable - 8, 8);
    memory.Put(kVtable - 8, kCol);
    for (std::size_t index = 0; index < kVirtualSlots.size(); ++index) {
      memory.Add(kVtable + index * 8, 8);
      memory.Put(kVtable + index * 8, kVirtualSlots[index]);
    }
    memory.Add(kCol, sizeof(kColFields));
    memory.Put(kCol, kColFields);
    memory.Add(kTypeDescriptor, 16 + 192);
    memory.PutBytes(kTypeDescriptor + 16, kTypeName.data(), kTypeName.size());
  }

  Environment Bind() {
    return xar::ck3_12004::BindGuardianFactoryReadEnvironment12004V1(
        kModule, xar::ck3_12004::kExecutableSha256, &memory, &SparseMemory::Read);
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
    memory.Put(address, kVtable);
    memory.Put(address + 0x08, descriptor);
    memory.Put(address + 0x10, id);
    memory.Add(address + 0x18, sizeof(std::uint64_t));
    memory.Put(address + 0x18, address == kGuardianRecord
        ? std::uint64_t{0xFEDCBA9876543210ULL} : std::uint64_t{0});
  }
};

bool Check(bool condition, const char *label) {
  if (!condition) std::fprintf(stderr, "NEW_CURRENT_RELATION_FAIL: %s\n", label);
  return condition;
}

using Job = xar::bridge::GuardianFactoryDiscoveryJobV1;

xar::game::Snapshot PausedSnapshot() {
  xar::game::Snapshot snapshot{};
  snapshot.date_raw = 53220000;
  snapshot.paused = true;
  snapshot.map_ready = true;
  snapshot.has_played_character = true;
  snapshot.played_character_id = 0x03000001;
  snapshot.played_character_alive = true;
  return snapshot;
}

struct SnapshotSequence {
  xar::game::Snapshot before{PausedSnapshot()};
  xar::game::Snapshot after{before};
  std::size_t reads{};
  static bool Read(void *context, xar::game::Snapshot &output) noexcept {
    auto &sequence = *static_cast<SnapshotSequence *>(context);
    try {
      output = sequence.reads == 0 ? sequence.before : sequence.after;
      ++sequence.reads;
      return true;
    } catch (...) { return false; }
  }
};

Job MakeJob(Fixture &fixture, SnapshotSequence &snapshots, std::string_view request) {
  Job job{};
  job.expected_snapshot = snapshots.before;
  job.environment = fixture.Bind();
  job.image_size = kImageSize;
  job.executable_sha256 = xar::ck3_12004::kExecutableSha256;
  job.native_revision = 7;
  job.heir_character_id = 0x03000002;
  job.request_id = request;
  job.snapshot_context = &snapshots;
  job.read_snapshot = &SnapshotSequence::Read;
  return job;
}

bool Execute(Job &job) {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.paused = true;
  stamp.date_raw = job.expected_snapshot.date_raw;
  stamp.pump_epoch = 19;
  stamp.thread_id = 23;
  return xar::bridge::ExecuteGuardianFactoryDiscoveryJobV1(&job, stamp);
}

bool Contains(std::string_view text, std::string_view token) {
  return text.find(token) != std::string_view::npos;
}

std::size_t Count(std::string_view text, std::string_view token) {
  std::size_t count{}, offset{};
  while ((offset = text.find(token, offset)) != std::string_view::npos) {
    ++count;
    offset += token.size();
  }
  return count;
}

bool Complete(const Job &job, const xar::game::Snapshot &snapshot,
              const std::filesystem::path &path, std::string &wire) {
  std::string error;
  if (!xar::bridge::CompleteGuardianFactoryDiscoveryJobV1(job, snapshot, path, error)
      || !error.empty()) return false;
  std::ifstream input(path, std::ios::binary);
  if (!input) return false;
  wire.assign(std::istreambuf_iterator<char>{input}, std::istreambuf_iterator<char>{});
  return !wire.empty();
}


// Nine new same-job branches. This source is AUTHOR_NOT_RUN until a fresh
// execution admission names this exact source and its qualified providers.
constexpr std::uintptr_t kStorage = 0x220000000ULL;
constexpr std::uintptr_t kCharacterSlots = 0x220001000ULL;
constexpr std::uintptr_t kRootCharacter = 0x220002000ULL;
constexpr std::uintptr_t kTargetCharacter = 0x220003000ULL;
constexpr std::uintptr_t kPeerExtension = 0x220004000ULL;
constexpr std::uintptr_t kPeerMap = 0x220005000ULL;
constexpr std::uintptr_t kPeerValue = 0x220006000ULL;
constexpr std::uintptr_t kRelationEntries = 0x220007000ULL;
constexpr std::uintptr_t kRelationStoredGuardian = 0x220008000ULL;
constexpr std::uintptr_t kStoredOther = 0x220009000ULL;
constexpr std::uintptr_t kWantedWard = 0x22000A000ULL;
constexpr std::uintptr_t kTaggedRows = 0x22000B000ULL;
constexpr std::uintptr_t kFallback = 0x22000C000ULL;

struct RelationFixture {
  Fixture lookup;
  SnapshotSequence snapshots;
  std::uint32_t root_id{0x03000001U};
  std::uint32_t target_id{0x03000002U};

  RelationFixture() {
    auto &m = lookup.memory;
    m.Add(kModule + xar::ck3_12004::kCharacterStorageSlotRva, 8);
    m.Put(kModule + xar::ck3_12004::kCharacterStorageSlotRva, kStorage);
    m.Add(kStorage, 0x30);
    m.Put(kStorage + 0x20, kCharacterSlots);
    m.Put(kStorage + 0x2C, std::int32_t{3});
    m.Add(kCharacterSlots, 3 * 16);
    m.Put(kCharacterSlots + 16 + 8, kRootCharacter);
    m.Put(kCharacterSlots + 32 + 8, kTargetCharacter);
    m.Add(kRootCharacter, 0x200);
    m.Add(kTargetCharacter, 0x200);
    m.Put(kRootCharacter + 0x18, root_id);
    m.Put(kTargetCharacter + 0x18, target_id);
    m.Put(kTargetCharacter + 0x1C, std::uint32_t{0x43686172U});
    m.Put(kRootCharacter + 0x1B0, kPeerExtension);
    m.Add(kPeerExtension, 0x20);
    m.Put(kPeerExtension + 8, kPeerMap);
    m.Put(kPeerExtension + 0x14, std::int32_t{1});
    m.Add(kPeerMap, 16);
    m.Put(kPeerMap, target_id);
    m.Put(kPeerMap + 8, kPeerValue);
    m.Add(kPeerValue, 0x30);
    m.Put(kPeerValue + 0x20, kRelationEntries);
    m.Put(kPeerValue + 0x2C, std::int32_t{2});
    m.Add(kRelationEntries, 2 * 40);
    m.Put(kRelationEntries, kRelationStoredGuardian);
    m.Put(kRelationEntries + 40, kStoredOther);
    m.Add(kRelationStoredGuardian, 0x230);
    m.Add(kStoredOther, 0x230);
    m.Put(kStoredOther + 0x220, kTaggedRows);
    m.Put(kStoredOther + 0x22C, std::int32_t{1});
    m.Add(kTaggedRows, 16);
    m.Put(kTaggedRows, kWantedWard);
    m.Put(kTaggedRows + 0x0C, std::uint8_t{2});
    m.Add(kModule + 0x5D1EBF8, 8);
    m.Put(kModule + 0x5D1EBF8, kFallback);
    m.Put(kGuardianRecord + 0x18, kRelationStoredGuardian);
    m.Put(kWardRecord + 0x18, kWantedWard);
    // +10 is independent of the lookup's name/map ID; retain the source
    // fact rather than silently demanding equality that the source lacks.
    m.Put(kGuardianRecord + 0x10, std::uint32_t{9041});
    m.Put(kWardRecord + 0x10, std::uint32_t{9073});
  }

  void CurrentIds(std::uint32_t root, std::uint32_t target) {
    root_id = root;
    target_id = target;
    lookup.memory.Put(kRootCharacter + 0x18, root);
    lookup.memory.Put(kTargetCharacter + 0x18, target);
    lookup.memory.Put(kPeerMap, target);
    snapshots.before.played_character_id = std::bit_cast<std::int32_t>(root);
    snapshots.after = snapshots.before;
  }
};

bool NewCases(const std::filesystem::path &directory) {
  constexpr std::array<std::string_view, 9> requests{
    "family-relation-fixture-current-relation-full",
    "family-relation-fixture-current-relation-empty",
    "family-relation-fixture-current-relation-current-ids",
    "family-relation-fixture-current-relation-generation-mismatch",
    "family-relation-fixture-current-relation-bookend-changed",
    "family-relation-fixture-current-relation-fallback",
    "family-relation-fixture-current-relation-negative-count",
    "family-relation-fixture-current-relation-after-changed",
    "family-relation-fixture-current-relation-completion-changed"};
  for (std::size_t scene = 0; scene < requests.size(); ++scene) {
    RelationFixture fixture;
    auto &m = fixture.lookup.memory;
    if (scene == 1) {
      m.Put(kPeerValue + 0x20, std::uintptr_t{0});
      m.Put(kPeerValue + 0x2C, std::int32_t{0});
      m.fail_qword[1] = true;
    }
    if (scene == 2) fixture.CurrentIds(0x04000001U, 0x05000002U);
    if (scene == 3) m.Put(kRootCharacter + 0x18, std::uint32_t{0x04000001U});
    if (scene == 4) {
      m.change_address = kRootCharacter + 0x18;
      m.change_value = 0x04000001U;
      m.change_read = 2;
    }
    if (scene == 5) {
      m.Put(kWardRecord + 0x18, std::uint64_t{0});
      m.Put(kModule + 0x5D1EBF8, std::uint64_t{0});
      m.Put(kTaggedRows + 0x0C, std::uint8_t{0});
    }
    if (scene == 6) m.Put(kPeerExtension + 0x14, std::int32_t{-1});
    if (scene == 7) ++fixture.snapshots.after.date_raw;
    auto job = MakeJob(fixture.lookup, fixture.snapshots, requests[scene]);
    job.heir_character_id = std::bit_cast<std::int32_t>(fixture.target_id);
    if (!Check(Execute(job) && fixture.snapshots.reads == 2,
               "new relation stays inside the same two-bookend executor")) return false;
    if (scene != 7) {
      if (!Check(job.frame_observed && job.current_family_relation.has_value(),
                 "stable enclosing query owns the new directed value")) return false;
      const auto &value = *job.current_family_relation;
      const bool ready = scene == 0 || scene == 1 || scene == 2 || scene == 5 || scene == 8;
      if (!Check(value.ready == ready, "ready includes observed false and excludes failed reached inputs")) return false;
      if (ready) {
        const bool expected = scene != 1;
        if (!Check(value.root_character_id == fixture.root_id &&
                   value.target_character_id == fixture.target_id &&
                   value.root_address == kRootCharacter && value.target_address == kTargetCharacter &&
                   value.identity_round_trip && value.sample_stable &&
                   value.rows[0].raw_value.has_value() && *value.rows[0].raw_value == expected &&
                   value.rows[1].raw_value.has_value() && *value.rows[1].raw_value == expected,
                   "current complete IDs/pointers and both keyed bools are owning facts")) return false;
      } else if (!Check(!value.rows[0].available && !value.rows[1].available &&
                        !value.rows[0].raw_value && !value.rows[1].raw_value,
                        "unknown domain/bookend cannot become false")) return false;
      if (scene == 1 && !Check(!value.rows[0].descriptor_reached &&
                              !value.rows[1].descriptor_reached &&
                              !value.rows[1].descriptor_raw,
                              "empty source branch needs no failed raw18 input")) return false;
      if (scene == 5 && !Check(value.rows[1].descriptor_raw == std::uint64_t{0} &&
                              value.rows[1].basis == "fallback_raw_equal",
                              "zero raw input and fallback tag branch are preserved")) return false;
      if (scene == 6 && !Check(value.rows[0].peer_count_raw == std::int32_t{-1},
                              "negative source count remains observed but unavailable")) return false;
    }
    auto completion = job.expected_snapshot;
    if (scene == 8) ++completion.date_raw;
    std::string wire;
    if (!Check(Complete(job, completion, directory/(std::string(requests[scene])+".json"), wire) &&
               Count(wire, "\"current_family_relation_v1\":{") == 1,
               "same production completion serializer emits the single private child")) return false;
    const bool wire_ready = scene == 0 || scene == 1 || scene == 2 || scene == 5;
    if (!Check(Contains(wire, wire_ready ? "\"ready\":true" : "\"ready\":false") &&
               Contains(wire, "\"native_trigger_invoked\":false") &&
               Contains(wire, "\"guardian_membership_observed\":false"),
               "lower relation readiness does not invent natural template credit")) return false;
    if (scene >= 7 && !Check(Contains(wire, "\"qualified\":false") &&
                            Contains(wire, "\"root_address\":null") &&
                            Contains(wire, "\"target_address\":null"),
                            "either enclosing frame boundary suppresses observed pointers/results")) return false;
  }
  std::puts("native_current_family_relation_new_cases=9 PASS; old_cases=0; native_getter_invocations=0; game_values=0");
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    return NewCases(directory) ? 0 : 1;
  } catch (const std::exception &exception) {
    std::fprintf(stderr, "new current relation fixture exception: %s\n", exception.what());
    return 3;
  }
}
