// AUTHORED_NOTRUN: ten fresh stable local-Title worlds through the real
// current-person query and whole-command formatter. Reuse only synthetic World
// setup; its historical main/Produce are never invoked by this target.
#define main PersonFollowing2922680HistoricalMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_local_titles.hpp"

namespace {
enum class LocalTitleKind {
  empty, absent_empty, positive_duplicates, excluded, generation_fallback,
  null_registry, composer_partial, negative_count, tier1_primary, tier2_empty
};
struct LocalTitleSpec {
  const char *name;
  LocalTitleKind kind;
};
constexpr LocalTitleSpec kLocalTitleCases[] = {
    {"context-empty", LocalTitleKind::empty},
    {"absent-context-static-empty", LocalTitleKind::absent_empty},
    {"eligible-tier3-composer-duplicates", LocalTitleKind::positive_duplicates},
    {"excluded-byte-and-dword", LocalTitleKind::excluded},
    {"generation-fallback", LocalTitleKind::generation_fallback},
    {"null-title-registry-ids-retained", LocalTitleKind::null_registry},
    {"composer-values-unread-independent-sibling", LocalTitleKind::composer_partial},
    {"negative-header-count", LocalTitleKind::negative_count},
    {"eligible-tier1-primary-positive", LocalTitleKind::tier1_primary},
    {"eligible-tier2-primary-supplemental-empty", LocalTitleKind::tier2_empty},
};

struct LocalTitleWorld : World {
  static constexpr std::uintptr_t kStaticTitleHeader = kModule + 0x5459C88;
  static constexpr std::uintptr_t kTitleRegistry = kModule + 0x5D1DAF8;
  static constexpr std::uintptr_t kTitleFallback = kModule + 0x5D1DAE0;
  static constexpr std::uint32_t kTitleA = 0x03000001U;
  static constexpr std::uint32_t kTitleB = 0x03000002U;
  static constexpr std::uint32_t kFallbackTitle = 0x05000003U;
  void *title_context = memory.Allocate(0x1F0);
  void *title_ids = memory.Allocate(3 * 4);
  void *static_title_header = memory.Allocate(0x10, kStaticTitleHeader);
  void *title_registry_slot = memory.Allocate(8, kTitleRegistry);
  void *title_fallback_slot = memory.Allocate(8, kTitleFallback);
  void *title_registry = memory.Allocate(0x30);
  void *title_slots = memory.Allocate(3 * 0x10);
  void *title_a = memory.Allocate(0x340);
  void *title_b = memory.Allocate(0x340);
  void *title_fallback = memory.Allocate(0x238);
  void *title_template = memory.Allocate(0x68);
  void *composer_array_a = memory.Allocate(3 * 8);
  void *composer_array_b = memory.Allocate(8);
  void *composer_array_fallback = memory.Allocate(8);
  void *component_p = memory.Allocate(0x148);
  void *component_q = memory.Allocate(0x148);
  void *component_c = memory.Allocate(0x148);
  void *component_p_keys = memory.Allocate(2 * 2);
  void *component_p_values = memory.Allocate(2 * 8);
  void *component_q_keys = memory.Allocate(2 * 2);
  void *component_q_values = memory.Allocate(2 * 8);
  void *component_c_keys = memory.Allocate(2);
  void *component_c_values = memory.Allocate(8);
  void *destination_pc = memory.Allocate(0x70);
  void *province = memory.Allocate(0x860);
  void *province_keys = memory.Allocate(2);
  void *province_values = memory.Allocate(8);
  void *child_ids = memory.Allocate(4);
  void *child_template = memory.Allocate(0x68);
  void *county_data = memory.Allocate(0x38);

