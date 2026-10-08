// AUTHORED_NOTRUN. The preceding producer's owned Memory and actual4 factory
// setup are source reuse only: its renamed main is never executed. Every file
// here is a new original whole body from the production terminal double sample.
#define main PersonFollowing2921a90OpinionSourceProducerNotExecuted
#include "person_following_2921a90_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_conditional_opinion.hpp"
#include <algorithm>

namespace {
struct OpinionFixture {
  static constexpr std::uint32_t kOwnerA = 0x06000004U;
  static constexpr std::uint32_t kOwnerB = 0x07000005U;
  static constexpr std::uint32_t kOwnerC = 0x08000006U;
  Fixture f;
  void *owner_a = f.memory.Allocate(0x1D0);
  void *owner_b = f.memory.Allocate(0x1D0);
  void *owner_c = f.memory.Allocate(0x1D0);
  void *land = f.memory.Allocate(0xB8);
  void *ids = f.memory.Allocate(12);
  void *classifier_registry_slot = f.memory.Allocate(8, Fixture::kModule + 0x5C67568);
  void *classifier_fallback_slot = f.memory.Allocate(8, Fixture::kModule + 0x5C67570);
  void *high = f.memory.Allocate(4, Fixture::kModule + 0x5C68EE0);
  void *low = f.memory.Allocate(4, Fixture::kModule + 0x5C68EF4);
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
  std::int32_t opinion_a = 75, opinion_b = 60, opinion_c = 0;
  std::size_t reads_a = 0, reads_b = 0, reads_c = 0;

