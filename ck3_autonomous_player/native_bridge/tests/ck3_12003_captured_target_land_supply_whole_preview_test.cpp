// SOURCE_PREPARED/NOTRUN. Root owns the fresh FIRST build and invocation.
// Only accepted preview/transport context and callbacks are synthetic. The
// whole province-supply reader and whole route-preview serializer are production.
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
constexpr std::int32_t kUnit = 67108883;
constexpr std::int32_t kArmy = 33554443;
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kCommander = 29830;
constexpr std::int32_t kOrigin = 470;
constexpr std::int32_t kTarget = 471;
constexpr std::int32_t kFleet = 16777217;
constexpr std::int64_t kComponent = -612345;
constexpr std::int64_t kGain = 1750000;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void JsonString(std::string &output, std::string_view value) {
  output += '"';
  for (const char character : value) {
    if (character == '"' || character == '\\') output += '\\';
    output += character;
  }
  output += '"';
}
void Int32Array(std::string &output, const std::vector<std::int32_t> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) output += ',';
    output += std::to_string(values[index]);
  }
  output += ']';
}

struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template<class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof value);
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions)
      result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
};
struct Registry {
  Memory &memory;
  void *storage;
  void *table;
  Registry(Memory &source, std::int32_t capacity)
      : memory(source), storage(source.Allocate(0x30)),
        table(source.Allocate(static_cast<std::size_t>(capacity) * 16)) {
    memory.Put(storage, 0x20, table); memory.Put(storage, 0x2C, capacity);
  }
  void Add(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    memory.Put(table, static_cast<std::size_t>(index) * 16 + 8, object);
    memory.Put(object, 0x10, id);
  }
};

struct Event {
  std::string_view callback;
  std::int32_t requested_id = -1;
  std::int32_t province_id = -1;
  bool receiver_exact = true;
  bool owner_exact = true;
  bool commander_exact = true;
  bool details_null = true;
  std::int32_t ordinal = 0;
  std::int32_t mode = 0;
  std::int64_t multiplier = 0;
  std::optional<std::int64_t> returned_raw;
  bool returned_bool = false;
  bool returned_null_output = false;
};

struct Fixture;
Fixture *active = nullptr;
struct Fixture {
  Memory memory;
  Registry units{memory, 20}, armies{memory, 12};
  void *unit = memory.Allocate(0x180);
  void *army = memory.Allocate(0x210);
  void *owner = memory.Allocate(0x30);
  void *commander = memory.Allocate(0x30);
  void *fallback_commander = memory.Allocate(0x30);
  void *origin = memory.Allocate(0x864);
  void *target = memory.Allocate(0x864);
  void *gain_slot = memory.Allocate(8);
  ck3_12002::ArmyBindings bindings{};
  ck3_12002::MilitaryWorldAccess world{};
  std::vector<Event> events;
  bool same_origin_target = false;
  bool use_native_commander_fallback = false;
  bool component_applicable = true;
  bool component_output_missing = false;
  bool resupply_eligible = true;
  std::size_t limit_calls = 0, usage_calls = 0, component_predicate_calls = 0;
  std::size_t component_reader_calls = 0, resupply_calls = 0, fleet_calls = 0;
  bool abi_arguments_ok = true;

