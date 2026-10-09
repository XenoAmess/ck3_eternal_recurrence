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
  }
};

bool Check(bool condition, const char *label) {
  if (!condition)
    std::fprintf(stderr, "SOURCE_FIXTURE_FAIL: %s\n", label);
  return condition;
}

bool FoundLookup(const TypedMetadata &row, std::string_view key,
                 std::uint32_t id, std::uintptr_t record,
                 std::uintptr_t descriptor) {
  return row.lookup.key == key && row.lookup.status == Status::found &&
         row.lookup.failure == Failure::none && row.lookup.name_id == id &&
         row.lookup.map_name_id == id && row.lookup.record_name_id == id &&
         row.lookup.factory_address == record &&
         row.lookup.vtable_address == kVtable &&
         row.lookup.descriptor_address == descriptor;
}

bool FullTypedMetadata(const TypedMetadata &row) {
  for (std::size_t index = 0; index < kVirtualSlots.size(); ++index) {
    if (!row.virtual_slots[index].available ||
        row.virtual_slots[index].address != kVirtualSlots[index] ||
        row.virtual_slots[index].rva != kVirtualSlots[index] - kModule)
      return false;
  }
  return row.rtti.col_pointer_available && row.rtti.col_address == kCol &&
         row.rtti.col_fields_available && row.rtti.col_fields == kColFields &&
         row.rtti.type_descriptor_address == kTypeDescriptor &&
         row.rtti.type_name_available && row.rtti.type_name == kTypeName &&
         !row.rtti.type_name_truncated && row.rtti.unavailable_reason.empty();
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
    } catch (...) {
      return false;
    }
  }
};

