// AUTHORED_NOTRUN. External synthetic four-collector/serializer fixture.
// No whole Strength producer, native function pointer, SDK or game is called.
#include "xar_bridge/ck3_12004_future_daily_supply_schedule.hpp"
#include "xar_bridge/ck3_12004_current_detachment_callback_inputs.hpp"
#include "xar_bridge/ck3_12004_current_detachment_store_inputs.hpp"
#include "xar_bridge/ck3_12004_current_character_detachment_inputs.hpp"
#include "xar_bridge/army_future_daily_supply_schedule_serializer_v1.hpp"
#include "xar_bridge/army_current_detachment_callback_inputs_serializer_v1.hpp"
#include "xar_bridge/army_current_detachment_store_inputs_serializer_v1.hpp"
#include "xar_bridge/army_current_character_detachment_inputs_serializer_v1.hpp"

#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
static_assert(sizeof(std::uintptr_t) == 8, "compile this fixture for x64");
constexpr std::uintptr_t kImageBase = 0x140000000ULL;
constexpr std::uint32_t kPublicArmy = 11, kCArmy = 12;
constexpr std::uint32_t kIncoming0 = 0x2B000001U, kIncoming1 = 0x2B000002U;
constexpr std::uint32_t kCharacter = 0x1B000003U;
constexpr std::int64_t kDate = 53238336;
constexpr std::int32_t kStoredD = 7;
constexpr std::int64_t kBefore100 = -1234567890123LL;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

// Allocated backing regions follow the existing DATA fixture's read seam.
// One source-vtable address alias lets the exact4 binder keep its real source
// witness while every actual byte comes from owned synthetic allocation.
struct Memory {
  struct Region {
    std::unique_ptr<std::byte[]> bytes;
    std::uintptr_t address;
    std::size_t size;
  };
  struct Request { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Request> requests;

  void *Allocate(std::size_t size, std::uintptr_t alias = 0) {
    auto bytes = std::make_unique<std::byte[]>(size);
    const auto address = alias ? alias : reinterpret_cast<std::uintptr_t>(bytes.get());
    regions.push_back({std::move(bytes), address, size});
    return reinterpret_cast<void *>(address);
  }
  template <class T> void Put(void *object, std::size_t offset, const T &value) {
    const auto address = reinterpret_cast<std::uintptr_t>(object) + offset;
    for (auto &region : regions) {
      if (address >= region.address && address - region.address <= region.size &&
          sizeof(value) <= region.size - (address - region.address)) {
        std::memcpy(region.bytes.get() + (address - region.address), &value, sizeof(value));
        return;
      }
    }
    throw std::runtime_error("fixture Put outside allocated backing region");
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    memory.requests.push_back({address, size});
    const auto requested = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region : memory.regions) {
      if (requested >= region.address && requested - region.address <= region.size &&
          size <= region.size - (requested - region.address)) {
        std::memcpy(output, region.bytes.get() + (requested - region.address), size);
        return true;
      }
    }
    return false;
  }
  bool WasRead(const void *object, std::size_t offset) const {
    const auto address = reinterpret_cast<std::uintptr_t>(object) + offset;
    for (const auto &request : requests)
      if (reinterpret_cast<std::uintptr_t>(request.address) == address) return true;
    return false;
  }
};

void AppendJsonString(std::string &output, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  output += '"';
  for (const unsigned char ch : text) {
    if (ch == '"' || ch == '\\') { output += '\\'; output += static_cast<char>(ch); }
    else if (ch < 0x20) {
      output += "\\u00"; output += hex[ch >> 4]; output += hex[ch & 15];
    } else output += static_cast<char>(ch);
  }
  output += '"';
}