  void *TargetObject() const { return same_origin_target ? origin : target; }
  std::int32_t TargetId() const { return same_origin_target ? kOrigin : kTarget; }
  void *CommanderObject() const {
    return use_native_commander_fallback ? fallback_commander : commander;
  }
  static void *ResolveCharacter(void *context, std::int32_t id) noexcept {
    auto &fixture = *static_cast<Fixture *>(context);
    Event event{"resolve_character"}; event.requested_id = id;
    fixture.events.push_back(event);
    if (id == kOwner) return fixture.owner;
    if (id == kCommander) return fixture.commander;
    return nullptr;
  }
  static void *ResolveProvince(void *context, std::int32_t id) noexcept {
    auto &fixture = *static_cast<Fixture *>(context);
    Event event{"resolve_province"}; event.requested_id = id;
    fixture.events.push_back(event);
    if (id == kOrigin) return fixture.origin;
    if (id == kTarget) return fixture.target;
    return nullptr;
  }
  static std::int32_t Limit(void *province, void *owner_argument,
                            void *commander_argument, void *details) {
    auto &fixture = *active;
    ++fixture.limit_calls;
    Event event{"province_supply_limit"};
    event.province_id = province == fixture.origin ? kOrigin : kTarget;
    event.receiver_exact = province == fixture.origin || province == fixture.TargetObject();
    event.owner_exact = owner_argument == fixture.owner;
    event.commander_exact = commander_argument == fixture.CommanderObject();
    event.details_null = details == nullptr;
    event.returned_raw = province == fixture.origin ? 1000 : 2345;
    fixture.abi_arguments_ok = fixture.abi_arguments_ok && event.receiver_exact &&
        event.owner_exact && event.commander_exact && event.details_null;
    fixture.events.push_back(event);
    return static_cast<std::int32_t>(*event.returned_raw);
  }
  static std::int32_t Usage(void *province, void *owner_argument,
                            std::int32_t mode, std::int64_t *details) {
    auto &fixture = *active;
    ++fixture.usage_calls;
    Event event{"province_supply_usage"};
    event.province_id = province == fixture.origin ? kOrigin : kTarget;
    event.receiver_exact = province == fixture.origin || province == fixture.TargetObject();
    event.owner_exact = owner_argument == fixture.owner;
    event.details_null = details == nullptr; event.mode = mode;
    event.returned_raw = province == fixture.origin ? 321 : 678;
    fixture.abi_arguments_ok = fixture.abi_arguments_ok && event.receiver_exact &&
        event.owner_exact && event.details_null && mode == 0;
    fixture.events.push_back(event);
    return static_cast<std::int32_t>(*event.returned_raw);
  }
  static bool ComponentPredicate(void *province) {
    auto &fixture = *active;
    ++fixture.component_predicate_calls;
    Event event{"target_component_predicate"}; event.province_id = fixture.TargetId();
    event.receiver_exact = province == fixture.TargetObject();
    event.returned_bool = fixture.component_applicable;
    fixture.abi_arguments_ok = fixture.abi_arguments_ok && event.receiver_exact;
    fixture.events.push_back(event);
    return fixture.component_applicable;
  }
  static std::int64_t *Component(std::int64_t *output, void *receiver,
      std::int32_t ordinal, void *details, std::int64_t multiplier, std::int32_t mode) {
    auto &fixture = *active;
    ++fixture.component_reader_calls;
    Event event{"target_component_reader"}; event.province_id = fixture.TargetId();
    event.receiver_exact = receiver == static_cast<std::byte *>(fixture.TargetObject()) + 0x30;
    event.ordinal = ordinal; event.details_null = details == nullptr;
    event.multiplier = multiplier; event.mode = mode;
    event.returned_null_output = fixture.component_output_missing;
    if (!fixture.component_output_missing) event.returned_raw = kComponent;
    fixture.abi_arguments_ok = fixture.abi_arguments_ok && event.receiver_exact &&
        output != nullptr && ordinal == 0x1AB && event.details_null && multiplier == 100000 && mode == 0;
    fixture.events.push_back(event);
    if (fixture.component_output_missing) return nullptr;
    *output = kComponent;
    return output;
  }
  static bool Resupply(void *owner_argument, void *province) {
    auto &fixture = *active;
    ++fixture.resupply_calls;
    Event event{"target_resupply_predicate"}; event.province_id = fixture.TargetId();
    event.owner_exact = owner_argument == fixture.owner;
    event.receiver_exact = province == fixture.TargetObject();
    event.returned_bool = fixture.resupply_eligible;
    fixture.abi_arguments_ok = fixture.abi_arguments_ok && event.owner_exact && event.receiver_exact;
    fixture.events.push_back(event);
    return fixture.resupply_eligible;
  }
  static bool FleetPredicate(void *) {
    ++active->fleet_calls;
    return true;
  }

