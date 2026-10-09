// AUTHORED_NOTRUN: six new supplemental input worlds, real whole-query reader
// and formatter. Reuse only synthetic World; historical main/Produce never run.
#define main PersonFollowing2922680HistoricalMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_local_titles.hpp"

namespace {
enum class SupplementalKind { ordered, no_match, shortcircuits, generation, null_rite, pc_partial };
struct SupplementalSpec { const char *name; SupplementalKind kind; };
constexpr SupplementalSpec kSupplementalCases[] = {
    {"supplemental-ordered-avx-tail-duplicates", SupplementalKind::ordered},
    {"supplemental-no-match-and-empty", SupplementalKind::no_match},
    {"supplemental-definition-byte-shortcircuits", SupplementalKind::shortcircuits},
    {"supplemental-generation-fallback", SupplementalKind::generation},
    {"supplemental-null-rite-registry-fallback", SupplementalKind::null_rite},
    {"supplemental-pc-partial-independent-sibling", SupplementalKind::pc_partial},
};

struct SupplementalWorld : World {
  static constexpr std::uintptr_t kTitleRegistry = kModule + 0x5D1DAF8;
  static constexpr std::uintptr_t kTitleFallback = kModule + 0x5D1DAE0;
  static constexpr std::uintptr_t kSupplementalRegistry = kModule + 0x5D1DE80;
  static constexpr std::uintptr_t kSupplementalFallback = kModule + 0x5D1DE20;
  static constexpr std::uint32_t kTitleA = 0x03000001U, kTitleB = 0x03000002U;
  static constexpr std::uint32_t kChildTitle = 0x03000003U;
  static constexpr std::uint32_t kObjectA = 0x07000001U, kObjectB = 0x07000002U;
  static constexpr std::uint32_t kObjectC = 0x07000003U, kFallbackObject = 0x09000004U;
  static constexpr std::uint32_t kRiteId = 0x06000001U;
  static constexpr std::uint32_t kMembershipKey = 0x0100BEEFU;
  static constexpr std::uint32_t kLow24Collision = 0x0200BEEFU;
  void *title_context = memory.Allocate(0x1F0);
  void *title_ids = memory.Allocate(3 * 4);
  void *title_registry_slot = memory.Allocate(8, kTitleRegistry);
  void *title_fallback_slot = memory.Allocate(8, kTitleFallback);
  void *title_registry = memory.Allocate(0x30);
  void *title_slots = memory.Allocate(4 * 0x10);
  void *title_a = memory.Allocate(0x340);
  void *title_b = memory.Allocate(0x340);
  void *title_child = memory.Allocate(0x340);
  void *title_template = memory.Allocate(0x68);
  void *child_template = memory.Allocate(0x68);
  void *child_ids = memory.Allocate(4);
  void *province = memory.Allocate(0x860);
  void *county_data = memory.Allocate(0x38);
  void *destination_pc = memory.Allocate(0x70);
  void *supplemental_ids_a = memory.Allocate(3 * 4);
  void *supplemental_ids_b = memory.Allocate(4);
  void *supplemental_registry_slot = memory.Allocate(8, kSupplementalRegistry);
  void *supplemental_fallback_slot = memory.Allocate(8, kSupplementalFallback);
  void *supplemental_registry = memory.Allocate(0x30);
  void *supplemental_slots = memory.Allocate(4 * 0x10);
  void *object_a = memory.Allocate(0xA8);
  void *object_b = memory.Allocate(0xA8);
  void *object_c = memory.Allocate(0xA8);
  void *object_fallback = memory.Allocate(0xA8);
  void *definition_a = memory.Allocate(0x288);
  void *definition_b = memory.Allocate(0x288);
  void *definition_c = memory.Allocate(0x288);
  void *definition_fallback = memory.Allocate(0x288);
  void *a_keys = memory.Allocate(2 * 2), *a_values = memory.Allocate(2 * 8);
  void *b_keys = memory.Allocate(2 * 2), *b_values = memory.Allocate(2 * 8);
  void *c_keys = memory.Allocate(2), *c_values = memory.Allocate(8);
  void *fallback_keys = memory.Allocate(2), *fallback_values = memory.Allocate(8);
  void *members_a = memory.Allocate(12 * 4), *members_b = memory.Allocate(12 * 4);
  void *members_c = memory.Allocate(4), *members_fallback = memory.Allocate(4);
  void *rite_registry = memory.Allocate(0x30), *rite_slots = memory.Allocate(2 * 0x10);

