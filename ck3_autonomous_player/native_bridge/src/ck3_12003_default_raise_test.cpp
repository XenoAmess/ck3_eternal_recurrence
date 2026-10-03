#include "xar_bridge/ck3_12003_default_raise_mailbox.hpp"

#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12002;
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <typename T, std::size_t N>
void Store(std::array<std::byte, N> &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
struct Fixture {
  std::array<std::byte, 0x40> actor{};
  std::array<std::byte, 0x860> province{};
  xar::game::Snapshot snapshot{};
  MilitaryBindings bindings{};
  MilitaryWorldAccess world{};
  bool native_legal = false;
  bool missing_province = false;
  int constructors = 0, validators = 0, destructors = 0, submissions = 0;
};
Fixture *active = nullptr;
bool ReadSnapshot(void *context, xar::game::Snapshot &out) noexcept {
  out = static_cast<Fixture *>(context)->snapshot;
  return true;
}
void *ResolveCharacter(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  return id == 29829 ? f.actor.data() : nullptr;
}
void *ResolveProvince(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  return id == 2610 && !f.missing_province ? f.province.data() : nullptr;
}
void *Capital(void *character) {
  Require(character == active->actor.data(), "only current player is resolved");
  return active->province.data();
}
void *SelectDefault(void *character, void *capital, std::int32_t mode,
                    std::int32_t selected) {
  Require(character == active->actor.data() && capital == active->province.data()
              && mode == 0 && selected == -1,
          "same native default selector arguments as typed raise");
  return active->missing_province ? nullptr : capital;
}
void *Construct(void *command, std::int32_t actor, const void *entry) {
  ++active->constructors;
  const auto *values = static_cast<const std::int32_t *>(entry);
  Require(actor == 29829 && values[0] == 2610 && values[1] == -1,
          "actor-only normal raise command payload");
  std::memcpy(command, &active->bindings.raise_primary, sizeof(std::uintptr_t));
  std::memcpy(static_cast<std::byte *>(command) + 0x18,
              &active->bindings.raise_secondary, sizeof(std::uintptr_t));
  return command;
}
bool Validate(void *, void *reason) {
  ++active->validators;
  Require(reason == nullptr, "query final validation has no mutable reason context");
  return active->native_legal;
}
void *Destroy(void *command, std::int32_t flags) {
  ++active->destructors;
  Require(flags == 0, "temporary command destroyed without deleting stack storage");
  return command;
}
bool Submit(void *context, void *, std::uint32_t) noexcept {
  ++static_cast<Fixture *>(context)->submissions;
  return true;
}
void Prepare(Fixture &f) {
  active = &f;
  Store(f.actor, 0x18, std::int32_t{29829});
  Store(f.province, 0x10, std::int32_t{2610});
  Store(f.province, 0x85c, std::uint32_t{0x50726f76});
  f.snapshot.paused = true;
  f.snapshot.map_ready = true;
  f.snapshot.date_raw = 53238336;
  f.snapshot.has_played_character = true;
  f.snapshot.played_character_alive = true;
  f.snapshot.played_character_id = 29829;
  xar::game::ArmySnapshot raised{};
  raised.army_id = 83886367;
  raised.owner_character_id = 29829;
  raised.controllable = true;
  f.snapshot.player_armies.push_back(raised);
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
    Require(argc == 2, "native fixture JSON output path required");
    Fixture f;
    Prepare(f);
    const auto before = f.snapshot;
    PlayerDefaultRaiseObservationV1 observation{};
    Require(ReadPlayerDefaultRaiseV1(f.bindings, f.world, observation) ==
                PrewarDefaultMusterStatusV1::available &&
                observation.default_raise_legality_ready &&
                observation.actor.native_default_raise_legal == false,
            "native false is available despite an already raised army");
    const auto illegal = xar::ck3_12003::SerializePlayerDefaultRaiseV1(
        observation, 1, 11, before.date_raw);
    f.native_legal = true;
    Require(ReadPlayerDefaultRaiseV1(f.bindings, f.world, observation) ==
                PrewarDefaultMusterStatusV1::available &&
                observation.actor.native_default_raise_legal == true,
            "native true is observable without resolving a defender");
    const auto legal = xar::ck3_12003::SerializePlayerDefaultRaiseV1(
        observation, 2, 11, before.date_raw);
    Require(f.constructors == 2 && f.validators == 2 && f.destructors == 2 &&
                f.submissions == 0 && f.snapshot == before,
            "temporary commands released; no submit, time or army change");
    f.missing_province = true;
    Require(ReadPlayerDefaultRaiseV1(f.bindings, f.world, observation) ==
                PrewarDefaultMusterStatusV1::partial &&
                !observation.default_raise_legality_ready &&
                !observation.actor.native_default_raise_legal.has_value() &&
                f.constructors == 2,
            "missing native location yields partial null without construction");
    f.missing_province = false;
    f.snapshot.paused = false;
    Require(ReadPlayerDefaultRaiseV1(f.bindings, f.world, observation) ==
                PrewarDefaultMusterStatusV1::requires_paused && f.constructors == 2,
            "unpaused read cannot construct a native command");
    std::ofstream file(argv[1], std::ios::binary);
    file << "{\"illegal\":" << illegal << ",\"legal\":" << legal << "}\n";
    Require(static_cast<bool>(file), "production serializer fixture written");
    std::cout << "PASS: 4 actor-only production reader/serializer cases\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
