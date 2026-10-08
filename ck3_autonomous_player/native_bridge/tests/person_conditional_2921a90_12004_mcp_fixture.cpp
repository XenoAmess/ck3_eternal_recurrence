// AUTHORED_NOTRUN. Reuse the preceding fixture's guarded Memory and actual4
// factory setup only. Its renamed producer entry is never called: all packets
// below exercise the new conditional source through production double sample
// and the whole formatter. No old scene/test or native callback executes.
#define main PersonFollowing2921a90OldProducerNotExecuted
#include "person_following_2921a90_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_conditional_2921a90.hpp"
#include <algorithm>

namespace {
struct ConditionalFixture {
  Fixture f;
  void *land = f.memory.Allocate(0xB8);
  void *ids = f.memory.Allocate(8);
  void *classifier_registry_slot = f.memory.Allocate(8, Fixture::kModule + 0x5C67568);
  void *classifier_fallback_slot = f.memory.Allocate(8, Fixture::kModule + 0x5C67570);
  void *clamps = f.memory.Allocate(8, Fixture::kModule + 0x5C6A1E8);
  void *high = f.memory.Allocate(4, Fixture::kModule + 0x5C68EE0);
  void *low = f.memory.Allocate(4, Fixture::kModule + 0x5C68EF4);
  void *default_header = f.memory.Allocate(0x1C, Fixture::kModule + 0x5D21338);
  void *metadata_slot = f.memory.Allocate(8, Fixture::kModule + 0x5D1F7B0);
  void *metadata_registry = f.memory.Allocate(0x58);
  void *metadata_table = f.memory.Allocate(3 * 0xC8);
  void *sentinel_metadata = f.memory.Allocate(0xC8, Fixture::kModule + 0x5461F40);
  void *selected_list = f.memory.Allocate(5 * 8);
  void *low_list = f.memory.Allocate(8);
  void *literal = f.memory.Allocate(0x288);
  void *raw = f.memory.Allocate(0x288);
  void *zero = f.memory.Allocate(0x288);
  void *empty = f.memory.Allocate(0x288);
  void *literal_keys = f.memory.Allocate(8);
  void *literal_values = f.memory.Allocate(32);
  void *raw_keys = f.memory.Allocate(4);
  void *raw_values = f.memory.Allocate(16);

