// UNIQUE PROPOSED RECIPE, NOT REGISTERED / NOT RUN in this package:
// add_executable(person_carrier_direct12004_first_fixture
//   tests/person_carrier_direct12004_fixture.cpp
//   src/ck3_12004_person_carrier_direct.cpp)
// target_include_directories(person_carrier_direct12004_first_fixture PRIVATE include)
// add_test(NAME person_carrier_direct12004_first
//   COMMAND person_carrier_direct12004_first_fixture
//   ${CMAKE_CURRENT_BINARY_DIR}/person_carrier_direct12004_first)
// This is the production bounded reader+serializer with fake memory only.
// It does not qualify the owning whole query, logical baseline, or live Entry.
#include "xar_bridge/ck3_12004_person_carrier_direct.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace {
using namespace xar::ck3_12004;

void Require(bool condition, std::string_view message) {
  if (!condition) {
    std::cerr << "person-carrier-direct12004: " << message << '\n';
    std::exit(1);
  }
}

struct Memory {
  struct Interval {
    std::uintptr_t address;
    std::size_t size;
    std::size_t attempts = 0;
  };
  std::map<std::uintptr_t, std::vector<std::byte>> regions;
  std::vector<Interval> denied;
  std::vector<Interval> hidden;

  void Add(std::uintptr_t address, std::size_t size) {
    regions.emplace(address, std::vector<std::byte>(size));
  }
  template <typename T>
  void Put(std::uintptr_t base, std::size_t offset, T value) {
    auto &region = regions.at(base);
    Require(offset <= region.size() && sizeof(value) <= region.size() - offset,
            "fake-memory setup outside declared region");
    std::memcpy(region.data() + offset, &value, sizeof(value));
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    const auto overlaps = [begin, size](const Interval &interval) {
      return begin < interval.address + interval.size &&
             interval.address < begin + size;
    };
    for (auto &interval : memory.denied) {
      if (overlaps(interval)) { ++interval.attempts; return false; }
    }
    for (auto &interval : memory.hidden) {
      if (overlaps(interval)) { ++interval.attempts; return false; }
    }
    for (const auto &[base, bytes] : memory.regions) {
      if (begin >= base && begin - base <= bytes.size() &&
          size <= bytes.size() - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, bytes.data() + (begin - base), size);
        return true;
      }
    }
    return false;
  }
  void NoRead(std::uintptr_t address, std::size_t size) {
    denied.push_back({address, size});
  }
  std::size_t UndemandedAttempts() const {
    std::size_t attempts = 0;
    for (const auto &interval : denied) attempts += interval.attempts;
    return attempts;
  }
};

struct Fixture {
  static constexpr std::uintptr_t kModule = 0x140000000;
  static constexpr std::uintptr_t kModel = 0x100000;
  static constexpr std::uintptr_t kCharacter = 0x200000;
  static constexpr std::uintptr_t kCarrier = 0x300000;
  static constexpr std::uintptr_t kDefinition = 0x400000;
  static constexpr std::uintptr_t kTable = 0x500000;
  static constexpr std::uintptr_t kMapped = kTable + 0x340;
  static constexpr std::uintptr_t kDefault = kModule + kPersonCarrierDefaultPcRva12004;
  static constexpr std::uintptr_t kGuard = kModule + kPersonCarrierDefaultGuardRva12004;
  static constexpr std::uintptr_t kMappedKeys = 0x600000;
  static constexpr std::uintptr_t kMappedValues = 0x700000;
  static constexpr std::uintptr_t kDefaultKeys = 0x800000;
  static constexpr std::uintptr_t kDefaultValues = 0x900000;
  static constexpr std::uint32_t kCharacterId = 0xAB007485U;
  Memory memory;
  PersonCarrierDirect12004Bindings bindings;