  OpinionFixture() {
    f.memory.denied.erase(std::remove_if(f.memory.denied.begin(), f.memory.denied.end(),
        [&](const Memory::Interval &i) {
          return i.address == Address(f.definition) + 0xB80 ||
                 i.address == Address(f.definition) + 0xBB0;
        }), f.memory.denied.end());
    f.Store(static_cast<std::int32_t>(kOwnerA), owner_a);
    f.Store(static_cast<std::int32_t>(kOwnerB), owner_b);
    f.Store(static_cast<std::int32_t>(kOwnerC), owner_c);
    f.memory.Put(owner_a, native4::kCharacterFullIdOffset, kOwnerA);
    f.memory.Put(owner_b, native4::kCharacterFullIdOffset, kOwnerB);
    f.memory.Put(owner_c, native4::kCharacterFullIdOffset, kOwnerC);
    f.memory.Put(f.enemy, 0x1C, std::uint32_t{0x43686172});
    f.memory.Put(f.enemy, 0x1C0, land);
    f.memory.Put(land, 0xA8, ids);
    f.memory.Put(land, 0xB4, std::int32_t{3});
    f.memory.Put(ids, 0, kOwnerA); f.memory.Put(ids, 4, kOwnerB); f.memory.Put(ids, 8, kOwnerA);
    f.memory.Put(classifier_registry_slot, 0, f.character_storage);
    f.memory.Put(classifier_fallback_slot, 0, f.player);
    f.memory.Put(high, 0, float{50.0F}); f.memory.Put(low, 0, float{-50.0F});
    // The pair provider already returns post-clamp total. A second clamp would
    // read a denied native operand and fail the inherited demand assertions.
    f.memory.NoReadVirtual(Fixture::kModule + 0x5C6A1E8, 8);
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
    f.memory.Put(selected_list, 0, literal); f.memory.Put(selected_list, 8, raw);
    f.memory.Put(selected_list, 16, literal); f.memory.Put(selected_list, 24, zero);
    f.memory.Put(selected_list, 32, empty);
    Pc(literal, literal_keys, literal_values, {1, 2, 0xFFFF, 1},
       {250'001, -250'001, 999'000, 123'456});
    Pc(raw, raw_keys, raw_values, {1, 2}, {250'001, -250'001});
    Pc(empty, nullptr, nullptr, {}, {});
    f.memory.Put(literal, 0x280, std::int32_t{0});
    f.memory.Put(empty, 0x280, std::int32_t{0});
    Raw(raw, -150'000); Raw(zero, 0);
    for (const auto p : {literal, empty}) {
      f.memory.NoRead(p, 0x278, 8); f.memory.NoRead(p, 0x268, 8);
      f.memory.NoRead(p, 0x1D4, 4); f.memory.NoRead(p, 0x258, 8);
    }
    f.memory.NoRead(zero, 0, 0x78);
    auto &binding = f.bindings.current_person_conditional_opinion;
    Require(binding.enabled && binding.opinion.enabled && binding.opinion.core.enabled &&
        binding.module_base == Fixture::kModule &&
        reinterpret_cast<std::uintptr_t>(binding.opinion.read_opinion) ==
            Fixture::kModule + native4::kReadCharacterOpinionRva &&
        reinterpret_cast<std::uintptr_t>(binding.opinion.core.character_storage_slot) ==
            Fixture::kModule + native4::kCharacterStorageSlotRva,
        "production actual4 pair binder, getter and storage identities differ");
    // Explicit fixture seam: real owned Core storage/full IDs and one native
    // getter callback. The production repeated pair reader remains unchanged.
    binding.opinion.core.character_storage_slot = &f.character_storage;
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
    f.memory.Put(p, 0x1D4, std::int32_t{0}); f.memory.Put(p, 0x258, value);
  }
  void NoSelectedLists() {
    f.memory.NoRead(f.definition, 0xB80, 8); f.memory.NoRead(f.definition, 0xBB0, 8);
    f.memory.NoRead(selected_list, 0, 40); f.memory.NoRead(low_list, 0, 8);
  }
};
OpinionFixture *opinion_current = nullptr;
std::int32_t PairTotal(void *owner, void *toward) {
  Require(opinion_current && toward == opinion_current->f.enemy &&
      toward != opinion_current->f.player,
      "toward must be the original queried full enemy, never GetPlayer");
  auto &c = *opinion_current;
  if (owner == c.owner_a) { ++c.reads_a; return c.opinion_a; }
  if (owner == c.owner_b) { ++c.reads_b; return c.opinion_b; }
  Require(owner == c.owner_c, "provider owner must be the actual selected Character");
  ++c.reads_c; return c.opinion_c;
}
enum class OpinionCase { high, low, mixed_tie, unavailable, dynamic };
struct OpinionSpec { const char *name; OpinionCase kind; };
constexpr OpinionSpec kOpinionCases[] = {
    {"opinion-high", OpinionCase::high},
    {"opinion-low", OpinionCase::low},
    {"opinion-mixed-tie", OpinionCase::mixed_tie},
    {"opinion-provider-unavailable", OpinionCase::unavailable},
    {"opinion-dynamic-weight-later-ready", OpinionCase::dynamic},
};

void ProduceOpinion(const std::filesystem::path &directory,
                    const OpinionSpec &spec, std::uint64_t sequence) {
  OpinionFixture c; opinion_current = &c;
  auto &f = c.f;
  f.bindings.current_person_conditional_opinion.opinion.read_opinion = &PairTotal;
  switch (spec.kind) {
  case OpinionCase::high: break;
  case OpinionCase::low:
    c.opinion_a = -75; c.opinion_b = -60;
    f.memory.NoRead(f.definition, 0xBB0, 8);
    f.memory.NoRead(c.selected_list, 0, 40);
    break;
  case OpinionCase::mixed_tie:
    c.opinion_b = -75; c.opinion_c = 0;
    f.memory.Put(c.ids, 8, OpinionFixture::kOwnerC);
    c.NoSelectedLists(); break;
  case OpinionCase::unavailable:
    f.bindings.current_person_conditional_opinion.opinion.read_opinion = nullptr;
    c.NoSelectedLists();
    f.memory.NoReadVirtual(Fixture::kModule + 0x5C68EE0, 4);
    f.memory.NoReadVirtual(Fixture::kModule + 0x5C68EF4, 4);
    break;
  case OpinionCase::dynamic:
    f.memory.Put(c.literal, 0x280, std::int32_t{1});
    f.memory.denied.erase(std::remove_if(f.memory.denied.begin(), f.memory.denied.end(),
        [&](const Memory::Interval &i) { return i.address == Address(c.literal) + 0x278; }),
        f.memory.denied.end());
    f.memory.Put(c.literal, 0x278, std::uintptr_t{0x12345678});
    f.memory.NoRead(c.literal, 0, 0x78); break;
  }
  const auto snapshot = f.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_2921a90_conditional && person.following_2921a90_opinion,
      "both unchanged source44 and new opinion siblings must be present");
  const auto &source = *person.following_2921a90_conditional;
  const auto &d = *person.following_2921a90_opinion;
  Require(d.source_inputs == source && !source.ready && !source.classifier_ready &&
      !source.classifier_result_i32 && source.rows.empty() &&
      source.reason == "classifier_25a1220_directional_opinion_unobserved",
      "new pair opinion must retain the original44 partial DTO unchanged");
  Require(d.character_id == Fixture::kEnemyUnsigned &&
      d.source_inputs.character_identity == Address(f.enemy) &&
      d.build_version == native4::kGameVersion && d.executable_sha256 == native4::kExecutableSha256 &&
      d.opinion_rows.size() == 3U,
      "same actual full enemy and three physical opinion occurrences must be retained");
  for (std::size_t i = 0; i < d.opinion_rows.size(); ++i) {
    const auto &row = d.opinion_rows[i];
    Require(row.source_index == static_cast<std::uint32_t>(i) &&
        row.toward_full_character_id == Fixture::kEnemyUnsigned &&
        row.toward_character_identity == Address(f.enemy) &&
        row.selected_character_identity != row.toward_character_identity &&
        !row.base_value && !row.additional_value,
        "physical ordinal, pair direction or unobserved base/additional were changed");
  }
  if (spec.kind == OpinionCase::unavailable) {
    Require(!d.ready && !d.classifier_ready && !d.classifier_result_i32 && d.rows.empty() &&
        d.reason == "pair_opinion_provider_unavailable" &&
        c.reads_a == 0U && c.reads_b == 0U && c.reads_c == 0U,
        "unavailable provider must not supply votes, zero or an array");
    for (const auto &row : d.opinion_rows)
      Require(!row.ready && !row.total_opinion_i32 && row.vote.empty() &&
          row.reason == "pair_opinion_provider_unavailable", "failed pair became an observed vote");
  } else {
    const auto expected = spec.kind == OpinionCase::low ? 2
        : spec.kind == OpinionCase::mixed_tie ? 1 : 0;
    Require(d.classifier_ready && d.classifier_result_i32 == expected &&
        c.reads_a == (spec.kind == OpinionCase::mixed_tie ? 4U : 8U) && c.reads_b == 4U &&
        c.reads_c == (spec.kind == OpinionCase::mixed_tie ? 4U : 0U),
        "actual full pair repeat-read or physical strict majority differs");
    for (const auto &row : d.opinion_rows)
      Require(row.ready && row.total_opinion_i32 &&
          row.source_selection == "native_pair_postclamp_28bc470" &&
          row.high_threshold_bits_u32,
          "new opinion total, threshold or actual provider provenance was lost");
    if (spec.kind == OpinionCase::mixed_tie)
      Require(d.ready && d.selected_family == "classifier_other_empty" &&
          d.rows.empty() && d.occurrence_count == 0U, "tie must be classifier1 and known empty");
    else if (spec.kind == OpinionCase::low)
      Require(d.ready && d.selected_family == "b80_b8c" && d.rows.size() == 1U &&
          d.rows[0].weight_q64 == -150'000 && d.occurrence_count == 1U,
          "low majority must demand the actual B80 pointer family");
    else {
      Require(d.rows.size() == 5U && d.selected_family == "bb0_bbc" &&
          d.rows[0].object_identity == d.rows[2].object_identity && d.rows[1].ready &&
          d.rows[1].weight_q64 == -150'000 && d.rows[3].ready &&
          d.rows[3].weight_q64 == 0 && !d.rows[3].properties && d.rows[4].ready &&
          d.rows[4].keys_count_i32 == 0 && d.rows[4].values_count_i32 == 0,
          "duplicate, raw, zero or independently ready empty source changed");
      if (spec.kind == OpinionCase::dynamic)
        Require(!d.ready && !d.occurrence_count && !d.rows[0].ready && !d.rows[2].ready &&
            d.reason == "weight_virtual_expression_9d7060_unobserved",
            "dynamic weight must remain partial while later raw rows survive");
      else Require(d.ready && d.rows[0].ready && d.rows[2].ready && d.occurrence_count == 4U,
          "five physical high-family rows must retain four nonzero occurrences");
    }
  }
  const auto id = std::string("person-conditional-opinion-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      id, Fixture::kStep, sequence, snapshot);
  Require(packet.find("\"following_2921a90_opinion\":{") != std::string::npos &&
      packet.find("\"source_inputs\":{") != std::string::npos,
      "production original whole formatter omitted the new sibling or unchanged source");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet; output.close();
  Require(static_cast<bool>(output), "cannot write NEW original whole opinion packet");
  opinion_current = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create NEW opinion whole output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kOpinionCases) ProduceOpinion(directory, spec, ++sequence);
  std::cout << "person conditional opinion: five NEW original whole-command packets\n";
  return 0;
}
