#include "xar_bridge/ck3_12003_challenger_graph_readback.hpp"
#include "xar_bridge/ck3_12004_confucian_title_profile.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>

// Actual4 FIRST source fixture. The author did not compile or execute it.
// All observations below use synthetic owned memory and injected callbacks.
// ROOT must link this against its current actual4 runtime, without loading CK3.
namespace rt = xar::ck3_12003::religious_title;
namespace graph = xar::ck3_12003::challenger_graph;
namespace props = xar::ck3_12003::title_properties;
namespace laws = xar::ck3_12003::title_laws;
namespace profile = xar::ck3_12004::confucian_titles;
namespace actual = xar::ck3_12004;

namespace {
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, const T &value) {
  Require(offset + sizeof(value) <= bytes.size(), "synthetic write out of bounds");
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
void *Immediate(void *) { return nullptr; }
void *Top(void *character) { return character; }
struct World;
World *active = nullptr;
void *CurrentFaith(void *);
void *HeadTitle(void *);
void *Head(void *);

struct World {
  static constexpr std::uintptr_t base = 0x10000000;
  static constexpr std::uint32_t actor_id = 0x01000000;
  static constexpr std::uint32_t holder_id = 0x82000002;
  static constexpr std::uint32_t title_id = 0x81000001;
  static constexpr std::uint32_t faith_id = 107;
  std::array<std::byte, 0x80> character_storage{}, title_storage{}, faith_storage{};
  std::array<std::byte, 0x30> character_slots{}, title_slots{};
  std::array<std::byte, 108 * 0x10> faith_slots{};
  std::array<std::byte, 0x220> actor{}, holder{}, character_fallback{};
  std::array<std::byte, 0x400> title{}, title_fallback{}, faith{}, faith_fallback{};
  std::array<std::byte, 0x80> law{};
  std::string key = std::string(laws::kExpectedLawKey);
  std::array<void *, 1> law_slots{law.data()};
  std::array<graph::NativeRecord, 1> challengers{{{title_id, title_id}}};
  void *character_storage_pointer = character_storage.data();
  void *title_storage_pointer = title_storage.data();
  void *faith_storage_pointer = faith_storage.data();
  void *character_fallback_pointer = character_fallback.data();
  void *title_fallback_pointer = title_fallback.data();
  void *faith_fallback_pointer = faith_fallback.data();
  rt::Bindings titles = rt::BindImage(base, actual::kExecutableSha256);
  graph::Bindings bindings = graph::BindImage(base, actual::kExecutableSha256);
  xar::game::Snapshot frame{};

  World() {
    active = this;
    Require(titles.enabled && titles.properties.actual4, "actual4 title image admission");
    Require(bindings.enabled && bindings.titles.properties.actual4, "actual4 graph image admission");
    Require(titles.properties.primary_title_vtable_rva == profile::kCLandedTitlePrimaryVtableRva,
            "actual4 title vtable factory");
    Require(bindings.primary_faith_vtable_rva == profile::kCFaithPrimaryVtableRva,
            "actual4 Faith vtable factory");
    Require(reinterpret_cast<std::uintptr_t>(titles.character_faith) ==
            base + actual::religion::profile::kCharacterFaithRva, "actual4 context callback");
    Require(reinterpret_cast<std::uintptr_t>(titles.faith_head_title) == base + 0x2443F80,
            "actual4 head title callback");
    Require(reinterpret_cast<std::uintptr_t>(titles.faith_head) == base + 0x2439DF0,
            "actual4 head callback");
    Put(character_storage, 0x20, static_cast<void *>(character_slots.data()));
    Put(character_storage, 0x2C, std::int32_t{3});
    Put(character_slots, 8, static_cast<void *>(actor.data()));
    Put(character_slots, 2 * 0x10 + 8, static_cast<void *>(holder.data()));
    Put(actor, 0x18, actor_id);
    Put(actor, 0x1C, std::uint32_t{0x43686172});
    Put(holder, 0x18, holder_id);
    Put(holder, 0x1C, std::uint32_t{0x43686172});
    Put(title_storage, 0x20, static_cast<void *>(title_slots.data()));
    Put(title_storage, 0x2C, std::int32_t{3});
    Put(title_slots, 0x10 + 8, static_cast<void *>(title.data()));
    Put(faith_storage, 0x20, static_cast<void *>(faith_slots.data()));
    Put(faith_storage, 0x2C, std::int32_t{108});
    Put(faith_slots, faith_id * 0x10 + 8, static_cast<void *>(faith.data()));
    Put(faith, 0, base + profile::kCFaithPrimaryVtableRva);
    Put(faith, 8, faith_id);
    Put(faith, 0xC, graph::kFaithKindMagic);
    Put(faith, rt::kFaithHeadTitleIdOffset, title_id);
    Put(faith, graph::kFaithChallengersDataOffset, static_cast<void *>(challengers.data()));
    Put(faith, graph::kFaithChallengersCountOffset, std::int32_t{0});
    Put(title, 0, base + profile::kCLandedTitlePrimaryVtableRva);
    Put(title, 0x10, title_id);
    Put(title, 0x128, holder_id);
    Put(title, props::kNativeDestroyIfInvalidHeirOffset, std::uint8_t{1});
    Put(title, props::kNativeNoAutomaticClaimsOffset, std::uint8_t{1});
    Put(title, props::kNativeDefinitiveFormOffset, std::uint8_t{1});
    Put(title, props::kNativeAlwaysFollowsPrimaryHeirOffset, std::uint8_t{0});
    Put(law, 0, base + profile::kCLawPrimaryVtableRva);
    Put(law, 0x10, std::uint32_t{95});
    Put(law, 0x18, key.c_str());
    Put(law, 0x28, static_cast<std::uint64_t>(key.size()));
    Put(law, 0x30, static_cast<std::uint64_t>(key.size()));
    Put(law, 0x38, laws::kCLawDatabaseObjectMagic);
    Put(title, 0x228, static_cast<void *>(law_slots.data()));
    Put(title, 0x230, std::int32_t{1});
    Put(title, 0x234, std::int32_t{1});
    auto &h = titles.properties.title_holder;
    h.provinces.landed_title_storage_slot = &title_storage_pointer;
    h.character_storage_slot = &character_storage_pointer;
    h.character_fallback_slot = &character_fallback_pointer;
    h.immediate_liege = &Immediate;
    h.top_liege = &Top;
    titles.title_fallback_slot = &title_fallback_pointer;
    titles.faith_fallback_slot = &faith_fallback_pointer;
    titles.character_faith = &CurrentFaith;
    titles.faith_head_title = &HeadTitle;
    titles.faith_head = &Head;
    bindings.titles = titles;
    bindings.faith_storage_slot = &faith_storage_pointer;
    frame.date_raw = 53144712;
    frame.played_character_id = std::bit_cast<std::int32_t>(actor_id);
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
  }
};
void *CurrentFaith(void *character) {
  return character == active->actor.data() || character == active->holder.data()
      ? active->faith.data() : nullptr;
}
void *HeadTitle(void *faith) {
  return faith == active->faith.data() ? active->title.data() : nullptr;
}
void *Head(void *faith) {
  return faith == active->faith.data() ? active->holder.data() : nullptr;
}
} // namespace