  Fixture() {
    memory.Add(kModel, 0x20);
    memory.Add(kCharacter, 0x1D0);
    memory.Add(kCarrier, 0xB74);
    memory.Add(kDefinition, 0x3E8);
    memory.Add(kTable, 2 * 0x340);
    memory.Add(kDefault, 0x78);
    memory.Add(kGuard, 4);
    memory.Add(kMappedKeys, 8);
    memory.Add(kMappedValues, 32);
    memory.Add(kDefaultKeys, 8);
    memory.Add(kDefaultValues, 32);
    memory.Put(kModel, 8, kCharacter);
    memory.Put(kCharacter, kCharacterFullIdOffset, kCharacterId);
    memory.Put(kCharacter, 0x1C8, kCarrier);
    memory.Put(kCarrier, 0x20, kDefinition);
    memory.Put(kCarrier, 0xB70, std::int32_t{1});
    memory.Put(kDefinition, 0x38, std::uint32_t{0x4744624F});
    memory.Put(kDefinition, 0x3D8, kTable);
    memory.Put(kDefinition, 0x3E4, std::int32_t{2});
    memory.Put(kGuard, 0, std::int32_t{7});
    Property(kMapped, kMappedKeys, kMappedValues,
             {0x22A, 0xFFFF, 0x22A, 0},
             {-100'000, std::numeric_limits<std::int64_t>::min(), 0,
              std::numeric_limits<std::int64_t>::max()});
    Property(kDefault, kDefaultKeys, kDefaultValues, {0x22A}, {-250'000});
    // Destination Model+10 and old numeric +74 are deliberately undemanded.
    memory.NoRead(kModel + 0x10, 0x10);
    memory.NoRead(kMapped + 0x74, 4);
    memory.NoRead(kDefault + 0x74, 4);
    bindings = BindPersonCarrierDirect12004(
        kModule, kGameVersion, kExecutableSha256, &Memory::Read, &memory);
    Require(bindings.enabled, "exact actual4 binding unavailable");
  }

  void Property(std::uintptr_t pc, std::uintptr_t keys,
                std::uintptr_t values,
                const std::vector<std::uint16_t> &raw_keys,
                const std::vector<std::int64_t> &raw_values) {
    Require(raw_keys.size() == raw_values.size(), "fixture raw pair length differs");
    const auto region = pc == kMapped ? kTable : kDefault;
    const auto offset = static_cast<std::size_t>(pc - region);
    memory.Put(region, offset + 0xC, static_cast<std::int32_t>(raw_keys.size()));
    if (raw_keys.empty()) return;
    memory.Put(region, offset, keys);
    memory.Put(region, offset + 0x68, values);
    for (std::size_t i = 0; i < raw_keys.size(); ++i) {
      memory.Put(keys, i * 2, raw_keys[i]);
      memory.Put(values, i * 8, raw_values[i]);
    }
  }
  void NoDefault() {
    memory.NoRead(kGuard, 4);
    memory.NoRead(kDefault, 0x70);
  }
  void NoMappedTable() {
    memory.NoRead(kDefinition + 0x3D8, 8);
    memory.NoRead(kTable, 2 * 0x340);
  }
  PersonCarrierDirect12004DTO Observe() {
    auto dto = ReadPersonCarrierDirect12004(bindings, kModel);
    Require(memory.UndemandedAttempts() == 0, "reader demanded a skipped field");
    Require(dto.character_id == kCharacterId &&
                dto.character_identity == kCharacter &&
                dto.selected_model_identity == kModel &&
                dto.destination_pc_identity == kModel + 0x10 &&
                dto.build_version == kGameVersion &&
                dto.executable_sha256 == kExecutableSha256 &&
                dto.weight_q100000 == 100'000,
            "actual model/Character/full-ID or exact pin provenance differs");
    return dto;
  }
};

void Save(const std::filesystem::path &directory, const char *name,
          const PersonCarrierDirect12004DTO &dto) {
  const auto wire = SerializePersonCarrierDirect12004(dto);
  Require(wire.find("\"schema\":\"xar.ck3.person-carrier-direct-12004-v1\"") !=
              std::string::npos &&
              (wire.find("\"values_q64\":") != std::string::npos) ==
                  dto.properties.has_value(),
          "production leaf serializer shape differs");
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << wire;
  Require(static_cast<bool>(output), "cannot write production leaf fixture wire");
}

void Run(const std::filesystem::path &directory) {
  Require(!BindPersonCarrierDirect12004(Fixture::kModule, "1.20.0.3",
              kExecutableSha256, &Memory::Read).enabled &&
              !BindPersonCarrierDirect12004(Fixture::kModule, kGameVersion,
              "wrong-sha", &Memory::Read).enabled,
          "binder admitted a non-actual4 pin");
  {
    Fixture f;
    f.memory.Put(Fixture::kCharacter, 0x1C8, std::uintptr_t{0});
    f.memory.NoRead(Fixture::kCarrier, 0xB74);
    f.memory.NoRead(Fixture::kDefinition, 0x3E8);
    f.NoDefault();
    const auto dto = f.Observe();
    Require(dto.ready && dto.reason.empty() && dto.carrier_present == false &&
                dto.carrier_identity == std::uintptr_t{0} && dto.selection == "none" &&
                dto.source_occurrence_count == 0U && !dto.definition_identity &&
                !dto.rank_i32 && !dto.row_count_i32 && !dto.properties,
            "absent carrier failed to remain known zero");
    Save(directory, "absent-carrier", dto);
  }
  {
    Fixture f;
    f.memory.Put(Fixture::kDefinition, 0x38, std::uint32_t{0});
    f.memory.NoRead(Fixture::kCarrier + 0xB70, 4);
    f.memory.NoRead(Fixture::kDefinition + 0x3E4, 4);
    f.NoMappedTable();
    f.NoDefault();
    const auto dto = f.Observe();
    Require(dto.ready && dto.definition_magic_u32 == 0U &&
                dto.source_occurrence_count == 0U && dto.selection == "none" &&
                !dto.rank_i32 && !dto.row_count_i32 && !dto.properties,
            "observed wrong magic failed to skip later operands");
    Save(directory, "wrong-magic", dto);
  }
  {
    Fixture f;
    f.Property(Fixture::kMapped, Fixture::kMappedKeys, Fixture::kMappedValues, {}, {});
    f.memory.NoRead(Fixture::kMapped, 8);
    f.memory.NoRead(Fixture::kMapped + 0x68, 8);
    f.NoDefault();
    const auto dto = f.Observe();
    Require(dto.ready && dto.selection == "mapped_row" &&
                dto.selected_pc_count_i32 == 0 && dto.source_occurrence_count == 0U &&
                dto.properties && dto.properties->keys_u16->empty() &&
                dto.properties->values_q64->empty(),
            "mapped count zero demanded arrays or lost known empty");
    Save(directory, "mapped-empty", dto);
  }
  {
    Fixture f;
    f.NoDefault();
    const auto dto = f.Observe();
    Require(dto.ready && dto.selected_pc_identity == Fixture::kMapped &&
                dto.rank_i32 == 1 && dto.row_count_i32 == 2 &&
                dto.selected_pc_count_i32 == 4 && dto.source_occurrence_count == 1U &&
                dto.properties && *dto.properties->keys_u16 ==
                    std::vector<std::uint16_t>{0x22A, 0xFFFF, 0x22A, 0} &&
                *dto.properties->values_q64 == std::vector<std::int64_t>{
                    -100'000, std::numeric_limits<std::int64_t>::min(), 0,
                    std::numeric_limits<std::int64_t>::max()},
            "mapped physical signed prowess/duplicate/sentinel/extrema changed");
    const auto wire = SerializePersonCarrierDirect12004(dto);
    Require(wire.find("\"values_q64\":[\"-100000\",\"-9223372036854775808\",\"0\",\"9223372036854775807\"]") !=
                std::string::npos,
            "signed Q64 values were not preserved as decimal strings");
    Save(directory, "mapped-nonempty-signed-prowess", dto);
  }
  {
    Fixture f;
    f.memory.Put(Fixture::kCarrier, 0xB70, std::int32_t{2});
    f.memory.Put(Fixture::kGuard, 0, std::int32_t{-2});
    f.NoMappedTable();
    const auto dto = f.Observe();
    Require(dto.ready && dto.rank_i32 == dto.row_count_i32 &&
                dto.selection == "static_default_5d71200" &&
                dto.default_guard_raw == -2 && dto.selected_pc_identity == Fixture::kDefault &&
                dto.source_occurrence_count == 1U && dto.properties &&
                *dto.properties->values_q64 == std::vector<std::int64_t>{-250'000},
            "rank==count fallback or completed signed guard selection differs");
    Save(directory, "fallback-initialized", dto);
  }
  {
    Fixture f;
    f.memory.Put(Fixture::kCarrier, 0xB70, std::int32_t{2});
    f.memory.Put(Fixture::kGuard, 0, std::int32_t{0});
    f.NoMappedTable();
    const auto dto = f.Observe();
    Require(!dto.ready && !dto.source_occurrence_count && dto.default_guard_raw == 0 &&
                dto.reason == "fallback_31937a0_default_initialization_unobserved" &&
                dto.selected_pc_count_i32 == 1 && dto.properties &&
                *dto.properties->keys_u16 == std::vector<std::uint16_t>{0x22A} &&
                *dto.properties->values_q64 == std::vector<std::int64_t>{-250'000},
            "guard zero fabricated an initialized default or discarded raw copy");
    Save(directory, "fallback-guard-zero", dto);
  }
  {
    Fixture f;
    f.NoDefault();
    f.memory.hidden.push_back({Fixture::kMappedValues, 32});
    const auto dto = f.Observe();
    Require(!dto.ready && !dto.source_occurrence_count &&
                dto.reason == "selected_pc_values_unread" &&
                dto.selected_pc_count_i32 == 4 && dto.properties &&
                *dto.properties->keys_u16 == std::vector<std::uint16_t>{0x22A, 0xFFFF, 0x22A, 0} &&
                !dto.properties->values_q64 && f.memory.hidden[0].attempts == 1,
            "partial values copy lost independent physical keys");
    Save(directory, "raw-partial-values", dto);
  }
  {
    Fixture f;
    f.memory.Put(Fixture::kCarrier, 0xB70, std::int32_t{-1});
    f.Property(Fixture::kDefault, Fixture::kDefaultKeys, Fixture::kDefaultValues, {}, {});
    f.memory.NoRead(Fixture::kDefinition + 0x3E4, 4);
    f.memory.NoRead(Fixture::kDefault, 8);
    f.memory.NoRead(Fixture::kDefault + 0x68, 8);
    f.NoMappedTable();
    const auto dto = f.Observe();
    Require(dto.ready && dto.rank_i32 == -1 && !dto.row_count_i32 &&
                dto.selection == "static_default_5d71200" &&
                dto.selected_pc_count_i32 == 0 && dto.source_occurrence_count == 0U,
            "negative rank read undemanded row count or fabricated a mapped row");
    Save(directory, "negative-rank-undemanded-count", dto);
  }
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: person_carrier_direct12004_first_fixture output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create fixture output directory");
  Run(directory);
  std::ofstream manifest(directory / "producer-manifest.json", std::ios::binary);
  manifest << "{\"producer\":\"person-carrier-direct12004-first\","
              "\"evidence_kind\":\"offline-native-leaf-fixture\","
              "\"owning_query_qualification\":false,\"live_qualification\":false,"
              "\"leaf_wires\":[\"absent-carrier.json\",\"wrong-magic.json\","
              "\"mapped-empty.json\",\"mapped-nonempty-signed-prowess.json\","
              "\"fallback-initialized.json\",\"fallback-guard-zero.json\","
              "\"raw-partial-values.json\",\"negative-rank-undemanded-count.json\"]}";
  Require(static_cast<bool>(manifest), "cannot write fixture producer manifest");
  std::cout << "person carrier direct12004: eight production bounded-leaf wires\n";
  return 0;
}
