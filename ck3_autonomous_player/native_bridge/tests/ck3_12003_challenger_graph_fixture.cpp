#include "xar_bridge/ck3_12003_challenger_graph_readback.hpp"
#include <array>
#include <bit>
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>

// Synthetic owned bytes only. These focused tests execute the production reader
// and serializer without any game process or runtime business acceptance.
namespace cg = xar::ck3_12003::challenger_graph;
namespace props = xar::ck3_12003::title_properties;
namespace laws = xar::ck3_12003::title_laws;
namespace {
unsigned checks = 0;
void Check(bool value) {
  ++checks;
  if (!value) throw std::runtime_error("check failed: " + std::to_string(checks));
}
template <class T, std::size_t N> void Put(std::array<std::byte, N> &b, std::size_t at, T value) {
  Check(at + sizeof(value) <= b.size()); std::memcpy(b.data() + at, &value, sizeof(value));
}
struct Fixture;
Fixture *active = nullptr;
void *CharacterFaith(void *);
struct Fixture {
  static constexpr std::uintptr_t base = 0x10000000;
  static constexpr std::uint32_t actor_id = 0x81000000, holder_id = 0x82000002;
  static constexpr std::uint32_t first_faith = 0, second_faith = 0xAB000003;
  static constexpr std::uint32_t first_title = 0x81000001, second_title = 0x02000002;
  std::array<std::byte, 0x80> characters{}, titles{}, faith_storage{};
  std::array<std::byte, 0x30> character_slots{}, title_slots{};
  std::array<std::byte, 0x40> faith_slots{};
  std::array<std::byte, 0x220> actor{}, holder{}, character_fallback{};
  std::array<std::byte, 0x400> faith_a{}, faith_b{}, faith_fallback{}, title_a{}, title_b{}, title_fallback{};
  std::array<std::byte, 0x80> law{}, definition{};
  std::array<void *, 1> law_slots{};
  std::array<cg::NativeRecord, 2> records{{{first_title, first_title}, {second_title, first_title}}};
  std::string key = std::string(laws::kExpectedLawKey);
  void *characters_pointer = characters.data(), *titles_pointer = titles.data(), *faith_storage_pointer = faith_storage.data();
  void *character_fallback_pointer = character_fallback.data(), *title_fallback_pointer = title_fallback.data();
  void *faith_fallback_pointer = faith_fallback.data();
  cg::Bindings bindings{};
  xar::game::Snapshot frame{};
  bool holder_moved = false, getter_fallback = false, mutate_record = false, mutate_property = false;
  unsigned getter_calls = 0;
  Fixture() {
    active = this;
    Put(characters, 0x20, static_cast<void *>(character_slots.data())); Put(characters, 0x2C, std::int32_t{3});
    Put(character_slots, 8, static_cast<void *>(actor.data())); Put(character_slots, 0x28, static_cast<void *>(holder.data()));
    Put(actor, 0x18, actor_id); Put(actor, 0x1C, std::uint32_t{0x43686172});
    Put(holder, 0x18, holder_id); Put(holder, 0x1C, std::uint32_t{0x43686172});
    Put(titles, 0x20, static_cast<void *>(title_slots.data())); Put(titles, 0x2C, std::int32_t{3});
    Put(title_slots, 0x18, static_cast<void *>(title_a.data())); Put(title_slots, 0x28, static_cast<void *>(title_b.data()));
    Put(faith_storage, 0x20, static_cast<void *>(faith_slots.data())); Put(faith_storage, 0x2C, std::int32_t{4});
    Put(faith_slots, 8, static_cast<void *>(faith_a.data())); Put(faith_slots, 0x38, static_cast<void *>(faith_b.data()));
    for (auto *f : {&faith_a, &faith_b}) {
      Put(*f, 0, base + cg::kCFaithPrimaryVtableRva); Put(*f, 0x0C, cg::kFaithKindMagic);
      Put(*f, 0xCC, std::int32_t{0}); Put(*f, 0xC8, std::int32_t{-700}); // Unqualified capacity is never read.
    }
    Put(faith_a, 8, first_faith); Put(faith_b, 8, second_faith);
    Put(faith_a, 0xC0, static_cast<void *>(records.data())); Put(faith_a, 0xCC, std::int32_t{1});
    for (auto *t : {&title_a, &title_b}) {
      Put(*t, 0, base + props::kCLandedTitlePrimaryVtableRva);
      Put(*t, 0x48, static_cast<void *>(definition.data()));
      Put(*t, props::kNativeDestroyIfInvalidHeirOffset, std::uint8_t{1});
      Put(*t, props::kNativeNoAutomaticClaimsOffset, std::uint8_t{1});
      Put(*t, props::kNativeDefinitiveFormOffset, std::uint8_t{1});
      Put(*t, props::kNativeAlwaysFollowsPrimaryHeirOffset, std::uint8_t{1});
      Put(*t, 0x230, std::int32_t{0}); Put(*t, 0x234, std::int32_t{0});
    }
    Put(definition, 0x64, std::int32_t{3});
    Put(title_a, 0x10, first_title); Put(title_b, 0x10, second_title);
    Put(title_a, 0x128, holder_id); Put(title_b, 0x128, actor_id);
    Put(law, 0, base + laws::kCLawPrimaryVtableRva); Put(law, 0x10, std::uint32_t{27});
    Put(law, 0x18, key.c_str()); Put(law, 0x28, static_cast<std::uint64_t>(key.size()));
    Put(law, 0x30, static_cast<std::uint64_t>(key.size())); Put(law, 0x38, laws::kCLawDatabaseObjectMagic);
    law_slots[0] = law.data(); Put(title_a, 0x228, static_cast<void *>(law_slots.data()));
    Put(title_a, 0x230, std::int32_t{1}); Put(title_a, 0x234, std::int32_t{1});
    bindings.enabled = true; bindings.titles.enabled = true; bindings.titles.properties.enabled = true;
    bindings.titles.properties.image_base = base;
    auto &h = bindings.titles.properties.title_holder;
    h.enabled = true; h.provinces.enabled = true; h.provinces.landed_title_storage_slot = &titles_pointer;
    h.character_storage_slot = &characters_pointer; h.character_fallback_slot = &character_fallback_pointer;
    bindings.titles.title_fallback_slot = &title_fallback_pointer;
    bindings.titles.faith_fallback_slot = &faith_fallback_pointer;
    bindings.titles.character_faith = &CharacterFaith; bindings.faith_storage_slot = &faith_storage_pointer;
    frame.date_raw = 720123; frame.played_character_id = std::bit_cast<std::int32_t>(actor_id);
    frame.paused = frame.map_ready = frame.has_played_character = frame.played_character_alive = true;
  }
};
void *CharacterFaith(void *character) {
  ++active->getter_calls;
  if (active->mutate_record && active->getter_calls == 1) active->records[0].sponsor_title_full_id = UINT32_MAX;
  if (active->mutate_property && active->getter_calls == 2)
    Put(active->title_a, props::kNativeDefinitiveFormOffset, std::uint8_t{0});
  if (active->getter_fallback) return active->faith_fallback.data();
  if (character == active->holder.data()) return active->holder_moved ? active->faith_b.data() : active->faith_a.data();
  if (character == active->actor.data()) return active->faith_a.data();
  return nullptr;
}
bool Read(Fixture &f, cg::Observation &o) {
  const std::array ids{Fixture::first_faith, Fixture::second_faith};
  return cg::Read(f.bindings, f.frame, 9, ids, o);
}
void Unknown(const cg::Observation &o) {
  Check(!o.available && !o.graph_complete && !o.faiths);
  Check(cg::Serialize(o).find("\"faiths\":null") != std::string::npos);
}
void ParserCases() {
  cg::Request request;
  Check(cg::ParseRequest(R"({"type":"execute_step","expected_snapshot_revision":7,"faith_full_ids":[0,2868903939]})", request));
  Check(request.expected_snapshot_revision == 7 && request.faith_count == 2 && request.faith_full_ids[0] == 0);
  Check(cg::ParseRequest(R"({"expected_snapshot_revision":18446744073709551615,"faith_full_ids":[4294967294]})", request));
  Check(cg::ParseRequest(R"({"expected_revision":7,"faith_\u0066ull_ids":[0]})", request));
  for (const auto invalid : {
      R"({"expected_snapshot_revision":7,"faith_\full_ids":[0]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[0,0]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[4294967295]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[4294967296]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[-1]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[1.0]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[1e0]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[true]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":["0"]})",
      R"({"expected_snapshot_revision":7,"nested":{"faith_full_ids":[0]}})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[0],"faith_\u0066ull_ids":[1]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[0,1,2,3,4,5,6,7,8]})",
      R"({"expected_snapshot_revision":0,"faith_full_ids":[0]})",
      R"({"expected_snapshot_revision":7,"expected_revision":8,"faith_full_ids":[0]})",
      R"({"expected_snapshot_revision":7,"faith_full_ids":[0]}garbage)"}) {
    Check(!cg::ParseRequest(invalid, request)); Check(request.faith_count == 0);
  }
}
} // namespace
int main(int argc, char **argv) {
  ParserCases();
  if (argc > 2) {
    std::ifstream source(argv[2], std::ios::binary);
    Check(source.good());
    const std::string packet((std::istreambuf_iterator<char>(source)), std::istreambuf_iterator<char>());
    cg::Request request;
    Check(cg::ParseRequest(packet, request));
    Check(request.expected_snapshot_revision == 7 && request.faith_count == 2);
    Check(request.faith_full_ids[0] == Fixture::first_faith && request.faith_full_ids[1] == Fixture::second_faith);
  }
  Check(!cg::BindImage(Fixture::base, "old-or-wrong").enabled);
  Check(!cg::BindImage(0, xar::ck3_12003::kExecutableSha256).enabled);
  {
    Fixture f; cg::Observation o; Check(Read(f, o));
    Check(o.available && o.graph_complete && o.faiths->size() == 2);
    const auto &a = o.faiths->at(0), &b = o.faiths->at(1);
    Check(a.native_count == 1 && a.complete_native_challenger_title_ids->at(0) == Fixture::first_title);
    Check(b.native_count == 0 && b.challengers->empty() && b.complete_native_challenger_title_ids->empty());
    const auto &c = a.challengers->at(0);
    Check(c.challenger_title.holder_character_full_id == Fixture::holder_id);
    Check(c.registered_sponsor_title.title_full_id == Fixture::first_title);
    Check(c.scope_sponsor_title.title_full_id == Fixture::first_title && c.scope_matches_registered_pair == true);
    Check(c.scope_lookup_faith_full_id == 0U && c.scope_lookup_complete);
    Check(c.challenger_title.laws.temporal_head_of_faith_succession_law_member == true);
    if (argc > 1) {
      std::filesystem::create_directories(argv[1]);
      std::ofstream out(std::filesystem::path(argv[1]) / "complete-self-sponsor.json", std::ios::binary);
      out << cg::Serialize(o); Check(out.good());
    }
  }
  {
    Fixture f; f.holder_moved = true; cg::Observation o; Check(Read(f, o));
    const auto &c = o.faiths->at(0).challengers->at(0);
    Check(c.registered_sponsor_title.title_full_id == Fixture::first_title);
    Check(c.scope_lookup_faith_full_id == Fixture::second_faith && c.scope_lookup_faith_matches_collection == false);
    Check(c.scope_matches_registered_pair == false && c.scope_sponsor_title.title_absent == true);
    Check(!c.scope_sponsor_title.title_full_id && c.scope_lookup_native_count == 0);
    if (argc > 1) {
      std::ofstream out(std::filesystem::path(argv[1]) / "old-owner-scope-mismatch.json", std::ios::binary);
      out << cg::Serialize(o); Check(out.good());
    }
  }
  {
    Fixture f; Put(f.faith_a, 0xCC, std::int32_t{2}); cg::Observation o; Check(Read(f, o));
    const auto &rows = *o.faiths->at(0).challengers;
    Check(rows.size() == 2 && rows[0].registered_sponsor_title.title_full_id == rows[1].registered_sponsor_title.title_full_id);
    Check(rows[1].challenger_title.laws.complete_laws->empty());
    Check(rows[1].challenger_title.laws.temporal_head_of_faith_succession_law_member == false);
  }
  {
    Fixture f; f.records[0].sponsor_title_full_id = UINT32_MAX; cg::Observation o; Check(Read(f, o));
    const auto &c = o.faiths->at(0).challengers->at(0);
    Check(c.registered_sponsor_title.title_absent == true && c.scope_matches_registered_pair == true);
  }
  {
    Fixture f; cg::Observation o;
    Put(f.title_a, 0x10, std::uint32_t{0}); Put(f.title_slots, 8, static_cast<void *>(f.title_a.data()));
    f.records[0] = {0, 0}; Check(Read(f, o));
    Check(o.faiths->at(0).challengers->at(0).challenger_title.title_full_id == 0U);
  }
  for (unsigned scenario = 0; scenario != 14; ++scenario) {
    Fixture f; cg::Observation o;
    switch (scenario) {
    case 0: f.frame.paused = false; break;
    case 1: Put(f.faith_a, 0xCC, std::int32_t{-1}); break;
    case 2: Put(f.faith_a, 0xCC, cg::kMaximumChallengersPerFaith + 1); break;
    case 3: Put(f.faith_a, 0xC0, static_cast<void *>(nullptr)); break;
    case 4: f.records[0].challenger_title_full_id = UINT32_MAX; break;
    case 5: f.records[1] = f.records[0]; Put(f.faith_a, 0xCC, std::int32_t{2}); break;
    case 6: Put(f.faith_a, 8, std::uint32_t{0x01000000}); break;
    case 7: f.getter_fallback = true; break;
    case 8: f.mutate_record = true; break;
    case 9: f.mutate_property = true; break;
    case 10: f.records[0].sponsor_title_full_id = Fixture::first_title + 0x01000000; break;
    case 11: Put(f.faith_b, 0xCC, std::int32_t{-1}); f.holder_moved = true; break;
    case 12: Put(f.title_a, 0x128, std::uint32_t{UINT32_MAX}); break;
    case 13: Put(f.faith_a, 0xC0, reinterpret_cast<void *>(1)); break;
    }
    Check(!Read(f, o)); Unknown(o);
  }
  {
    Fixture f; cg::Observation o; Put(f.faith_a, 0, std::uintptr_t{0});
    Check(!Read(f, o)); Unknown(o);
  }
  {
    Fixture f; cg::Observation o; Put(f.title_a, props::kNativeDefinitiveFormOffset, std::uint8_t{2});
    Check(!Read(f, o)); Unknown(o);
  }
  std::cout << "PASS checks=" << checks << " actual_reader=true actual_serializer=true live=false\n";
  return 0;
}
