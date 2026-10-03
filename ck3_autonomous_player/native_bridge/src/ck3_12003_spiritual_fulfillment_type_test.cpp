#include "xar_bridge/ck3_12003_spiritual_fulfillment_type.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace f = xar::ck3_12003::religion::fulfillment_type;
namespace {
int checks = 0;
void Check(bool condition, const char *message) {
  ++checks; if (!condition) throw std::runtime_error(message);
}
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
struct Fixture {
  std::array<std::byte, 0x40> actor{}, type{};
  std::byte database{};
  void *database_pointer = &database;
  std::string key;
  f::CurrentContext current{};
  int getter_calls = 0;
  explicit Fixture(std::string text) : key(std::move(text)) {
    current.available = true; current.capture_epoch = 93;
    current.date_raw = 53175816; current.played_character_id = 0x03000004;
    current.faith_key = "catholic"; current.spiritual_fulfillment_raw = 500000;
    Put(actor.data(), 0x18, current.played_character_id);
    if (key.size() <= 15) {
      std::memcpy(type.data() + 0x18, key.c_str(), key.size() + 1);
      Put(type.data(), 0x30, std::size_t{15});
    } else {
      Put(type.data(), 0x18, key.data()); Put(type.data(), 0x30, key.size());
    }
    Put(type.data(), 0x28, key.size());
  }
};
Fixture *active = nullptr;
void *TypeForCharacter(void *database, void *actor) {
  Check(database == &active->database && actor == active->actor.data(),
        "existing getter receives actual supplied database and player pointer");
  ++active->getter_calls; return active->type.data();
}
void Run(Fixture &fixture, const std::filesystem::path &output, const char *filename, bool christian) {
  active = &fixture;
  f::Bindings bindings{}; bindings.enabled = true;
  bindings.database_slot = &fixture.database_pointer;
  bindings.type_for_character = &TypeForCharacter;
  // Other progress arithmetic callbacks are not used by this type reader.
  f::Type result{};
  Check(f::ReadPlayerSpiritualFulfillmentType12003(bindings, fixture.actor.data(), fixture.current, result),
        "actual unique production reader completed");
  Check(result.available && result.unavailable_reason.empty(), "valid type read remains available");
  Check(result.spiritual_fulfillment_type_key == fixture.key &&
      result.has_christian_fulfillment_type == christian, "copied stable key determines Christian condition, including legal false");
  Check(result.capture_epoch == fixture.current.capture_epoch && result.date_raw == fixture.current.date_raw &&
      result.played_character_id == fixture.current.played_character_id, "existing current-context frame copied unchanged");
  Check(fixture.getter_calls == 1, "existing type getter called once; no old progress/tenet/DLC fixture");
  const auto body = f::SerializePlayerSpiritualFulfillmentType12003(result);
  const std::string envelope = "{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" +
      std::string(xar::ck3_12002::kExecutableSha256) + "\",\"player_spiritual_fulfillment_type\":" + body + "}";
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "synthetic-new-type-leaf", {}};
  const auto rendered = xar::game::RenderCrozierBuildIdentity(envelope, descriptor);
  Check(rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(body) != std::string::npos, "actual existing renderer retains genuine unique leaf body");
  std::ofstream(output / filename, std::ios::binary) << rendered << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output path argument");
    const std::filesystem::path output(argv[1]);
    Fixture christian{std::string(f::kChristianType)};
    Run(christian, output, "type-christian-heap.json", true);
    Fixture other{"other"};
    Run(other, output, "type-other-inline.json", false);
    std::cout << "PASS cases=1 scenarios=2 checks=" << checks
              << " actual_reader_serializer_renderer=true synthetic_native_callbacks=true"
                 " progress_tenet_dlc_tests_repeated=false game=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