struct Fixture {
  Memory memory;
  ck3_12002::ArmyBindings army_bindings{};
  ck3_12003::CurrentDetachmentDataBindings12003 software{};
  game::ArmyCurrentDetachmentDataInputsV1 seed{};
  ck3_12004::FutureDailySupplyScheduleBindings12004 schedule_binding =
      ck3_12004::BindFutureDailySupplySchedule12004(kImageBase, ck3_12004::kExecutableSha256);
  ck3_12004::CurrentDetachmentCallbackBindings12004 callback_binding =
      ck3_12004::BindCurrentDetachmentCallbackInputs12004(kImageBase, ck3_12004::kExecutableSha256);
  ck3_12004::CurrentDetachmentStoreBindings12004 store_binding =
      ck3_12004::BindCurrentDetachmentStoreInputs12004(kImageBase, ck3_12004::kExecutableSha256);
  ck3_12004::CurrentCharacterDetachmentBindings12004 character_binding =
      ck3_12004::BindCurrentCharacterDetachmentInputs12004(kImageBase, ck3_12004::kExecutableSha256);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *game_data = memory.Allocate(0x2B000);
  void *unit = memory.Allocate(0x180), *army = memory.Allocate(0x208);
  void *arrg0 = memory.Allocate(0x150), *arrg1 = memory.Allocate(0x150);
  void *arrg_slot = memory.Allocate(8), *arrg_fallback_slot = memory.Allocate(8);
  void *arrg_store = memory.Allocate(0x50), *arrg_table = memory.Allocate(32U * 16U);
  void *army_slot = memory.Allocate(8), *army_fallback_slot = memory.Allocate(8);
  void *unit_slot = memory.Allocate(8);
  void *character = memory.Allocate(0x1C0), *extension = memory.Allocate(0x108);
  void *province0 = memory.Allocate(8), *province1 = memory.Allocate(8);
  void *primary_vtable = memory.Allocate(8,
      reinterpret_cast<std::uintptr_t>(callback_binding.known_primary_vtable));

  explicit Fixture(bool nonnull_extension) {
    army_bindings.enabled = true;
    army_bindings.game_state_slot = static_cast<void **>(state_slot);
    memory.Put(state_slot, 0, state);
    memory.Put(state, 8, kDate);
    memory.Put(state, 0x9C, kStoredD);
    memory.Put(state, 0xA0, game_data);
    memory.Put(unit, 0x10, kPublicArmy);
    memory.Put(unit, 0x178, kCArmy);
    memory.Put(army, 0x10, kCArmy);
    memory.Put(army, 0x124, kPublicArmy);
    // Zero-initialized all30 headers have count0/capacity0/null vector.
    software.common.enabled = true;
    software.common.game_state_slot = state_slot;
    software.common.read_memory = Memory::Read;
    software.common.read_context = &memory;
    software.common.arrg_registry_slot = arrg_slot;
    software.common.arrg_fallback_slot = arrg_fallback_slot;
    software.common.army_registry_slot = army_slot;
    software.common.army_fallback_slot = army_fallback_slot;
    software.unit_registry_slot = unit_slot;
    // Unit fallback intentionally unavailable in selected scene: current
    // source chain partial must not suppress the independent reset descriptor.
    software.unit_fallback_slot = nullptr;
    memory.Put(army_slot, 0, static_cast<void *>(nullptr));
    memory.Put(army_fallback_slot, 0, army);
    memory.Put(unit_slot, 0, static_cast<void *>(nullptr));
    memory.Put(arrg_slot, 0, arrg_store);
    memory.Put(arrg_fallback_slot, 0, arrg0);
    memory.Put(arrg_store, 0x20, arrg_table);
    memory.Put(arrg_store, 0x2C, std::uint32_t{32});
    memory.Put(arrg_store, 0x48, std::uint8_t{0});
    memory.Put(arrg_store, 0x3C, std::uint32_t{0});
    memory.Put(arrg_store, 0x4A, std::uint8_t{0});
    memory.Put(arrg_store, 0x38, std::uint32_t{2});
    memory.Put(arrg_store, 0x40, std::uint32_t{0xFFFFFFFFU});
    memory.Put(primary_vtable, 0, callback_binding.known_primary_slot0_target);
    memory.Put(character, 0x18, kCharacter);
    memory.Put(character, 0x1B8, nonnull_extension ? extension : static_cast<void *>(nullptr));
    memory.Put(extension, 0xF8, kIncoming0);
    memory.Put(extension, 0x100, kBefore100);
    seed.selection_ready = true; seed.roster_ready = true;
    seed.current_date_storage_raw64 = kDate;
    // This synthetic seed is not a run of the old DATA/whole Strength producer.
    seed.ready = false;
    for (std::int32_t index = 0; index < 2; ++index) {
      void *arrg = index == 0 ? arrg0 : arrg1;
      const std::uint32_t id = index == 0 ? kIncoming0 : kIncoming1;
      memory.Put(arrg, 0, primary_vtable);
      memory.Put(arrg, 0x10, id);
      memory.Put(arrg, 0x20, static_cast<void *>(nullptr));
      memory.Put(arrg, 0x2C, std::int32_t{-2});
      memory.Put(arrg, 0x28, std::int32_t{7});
      memory.Put(arrg_table, static_cast<std::size_t>(id & 0xFFFFFFU) * 16 + 8, arrg);
      game::ArmyCurrentDetachmentIncomingV1 incoming{};
      incoming.native_index = index;
      incoming.arrg_identity = ck3_12003::daily_assault_table_detail::Identity(arrg);
      incoming.arrg_full_id_u32 = id;
      incoming.character_full_id_148_u32 = kCharacter;
      incoming.passed_province_identity = ck3_12003::daily_assault_table_detail::Identity(
          index == 0 ? province0 : province1);
      auto &resolution = incoming.character_resolution;
      resolution.status = "available"; resolution.ready = true;
      resolution.requested_full_id_u32 = kCharacter;
      resolution.registry_loaded = true;
      resolution.registry_capacity_u32 = 32;
      resolution.registry_index_u32 = kCharacter & 0xFFFFFFU;
      resolution.indexed_identity = ck3_12003::daily_assault_table_detail::Identity(character);
      resolution.indexed_full_id_u32 = kCharacter;
      resolution.selection = "registry_full_id"; resolution.used_fallback = false;
      resolution.object_identity = resolution.indexed_identity;
      resolution.selected_full_id_u32 = kCharacter;
      seed.incoming.push_back(std::move(incoming));
    }
  }
};