  Fixture() {
    active = this;
    units.Add(kUnit, unit); armies.Add(kArmy, army);
    memory.Put(unit, 0x20, origin); memory.Put(unit, 0x174, kOwner);
    memory.Put(unit, 0x178, kArmy);
    memory.Put(army, 0x14, std::uint32_t{0x41726D79});
    memory.Put(army, 0x120, kCommander); memory.Put(army, 0x124, kUnit);
    // Synthetic current Fleet association stays unchanged. The target observer
    // must not query the present Fleet/land predicate or execute disembarkation.
    memory.Put(army, 0x12C, kFleet);
    memory.Put(owner, 0x18, kOwner); memory.Put(commander, 0x18, kCommander);
    memory.Put(fallback_commander, 0x18, std::int32_t{-1});
    memory.Put(origin, 0x10, kOrigin); memory.Put(target, 0x10, kTarget);
    memory.Put(origin, 0x85C, std::uint32_t{0x50726F76});
    memory.Put(target, 0x85C, std::uint32_t{0x50726F76});
    memory.Put(gain_slot, 0, kGain);
    bindings.enabled = true;
    bindings.unit_storage_slot = &units.storage;
    bindings.internal_army_storage_slot = &armies.storage;
    bindings.get_province_supply_limit = Limit; bindings.get_province_supply_usage = Usage;
    bindings.province_supply_character_fallback_slot = &fallback_commander;
    auto &rate = bindings.current_land_supply_rate_bindings;
    rate.enabled = true; rate.province_component_condition = ComponentPredicate;
    rate.read_province_component = Component;
    auto &resupply = bindings.current_land_resupply_bindings;
    resupply.enabled = true; resupply.is_resupply_eligible = Resupply;
    resupply.is_army_fleet_supply_active = FleetPredicate;
    resupply.loaded_gain_raw = static_cast<const std::int64_t *>(gain_slot);
    world.context = this; world.resolve_character = ResolveCharacter;
    world.resolve_province = ResolveProvince;
  }

  game::PreviewMoveArmyResult Observe() {
    game::PreviewMoveArmyResult preview{};
    preview.status = game::PreviewMoveArmyStatus::available;
    preview.army_id = kUnit; preview.origin_province_id = kOrigin;
    preview.target_province_id = TargetId();
    preview.route_province_ids = same_origin_target ? std::vector<std::int32_t>{kOrigin}
        : std::vector<std::int32_t>{kOrigin, kTarget};
    const auto original_preview = preview;
    const auto before = memory.Snapshot();
    auto supply = ck3_12002::ReadArmyProvinceSupplyForPreview(bindings, world, preview);
    Check(preview == original_preview, "whole province-supply query mutated the input preview fields");
    Check(before == memory.Snapshot(), "whole province-supply query wrote synthetic game input memory");
    Check(abi_arguments_ok, "whole target-preview callback argument/receiver ABI differs");
    Check(fleet_calls == 0, "target context collector queried the present Fleet predicate");
    Check(supply.status == game::ArmyProvinceSupplyStatus::available &&
              supply.unavailable_reason.empty() && supply.army_id == kUnit &&
              supply.native_carmy_id == kArmy && supply.owner_character_id == kOwner &&
              supply.commander_character_id == (use_native_commander_fallback
                  ? std::optional<std::int32_t>{} : std::optional<std::int32_t>{kCommander}),
          "new sibling changed existing whole province-supply context/status");
    Check(supply.current.available && supply.current.role == game::ArmyProvinceSupplyRole::current &&
              supply.current.province_id == kOrigin && supply.current.native_supply_limit_soldiers == 1000 &&
              supply.current.native_supply_usage_soldiers == 321 &&
              !supply.current.captured_target_land_supply_inputs_v1,
          "current row changed or acquired a target-only sibling");
    Check(supply.target.available && supply.target.role == game::ArmyProvinceSupplyRole::target &&
              supply.target.province_id == TargetId() &&
              supply.target.native_supply_limit_soldiers == (same_origin_target ? 1000 : 2345) &&
              supply.target.native_supply_usage_soldiers == (same_origin_target ? 321 : 678) &&
              supply.current.unavailable_reason.empty() && supply.target.unavailable_reason.empty(),
          "new sibling changed the old target row status/limits/usage");
    Check(limit_calls == (same_origin_target ? 1U : 2U) && usage_calls == limit_calls,
          "new target observer duplicated legacy limit/usage calls");
    preview.province_supply = std::move(supply);
    return preview;
  }
};