  SupplementalWorld() {
    model = memory.Allocate(0x20);
    memory.Put(model, 8, subject);
    memory.Put(model, 0x10, destination_pc);
    memory.Put(scratch, 0x258, model);
    memory.Put(subject, 0x1C0, title_context);
    memory.Put(title_context, 0x198 + 0xC, std::int32_t{0});
    memory.Put(title_context, 0x1E0, title_ids);
    memory.Put(title_context, 0x1EC, std::int32_t{3});
    memory.Put(title_ids, 0, kTitleA); memory.Put(title_ids, 4, kTitleB);
    memory.Put(title_ids, 8, kTitleA);
    memory.Put(title_registry_slot, 0, title_registry);
    memory.Put(title_fallback_slot, 0, title_child);
    memory.Put(title_registry, 0x20, title_slots);
    memory.Put(title_registry, 0x2C, std::uint32_t{4});
    memory.Put(title_slots, 0x10 + 8, title_a);
    memory.Put(title_slots, 0x20 + 8, title_b);
    memory.Put(title_slots, 0x30 + 8, title_child);
    memory.Put(title_a, 0x10, kTitleA); memory.Put(title_b, 0x10, kTitleB);
    memory.Put(title_child, 0x10, kChildTitle);
    memory.Put(title_template, 0x64, std::int32_t{2});
    memory.Put(child_template, 0x64, std::int32_t{3});
    memory.Put(child_ids, 0, kChildTitle);
    for (const auto title : {title_a, title_b}) {
      memory.Put(title, 0x130, std::uint8_t{0});
      memory.Put(title, 0x12C, std::int32_t{-1});
      memory.Put(title, 0x48, title_template);
      memory.Put(title, 0x110, child_ids); memory.Put(title, 0x11C, std::int32_t{1});
      memory.Put(title, 0x228, static_cast<void *>(nullptr));
      memory.Put(title, 0x234, std::int32_t{0});
    }
    memory.Put(title_child, 0x48, child_template);
    memory.Put(title_child, 0x338, province);
    memory.Put(province, 0x85C, std::uint32_t{0x50726F76U});
    memory.Put(province, 0x848, county_data);
    memory.Put(county_data, 0x28, static_cast<void *>(nullptr));
    memory.Put(county_data, 0x34, std::int32_t{0});
    memory.Put(title_a, 0x1E0, supplemental_ids_a); memory.Put(title_a, 0x1EC, std::int32_t{3});
    memory.Put(title_b, 0x1E0, supplemental_ids_b); memory.Put(title_b, 0x1EC, std::int32_t{1});
    memory.Put(supplemental_ids_a, 0, kObjectA); memory.Put(supplemental_ids_a, 4, kObjectB);
    memory.Put(supplemental_ids_a, 8, kObjectA); memory.Put(supplemental_ids_b, 0, kObjectC);
    memory.Put(supplemental_registry_slot, 0, supplemental_registry);
    memory.Put(supplemental_fallback_slot, 0, object_fallback);
    memory.Put(supplemental_registry, 0x20, supplemental_slots);
    memory.Put(supplemental_registry, 0x2C, std::uint32_t{4});
    memory.Put(supplemental_slots, 0x10 + 8, object_a);
    memory.Put(supplemental_slots, 0x20 + 8, object_b);
    memory.Put(supplemental_slots, 0x30 + 8, object_c);
    Object(object_a, kObjectA, definition_a, members_a, 12);
    Object(object_b, kObjectB, definition_b, members_b, 12);
    Object(object_c, kObjectC, definition_c, members_c, 1);
    Object(object_fallback, kFallbackObject, definition_fallback, members_fallback, 1);
    // Definition+224 is also PC(Definition+218)+C: keep the gate/count identical.
    Property(Offset(definition_a, 0x218), a_keys, a_values, {0x22A, 0x333}, {100'000, -50'000});
    Property(Offset(definition_b, 0x218), b_keys, b_values, {0x22A, 0x444}, {-200'000, 300'000});
    Property(Offset(definition_c, 0x218), c_keys, c_values, {0x555}, {125'000});
    Property(Offset(definition_fallback, 0x218), fallback_keys, fallback_values, {0x777}, {75'000});
    for (std::size_t index = 0; index < std::size_t{12}; ++index) {
      memory.Put(members_a, index * 4, std::uint32_t{0x100U} + static_cast<std::uint32_t>(index));
      memory.Put(members_b, index * 4, std::uint32_t{0x200U} + static_cast<std::uint32_t>(index));
    }
    memory.Put(members_a, 0, kLow24Collision); memory.Put(members_a, 2 * 4, kMembershipKey);
    memory.Put(members_a, 7 * 4, kMembershipKey);
    memory.Put(members_b, 0, kLow24Collision); memory.Put(members_b, 9 * 4, kMembershipKey);
    memory.Put(members_b, 11 * 4, kMembershipKey);
    memory.Put(members_c, 0, kMembershipKey); memory.Put(members_fallback, 0, kMembershipKey);
    memory.Put(rite_registry_slot, 0, rite_registry);
    memory.Put(rite_registry, 0x20, rite_slots); memory.Put(rite_registry, 0x2C, std::uint32_t{2});
    memory.Put(rite_slots, 0x10 + 8, rite); memory.Put(subject, 0xB4, kRiteId);
    memory.Put(rite, 8, kRiteId); memory.Put(rite, 0x4B8, kMembershipKey);
  }
  void Object(void *object, std::uint32_t id, void *definition, void *members, std::int32_t count) {
    memory.Put(object, 0x10, id); memory.Put(object, 0x20, definition);
    memory.Put(object, 0x18, std::uint8_t{1}); memory.Put(object, 0x98, members);
    memory.Put(object, 0xA4, count);
  }
  void NoPcDemand(void *definition) {
    memory.Refuse(definition, 0x218, 8); memory.Refuse(definition, 0x280, 8);
  }
  void Configure(SupplementalKind kind) {
    switch (kind) {
    case SupplementalKind::no_match:
      memory.Put(members_a, 2 * 4, kLow24Collision); memory.Put(members_a, 7 * 4, kLow24Collision);
      memory.Put(object_b, 0xA4, std::int32_t{0}); memory.Put(object_b, 0x98, static_cast<void *>(nullptr));
      memory.Put(members_c, 0, kLow24Collision);
      for (const auto definition : {definition_a, definition_b, definition_c}) NoPcDemand(definition);
      break;
    case SupplementalKind::shortcircuits:
      memory.Put(definition_a, 0x224, std::int32_t{0});
      memory.Put(definition_c, 0x224, std::int32_t{0});
      memory.Put(object_b, 0x18, std::uint8_t{0});
      memory.Refuse(object_a, 0x18, 1); memory.Refuse(object_c, 0x18, 1);
      for (const auto object : {object_a, object_b, object_c}) memory.Refuse(object, 0x98, 0x10);
      for (const auto definition : {definition_a, definition_b, definition_c}) NoPcDemand(definition);
      memory.Refuse(kRiteRegistry, 8); memory.Refuse(kRiteFallback, 8);
      break;
    case SupplementalKind::generation:
      memory.Put(object_a, 0x10, std::uint32_t{0x08000001U});
      memory.Refuse(object_a, 0x20, 8);
      break;
    case SupplementalKind::null_rite:
      memory.Put(rite_registry_slot, 0, static_cast<void *>(nullptr));
      memory.Refuse(subject, 0xB4, 4);
      break;
    case SupplementalKind::pc_partial:
      memory.Refuse(a_values, 0, 2 * 8, false);
      break;
    default: break;
    }
    if (kind != SupplementalKind::no_match && kind != SupplementalKind::shortcircuits) {
      // A first match in the eight-lane block and one in the scalar tail make
      // later elements irrelevant to the software observation of the result.
      memory.Refuse(members_a, 3 * 4, 9 * 4);
      memory.Refuse(members_b, 10 * 4, 2 * 4);
    }
  }
};

void ProduceSupplemental(const std::filesystem::path &directory,
                         const SupplementalSpec &spec, std::uint64_t sequence) {
  SupplementalWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_291e3a0_local_titles.has_value(), "same-query supplemental leaf missing");
  const auto &leaf = *person.following_291e3a0_local_titles;
  const bool partial = spec.kind == SupplementalKind::pc_partial;
  const bool no_match = spec.kind == SupplementalKind::no_match;
  const bool shortcircuits = spec.kind == SupplementalKind::shortcircuits;
  const bool known_empty = no_match || shortcircuits;
  Require(leaf.character_id == static_cast<std::uint32_t>(World::kSubject) &&
              leaf.character_identity == Address(world.subject) &&
              leaf.selected_model_identity == Address(world.model) &&
              leaf.destination_pc_identity == Address(world.destination_pc) &&
              leaf.build_version == native4::kGameVersion &&
              leaf.executable_sha256 == native4::kExecutableSha256 &&
              leaf.ready == !partial && leaf.family_input_ready && leaf.composer_ready &&
              leaf.primary_ready && leaf.supplemental_ready == !partial &&
              leaf.family_known_zero == known_empty &&
              !leaf.full_helper_ready && leaf.full_helper_reason == "actual2b986b0_vector_unobserved" &&
              leaf.count_i32 == 3 && leaf.rows.size() == 3,
          "supplemental family readiness, receiver or full-helper boundary changed");
  Require(leaf.reason == (partial ? "supplemental_inputs_partial" : ""),
          "partial supplemental family lost its precise root reason");
  for (std::size_t outer = 0; outer < leaf.rows.size(); ++outer) {
    const auto &title = leaf.rows[outer];
    const bool title_a = outer != 1;
    const bool title_partial = partial && title_a;
    const auto &family = title.supplemental;
    Require(title.native_index == outer && title.input_ready && title.ready == !title_partial &&
                title.template_tier_i32 == 2 && title.native_contribution_eligible == true &&
                title.composer.ready && title.composer.known_empty == true &&
                title.primary.ready && title.primary.known_empty == true &&
                family.ready == !title_partial && family.known_empty == known_empty &&
                family.count_i32 == (title_a ? 3 : 1) && family.rows.size() == (title_a ? 3U : 1U) &&
                title.supplemental_array_identity == family.array_identity &&
                title.supplemental_count_i32 == family.count_i32 &&
                title.supplemental_ready == family.ready && title.supplemental_reason == family.reason &&
                family.reason == (title_partial ? "supplemental_rows_partial" : ""),
            "ordered supplemental family, compatibility mirror or independently ready sibling lost");
    for (std::size_t index = 0; index < family.rows.size(); ++index) {
      const auto &source = family.rows[index];
      const bool object_a = title_a && index != 1;
      const bool object_b = title_a && index == 1;
      const bool fallback = object_a && spec.kind == SupplementalKind::generation;
      const auto requested = object_a ? SupplementalWorld::kObjectA
          : object_b ? SupplementalWorld::kObjectB : SupplementalWorld::kObjectC;
      const auto definition = fallback ? world.definition_fallback
          : object_a ? world.definition_a : object_b ? world.definition_b : world.definition_c;
      const bool source_partial = partial && object_a;
      Require(source.native_index == index && source.requested_full_id_u32 == requested &&
                  source.resolution.requested_full_id_u32 == requested && source.resolution.ready &&
                  source.resolution.selection == (fallback ? "fallback" : "mapped") &&
                  source.definition_identity == Address(definition) && source.ready == !source_partial &&
                  source.reason == (source_partial ? "supplemental_pc_partial" : ""),
              "supplemental full-ID generation, duplicate order or source reason changed");
      if (fallback)
        Require(source.resolution.candidate_full_id_u32 == std::uint32_t{0x08000001U} &&
                    source.resolution.selected_identity == Address(world.object_fallback),
                "full generation mismatch did not use genuine supplemental fallback");
      if (shortcircuits) {
        Require(source.admitted == false && !source.rite_id_demanded &&
                    !source.membership_count_i32 && source.membership_full_ids_u32.empty() &&
                    !source.first_match_index &&
                    source.definition_gate_224_i32 == (object_b ? 2 : 0) &&
                    (object_b ? source.object_gate_18_u8 == std::uint8_t{0}
                              : !source.object_gate_18_u8),
                "definition/byte shortcircuit demanded a later input or became a contribution");
      } else {
        Require(source.definition_gate_224_i32 == (fallback || !title_a ? 1 : 2) &&
                    source.object_gate_18_u8 == std::uint8_t{1} &&
                    source.rite_resolution.ready &&
                    source.rite_membership_key_u32 == SupplementalWorld::kMembershipKey &&
                    source.rite_id_demanded == (spec.kind != SupplementalKind::null_rite),
                "guard/PC count alias or demanded Rite key changed");
        if (spec.kind == SupplementalKind::null_rite)
          Require(!source.character_rite_full_id_u32 &&
                      !source.rite_resolution.requested_full_id_u32 &&
                      source.rite_resolution.selection == "fallback",
                  "null Rite registry demanded CharacterB4 instead of genuine fallback");
        else
          Require(source.character_rite_full_id_u32 == SupplementalWorld::kRiteId &&
                      source.rite_resolution.requested_full_id_u32 == SupplementalWorld::kRiteId,
                  "Rite full-ID input was truncated or erased");
        if (no_match) {
          Require(source.admitted == false && !source.first_match_index &&
                      source.membership_count_i32 == (object_a ? 12 : object_b ? 0 : 1) &&
                      source.membership_full_ids_u32.size() == (object_a ? 12U : object_b ? 0U : 1U),
                  "empty/no-match membership became an admitted PC or lost full traversal");
          if (object_b)
            Require(source.membership_array_identity == std::uintptr_t{0} &&
                        source.rite_membership_key_u32 == SupplementalWorld::kMembershipKey,
                    "count0 lost the demanded array pointer or Rite key");
          else
            Require(source.membership_full_ids_u32.front() == SupplementalWorld::kLow24Collision,
                    "complete DWORD comparison accepted a low24 collision");
        } else {
          const auto expected_index = fallback || !title_a ? std::uint32_t{0}
              : object_a ? std::uint32_t{2} : std::uint32_t{9};
          const auto members = fallback ? world.members_fallback
              : object_a ? world.members_a : object_b ? world.members_b : world.members_c;
          Require(source.admitted == true && source.first_match_index == expected_index &&
                      source.match_identity == Address(members) + static_cast<std::uintptr_t>(expected_index) * 4 &&
                      source.membership_full_ids_u32.size() == static_cast<std::size_t>(expected_index) + 1 &&
                      source.membership_full_ids_u32.back() == SupplementalWorld::kMembershipKey,
                  "first full-DWORD AVX-block/tail match or observed prefix changed");
          if (expected_index != 0)
            Require(source.membership_full_ids_u32.front() == SupplementalWorld::kLow24Collision,
                    "full DWORD first-match search collapsed the high generation byte");
        }
      }
      const auto &pc = source.source_pc;
      if (known_empty) {
        Require(pc.ready && pc.admitted == false && !pc.identity && !pc.count_i32 && !pc.properties,
                "skipped supplemental source invented a copied PC");
      } else {
        Require(pc.admitted == true && pc.identity == Address(definition) + 0x218 &&
                    pc.count_i32 == source.definition_gate_224_i32 && pc.weight_q100000 == 100'000 &&
                    pc.ready == !source_partial && pc.reason == (source_partial ? "pc_values_unread" : "") &&
                    pc.properties && pc.properties->keys_u16 &&
                    static_cast<bool>(pc.properties->values_q64) == !source_partial,
                "source PC pair, physical count alias, inner unit weight or ready sibling lost");
      }
    }
  }
  Require(leaf.rows[0].supplemental.array_identity == leaf.rows[2].supplemental.array_identity,
          "repeated outer Title no longer retains the same ordered source list");
  const auto request_id = std::string("person-title-supplemental-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_291e3a0_local_titles\":{") != std::string::npos &&
              packet.find("\"supplemental\":{") != std::string::npos,
          "real whole-command formatter omitted typed supplemental family");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original supplemental whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_local_titles_supplemental_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create supplemental packet output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kSupplementalCases) ProduceSupplemental(directory, spec, ++sequence);
  std::cout << "person local-Title supplemental: six fresh production whole-command packets\n";
  return 0;
}