Job MakeJob(Fixture &fixture, SnapshotSequence &snapshots,
            std::string_view request_id) {
  Job job{};
  job.expected_snapshot = snapshots.before;
  job.environment = fixture.Bind();
  job.image_size = kImageSize;
  job.executable_sha256 = xar::ck3_12004::kExecutableSha256;
  job.native_revision = 7;
  job.heir_character_id = 0x03000002;
  job.request_id = request_id;
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

bool Captured(const Job &job, const SnapshotSequence &snapshots) {
  return job.executed && job.frame_observed && job.metadata.has_value() &&
         job.unavailable_reason.empty() && snapshots.reads == 2 &&
         job.metadata->module_base == kModule &&
         job.metadata->image_size == kImageSize;
}

bool Contains(std::string_view text, std::string_view token) {
  return text.find(token) != std::string_view::npos;
}

std::size_t Count(std::string_view text, std::string_view token) {
  std::size_t count{};
  std::size_t offset{};
  while ((offset = text.find(token, offset)) != std::string_view::npos) {
    ++count;
    offset += token.size();
  }
  return count;
}

bool CompleteAndRead(const Job &job, const std::filesystem::path &path,
                     std::string &json) {
  std::string error;
  if (!xar::bridge::CompleteGuardianFactoryDiscoveryJobV1(
          job, job.expected_snapshot, path, error) || !error.empty())
    return false;
  std::ifstream input(path, std::ios::binary);
  if (!input) return false;
  json.assign(std::istreambuf_iterator<char>{input},
              std::istreambuf_iterator<char>{});
  return !json.empty();
}

bool CommonSidecar(const std::string &json, const Job &job, bool qualified) {
  const auto guardian = json.find("\"key\":\"has_relation_guardian\"");
  const auto ward = json.find("\"key\":\"has_relation_ward\"");
  return Contains(json,
                  "\"schema\":\"xar.ck3.guardian-factory-discovery.v1\"") &&
         Contains(json, "\"read_only\":true") &&
         Contains(json, "\"advertised\":false") &&
         Contains(json, "\"source_discovery_only\":true") &&
         Contains(json, "\"guardian_membership_observed\":false") &&
         Contains(json, qualified ? "\"qualified\":true"
                                  : "\"qualified\":false") &&
         Contains(json, "\"request_id\":\"" + job.request_id + "\"") &&
         Contains(json, "\"native_revision\":7") &&
         Contains(json, "\"heir_character_id\":" +
                            std::to_string(job.heir_character_id)) &&
         Contains(json, "\"date_raw\":" +
                            std::to_string(job.expected_snapshot.date_raw)) &&
         Contains(json, "\"played_character_id\":" +
                            std::to_string(
                                job.expected_snapshot.played_character_id)) &&
         Contains(json, "\"paused\":true") &&
         Contains(json, "\"pump_epoch\":19") &&
         Contains(json, "\"thread_id\":23") &&
         Count(json, "\"key\":") == 2 &&
         guardian != std::string::npos && ward != std::string::npos &&
         guardian < ward && Count(json, "\"slot_index\":") == 8;
}

bool RunChecks(const std::filesystem::path &directory) {
  {
    Fixture fixture;
    SnapshotSequence snapshots;
    auto job = MakeJob(fixture, snapshots, "fixture-discovery-found");
    if (!Check(Execute(job) && Captured(job, snapshots),
               "found job uses the shared executor in one paused frame"))
      return false;
    const auto &rows = job.metadata->factories;
    if (!Check(FoundLookup(rows[0], kGuardian, kGuardianId, kGuardianRecord,
                           kGuardianDescriptor) &&
                   FoundLookup(rows[1], kWard, kWardId, kWardRecord,
                               kWardDescriptor) &&
                   FullTypedMetadata(rows[0]) && FullTypedMetadata(rows[1]),
               "two records retain four unlabeled slots and synthetic RTTI"))
      return false;
    std::string json;
    if (!Check(CompleteAndRead(
                   job, directory / "guardian-factory-discovery-found.json",
                   json) &&
                   CommonSidecar(json, job, true) &&
                   Contains(json, "\"status\":\"captured\"") &&
                   Count(json, "\"status\":\"found\"") == 2 &&
                   Contains(json, "\"stored_name\":\"HaS_ReLaTiOn_GuArDiAn\"") &&
                   Contains(json, "\"stored_name\":\"HAS_RELATION_WARD\"") &&
                   Count(json, "\"available\":true") == 8 &&
                   Count(json, "\"type_name_available\":true") == 2 &&
                   Count(json,
                         "\"type_name\":\".?AVFixtureGuardianFactory@@\"") ==
                       2 &&
                   Count(json, "\"col_fields\":[1,0,0,262144,282624,196608]") ==
                       2 &&
                   Contains(json, "\"opaque_descriptor_address\":" +
                                      std::to_string(kGuardianDescriptor)) &&
                   Contains(json, "\"opaque_descriptor_address\":" +
                                      std::to_string(kWardDescriptor)) &&
                   Contains(json, "\"name_id\":41") &&
                   Contains(json, "\"name_id\":73"),
               "production completion writes qualified private metadata"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Put(kGuardianNameSlot + 0x04, std::uint8_t{1});
    fixture.memory.Put(kWardFactorySlot + 0x04, std::uint8_t{1});
    SnapshotSequence snapshots;
    auto job = MakeJob(fixture, snapshots, "fixture-discovery-missing");
    if (!Check(Execute(job) && Captured(job, snapshots),
               "missing records still produce a same-frame capture"))
      return false;
    const auto &rows = job.metadata->factories;
    if (!Check(rows[0].lookup.status == Status::name_missing &&
                   rows[0].lookup.failure == Failure::none &&
                   !rows[0].lookup.name_id &&
                   rows[1].lookup.status == Status::factory_missing &&
                   rows[1].lookup.failure == Failure::none &&
                   rows[1].lookup.name_id == kWardId &&
                   !rows[1].lookup.map_name_id &&
                   rows[0].rtti.unavailable_reason == "factory_not_found" &&
                   rows[1].rtti.unavailable_reason == "factory_not_found",
               "name missing and factory missing remain distinct"))
      return false;
    std::string json;
    if (!Check(CompleteAndRead(
                   job, directory / "guardian-factory-discovery-missing.json",
                   json) &&
                   CommonSidecar(json, job, true) &&
                   Count(json, "\"status\":\"name_missing\"") == 1 &&
                   Count(json, "\"status\":\"factory_missing\"") == 1 &&
                   Contains(json, "\"name_id\":73") &&
                   Count(json, "\"available\":false") == 8,
               "completion preserves the two kinds of missing metadata"))
      return false;
  }
  {
    Fixture fixture;
    fixture.memory.Remove(kVtable + 2 * 8);
    fixture.memory.Remove(kWardRecord);
    SnapshotSequence snapshots;
    auto job = MakeJob(fixture, snapshots, "fixture-discovery-unreadable");
    if (!Check(Execute(job) && Captured(job, snapshots),
               "partial read failure preserves the captured frame"))
      return false;
    const auto &rows = job.metadata->factories;
    if (!Check(FoundLookup(rows[0], kGuardian, kGuardianId, kGuardianRecord,
                           kGuardianDescriptor) &&
                   rows[0].virtual_slots[0].available &&
                   rows[0].virtual_slots[1].available &&
                   !rows[0].virtual_slots[2].available &&
                   !rows[0].virtual_slots[2].rva &&
                   rows[0].virtual_slots[3].available &&
                   rows[0].rtti.type_name_available &&
                   rows[0].rtti.type_name == kTypeName &&
                   rows[1].lookup.status == Status::unavailable &&
                   rows[1].lookup.failure ==
                       Failure::factory_record_unreadable &&
                   rows[1].lookup.name_id == kWardId &&
                   rows[1].lookup.map_name_id == kWardId,
               "slot failure and independent record failure stay visible"))
      return false;
    std::string json;
    if (!Check(CompleteAndRead(
                   job,
                   directory / "guardian-factory-discovery-unreadable.json",
                   json) &&
                   CommonSidecar(json, job, true) &&
                   Contains(json,
                            "\"unavailable_reason\":\"factory_record_unreadable\"") &&
                   Contains(json,
                            "\"slot_index\":2,\"available\":false,\"address\":null,\"rva\":null") &&
                   Count(json, "\"available\":true") == 3 &&
                   Count(json, "\"available\":false") == 5 &&
                   Count(json,
                         "\"type_name\":\".?AVFixtureGuardianFactory@@\"") ==
                       1,
               "completion writes partial metadata without losing healthy fields"))
      return false;
  }
  {
    Fixture fixture;
    SnapshotSequence snapshots;
    ++snapshots.after.date_raw;
    auto job = MakeJob(fixture, snapshots, "fixture-discovery-frame-changed");
    if (!Check(Execute(job) && job.executed && !job.frame_observed &&
                   !job.metadata && snapshots.reads == 2 &&
                   job.unavailable_reason == "frame_changed",
               "changed post-read frame cannot qualify captured metadata"))
      return false;
    std::string json;
    if (!Check(CompleteAndRead(
                   job,
                   directory / "guardian-factory-discovery-frame-changed.json",
                   json) &&
                   CommonSidecar(json, job, false) &&
                   Count(json, "\"status\":\"unavailable\"") == 3 &&
                   Contains(json, "\"unavailable_reason\":\"frame_changed\"") &&
                   Count(json, "\"name_id\":null") == 2 &&
                   Count(json, "\"factory_address\":0") == 2 &&
                   Count(json, "\"available\":false") == 8 &&
                   Count(json, "\"type_name\":null") == 2,
               "completion emits fixed unavailable rows for a changed frame"))
      return false;
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::fputs("usage: guardian_factory_discovery_job_test <sidecar-directory>\n",
               stderr);
    return 2;
  }
  try {
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    if (!RunChecks(directory)) return 1;
    std::puts("SOURCE_FIXTURE_PASS");
    return 0;
  } catch (const std::exception &error) {
    std::fprintf(stderr, "SOURCE_FIXTURE_FAIL: %s\n", error.what());
    return 1;
  }
}
