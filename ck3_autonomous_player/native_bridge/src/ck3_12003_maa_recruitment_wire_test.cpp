#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12002_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12003_maa_recruitment.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kUnit1 = 301989997;
constexpr std::int32_t kUnit2 = 184549452;
constexpr std::array<std::int64_t, 10> kQuantity10Raw{
    125000, 0, 750000, 0, 0, 0, 0, 910000, -25000, 0};
constexpr std::array<std::int64_t, 10> kQuantity20Raw{
    350000, 0, 900000, 0, 0, 0, 0, 1200000, -10000, 0};

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <typename T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Require(offset + sizeof(T) <= N, "fixture backing range");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
template <typename T> T Load(const void *object, std::size_t offset) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(result));
  return result;
}

struct Backing {
  std::array<std::byte, 0x200> owner{};
  std::array<std::byte, 0x80> character_storage{};
  std::array<std::byte, 0x80> unit_storage{};
  std::array<std::byte, 0x180> unit1{}, unit2{};
  std::array<std::byte, 0x80> registry{}, mangonel{}, onager{};
  std::vector<std::byte> character_rows{static_cast<std::size_t>(kOwner + 1) * 16};
  std::vector<std::byte> unit_rows{110 * 16};
  std::array<void *, 2> types{};
  void *character_slot = character_storage.data();
  void *unit_slot = unit_storage.data();
  void *registry_slot = registry.data();

  Backing() {
    Store(owner, 0x18, kOwner);
    Store(owner, 0x1C, std::uint32_t{0x43686172});
    Store(character_storage, 0x20, character_rows.data());
    Store(character_storage, 0x2C, kOwner + 1);
    void *owner_pointer = owner.data();
    std::memcpy(character_rows.data() + static_cast<std::size_t>(kOwner) * 16 + 8,
                &owner_pointer, sizeof(owner_pointer));
    Store(unit_storage, 0x20, unit_rows.data());
    Store(unit_storage, 0x2C, std::int32_t{110});
    for (const auto entry : {std::pair{kUnit1, unit1.data()},
                             std::pair{kUnit2, unit2.data()}}) {
      std::memcpy(entry.second + 0x10, &entry.first, sizeof(entry.first));
      std::memcpy(entry.second + 0x174, &kOwner, sizeof(kOwner));
      void *pointer = entry.second;
      const auto index = static_cast<std::uint32_t>(entry.first) & 0xFFFFFFu;
      std::memcpy(unit_rows.data() + static_cast<std::size_t>(index) * 16 + 8,
                  &pointer, sizeof(pointer));
    }
    const auto init_type = [](auto &type, const std::string &key,
                              std::int32_t index, std::int32_t chunk) {
      Store(type, 0x10, index);
      std::memcpy(type.data() + 0x18, key.data(), key.size());
      Store(type, 0x28, static_cast<std::uint32_t>(key.size()));
      Store(type, 0x30, std::uint64_t{15});
      Store(type, 0x38, std::uint32_t{0x4744624F});
      Store(type, 0x70, chunk);
    };
    init_type(mangonel, "mangonel", 7, 10);
    init_type(onager, "onager", 4, 20);
    types = {mangonel.data(), onager.data()};
    Store(registry, 0x50, types.data());
    Store(registry, 0x5C, std::int32_t{2});
  }
};

struct Observations {
  Backing *backing = nullptr;
  bool denied_case = false;
  int validator_calls = 0;
  int quote_calls = 0;
};
Observations observed;

bool Validator(const void *command, void *reason) {
  Require(reason == nullptr, "CanCreate reason must be null");
  Require(reinterpret_cast<std::uintptr_t>(command) % 8 == 0,
          "regular56B caller-local alignment");
  Require(Load<std::int32_t>(command, 0x20) == 1, "regular creation kind");
  Require(Load<std::int32_t>(command, 0x24) == -1, "personal title default");
  Require(Load<std::int32_t>(command, 0x28) == kOwner, "regular CanCreate owner");
  const auto index = Load<std::int32_t>(command, 0x2C);
  Require(index == 7 || index == 4, "regular CanCreate native type index");
  Require(Load<std::int32_t>(command, 0x30) == -1, "native default quantity");
  Require(Load<std::uint8_t>(command, 0x34) == 1, "native pay-cost default");
  ++observed.validator_calls;
  return !observed.denied_case;
}
xar::ck3_12003::NativeMaaCost80 *Quote(
    const void *type, xar::ck3_12003::NativeMaaCost80 *output,
    const void *owner, std::int64_t fixed_quantity, bool title_scope) {
  Require(owner == observed.backing->owner.data(), "regular quote owner identity");
  Require(!title_scope, "regular personal final-charge title scope false");
  const bool first_type = type == observed.backing->mangonel.data();
  Require(first_type || type == observed.backing->onager.data(),
          "regular quote native Type identity");
  Require(fixed_quantity == (first_type ? 1000000 : 2000000),
          "actual Type70 default quantity Q100000 argument");
  ++observed.quote_calls;
  if (observed.denied_case && !first_type) return nullptr;
  // Fixed callback observations, no native price calculation is mirrored.
  output->resources_raw = first_type ? kQuantity10Raw : kQuantity20Raw;
  return output;
}

void AppendJsonString(std::string &out, std::string_view value) {
  out += '"';
  for (const char ch : value) {
    if (ch == '"' || ch == '\\') out += '\\';
    Require(static_cast<unsigned char>(ch) >= 32, "fixture JSON control byte");
    out += ch;
  }
  out += '"';
}
void AppendIds(std::string &out, const std::vector<std::int32_t> &ids) {
  out += '[';
  bool first = true;
  for (auto id : ids) {
    if (!first) out += ',';
    first = false;
    out += std::to_string(id);
  }
  out += ']';
}

