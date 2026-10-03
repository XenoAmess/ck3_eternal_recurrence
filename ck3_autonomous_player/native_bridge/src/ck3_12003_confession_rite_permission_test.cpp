#include "xar_bridge/ck3_12003_confession_rite_permission.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace f = xar::ck3_12003::religion::confession_permission;
namespace r = xar::ck3_12002::religion;
namespace {
int checks = 0;
void Check(bool value, const char *message) {
  ++checks; if (!value) throw std::runtime_error(message);
}
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void Definition(void *object, std::string &key) {
  if (key.size() <= 15) {
    std::memcpy(static_cast<std::byte *>(object) + 0x18, key.c_str(), key.size() + 1);
    Put(object, 0x30, std::size_t{15});
  } else {
    Put(object, 0x18, key.data()); Put(object, 0x30, key.size());
  }
  Put(object, 0x28, key.size()); Put(object, 0x38, std::uint32_t{0x4744624F});
}
struct Fixture {
  std::array<std::byte, 0xC0> actor{};
  std::array<std::byte, 0x10> rite{};
  std::array<std::byte, 0xF00> database{};
  std::array<std::byte, 0x40> other_definition{}, confession_definition{};
  std::string other_key{"other"}, confession_key{"tenet_confession"};
  std::array<const void *, 2> definitions{};
  void *database_pointer = database.data();
  f::CurrentContext current{};
  std::uint8_t state{};
  int native_state_calls = 0;
  Fixture() {
    current.available = true; current.capture_epoch = 81701;
    current.date_raw = 53236344; current.played_character_id = 29829; current.rite_id = 152;
    Put(actor.data(), 0x18, current.played_character_id);
    Put(actor.data(), r::kCharacterRiteIdOffset, *current.rite_id);
    Put(rite.data(), r::kReferenceIdentityOffset, *current.rite_id);
    Definition(other_definition.data(), other_key);
    Definition(confession_definition.data(), confession_key);
    definitions = {other_definition.data(), confession_definition.data()};
    Put(database.data(), 0xEF0, definitions.data());
    Put(database.data(), 0xEF8, std::int32_t{2});
    Put(database.data(), 0xEFC, std::int32_t{2});
  }
};
Fixture *active = nullptr;
void *CharacterRite(void *actor) {
  Check(actor == active->actor.data(), "actual supplied played actor is used");
  return active->rite.data();
}
std::uint8_t NativeState(void *rite, const void *definition) {
  Check(rite == active->rite.data(), "native state uses current Rite rather than Faith main Rite");
  Check(definition == active->confession_definition.data(), "native state uses exact fixed definition from loaded DB");
  ++active->native_state_calls; return active->state;
}
void Run(Fixture &fixture, const std::filesystem::path &output, const std::string &filename,
         bool available, int expected_state = -1) {
  active = &fixture;
  f::Bindings bindings{}; bindings.enabled = true;
  bindings.tenet_database_global = &fixture.database_pointer;
  bindings.source_main_rite_status = &NativeState;
  r::Bindings religion_bindings{}; religion_bindings.enabled = true;
  religion_bindings.character_rite = &CharacterRite;
  f::Terms terms{};
  const auto read = f::ReadPlayerConfessionRitePermission12003(bindings, religion_bindings,
      fixture.actor.data(), fixture.current, terms);
  Check(read == available && terms.available == available, "new production reader returns actual availability");
  Check(terms.capture_epoch == fixture.current.capture_epoch && terms.date_raw == fixture.current.date_raw &&
      terms.played_character_id == fixture.current.played_character_id && terms.rite_id == fixture.current.rite_id,
      "current owning Context frame and Rite are preserved");
  if (available) {
    Check(terms.unavailable_reason.empty(), "valid native state has no read failure");
    Check(terms.current_rite_status == expected_state, "raw native state including zero is preserved");
    Check(terms.has_at_least_permitted == (expected_state == 3 || expected_state == 4),
          "only native permitted or Core satisfies the closed threshold branch");
    Check(fixture.native_state_calls == 1, "current fixed state getter called once");
  } else {
    Check(!terms.unavailable_reason.empty(), "definition or native-state fault has its own read reason");
    Check(!terms.current_rite_status && !terms.has_at_least_permitted,
          "read fault cannot fabricate a legal native zero or false");
  }
  const auto body = f::SerializePlayerConfessionRitePermission12003(terms);
  const std::string envelope = "{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" +
      std::string(xar::ck3_12002::kExecutableSha256) + "\",\"player_confession_rite_permission\":" + body + "}";
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "synthetic-fixed-confession-permission-leaf", {}};
  const auto rendered = xar::game::RenderCrozierBuildIdentity(envelope, descriptor);
  Check(rendered.find(body) != std::string::npos &&
      rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos,
      "existing actual renderer preserves genuine production reader and serializer body");
  std::ofstream(output / filename, std::ios::binary) << rendered << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output argument");
    const std::filesystem::path output(argv[1]);
    for (std::uint8_t status = 0; status <= 4; ++status) {
      Fixture fixture; fixture.state = status;
      Run(fixture, output, "permission-state" + std::to_string(status) + ".json", true, status);
    }
    Fixture absent; Put(absent.database.data(), 0xEFC, std::int32_t{1});
    Run(absent, output, "permission-missing-definition.json", false);
    Check(absent.native_state_calls == 0, "absent definition never calls getter with invented object");
    Fixture key_fault; Put(key_fault.other_definition.data(), 0x38, std::uint32_t{0});
    Run(key_fault, output, "permission-key-fault.json", false);
    Check(key_fault.native_state_calls == 0, "actual production definition key-copy failure stays unavailable");
    Fixture invalid; invalid.state = 5;
    Run(invalid, output, "permission-invalid-state.json", false);
    Check(invalid.native_state_calls == 1, "out-of-range native state was actually returned");
    std::cout << "PASS cases=1 scenarios=8 checks=" << checks
              << " actual_reader_definition_key_serializer_renderer=true synthetic_callbacks=true"
                 " old_fixture_suite_abi_repeated=false game=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
