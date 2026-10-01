#include "xar_bridge/ck3_12002_prewar_muster.hpp"

#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12002;
template <typename T, std::size_t N>
void Store(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
template <typename T> T Load(void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<std::byte *>(object) + offset, sizeof(value));
  return value;
}
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Fixture {
  std::array<std::byte, 0x40> actor{}, defender{};
  std::array<std::byte, 0x860> actor_province{}, defender_province{};
  xar::game::Snapshot snapshot{};
  MilitaryBindings bindings{};
  MilitaryWorldAccess world{};
  bool missing_defender_location = false;
  bool submit_called = false;
  int constructors = 0, validators = 0, destructors = 0;
};
Fixture *active = nullptr;

bool ReadSnapshot(void *context, xar::game::Snapshot &output) noexcept {
  output = static_cast<Fixture *>(context)->snapshot;
  return true;
}
void *ResolveCharacter(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  if (id == 101) return f.actor.data();
  if (id == 202) return f.defender.data();
  return nullptr;
}
void *ResolveProvince(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  if (id == 701) return f.actor_province.data();
  if (id == 702) return f.defender_province.data();
  return nullptr;
}
void *Capital(void *character) {
  return character == active->actor.data() ? active->actor_province.data()
                                           : active->defender_province.data();
}
void *SelectDefault(void *character, void *capital, std::int32_t mode,
                    std::int32_t last) {
  Require(mode == 0 && last == -1, "native default selection arguments");
  Require(capital == Capital(character), "capital source");
  if (character == active->defender.data() &&
      active->missing_defender_location) return nullptr;
  return capital;
}
void *Construct(void *command, std::int32_t actor, const void *entry) {
  ++active->constructors;
  const auto *values = static_cast<const std::int32_t *>(entry);
  Require(values[0] == (actor == 101 ? 701 : 702) && values[1] == -1,
          "native one-entry raise payload");
  std::memcpy(command, &active->bindings.raise_primary, sizeof(std::uintptr_t));
  std::memcpy(static_cast<std::byte *>(command) + 0x18,
              &active->bindings.raise_secondary, sizeof(std::uintptr_t));
  std::memcpy(static_cast<std::byte *>(command) + 0x20, &actor, sizeof(actor));
  return command;
}
bool Validate(void *command, void *reason) {
  ++active->validators;
  Require(reason == nullptr, "query does not request mutable reason context");
  return Load<std::int32_t>(command, 0x20) == 101;
}
void *Destroy(void *command, std::int32_t flags) {
  Require(flags == 0, "temporary command never deleting stack storage");
  ++active->destructors;
  return command;
}
bool Submit(void *context, void *, std::uint32_t) noexcept {
  static_cast<Fixture *>(context)->submit_called = true;
  return true;
}

void Prepare(Fixture &f) {
  active = &f;
  Store(f.actor, 0x18, std::int32_t{101});
  Store(f.defender, 0x18, std::int32_t{202});
  Store(f.actor_province, 0x10, std::int32_t{701});
  Store(f.defender_province, 0x10, std::int32_t{702});
  Store(f.actor_province, 0x85c, std::uint32_t{0x50726f76});
  Store(f.defender_province, 0x85c, std::uint32_t{0x50726f76});
  f.snapshot.date_raw = 53220000;
  f.snapshot.paused = true;
  f.snapshot.map_ready = true;
  f.snapshot.has_played_character = true;
  f.snapshot.played_character_id = 101;
  f.snapshot.played_character_alive = true;
  f.bindings.enabled = true;
  f.bindings.raise_primary = 0x145345c0;
  f.bindings.raise_secondary = 0x14534658;
  f.bindings.get_character_capital = Capital;
  f.bindings.resolve_raise_province = SelectDefault;
  f.bindings.construct_raise = Construct;
  f.bindings.validate_raise = Validate;
  f.bindings.destroy_raise = Destroy;
  f.bindings.submit_context = &f;
  f.bindings.submit_copy = Submit;
  f.world.context = &f;
  f.world.read_snapshot = ReadSnapshot;
  f.world.resolve_character = ResolveCharacter;
  f.world.resolve_province = ResolveProvince;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Fixture fixture;
    Prepare(fixture);
    PrewarDefaultMusterObservationV1 output{};
    const PrewarDefaultMusterRequestV1 request{101, 202};
    Require(ReadPrewarDefaultMusterV1(fixture.bindings, fixture.world, request,
                                     output) ==
                PrewarDefaultMusterStatusV1::available,
            "both final legality observations available");
    Require(output.rows[0].native_default_raise_legal == true &&
                output.rows[1].native_default_raise_legal == false,
            "negative native legality remains a negative observation");
    Require(fixture.constructors == 2 && fixture.validators == 2 &&
                fixture.destructors == 2 && !fixture.submit_called,
            "both temporary commands released and no submission");
    Require(output.default_raise_legality_ready &&
                !output.hypothetical_raised_roster_ready &&
                !output.muster_time_ready && !output.future_supply_ready,
            "legality is not a full projected army forecast");
    const auto available = SerializePrewarDefaultMusterV1("fixture", 123, output);
    Require(available.find("\"native_default_raise_legal\":false") !=
                std::string::npos,
            "serialized false is not null");
    if (argc == 2) {
      std::ofstream file(argv[1], std::ios::binary);
      file << available << '\n';
      Require(static_cast<bool>(file), "fixture JSON output");
    }
    fixture.missing_defender_location = true;
    Require(ReadPrewarDefaultMusterV1(fixture.bindings, fixture.world, request,
                                     output) ==
                PrewarDefaultMusterStatusV1::partial &&
                output.rows[0].native_default_raise_legal == true &&
                !output.rows[1].native_default_raise_legal.has_value(),
            "missing defender retains independently useful actor legality");
    Require(SerializePrewarDefaultMusterV1("fixture", 123, output).find(
                "\"native_default_raise_legal\":null") != std::string::npos,
            "unavailable legality is null");
    fixture.snapshot.paused = false;
    const int calls_before_unpaused = fixture.constructors;
    Require(ReadPrewarDefaultMusterV1(fixture.bindings, fixture.world, request,
                                     output) ==
                PrewarDefaultMusterStatusV1::requires_paused &&
                fixture.constructors == calls_before_unpaused,
            "unpaused query does not construct");
    fixture.snapshot.paused = true;
    fixture.snapshot.played_character_id = 303;
    Require(ReadPrewarDefaultMusterV1(fixture.bindings, fixture.world, request,
                                     output) ==
                PrewarDefaultMusterStatusV1::invalid_request,
            "actor must be current player");
    std::cout << "PASS: native default-muster producer and wire\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