std::vector<xar::game::ArmyStrengthSnapshot> BaselineRows() {
  std::vector<xar::game::ArmyStrengthSnapshot> rows;
  for (const auto unit_id : {kUnit1, kUnit2}) {
    xar::game::ArmyStrengthSnapshot row;
    row.army_id = unit_id;
    row.available = true;
    row.native_carmy_id_observable = true;
    row.native_carmy_id = unit_id == kUnit1 ? 201326670 : 167772208;
    row.scope_role = xar::game::ArmyStrengthScopeRole::player;
    row.war_ids = {117440524};
    row.regiment_count = 1;
    row.current_soldiers = 100;
    row.maximum_soldiers = 100;
    row.ai_base_power_raw = 10'000'000;
    row.native_owner_recall_inputs_v1.emplace();
    row.native_owner_recall_inputs_v1->available = true;
    xar::game::BattleNativeOwnerRecallOwnerInputsV1 owner;
    owner.owner_character_id = kOwner;
    row.native_owner_recall_inputs_v1->owners_in_stored_order.push_back(owner);
    rows.push_back(std::move(row));
  }
  return rows;
}

std::string RunCase(bool denied_case) {
  Backing backing;
  observed = {};
  observed.backing = &backing;
  observed.denied_case = denied_case;
  constexpr std::uintptr_t base = 0x140000000;
  auto adapter = xar::game::BindCk3_12003AdapterImage(
      base, xar::ck3_12003::kExecutableSha256);
  auto &bindings = adapter.native_maa_recruitment;
  Require(bindings.enabled, "actual .3 factory enabled regular binding");
  Require(reinterpret_cast<std::uintptr_t>(bindings.type_registry_slot) ==
              base + 0x5C67558, "actual Type registry slot");
  Require(reinterpret_cast<std::uintptr_t>(bindings.regular_personal_can_create) ==
              base + 0x296F9F0, "actual regular CanCreate binding");
  Require(reinterpret_cast<std::uintptr_t>(bindings.regular_final_raw_quote) ==
              base + 0x30BCE20, "actual five-argument regular quote binding");
  bindings.character_storage_slot = &backing.character_slot;
  bindings.public_unit_storage_slot = &backing.unit_slot;
  bindings.type_registry_slot = &backing.registry_slot;
  bindings.regular_personal_can_create = Validator;
  bindings.regular_final_raw_quote = Quote;
  auto rows = BaselineRows();
  xar::game::AttachNativeMaaRecruitmentInputsToArmyRowsV1(bindings, rows);
  Require(observed.validator_calls == 2 && observed.quote_calls == 2,
          "same-owner row cache avoids repeated native calls");
  Require(rows[0].native_maa_recruitment_inputs_v1 ==
              rows[1].native_maa_recruitment_inputs_v1, "owner-local same query cache");
  const auto &block = *rows[0].native_maa_recruitment_inputs_v1;
  Require(block.command_class == "CCreateMAARegimentCommand" &&
              block.creation_scope == "regular_personal" &&
              block.title_id == -1 && block.requested_quantity == -1 && block.pay_cost,
          "true regular personal command identity/defaults");
  Require(block.owner_character_id == kOwner && block.catalog_observed,
          "generation-valid native owner/catalog");
  Require(block.types_in_native_order.size() == 2 &&
              block.types_in_native_order[0].type_key == "mangonel" &&
              block.types_in_native_order[1].type_key == "onager",
          "native catalog order");
  Require(block.missing_type_keys.size() == 7, "observed missing stock keys only");
  Require(block.status == (denied_case ? "partial" : "available"),
          "regular actual aggregate availability");
  const auto &first = block.types_in_native_order[0];
  const auto &second = block.types_in_native_order[1];
  Require(first.can_create == !denied_case && second.can_create == !denied_case,
          "native regular false remains an observed value");
  Require(first.effective_quantity == 10 && second.effective_quantity == 20,
          "native Type70 effective quantity survives");
  Require(first.inputs_ready && first.regular_personal_quote.resources_raw == kQuantity10Raw,
          "ordinary inputs remain ready with native false");
  if (denied_case) {
    Require(!second.inputs_ready &&
                !second.regular_personal_quote.resources_raw.has_value() &&
                second.regular_personal_quote.status == "unavailable",
            "failed native output identity retains typed unavailable quote");
  } else {
    Require(second.inputs_ready && second.regular_personal_quote.resources_raw == kQuantity20Raw,
            "true regular personal final-charge quote");
  }
  std::string wire = "{\"name\":\"";
  wire += denied_case ? "regular_native_false_and_quote_unavailable" : "regular_native_allowed";
  wire += "\",\"validator_calls\":" + std::to_string(observed.validator_calls);
  wire += ",\"quote_calls\":" + std::to_string(observed.quote_calls);
  wire += ",\"rows\":[";
  bool first_row = true;
  for (const auto &row : rows) {
    if (!first_row) wire += ',';
    first_row = false;
    xar::game::AppendArmyStrengthV1(wire, row,
        [](auto value) { return std::to_string(value); }, AppendIds, AppendJsonString);
  }
  wire += "]}";
  return wire;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one wire output path required");
    std::string wire = "{\"bounded_cases\":2,\"cases\":[";
    wire += RunCase(false);
    wire += ',';
    wire += RunCase(true);
    wire += "]}\n";
    std::ofstream out(argv[1], std::ios::binary);
    Require(static_cast<bool>(out), "wire output open");
    out << wire;
    Require(static_cast<bool>(out), "wire output write");
    std::cout << "GREEN: 2 NEW readonly production row publisher cases\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