  LocalTitleWorld() {
    // The older World guards its original inline Model+10. This helper copies
    // QWORD[Model+10] as a destination pointer, so give it a genuine new model.
    model = memory.Allocate(0x20);
    memory.Put(model, 8, subject);
    memory.Put(model, 0x10, destination_pc);
    memory.Put(scratch, 0x258, model);
    memory.Put(subject, 0x1C0, title_context);
    // Preceding helper remains genuinely empty and independent of this family.
    memory.Put(title_context, 0x198 + 0xC, std::int32_t{0});
    memory.Put(title_context, 0x1E0, title_ids);
    memory.Put(title_context, 0x1E0 + 0xC, std::int32_t{3});
    memory.Put(static_title_header, 0xC, std::int32_t{0});
    memory.Put(static_title_header, 0, static_cast<void *>(nullptr));
    memory.Put(title_ids, 0, kTitleA);
    memory.Put(title_ids, 4, kTitleB);
    memory.Put(title_ids, 8, kTitleA);
    memory.Put(title_registry_slot, 0, title_registry);
    memory.Put(title_fallback_slot, 0, title_fallback);
    memory.Put(title_registry, 0x20, title_slots);
    memory.Put(title_registry, 0x2C, std::uint32_t{3});
    memory.Put(title_slots, 0x10 + 8, title_a);
    memory.Put(title_slots, 0x20 + 8, title_b);
    memory.Put(title_a, 0x10, kTitleA);
    memory.Put(title_b, 0x10, kTitleB);
    memory.Put(title_fallback, 0x10, kFallbackTitle);
    memory.Put(title_template, 0x64, std::int32_t{3});
    for (const auto title : {title_a, title_b, title_fallback}) {
      memory.Put(title, 0x130, std::uint8_t{0});
      memory.Put(title, 0x12C, std::int32_t{-1});
      memory.Put(title, 0x48, title_template);
    }
    memory.Put(title_a, 0x228, composer_array_a);
    memory.Put(title_a, 0x234, std::int32_t{3});
    memory.Put(title_b, 0x228, composer_array_b);
    memory.Put(title_b, 0x234, std::int32_t{1});
    memory.Put(title_fallback, 0x228, composer_array_fallback);
    memory.Put(title_fallback, 0x234, std::int32_t{1});
    memory.Put(composer_array_a, 0, component_p);
    memory.Put(composer_array_a, 8, component_q);
    memory.Put(composer_array_a, 16, component_p);
    memory.Put(composer_array_b, 0, component_c);
    memory.Put(composer_array_fallback, 0, component_q);
    Property(Offset(component_p, 0xD8), component_p_keys, component_p_values,
             {0x22A, 0x333}, {100'000, -50'000});
    Property(Offset(component_q, 0xD8), component_q_keys, component_q_values,
             {0x22A, 0x444}, {-200'000, 300'000});
    Property(Offset(component_c, 0xD8), component_c_keys, component_c_values,
             {0x555}, {125'000});
    Property(Offset(province, 0x278), province_keys, province_values,
             {0x666}, {150'000});
  }
  void Configure(LocalTitleKind kind) {
    switch (kind) {
    case LocalTitleKind::empty:
      memory.Put(title_context, 0x1E0 + 0xC, std::int32_t{0});
      break;
    case LocalTitleKind::absent_empty:
      memory.Put(subject, 0x1C0, static_cast<void *>(nullptr));
      break;
    case LocalTitleKind::excluded:
      memory.Put(title_a, 0x130, std::uint8_t{1});
      memory.Put(title_b, 0x12C, std::int32_t{17});
      memory.Refuse(title_a, 0x12C, 4);
      for (const auto title : {title_a, title_b}) {
        memory.Refuse(title, 0x48, 8);
        memory.Refuse(title, 0x228, 0x10);
      }
      break;
    case LocalTitleKind::generation_fallback:
      memory.Put(title_a, 0x10, std::uint32_t{0x04000001});
      memory.Refuse(title_a, 0x130, 1);
      break;
    case LocalTitleKind::null_registry:
      memory.Put(title_registry_slot, 0, static_cast<void *>(nullptr));
      break;
    case LocalTitleKind::composer_partial:
      memory.Refuse(component_p_values, 0, 2 * 8, false);
      break;
    case LocalTitleKind::negative_count:
      memory.Put(title_context, 0x1E0 + 0xC, std::int32_t{-2});
      break;
    case LocalTitleKind::tier1_primary:
      memory.Put(title_context, 0x1E0 + 0xC, std::int32_t{1});
      memory.Put(title_template, 0x64, std::int32_t{1});
      memory.Put(title_a, 0x338, province);
      memory.Put(title_a, 0x1E0, static_cast<void *>(nullptr));
      memory.Put(title_a, 0x1EC, std::int32_t{0});
      break;
    case LocalTitleKind::tier2_empty:
      memory.Put(title_context, 0x1E0 + 0xC, std::int32_t{1});
      memory.Put(title_template, 0x64, std::int32_t{2});
      memory.Put(title_a, 0x110, child_ids);
      memory.Put(title_a, 0x11C, std::int32_t{1});
      memory.Put(child_ids, 0, kTitleB);
      memory.Put(title_b, 0x48, child_template);
      memory.Put(child_template, 0x64, std::int32_t{3});
      memory.Put(title_b, 0x338, province);
      memory.Put(province, 0x85C, std::uint32_t{0x50726F76U});
      memory.Put(province, 0x848, county_data);
      memory.Put(county_data, 0x28, static_cast<void *>(nullptr));
      memory.Put(county_data, 0x34, std::int32_t{0});
      memory.Put(title_a, 0x1E0, static_cast<void *>(nullptr));
      memory.Put(title_a, 0x1EC, std::int32_t{0});
      break;
    default: break;
    }
    if (kind == LocalTitleKind::empty || kind == LocalTitleKind::absent_empty ||
        kind == LocalTitleKind::negative_count) {
      memory.Refuse(kTitleRegistry, 8);
      memory.Refuse(kTitleFallback, 8);
    }
  }
};

void ProduceLocalTitles(const std::filesystem::path &directory,
                        const LocalTitleSpec &spec, std::uint64_t sequence) {
  LocalTitleWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_291e3a0_local_titles.has_value(),
          "same-query current-person local-Title input leaf is missing");
  const auto &leaf = *person.following_291e3a0_local_titles;
  const bool negative = spec.kind == LocalTitleKind::negative_count;
  const bool partial = spec.kind == LocalTitleKind::composer_partial;
  const bool empty = spec.kind == LocalTitleKind::empty ||
                     spec.kind == LocalTitleKind::absent_empty;
  const bool zero = empty || spec.kind == LocalTitleKind::excluded;
  const bool tier1 = spec.kind == LocalTitleKind::tier1_primary;
  const bool tier2 = spec.kind == LocalTitleKind::tier2_empty;
  const bool primary_tier = tier1 || tier2;
  Require(leaf.build_version == native4::kGameVersion &&
              leaf.executable_sha256 == native4::kExecutableSha256 &&
              leaf.character_id == static_cast<std::uint32_t>(World::kSubject) &&
              leaf.character_identity == Address(world.subject) &&
              leaf.selected_model_identity == Address(world.model) &&
              leaf.destination_pc_identity == Address(world.destination_pc) &&
              leaf.ready == !(negative || partial) &&
              leaf.family_input_ready == !negative &&
              leaf.composer_ready == !(negative || partial) &&
              leaf.primary_ready == !negative && leaf.supplemental_ready == !negative &&
              !leaf.full_helper_ready &&
              leaf.full_helper_reason == "actual2b986b0_vector_unobserved",
          "local family attribution/readiness was confused with complete helper state");
  Require(leaf.header_selection == (spec.kind == LocalTitleKind::absent_empty
              ? "existing_default_5459c88" : "context_1c0_1e0") &&
              leaf.header_identity == (spec.kind == LocalTitleKind::absent_empty
                  ? LocalTitleWorld::kStaticTitleHeader : Address(world.title_context) + 0x1E0) &&
              leaf.count_i32 == (negative ? -2 : empty ? 0 : primary_tier ? 1 : 3),
          "current local-Title header/count selection changed");
  if (negative) {
    Require(leaf.reason == "local_title_count_negative" &&
                !leaf.family_known_zero && leaf.array_identity == Address(world.title_ids) && leaf.rows.empty(),
            "negative local-Title count became a known empty family");
  } else {
    Require(leaf.family_known_zero == zero &&
                leaf.reason == (partial ? "composer_inputs_partial" : ""),
            "known empty family or precise composer partial reason changed");
  }
  if (empty) {
    Require(leaf.array_identity == (spec.kind == LocalTitleKind::absent_empty
                ? 0 : Address(world.title_ids)) && leaf.rows.empty(),
            "empty header lost the array pointer loaded before its count");
  } else if (!negative) {
    Require(leaf.array_identity == Address(world.title_ids) &&
                leaf.rows.size() == (primary_tier ? 1U : 3U),
            "physical title-ID order/cardinality changed");
    for (std::size_t index = 0; index < leaf.rows.size(); ++index) {
      const auto &row = leaf.rows[index];
      const bool first_title = index != 1;
      const auto requested = first_title ? LocalTitleWorld::kTitleA : LocalTitleWorld::kTitleB;
      const bool fallback = spec.kind == LocalTitleKind::null_registry ||
          (spec.kind == LocalTitleKind::generation_fallback && first_title);
      const auto selected = fallback ? world.title_fallback
          : first_title ? world.title_a : world.title_b;
      const auto selected_id = fallback ? LocalTitleWorld::kFallbackTitle : requested;
      Require(row.native_index == index && row.input_ready &&
                  row.requested_title_full_id_u32 == requested &&
                  row.resolution.requested_full_id_u32 == requested &&
                  row.resolution.selection == (fallback ? "fallback" : "mapped") &&
                  row.resolution.selected_identity == Address(selected) &&
                  row.selected_title_full_id_u32 == selected_id,
              "full title IDs, generation/fallback or duplicate order changed");
      if (spec.kind == LocalTitleKind::excluded) {
        Require(row.ready && row.native_contribution_eligible == false &&
                    row.exclusion == (first_title ? "byte_130_nonzero" : "dword_12c_not_minus_one") &&
                    row.exclusion_byte_130_u8 == static_cast<std::uint8_t>(first_title ? 1 : 0) &&
                    !row.template_identity && !row.template_tier_i32 &&
                    row.composer.ready && row.composer.known_empty == true &&
                    row.composer.source_pcs.empty(),
                "excluded title demanded template/composer or became a contribution");
        if (first_title)
          Require(!row.exclusion_dword_12c_i32,
                  "byte exclusion demanded the later DWORD predicate");
        else
          Require(row.exclusion_dword_12c_i32 == 17,
                  "DWORD exclusion lost its raw signed value");
        continue;
      }
      const bool failed = partial && first_title;
      Require(row.ready == !failed && row.reason == (failed ? "composer_inputs_partial" : "") &&
                  row.native_contribution_eligible == true && row.exclusion == "eligible" &&
                  row.exclusion_byte_130_u8 == std::uint8_t{0} && row.exclusion_dword_12c_i32 == -1 &&
                  row.template_identity == Address(world.title_template) &&
                  row.template_tier_i32 == (tier1 ? 1 : tier2 ? 2 : 3) &&
                  row.composer.ready == !failed && row.primary.ready &&
                  row.supplemental_ready,
              "composer or independently ready primary/supplemental family changed");
      if (tier1) {
        Require(row.primary.source_pcs.size() == 1U && row.primary.source_pcs[0].ready &&
                    row.primary.source_pcs[0].identity == Address(world.province) + 0x278 &&
                    row.primary.source_pcs[0].count_i32 == 1 &&
                    row.primary.source_pcs[0].properties &&
                    row.primary.source_pcs[0].properties->keys_u16 &&
                    *row.primary.source_pcs[0].properties->keys_u16 == std::vector<std::uint16_t>{0x666} &&
                    row.primary.source_pcs[0].properties->values_q64 &&
                    *row.primary.source_pcs[0].properties->values_q64 == std::vector<std::int64_t>{150'000},
                "tier1 direct Province+278 primary PC was not copied");
      } else {
        Require(row.primary.source_pcs.empty() && row.primary.known_empty == true,
                "known empty or unused primary family invented a constituent");
        if (tier2)
          Require(row.primary.array_identity == std::uintptr_t{0} && row.primary.count_i32 == 0,
                  "tier2 CountyData empty list lost its actually loaded pointer/count");
      }
      if (tier2)
        Require(row.supplemental_array_identity == std::uintptr_t{0} && row.supplemental_count_i32 == 0,
                "empty supplemental family lost pointer-before-count operands");
      else
        Require(!row.supplemental_array_identity && !row.supplemental_count_i32,
                "non-tier2 row demanded the supplemental family");
      const std::vector<void *> expected_sources = fallback
          ? std::vector<void *>{world.component_q}
          : first_title ? std::vector<void *>{world.component_p, world.component_q, world.component_p}
                        : std::vector<void *>{world.component_c};
      Require(row.composer.count_i32 == static_cast<std::int32_t>(expected_sources.size()) &&
                  row.composer.source_pcs.size() == expected_sources.size() &&
                  row.composer.known_empty == false &&
                  row.composer.reason == (failed ? "source_pcs_partial" : ""),
              "composer raw constituent count/order or partial reason changed");
      for (std::size_t source_index = 0; source_index < expected_sources.size(); ++source_index) {
        const auto &pc = row.composer.source_pcs[source_index];
        const bool pc_failed = failed && expected_sources[source_index] == world.component_p;
        Require(pc.identity == Address(expected_sources[source_index]) + 0xD8 &&
                    pc.admitted == true && pc.weight_q100000 == 100'000 &&
                    pc.ready == !pc_failed && pc.reason == (pc_failed ? "pc_values_unread" : "") &&
                    pc.properties && pc.properties->keys_u16 &&
                    static_cast<bool>(pc.properties->values_q64) == !pc_failed,
                "constituent PC pair, fixed inner weight or copied sibling was lost");
      }
      if (spec.kind == LocalTitleKind::generation_fallback && first_title)
        Require(row.resolution.candidate_full_id_u32 == 0x04000001U,
                "wrong full generation was truncated to low24 title slot");
    }
  }
  Require(person.following_2922680 && person.following_2922680->ready &&
              person.following_2922680->primary_ready &&
              person.following_2922680->append_occurrences.empty(),
          "new local family changed preceding independently empty helper");
  const auto request_id = std::string("person-local-titles-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_291e3a0_local_titles\":{") != std::string::npos &&
              packet.find(request_id) != std::string::npos,
          "real whole-command formatter lost local-Title input family");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original local-Title whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_following_291e3a0_local_titles_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create local-Title packet output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kLocalTitleCases) ProduceLocalTitles(directory, spec, ++sequence);
  std::cout << "person local Titles: ten fresh production whole-command packets\n";
  return 0;
}
