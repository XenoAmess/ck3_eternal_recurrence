#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12002_army.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace game = xar::game;
namespace native = xar::ck3_12002;

constexpr auto kUnitId = std::bit_cast<std::int32_t>(std::uint32_t{0x12000001});
constexpr auto kArmyId = std::bit_cast<std::int32_t>(std::uint32_t{0x34000002});
constexpr auto kOtherGenerationArmyId =
    std::bit_cast<std::int32_t>(std::uint32_t{0x35000002});
constexpr auto kRegimentId =
    std::bit_cast<std::int32_t>(std::uint32_t{0x56000003});

void Check(bool passed, const char *message) {
  if (!passed) throw std::runtime_error(message);
}

template <class T>
void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

struct Registry {
  std::array<std::byte, 0x30> header{};
  std::array<std::byte, 16 * 16> rows{};
  void *storage = header.data();

  Registry() {
    Put(header.data(), 0x20, static_cast<void *>(rows.data()));
    Put(header.data(), 0x2C, std::int32_t{16});
  }

  void Add(std::int32_t id, void *object) {
    const auto index = std::bit_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Put(rows.data(), static_cast<std::size_t>(index) * 16 + 8, object);
    Put(object, 0x10, id);
  }
};

struct NativeCalls {
  const void *army = nullptr;
  std::int32_t current = 0;
  std::int32_t maximum = 0;
  std::int32_t disembark = 0;
  bool receivers_match = true;
};

NativeCalls *g_calls = nullptr;

std::int32_t CurrentSoldiers(void *receiver, std::uint8_t flags) {
  if (g_calls == nullptr) return -1;
  ++g_calls->current;
  g_calls->receivers_match = g_calls->receivers_match &&
      receiver == static_cast<const std::byte *>(g_calls->army) + 0x38 &&
      flags == 0;
  return 20;
}

std::int32_t MaximumSoldiers(void *receiver) {
  if (g_calls == nullptr) return -1;
  ++g_calls->maximum;
  g_calls->receivers_match =
      g_calls->receivers_match && receiver == g_calls->army;
  return 40;
}

std::int32_t __fastcall DisembarkPenaltyDays(const void *receiver) {
  if (g_calls == nullptr) return 0;
  ++g_calls->disembark;
  if (receiver != g_calls->army) {
    g_calls->receivers_match = false;
    return 0;
  }
  // Exact .3 named core [0x24AA240, 0x24AA247): MOV EAX,[RCX+0x1D0]; RET.
  // RCX is the resolved CArmy. This stub neither clamps nor derives activity.
  std::int32_t result = 0;
  std::memcpy(&result, static_cast<const std::byte *>(receiver) + 0x1D0,
              sizeof(result));
  return result;
}

struct Fixture {
  Registry units;
  Registry armies;
  Registry regiments;
  std::array<std::byte, 0x200> unit{};
  std::array<std::byte, 0x300> army{};
  std::array<std::byte, 0x200> regiment{};
  std::array<std::int32_t, 1> regiment_ids{kRegimentId};
  NativeCalls calls;
  native::ArmyBindings bindings;

  explicit Fixture(std::int32_t days) {
    units.Add(kUnitId, unit.data());
    armies.Add(kArmyId, army.data());
    regiments.Add(kRegimentId, regiment.data());
    Put(unit.data(), 0x178, kArmyId);
    // The same numerical offset on the public CUnit must never supply this leaf.
    Put(unit.data(), 0x1D0, std::int32_t{777});
    Put(army.data(), 0x124, kUnitId);
    Put(army.data(), 0x38, static_cast<void *>(regiment_ids.data()));
    Put(army.data(), 0x40, std::int32_t{1});
    Put(army.data(), 0x44, std::int32_t{1});
    Put(army.data(), 0x1D0, days);
    Put(regiment.data(), 0x14, std::uint32_t{0x41725267});
    Put(regiment.data(), 0x38, std::int32_t{20});
    Put(regiment.data(), 0x3C, std::int32_t{40});
    Put(regiment.data(), 0x40, std::int64_t{4'000'000});

    calls.army = army.data();
    bindings.enabled = true;
    bindings.unit_storage_slot = &units.storage;
    bindings.internal_army_storage_slot = &armies.storage;
    bindings.regiment_storage_slot = &regiments.storage;
    bindings.get_army_current_soldiers = CurrentSoldiers;
    bindings.get_army_maximum_soldiers = MaximumSoldiers;
    bindings.current_disembark_penalty_enabled = true;
    bindings.get_army_disembark_penalty_days = DisembarkPenaltyDays;
  }

  std::vector<std::byte> Snapshot() const {
    std::vector<std::byte> bytes;
    const auto append = [&bytes](const auto &view) {
      const auto raw = std::as_bytes(std::span(view));
      bytes.insert(bytes.end(), raw.begin(), raw.end());
    };
    append(units.header);
    append(units.rows);
    append(armies.header);
    append(armies.rows);
    append(regiments.header);
    append(regiments.rows);
    append(unit);
    append(army);
    append(regiment);
    append(regiment_ids);
    return bytes;
  }
};

void AppendJsonString(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (char character : value) {
    const auto byte = static_cast<unsigned char>(character);
    switch (character) {
    case '"': out += "\\\""; break;
    case '\\': out += "\\\\"; break;
    case '\n': out += "\\n"; break;
    case '\r': out += "\\r"; break;
    case '\t': out += "\\t"; break;
    default:
      if (byte < 0x20) {
        out += "\\u00";
        out += hex[byte >> 4];
        out += hex[byte & 0x0F];
      } else {
        out += character;
      }
    }
  }
  out += '"';
}