  ConditionalFixture() {
    // Only replace the old source setup's two undemanded conditional-list
    // ranges; all other factory/readonly/frame assertions remain inherited.
    f.memory.denied.erase(std::remove_if(f.memory.denied.begin(), f.memory.denied.end(),
        [&](const Memory::Interval &i) {
          return i.address == Address(f.definition) + 0xB80 ||
                 i.address == Address(f.definition) + 0xBB0;
        }), f.memory.denied.end());
    f.memory.Put(f.enemy, 0x1C, std::uint32_t{0x43686172});
    f.memory.Put(f.enemy, 0x1C0, land);
    f.memory.Put(land, 0xA8, ids);
    f.memory.Put(land, 0xB4, std::int32_t{2});
    f.memory.Put(ids, 0, Fixture::kEnemyUnsigned);
    f.memory.Put(ids, 4, Fixture::kEnemyUnsigned);
    f.memory.Put(classifier_registry_slot, 0, f.character_storage);
    f.memory.Put(classifier_fallback_slot, 0, f.player);
    f.memory.Put(clamps, 0, std::int32_t{100});
    f.memory.Put(clamps, 4, std::int32_t{-100});
    f.memory.Put(high, 0, float{50.0F});
    f.memory.Put(low, 0, float{-50.0F});
    f.memory.Put(default_header, 0x18, std::int32_t{0});
    f.memory.NoReadVirtual(Fixture::kModule + 0x5D21350, 4);
    f.memory.Put(metadata_slot, 0, metadata_registry);
    f.memory.Put(metadata_registry, 0x50, metadata_table);
    f.memory.Put(metadata_table, 0xC8 + 0xBA, std::uint8_t{0});
    f.memory.Put(metadata_table, 0xC8 + 0xB8, std::uint8_t{0});
    f.memory.Put(metadata_table, 2 * 0xC8 + 0xBA, std::uint8_t{0});
    f.memory.Put(metadata_table, 2 * 0xC8 + 0xB8, std::uint8_t{1});
    f.memory.Put(sentinel_metadata, 0xBA, std::uint8_t{1});
    f.memory.NoReadVirtual(Fixture::kModule + 0x5461F40 + 0xB8, 1);
    f.memory.Put(f.definition, 0xB8C, std::int32_t{1});
    f.memory.Put(f.definition, 0xB80, low_list);
    f.memory.Put(f.definition, 0xBBC, std::int32_t{5});
    f.memory.Put(f.definition, 0xBB0, selected_list);
    f.memory.Put(low_list, 0, raw);
    f.memory.Put(selected_list, 0, literal);
    f.memory.Put(selected_list, 8, raw);
    f.memory.Put(selected_list, 16, literal);
    f.memory.Put(selected_list, 24, zero);
    f.memory.Put(selected_list, 32, empty);
    Pc(literal, literal_keys, literal_values, {1, 2, 0xFFFF, 1},
       {250'001, -250'001, (std::numeric_limits<std::int64_t>::max)(), 429'496'729'800'000});
    Pc(raw, raw_keys, raw_values, {1, 2}, {250'001, -250'001});
    Pc(empty, nullptr, nullptr, {}, {});
    f.memory.Put(literal, 0x280, std::int32_t{0});
    f.memory.Put(empty, 0x280, std::int32_t{0});
    Raw(raw, -150'000);
    Raw(zero, 0);
    for (const auto p : {literal, empty}) {
      f.memory.NoRead(p, 0x278, 8);
      f.memory.NoRead(p, 0x268, 8);
      f.memory.NoRead(p, 0x1D4, 4);
      f.memory.NoRead(p, 0x258, 8);
    }
    f.memory.NoRead(zero, 0, 0x78);
  }
  void Pc(void *p, void *keys, void *values,
          const std::vector<std::uint16_t> &k, const std::vector<std::int64_t> &v) {
    f.memory.Put(p, 0, keys); f.memory.Put(p, 0x68, values);
    f.memory.Put(p, 0xC, static_cast<std::int32_t>(k.size()));
    f.memory.Put(p, 0x74, static_cast<std::int32_t>(v.size()));
    for (std::size_t i = 0; i < k.size(); ++i) f.memory.Put(keys, i * 2, k[i]);
    for (std::size_t i = 0; i < v.size(); ++i) f.memory.Put(values, i * 8, v[i]);
  }
  void Raw(void *p, std::int64_t value) {
    f.memory.Put(p, 0x280, std::int32_t{1});
    f.memory.Put(p, 0x278, static_cast<void *>(nullptr));
    f.memory.Put(p, 0x268, static_cast<void *>(nullptr));
    f.memory.Put(p, 0x1D4, std::int32_t{0});
    f.memory.Put(p, 0x258, value);
  }
  void NoSelectedLists() {
    f.memory.NoRead(f.definition, 0xB80, 8); f.memory.NoRead(f.definition, 0xBB0, 8);
    f.memory.NoRead(selected_list, 0, 40); f.memory.NoRead(low_list, 0, 8);
  }
};
enum class ConditionalCase { high, low, middle, empty_classifier, other_opinion,
    dynamic_weight, values_partial, metadata_null, cold_default, negative_count,
    bypass, large_weight };
struct ConditionalSpec { const char *name; ConditionalCase kind; };
constexpr ConditionalSpec kConditionalCases[] = {
    {"self-high-default-and-raw", ConditionalCase::high},
    {"self-low-b80", ConditionalCase::low},
    {"self-middle-empty", ConditionalCase::middle},
    {"empty-classifier-list", ConditionalCase::empty_classifier},
    {"other-person-opinion", ConditionalCase::other_opinion},
    {"dynamic-weight", ConditionalCase::dynamic_weight},
    {"pc-values-partial", ConditionalCase::values_partial},
    {"metadata-registry-null", ConditionalCase::metadata_null},
    {"cold-default-classifier", ConditionalCase::cold_default},
    {"negative-selected-count", ConditionalCase::negative_count},
    {"zero-demand-bypass", ConditionalCase::bypass},
    {"large-max-operand-weight", ConditionalCase::large_weight},
};

void ProduceConditional(const std::filesystem::path &directory,
                        const ConditionalSpec &spec, std::uint64_t sequence) {
  ConditionalFixture c;
  auto &f = c.f;
  switch (spec.kind) {
  case ConditionalCase::high: break;
  case ConditionalCase::low:
    f.memory.Put(c.high, 0, float{200.0F}); f.memory.Put(c.low, 0, float{200.0F});
    f.memory.NoRead(f.definition, 0xBBC, 4);
    f.memory.NoRead(f.definition, 0xBB0, 8);
    break;
  case ConditionalCase::middle:
    f.memory.Put(c.high, 0, float{200.0F}); c.NoSelectedLists(); break;
  case ConditionalCase::empty_classifier:
    f.memory.Put(c.land, 0xA8, static_cast<void *>(nullptr));
    f.memory.Put(c.land, 0xB4, std::int32_t{0});
    c.NoSelectedLists();
    f.memory.NoReadVirtual(Fixture::kModule + 0x5C67568, 8);
    f.memory.NoReadVirtual(Fixture::kModule + 0x5C6A1E8, 8);
    f.memory.NoReadVirtual(Fixture::kModule + 0x5C68EE0, 4);
    break;
  case ConditionalCase::other_opinion:
    f.memory.Put(c.ids, 4, std::uint32_t{Fixture::kPlayer}); c.NoSelectedLists(); break;
  case ConditionalCase::dynamic_weight:
    f.memory.Put(c.literal, 0x280, std::int32_t{1});
    f.memory.denied.erase(std::remove_if(f.memory.denied.begin(), f.memory.denied.end(),
        [&](const Memory::Interval &i) { return i.address == Address(c.literal) + 0x278; }), f.memory.denied.end());
    f.memory.Put(c.literal, 0x278, std::uintptr_t{0x12345678});
    f.memory.NoRead(c.literal, 0, 0x78);
    break;
  case ConditionalCase::values_partial:
    f.memory.hidden.push_back({Address(c.literal_values), 32}); break;
  case ConditionalCase::metadata_null:
    f.memory.Put(c.metadata_slot, 0, static_cast<void *>(nullptr));
    f.memory.NoRead(c.metadata_registry, 0x50, 8); break;
  case ConditionalCase::cold_default:
    f.memory.Put(f.enemy, 0x1C0, static_cast<void *>(nullptr));
    f.memory.denied.erase(std::remove_if(f.memory.denied.begin(), f.memory.denied.end(),
        [](const Memory::Interval &i) { return i.address == Fixture::kModule + 0x5D21350; }), f.memory.denied.end());
    f.memory.NoReadVirtual(Fixture::kModule + 0x5D21338, 0x10);
    c.NoSelectedLists(); break;
  case ConditionalCase::negative_count:
    f.memory.Put(f.definition, 0xBBC, std::int32_t{-1});
    f.memory.NoRead(c.selected_list, 0, 40); break;
  case ConditionalCase::bypass:
    f.memory.Put(f.definition, 0xB8C, std::int32_t{0});
    f.memory.Put(f.definition, 0xBBC, std::int32_t{0});
    f.memory.NoRead(f.enemy, 0x1C, 4); c.NoSelectedLists(); break;
  case ConditionalCase::large_weight:
    f.memory.Put(f.definition, 0xBBC, std::int32_t{1});
    f.memory.Put(c.selected_list, 0, c.raw);
    c.Pc(c.raw, c.raw_keys, c.raw_values, {2}, {4'611'686'018'427'387'921});
    c.Raw(c.raw, 100'003); break;
  }
  const auto snapshot = f.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_2921a90_conditional.has_value(), "new conditional sibling missing");
  const auto &d = *person.following_2921a90_conditional;
  const auto id = std::string("person-conditional2921a90-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      id, Fixture::kStep, sequence, snapshot);
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet; output.close();
  Require(static_cast<bool>(output) && packet.find("\"following_2921a90_conditional\":{") != std::string::npos,
          "new original whole production packet missing");
  Require(d.character_id == Fixture::kEnemyUnsigned && d.character_identity == Address(f.enemy) &&
              d.selected_model_identity == Address(f.model) && d.selected_object_identity == Address(f.mapped_object) &&
              d.build_version == native4::kGameVersion && d.executable_sha256 == native4::kExecutableSha256,
          "new same-query actual Character/Model provenance differs");
  const bool partial = spec.kind == ConditionalCase::other_opinion ||
      spec.kind == ConditionalCase::dynamic_weight || spec.kind == ConditionalCase::values_partial ||
      spec.kind == ConditionalCase::metadata_null || spec.kind == ConditionalCase::cold_default ||
      spec.kind == ConditionalCase::negative_count;
  Require(d.ready == !partial, "conditional family readiness differs");
  if (spec.kind == ConditionalCase::bypass) {
    Require(!d.classifier_ready && !d.classifier_result_i32 && d.selected_family == "not_demanded" &&
                d.occurrence_count == 0U && d.rows.empty(), "actual zero-demand bypass failed");
  } else if (spec.kind == ConditionalCase::other_opinion || spec.kind == ConditionalCase::cold_default) {
    Require(!d.classifier_ready && !d.classifier_result_i32 && d.rows.empty(), "missing classifier was supplied");
    Require(d.reason == (spec.kind == ConditionalCase::other_opinion
        ? "classifier_25a1220_directional_opinion_unobserved" : "classifier_default_uninitialized"),
        "exact classifier missing dependency lost");
  } else {
    Require(d.classifier_ready && d.classifier_result_i32 == (spec.kind == ConditionalCase::low ? 2
        : spec.kind == ConditionalCase::middle || spec.kind == ConditionalCase::empty_classifier ? 1 : 0),
        "actual self/empty/majority classifier differs");
    if (spec.kind == ConditionalCase::middle || spec.kind == ConditionalCase::empty_classifier)
      Require(d.rows.empty() && d.occurrence_count == 0U && d.selected_family == "classifier_other_empty",
              "source classifier one did not suppress selected rows");
    else if (spec.kind == ConditionalCase::negative_count)
      Require(d.selected_count_i32 == -1 && d.rows.empty() && d.reason == "conditional_selected_count_negative",
              "negative selected count became empty");
    else if (spec.kind == ConditionalCase::low || spec.kind == ConditionalCase::large_weight)
      Require(d.rows.size() == 1U && d.occurrence_count == 1U && d.rows[0].weight_q64 ==
                  (spec.kind == ConditionalCase::low ? -150'000 : 100'003), "one weighted source changed");
    else {
      Require(d.rows.size() == 5U && d.rows[0].object_identity == d.rows[2].object_identity &&
                  d.rows[1].ready == (spec.kind != ConditionalCase::metadata_null) &&
                  d.rows[1].weight_q64 == -150'000 && d.rows[3].ready &&
                  d.rows[3].weight_q64 == 0 && !d.rows[3].properties && d.rows[4].ready &&
                  d.rows[4].keys_count_i32 == 0 && d.rows[4].values_count_i32 == 0,
              "duplicate, zero, empty or independent row changed");
      if (!partial) Require(d.occurrence_count == 4U && d.rows[0].ready && d.rows[2].ready,
                            "default and raw nonempty source missing");
      else Require(!d.occurrence_count && !d.rows[0].ready && !d.rows[2].ready,
                   "partial earlier source discarded or claimed complete");
    }
  }
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create new conditional whole output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kConditionalCases) ProduceConditional(directory, spec, ++sequence);
  std::cout << "person conditional2921a90: twelve NEW original whole-command packets\n";
  return 0;
}