void Write(const std::filesystem::path &path, const std::string &text) {
  std::ofstream output(path, std::ios::binary);
  Check(static_cast<bool>(output), "fresh target-preview artifact open failed");
  output << text << '\n';
  Check(static_cast<bool>(output), "fresh target-preview artifact write failed");
}
void Emit(const std::filesystem::path &directory, std::string_view name,
          const Fixture &fixture, const game::PreviewMoveArmyResult &preview) {
  std::string wire = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  JsonString(wire, "synthetic-target-preview-" + std::string(name));
  wire += ",\"ok\":true,\"result\":{\"step\":";
  JsonString(wire, "preview-move-army-" + std::to_string(kUnit) + "-to-" +
                   std::to_string(preview.target_province_id));
  wire += ",\"accepted\":true,\"status\":\"available\",\"route_preview\":";
  // Actual production whole route serializer invokes the actual whole supply
  // serializer and the installed target sibling hook. No leaf is transplanted.
  game::AppendMoveRoutePreviewV1(wire, preview,
      [](auto value) { return std::to_string(value); }, Int32Array, JsonString);
  wire += "}}";
  Write(directory / (std::string(name) + ".json"), wire);

  std::string context = "{\"schema\":\"xar.captured-target-land-supply.native-whole-context.v1\",\"case\":";
  JsonString(context, name);
  context += ",\"synthetic_fixture\":true,\"live_capture\":false,"
             "\"command_envelope_synthetic\":true,\"accepted_preview_synthetic\":true,"
             "\"input_memory_unchanged\":true,\"original_preview_fields_unchanged\":true,"
             "\"actual_target_arrival_observed\":false,\"actual_callback_observed\":false,"
             "\"full_target_rate_ready\":false,\"full_daily_supply_transition_ready\":false,"
             "\"full_monthly_ready\":false,\"supply_mutator_calls\":0,\"movement_mutator_calls\":0,"
             "\"fixture_subject_fleet_association_raw\":" + std::to_string(kFleet);
  context += ",\"native_commander_fallback_used\":";
  context += fixture.use_native_commander_fallback ? "true" : "false";
  context += ",\"counts\":{\"legacy_limit\":" + std::to_string(fixture.limit_calls) +
      ",\"legacy_usage\":" + std::to_string(fixture.usage_calls) +
      ",\"target_component_predicate\":" + std::to_string(fixture.component_predicate_calls) +
      ",\"target_component_reader\":" + std::to_string(fixture.component_reader_calls) +
      ",\"target_resupply_predicate\":" + std::to_string(fixture.resupply_calls) +
      ",\"present_fleet_predicate\":" + std::to_string(fixture.fleet_calls) + "},\"callbacks\":[";
  bool first = true;
  for (const auto &event : fixture.events) {
    if (!first) context += ',';
    first = false;
    context += "{\"callback\":"; JsonString(context, event.callback);
    context += ",\"requested_id\":" + std::to_string(event.requested_id) +
        ",\"province_id\":" + std::to_string(event.province_id);
    const auto boolean = [&](const char *key, bool value) {
      context += ",\""; context += key; context += "\":";
      context += value ? "true" : "false";
    };
    boolean("receiver_exact", event.receiver_exact); boolean("owner_exact", event.owner_exact);
    boolean("commander_exact", event.commander_exact); boolean("details_null", event.details_null);
    boolean("returned_bool", event.returned_bool); boolean("returned_null_output", event.returned_null_output);
    context += ",\"ordinal\":" + std::to_string(event.ordinal) + ",\"mode\":" + std::to_string(event.mode) +
        ",\"multiplier\":" + std::to_string(event.multiplier) +
        ",\"returned_raw\":" + (event.returned_raw ? std::to_string(*event.returned_raw) : "null") + '}';
  }
  context += "]}";
  Write(directory / (std::string(name) + "-native-context.json"), context);
}