int main() {
  try {
    Require(!rt::BindImage(World::base, "unsupported").enabled, "unknown image must reject");
    Require(!graph::BindImage(0, actual::kExecutableSha256).enabled, "zero base must reject");
    World w;
    rt::Observation title;
    Require(rt::Read(w.titles, w.frame, 9, title), "actual4 religious title read");
    Require(title.actual4 && title.head_title_full_id == World::title_id &&
            title.native_title_holder_full_id == World::holder_id, "complete high-generation graph");
    Require(title.title_properties.destroy_if_invalid_heir == true &&
            title.title_properties.no_automatic_claims == true &&
            title.title_properties.definitive_form == true &&
            title.title_properties.always_follows_primary_heir == false, "four native properties");
    Require(title.title_laws.native_count == 1 && title.title_laws.complete_laws &&
            title.title_laws.complete_laws->size() == 1 &&
            title.title_laws.temporal_head_of_faith_succession_law_member == true, "full native laws");
    const auto title_json = rt::Serialize(title);
    Require(title_json.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
            title_json.find(actual::kExecutableSha256) != std::string::npos &&
            title_json.find(profile::kFiniteMapSha256) != std::string::npos &&
            title_json.find("\"runtime_acceptance\":null") != std::string::npos, "actual4 title identity and credit");
    const std::array<std::uint32_t, 1> ids{World::faith_id};
    graph::Observation observation;
    Require(graph::Read(w.bindings, w.frame, 10, ids, observation), "actual4 known empty Faith107");
    Require(observation.actual4 && observation.graph_complete && observation.faiths &&
            observation.faiths->at(0).native_count == 0, "known empty complete collection");
    Put(w.faith, graph::kFaithChallengersCountOffset, std::int32_t{1});
    Require(graph::Read(w.bindings, w.frame, 11, ids, observation), "actual4 complete native pair");
    const auto &pair = observation.faiths->at(0).challengers->at(0);
    Require(pair.challenger_title.title_full_id == World::title_id &&
            pair.registered_sponsor_title.title_full_id == World::title_id &&
            pair.scope_matches_registered_pair == true, "self sponsor and current holder Faith scope");
    Require(graph::Serialize(observation).find(profile::kFiniteMapSha256) != std::string::npos,
            "actual4 challenger qualification");
    Put(w.title, 0, World::base + props::kCLandedTitlePrimaryVtableRva);
    Require(!rt::Read(w.titles, w.frame, 12, title) && title.actual4 && !title.graph_available,
            "old title vtable cannot qualify actual4");
    Put(w.title, 0, World::base + profile::kCLandedTitlePrimaryVtableRva);
    Put(w.law, 0, World::base + laws::kCLawPrimaryVtableRva);
    Require(!rt::Read(w.titles, w.frame, 13, title) && !title.title_laws.complete_laws,
            "old law vtable cannot qualify actual4");
    Put(w.law, 0, World::base + profile::kCLawPrimaryVtableRva);
    Put(w.faith, 0, World::base + graph::kCFaithPrimaryVtableRva);
    Require(!graph::Read(w.bindings, w.frame, 14, ids, observation) &&
            observation.actual4 && !observation.faiths, "old Faith vtable cannot qualify actual4");
    std::cout << "actual4_confucian_titles_binding_first_passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
