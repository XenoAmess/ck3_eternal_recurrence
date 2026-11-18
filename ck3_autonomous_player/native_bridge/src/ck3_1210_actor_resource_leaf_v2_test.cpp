// RAM formatter fixture and strict-source rejection cases. Owner compiles/runs.
// --emit partial|unavailable emits ORIGINAL C++ formatter bytes; it does not
// represent Game observation, deployment, installation or Runtime adoption.
#include "xar_bridge/ck3_1210_actor_resource_leaf_v2.hpp"
#include <bit>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string_view>
using namespace xar::ck3_1210;
namespace {
void Check(bool ok, const char *message) {
  if (!ok) { std::cerr << "FAIL " << message << '\n'; std::exit(1); }
}
ActorResourceLeafObservationV2 Ram() {
  ActorResourceLeafObservationV2 o{};
  o.exact_image_verified = o.application_main_observed = true;
  o.core_interval_verified = o.gold_interval_verified = true;
  o.before.clock = {123456, 4, true}; o.before.local_player_id = 7;
  o.before.map_ready = o.before.has_played_character = o.before.played_character_alive = true;
  o.before.played_character_id = std::bit_cast<std::int32_t>(0x81000001U);
  o.after = o.before; o.actor_character_id = o.before.played_character_id;
  o.personal_gold_before_raw = o.actor_gold_raw = o.personal_gold_after_raw = -500000;
  o.prestige_raw = (std::numeric_limits<std::int64_t>::min)();
  o.piety_raw = (std::numeric_limits<std::int64_t>::max)();
  o.unavailable_reason = {}; return o;
}
void Unavailable(const ActorResourceLeafObservationV2 &o) {
  const auto s = SerializeActorResourceLeafV2(o);
  Check(s.find("\"resources_available\":false") != std::string::npos &&
      s.find("\"personal_gold_interval\":null") != std::string::npos &&
      s.find("\"actor_character_id\":null") != std::string::npos &&
      s.find("\"status\":\"available\"") == std::string::npos,
      "inconsistent source cannot publish any available amount");
}
}
int main(int argc, char **argv) {
  if (argc == 3 && std::string_view(argv[1]) == "--emit") {
    const auto kind = std::string_view(argv[2]);
    Check(kind == "partial" || kind == "unavailable" || kind == "debt" || kind == "zero", "explicit RAM fixture kind required");
    auto observation = kind == "unavailable" ? ActorResourceLeafObservationV2{} : Ram();
    if(kind == "debt") {
      observation.prestige_raw = -200000;observation.piety_raw = -1;
    } else if(kind == "zero") {
      observation.personal_gold_before_raw = observation.actor_gold_raw = observation.personal_gold_after_raw = 0;
      observation.prestige_raw = observation.piety_raw = 0;
    }
    std::cout << SerializeActorResourceLeafCommandV2("ram-resource-leaf-v2",observation) << char(10);
    return 0;
  }
  const auto json = SerializeActorResourceLeafV2(Ram());
  Check(json.find("\"schema\":\"ck3_1210_actor_resource_leaf_v2\"") != std::string::npos &&
      json.find("\"raw\":-9223372036854775808,\"scale\":100000") != std::string::npos &&
      json.find("\"raw\":9223372036854775807,\"scale\":100000") != std::string::npos,
      "exact native signed64 extremes survive formatter");
  Check(json.find("\"renown\":{\"status\":\"unavailable\",\"amount\":null") != std::string::npos &&
      json.find("\"true_treasury\":{\"status\":\"unavailable\",\"amount\":null") != std::string::npos &&
      json.find("\"root_ready\":false,\"formal_action_ready\":false") != std::string::npos,
      "static getter candidates and personal gold never grant treasury/renown/action");
  for (int mutation = 0; mutation < 8; ++mutation) {
    auto o = Ram();
    switch (mutation) {
    case 0: o.personal_gold_after_raw = -500001; break;
    case 1: o.after.clock.date_raw++; break;
    case 2: o.after.played_character_id = 2; break;
    case 3: o.prestige_raw.reset(); break;
    case 4: o.application_main_observed = false; break;
    case 5: o.exact_image_verified = false; break;
    case 6: o.before.clock.paused = o.after.clock.paused = false; break;
    case 7: o.unavailable_reason = "original_failure"; break;
    }
    Unavailable(o);
  }
  for(const auto raw : {std::int64_t{0},std::int64_t{-1},std::int64_t{-500000}}) {
    auto o=Ram();o.personal_gold_before_raw=o.actor_gold_raw=o.personal_gold_after_raw=raw;
    o.prestige_raw=o.piety_raw=raw;
    const auto formatted=SerializeActorResourceLeafV2(o);
    Check(formatted.find("\"resources_available\":true")!=std::string::npos &&
        formatted.find("\"true_treasury\":{\"status\":\"unavailable\",\"amount\":null")!=std::string::npos,
        "zero/debt resource amounts remain observed while true treasury remains unknown");
  }
  ActorResourceLeafObservationV2 out = Ram();
  ActorResourceLeafSourceInputV2 input{};
  Check(!ReadActorResourceLeafV2(input, out) && !out.prestige_raw && !out.piety_raw &&
      out.unavailable_reason == "unsupported_image_identity", "empty input rejects before memory access");
  input.image_base = 0x140000000; input.game_version = kGameVersion;
  input.executable_sha256 = kExecutableSha256; input.adapter_id = kAdapterId;
  input.gold_bindings = BindPersonalGoldImageV1(input.image_base, input.executable_sha256);
  Check(!ReadActorResourceLeafV2(input, out) && out.exact_image_verified &&
      !out.application_main_observed && out.unavailable_reason == "application_main_owner_unavailable",
      "address binding alone never grants main custody or reads Game memory");
  input.gold_bindings.core.character_storage_slot = nullptr;
  Check(!ReadActorResourceLeafV2(input, out) && !out.exact_image_verified &&
      out.unavailable_reason == "image_core_binding_mismatch", "wrong-image actor store rejected");
  std::cout << "PASS resource leaf v2 RAM formatter and strict source boundaries\n";
}
