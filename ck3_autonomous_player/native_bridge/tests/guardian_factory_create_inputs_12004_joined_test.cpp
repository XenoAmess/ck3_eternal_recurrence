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
  if (!condition) std::fprintf(stderr, "NEW_FACTORY_INPUT_FAIL: %s\n", label);
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

bool NewCases(const std::filesystem::path &directory) {
  constexpr std::string_view child = "\"factory_create_inputs_v1\":{\"schema_version\":1";
  constexpr std::string_view empty10 = "\"field_10_dword\":{\"available\":false,\"raw_value\":null}";
  constexpr std::string_view empty18 = "\"field_18_qword\":{\"available\":false,\"raw_value\":null}";
  for (std::size_t scene = 0; scene < 5; ++scene) {
    Fixture fixture;
    SnapshotSequence snapshots;
    constexpr std::array<std::string_view, 5> requests{
      "family-relation-fixture-create-inputs-full", "family-relation-fixture-create-inputs-unreadable18",
      "family-relation-fixture-create-inputs-unreadable10", "family-relation-fixture-create-inputs-after-changed",
      "family-relation-fixture-create-inputs-completion-changed"};
    if (scene == 1) fixture.memory.fail_qword[1] = true;
    if (scene == 2) fixture.memory.fail_dword[1] = true;
    if (scene == 3) ++snapshots.after.date_raw;
    auto job = MakeJob(fixture, snapshots, requests[scene]);
    if (!Check(Execute(job) && snapshots.reads == 2,
               "new fields remain within the existing two-bookend job")) return false;
    if (!Check(fixture.memory.dword_reads == std::array<std::size_t, 2>{1, 1},
               "factory+10 uses precisely the original one DWORD read per key")) return false;
    const auto expected_qwords = scene == 2
        ? std::array<std::size_t, 2>{1, 0} : std::array<std::size_t, 2>{1, 1};
    if (!Check(fixture.memory.qword_reads == expected_qwords,
               "factory+18 reads one QWORD only after its own found guard")) return false;
    if (scene != 3) {
      if (!Check(job.frame_observed && job.metadata.has_value(), "stable frame admits owned metadata")) return false;
      const auto &rows = job.metadata->factories;
      if (!Check(rows[0].lookup.status == Status::found &&
                 rows[0].lookup.record_name_id == kGuardianId &&
                 rows[0].factory_create_input_18_qword == std::uint64_t{0xFEDCBA9876543210ULL},
                 "first field retains all 64 bits independently of factory+08")) return false;
      if (scene == 1) {
        if (!Check(rows[1].lookup.status == Status::found &&
                   rows[1].lookup.record_name_id == kWardId &&
                   !rows[1].factory_create_input_18_qword.has_value() &&
                   rows[1].virtual_slots[0].available,
                   "failed +18 read discards partial bytes and retains lookup/slots")) return false;
      } else if (scene == 2) {
        if (!Check(rows[1].lookup.status == Status::unavailable &&
                   !rows[1].lookup.record_name_id.has_value() &&
                   !rows[1].factory_create_input_18_qword.has_value(),
                   "failed original +10 read cannot reach the added read")) return false;
      } else if (!Check(rows[1].factory_create_input_18_qword.has_value() &&
                        *rows[1].factory_create_input_18_qword == std::uint64_t{0},
                        "observed zero QWORD remains independently available")) return false;
    } else if (!Check(!job.frame_observed && !job.metadata.has_value(),
                      "changed after bookend rejects the newly read values")) return false;
    auto completion = job.expected_snapshot;
    if (scene == 4) ++completion.date_raw;
    std::string wire;
    const auto path = directory / (std::string(requests[scene]) + ".json");
    if (!Check(Complete(job, completion, path, wire) && Count(wire, child) == 2,
               "actual completion serializer writes the versioned child in both rows")) return false;
    if (scene >= 3) {
      if (!Check(Contains(wire, "\"qualified\":false") &&
                 Count(wire, empty10) == 2 && Count(wire, empty18) == 2,
                 "either frame boundary suppresses all new raw values")) return false;
    } else if (scene == 0) {
      if (!Check(Contains(wire, "\"qualified\":true") &&
                 Contains(wire, "\"field_18_qword\":{\"available\":true,\"raw_value\":18364758544493064720}") &&
                 Contains(wire, "\"field_18_qword\":{\"available\":true,\"raw_value\":0}") &&
                 Contains(wire, "\"field_10_dword\":{\"available\":true,\"raw_value\":41}") &&
                 Contains(wire, "\"field_10_dword\":{\"available\":true,\"raw_value\":73}"),
                 "new production JSON preserves high uint64, zero and reused DWORDs")) return false;
    } else if (!Check(Count(wire, empty18) == 1 &&
                      Count(wire, empty10) == (scene == 2 ? std::size_t{1} : std::size_t{0}),
                      "new field availability is independent per row and per source field")) return false;
  }
  std::puts("guardian_factory_create_inputs_new_cases=5 PASS; added_found_row_reads=8+8; old_cases=0; game_values=0");
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
    std::fprintf(stderr, "new fixture exception: %s\n", exception.what());
    return 3;
  }
}