std::string CaptureScene(bool nonnull_extension) {
  Fixture fixture(nonnull_extension);
  const auto schedule = ck3_12004::ReadFutureDailySupplyScheduleInputs12004(
      fixture.schedule_binding, fixture.army_bindings, fixture.army, fixture.unit);
  const auto callback = ck3_12004::ReadCurrentDetachmentCallbackInputs12004(
      fixture.callback_binding, fixture.software, &fixture.seed);
  const auto store = ck3_12004::ReadCurrentDetachmentStoreInputs12004(
      fixture.store_binding, fixture.software, &fixture.seed);
  const auto character = ck3_12004::ReadCurrentCharacterDetachmentInputs12004(
      fixture.character_binding, fixture.software, &fixture.seed);

  Check(schedule.ready && schedule.phases.size() == 30, "all30 real collector empty headers");
  Check(schedule.subject_army_id_u32 == kPublicArmy && schedule.subject_carmy_id_u32 == kCArmy,
        "all30 subject IDs match the external whole-row template IDs");
  for (const auto &phase : schedule.phases)
    Check(phase.ready && phase.count_raw_i32 == 0 && phase.matching_positions &&
          phase.matching_positions->empty() && phase.data_pointer_present == false,
          "known empty0 stays distinct from a missing schedule phase");
  Check(callback.ready && callback.incoming.size() == 2, "callback independently captures both incoming");
  for (const auto &incoming : callback.incoming)
    Check(incoming.ready && incoming.data_pointer_present == false &&
          incoming.data_count_2c_raw_i32 == -2 && incoming.data_capacity_28_raw_i32 == 7 &&
          incoming.records.empty() && !incoming.data_allocator_identity,
          "null DATA skips records and allocator while retaining signed before context");
  Check(!fixture.memory.WasRead(fixture.arrg0, 0x30) &&
        !fixture.memory.WasRead(fixture.arrg1, 0x30), "null DATA performs no allocator read");
  Check(store.ready && store.requests.size() == 2 && store.active_count_3c_raw_u32 == 0,
        "real store admission seed is ready with unsigned0 prefix context");
  for (const auto &request : store.requests)
    Check(request.ready && request.selected_pointer_present == true &&
          request.requested_full_id_u32 == request.selected_full_id_10_raw_u32,
          "matching store IDs use the real current selected object");
  Check(character.ready && character.requests.size() == 2,
        "two Character requests remain independently ready without baseline DATA ready");
  Check(character.requests[0].seed_incoming_native_index == 0 &&
        character.requests[1].seed_incoming_native_index == 1 &&
        character.requests[0].character_resolution.object_identity ==
            character.requests[1].character_resolution.object_identity &&
        character.requests[0].passed_province_identity != character.requests[1].passed_province_identity,
        "same Character with distinct passed Provinces is not deduplicated");
  for (const auto &request : character.requests) {
    Check(request.current_extension_1b8_present == nonnull_extension,
          "current Character1B8 branch is actually captured");
    Check(request.extension_reset_inputs_ready == nonnull_extension,
          "reset descriptor follows current extension presence");
    if (nonnull_extension) {
      Check(request.extension_f8_raw_u32 == kIncoming0 && request.extension_100_raw64 == kBefore100,
            "before F8 and signed full QWORD100 come from actual fixture bytes");
      Check(!request.source_chain_ready && request.army_resolution.ready &&
            request.army_resolution.registry_loaded == false &&
            !request.army_full_id_140_u32 && !request.unit_full_id_124_u32,
            "registry-null roles do not demand unused member IDs; partial Unit does not gate reset");
    } else {
      Check(!request.extension_f8_raw_u32 && !request.extension_100_raw64,
            "null extension makes no extension-field observation");
    }
  }
  Check(!fixture.memory.WasRead(fixture.arrg0, 0x140) &&
        !fixture.memory.WasRead(fixture.army, 0x124), "registry-null branches do not read140/124");

  const auto number = [](auto value) { return std::to_string(value); };
  std::string output = "{\"future_daily_supply_schedule_inputs_v1\":";
  game::AppendArmyFutureDailySupplyScheduleInputsV1(output, schedule, number, AppendJsonString);
  output += ",\"current_detachment_callback_inputs_v1\":";
  game::AppendArmyCurrentDetachmentCallbackInputsV1(output, callback, number, AppendJsonString);
  output += ",\"current_detachment_store_inputs_v1\":";
  game::AppendArmyCurrentDetachmentStoreInputsV1(output, store, number, AppendJsonString);
  output += ",\"current_character_detachment_inputs_v1\":";
  game::AppendArmyCurrentCharacterDetachmentInputsV1(output, character, number, AppendJsonString);
  output += '}';
  return output;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: native_four_leaf_fixture.exe <native_bundle.json>\n";
    return 2;
  }
  try {
    const auto skip = CaptureScene(false);
    const auto selected = CaptureScene(true);
    const std::string bundle =
        "{\"schema_version\":1,\"subject_army_id\":11,\"subject_native_carmy_id\":12,"
        "\"scene_order\":[\"skip\",\"selected\"],"
        "\"provenance\":\"synthetic_new_collector_serializer_fragments_not_whole_native_strength\","
        "\"samples\":{\"skip\":" + skip + ",\"selected\":" + selected + "}}\n";
    std::ofstream file(argv[1], std::ios::binary | std::ios::trunc);
    if (!file) throw std::runtime_error("cannot open requested native bundle output");
    file.write(bundle.data(), static_cast<std::streamsize>(bundle.size()));
    file.close();
    if (!file) throw std::runtime_error("native bundle write failed");
    std::cout << "wrote two synthetic actual-collector/serializer scenes\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