void AppendInt32Array(std::string &out,
                      const std::vector<std::int32_t> &values) {
  out += '[';
  for (std::size_t i = 0; i < values.size(); ++i) {
    if (i != 0) out += ',';
    out += std::to_string(values[i]);
  }
  out += ']';
}

enum class CaseKind { available, invalid_army, type_unavailable };

std::string Produce(std::int32_t days, CaseKind kind) {
  Fixture fixture(days);
  if (kind == CaseKind::invalid_army) {
    // Keep CUnit+0x178 and its index intact; the actual full-ID resolver must
    // reject this occupied CArmy entry from a different generation.
    Put(fixture.army.data(), 0x10, kOtherGenerationArmyId);
  } else if (kind == CaseKind::type_unavailable) {
    // This additive leaf remains enabled. Only its typed native getter is absent.
    fixture.bindings.get_army_disembark_penalty_days = nullptr;
  }
  const auto before = fixture.Snapshot();
  const std::array<native::ArmyStrengthScope, 1> scope{
      native::ArmyStrengthScope{kUnitId, game::ArmyStrengthScopeRole::player, {}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  g_calls = &fixture.calls;
  const auto read_result =
      native::ReadArmyStrengthsForScope(fixture.bindings, scope, rows);
  g_calls = nullptr;

  Check(rows.size() == 1, "whole producer must return one scope row");
  Check(fixture.Snapshot() == before, "whole producer changed synthetic native memory");
  Check(fixture.calls.receivers_match, "native helper received a different receiver");
  const auto &row = rows.front();
  Check(row.army_id == kUnitId, "public full ID was not preserved");
  Check(row.scope_role == game::ArmyStrengthScopeRole::player,
        "player scope was not preserved");
  Check(row.native_army_resolution_v1.has_value(),
        "actual CUnit to CArmy resolver did not produce an observation");

  if (kind == CaseKind::invalid_army) {
    Check(read_result == game::ReadArmyStrengthsResult::partial,
          "invalid full-generation join must return partial");
    Check(!row.available && row.unavailable_reason == "native_carmy_not_found",
          "invalid full-generation join must fail the parent strength row");
    Check(!row.native_carmy_id_observable,
          "failed join must not publish a native CArmy identity");
    Check(!row.current_disembark_penalty_v1,
          "failed join must omit the disembark leaf");
    Check(fixture.calls.current == 0 && fixture.calls.maximum == 0 &&
              fixture.calls.disembark == 0,
          "failed join must not call fictive native helpers");
  } else {
    Check(read_result == game::ReadArmyStrengthsResult::available && row.available,
          "valid full-generation join must preserve available parent strength");
    Check(row.native_carmy_id_observable && row.native_carmy_id == kArmyId,
          "native full CArmy ID was not preserved");
    Check(row.regiment_count == 1 && row.current_soldiers == 20 &&
              row.maximum_soldiers == 40 && row.ai_base_power_raw == 4'000'000,
          "whole producer did not use actual regiment aggregation");
    Check(fixture.calls.current == 1 && fixture.calls.maximum == 1,
          "whole producer must call actual strength helpers once");
    Check(row.current_disembark_penalty_v1.has_value(),
          "enabled disembark leaf must be present for a valid backlink");
    const auto &leaf = *row.current_disembark_penalty_v1;
    if (kind == CaseKind::type_unavailable) {
      Check(!leaf.available && !leaf.remaining_days &&
                leaf.unavailable_reason == "disembark_getter_not_bound",
            "unbound typed getter must preserve leaf unavailability");
      Check(fixture.calls.disembark == 0,
            "unbound typed getter must not be called");
    } else {
      Check(leaf.available && leaf.remaining_days == days &&
                leaf.unavailable_reason.empty(),
            "native signed remaining days must be published unchanged");
      Check(fixture.calls.disembark == 1,
            "valid leaf must call the CArmy getter exactly once");
    }
  }

  std::string wire;
  game::AppendArmyStrengthV1(
      wire, row, [](auto value) { return std::to_string(value); },
      AppendInt32Array, AppendJsonString);
  return wire;
}

std::string ProduceWire() {
  std::string wire = "{\"schema_version\":1,\"samples\":{\"zero\":";
  wire += Produce(0, CaseKind::available);
  wire += ",\"negative\":";
  wire += Produce(-1, CaseKind::available);
  wire += ",\"nonstock\":";
  wire += Produce(34, CaseKind::available);
  wire += ",\"invalidArmy\":";
  wire += Produce(34, CaseKind::invalid_army);
  wire += ",\"typeUnavailable\":";
  wire += Produce(34, CaseKind::type_unavailable);
  wire += "}}\n";
  return wire;
}

void WriteWire(const std::filesystem::path &path, const std::string &wire) {
  if (!path.parent_path().empty())
    std::filesystem::create_directories(path.parent_path());
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  Check(output.is_open(), "cannot open native wire output");
  output.write(wire.data(), static_cast<std::streamsize>(wire.size()));
  output.close();
  Check(!output.fail(), "cannot finish native wire output");
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 3 || std::string_view(argv[1]) != "--emit-wire" ||
      std::string_view(argv[2]).empty()) {
    std::cerr << "usage: xar_bridge_ck3_12003_current_disembark_penalty_whole_test "
                 "--emit-wire <json-path>\n";
    return 2;
  }
  try {
    WriteWire(std::filesystem::path(argv[2]), ProduceWire());
    std::cout << "GREEN current_disembark_penalty_days_12003 whole producer fixture: 5 cases\n";
    return 0;
  } catch (const std::exception &error) {
    g_calls = nullptr;
    std::cerr << "RED current_disembark_penalty_days_12003 whole producer fixture: "
              << error.what() << '\n';
    return 1;
  }
}