void Scene(const std::filesystem::path &directory, std::int32_t scene) {
  Fixture fixture;
  const char *name = nullptr;
  switch (scene) {
  case 1: name = "01-at-sea-target-context"; break;
  case 2:
    name = "02-ready-false-and-zero"; fixture.component_applicable = false;
    fixture.resupply_eligible = false;
    fixture.bindings.current_land_supply_rate_bindings.read_province_component = nullptr;
    fixture.memory.Put(fixture.gain_slot, 0, std::int64_t{0}); break;
  case 3:
    name = "03-independent-component-failure"; fixture.component_output_missing = true; break;
  case 4:
    name = "04-independent-resupply-failure";
    fixture.bindings.current_land_resupply_bindings.is_resupply_eligible = nullptr; break;
  case 5:
    name = "05-absent-gain-resupply-false"; fixture.resupply_eligible = false;
    fixture.bindings.current_land_resupply_bindings.loaded_gain_raw = nullptr; break;
  case 6:
    name = "06-absent-gain-resupply-true";
    fixture.bindings.current_land_resupply_bindings.loaded_gain_raw = nullptr; break;
  case 7: name = "07-same-origin-target-copy"; fixture.same_origin_target = true; break;
  case 8:
    name = "08-legacy-omission-native-commander-context";
    fixture.use_native_commander_fallback = true;
    fixture.memory.Put(fixture.army, 0x120, std::int32_t{-1});
    fixture.bindings.current_land_supply_rate_bindings.enabled = false;
    fixture.bindings.current_land_resupply_bindings.enabled = false; break;
  default: throw std::runtime_error("only eight fresh target preview scenes exist");
  }
  const auto preview = fixture.Observe();
  const auto &target = preview.province_supply->target;
  if (scene == 8) {
    Check(!target.captured_target_land_supply_inputs_v1 && fixture.component_predicate_calls == 0 &&
              fixture.component_reader_calls == 0 && fixture.resupply_calls == 0,
          "disabled numerical bindings must preserve omission and native commander fallback");
  } else {
    Check(target.captured_target_land_supply_inputs_v1.has_value(),
          "actual whole preview reader did not attach target numerical sibling");
    const auto &inputs = *target.captured_target_land_supply_inputs_v1;
    Check(inputs.subject_army_id == kUnit && inputs.subject_carmy_id == kArmy &&
              inputs.owner_character_id == kOwner && inputs.province_id == fixture.TargetId(),
          "whole target numerical sibling lost same-preview subject/owner/target context");
    Check(fixture.component_predicate_calls == 1 &&
              fixture.component_reader_calls == (scene == 2 ? 0U : 1U) &&
              fixture.resupply_calls == (scene == 4 ? 0U : 1U),
          "new target observation callback count differs from the captured branches");
    Check(inputs.native_province_component_applicable == (scene != 2) &&
              inputs.province_component_observation_ready == (scene != 3) &&
              inputs.resupply_observation_ready == (scene != 4),
          "independent target predicate/readiness flags changed");
    if (scene == 3) {
      Check(!inputs.province_component_raw &&
                inputs.province_component_unavailable_reason == "native_target_province_component_output_unavailable",
            "component null output must remain null with its own reason");
    } else {
      Check(inputs.province_component_raw == (scene == 2 ? std::int64_t{0} : kComponent) &&
                !inputs.province_component_unavailable_reason,
            "signed target component or observed predicate-false0 was lost");
    }
    if (scene == 4) {
      Check(!inputs.native_resupply_eligible &&
                inputs.resupply_unavailable_reason == "native_target_resupply_predicate_unavailable",
            "absent resupply callback must preserve independent failure/null Boolean");
    } else {
      Check(inputs.native_resupply_eligible == (scene != 2 && scene != 5) && !inputs.resupply_unavailable_reason,
            "real target resupply true/false observation was lost");
    }
    Check(inputs.loaded_gain_raw == ((scene == 5 || scene == 6) ? std::optional<std::int64_t>{}
              : std::optional<std::int64_t>{scene == 2 ? std::int64_t{0} : kGain}),
          "independent optional loaded gain must retain zero or null without erasing predicates");
    if (scene == 3 || scene == 4) {
      Check(inputs.status == "partial" && !inputs.current_inputs_ready &&
                inputs.unavailable_reason == (scene == 3
                    ? "native_target_province_component_output_unavailable"
                    : "native_target_resupply_predicate_unavailable"),
            "independent target partial must not change available preview/legacy rows");
    } else {
      Check(inputs.status == "available" && inputs.current_inputs_ready && !inputs.unavailable_reason,
            "two independent observed target inputs remain ready even without loaded gain");
    }
  }
  Emit(directory, name, fixture, preview);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir",
          "usage: captured target whole native preview fixture --wire-dir FRESH_DIRECTORY");
    const std::filesystem::path directory(argv[2]);
    std::filesystem::create_directories(directory);
    for (std::int32_t scene = 1; scene <= 8; ++scene) Scene(directory, scene);
    std::cout << "captured target whole native preview fixture emitted8 response/context pairs\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
