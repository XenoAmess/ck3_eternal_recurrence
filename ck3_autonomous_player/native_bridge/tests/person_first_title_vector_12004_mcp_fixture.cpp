// AUTHORED_NOTRUN: new first-pointer-vector worlds through the real query and
// formatter. Reuse only synthetic World; its historical main/Produce never run.
#define main PersonFollowing2922680HistoricalMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_first_title_vector.hpp"

namespace {
enum class FirstVectorKind { receiver, direct_b, null_title_registry, generation, pc_partial, negative_b };
struct FirstVectorSpec { const char *name; FirstVectorKind kind; };
constexpr FirstVectorSpec kFirstVectorCases[] = {
    {"phase-a-distinct-receiver-nonzero-filter", FirstVectorKind::receiver},
    {"phase-b-direct-ignores-local-exclusions", FirstVectorKind::direct_b},
    {"null-title-registry-skips-list-ids", FirstVectorKind::null_title_registry},
    {"title-generation-fallback-preserves-order", FirstVectorKind::generation},
    {"composer-partial-independent-element", FirstVectorKind::pc_partial},
    {"phase-b-negative-count-preserves-phase-a", FirstVectorKind::negative_b},
};

struct FirstVectorWorld : World {
  static constexpr std::uintptr_t kTitleRegistry = kModule + 0x5D1DAF8;
  static constexpr std::uintptr_t kTitleFallback = kModule + 0x5D1DAE0;
  static constexpr std::uintptr_t kSecondRegistry = kModule + 0x5D1DF10;
  static constexpr std::uintptr_t kSecondFallback = kModule + 0x5D1DF00;
  static constexpr std::uint32_t kTitleA = 0x03000001U, kTitleB = 0x03000002U;
  static constexpr std::uint32_t kInitialTitle = 0x03000003U;
  static constexpr std::uint32_t kFallbackTitle = 0x05000004U;
  static constexpr std::uint32_t kSecondId = 0x09000001U;
  static constexpr std::uint32_t kReceiverId = 0x08000009U;
  void *subject_context = memory.Allocate(0x1F0);
  void *subject_title_ids = memory.Allocate(4);
  void *liege_link = memory.Allocate(0x30);
  void *receiver = memory.Allocate(0x1D8);
  void *receiver_context = memory.Allocate(0x1F0);
  void *phase_a_ids = memory.Allocate(3 * 4);
  void *title_registry_slot = memory.Allocate(8, kTitleRegistry);
  void *title_fallback_slot = memory.Allocate(8, kTitleFallback);
  void *title_registry = memory.Allocate(0x30);
  void *title_slots = memory.Allocate(4 * 0x10);
  void *title_a = memory.Allocate(0x340), *title_b = memory.Allocate(0x340);
  void *initial_title = memory.Allocate(0x340), *fallback_title = memory.Allocate(0x340);
  void *title_template = memory.Allocate(0x68);
  void *second_registry_slot = memory.Allocate(8, kSecondRegistry);
  void *second_fallback_slot = memory.Allocate(8, kSecondFallback);
  void *second_registry = memory.Allocate(0x30), *second_slots = memory.Allocate(2 * 0x10);
  void *second_object = memory.Allocate(0x60), *phase_b_ids = memory.Allocate(3 * 4);
  void *destination_pc = memory.Allocate(0x70);
  void *composer_a = memory.Allocate(3 * 8), *composer_b = memory.Allocate(8);
  void *composer_fallback = memory.Allocate(8);
  void *component_p = memory.Allocate(0x148), *component_q = memory.Allocate(0x148);
  void *component_c = memory.Allocate(0x148), *component_fallback = memory.Allocate(0x148);
  void *p_keys = memory.Allocate(2 * 2), *p_values = memory.Allocate(2 * 8);
  void *q_keys = memory.Allocate(2 * 2), *q_values = memory.Allocate(2 * 8);
  void *c_keys = memory.Allocate(2), *c_values = memory.Allocate(8);
  void *fallback_keys = memory.Allocate(2), *fallback_values = memory.Allocate(8);

  FirstVectorWorld() {
    model = memory.Allocate(0x20);
    memory.Put(model, 8, subject); memory.Put(model, 0x10, destination_pc);
    memory.Put(scratch, 0x258, model);
    memory.Put(subject, 0x1C0, subject_context);
    memory.Put(subject, 0x1B8, static_cast<void *>(nullptr));
    memory.Put(subject_context, 0x198 + 0xC, std::int32_t{0});
    memory.Put(subject_context, 0x1C0, liege_link); memory.Put(liege_link, 0x28, receiver);
    memory.Put(receiver, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(receiver, 0x18, kReceiverId); memory.Put(receiver, 0x1C0, receiver_context);
    memory.Put(receiver_context, 0x1B8, static_cast<std::uint32_t>(kSubject));
    memory.Put(receiver_context, 0x1E0, phase_a_ids);
    memory.Put(receiver_context, 0x1EC, std::int32_t{3});
    memory.Put(phase_a_ids, 0, kTitleA); memory.Put(phase_a_ids, 4, kTitleB);
    memory.Put(phase_a_ids, 8, kTitleA);
    memory.Put(subject_context, 0x1E0, subject_title_ids);
    memory.Put(subject_context, 0x1EC, std::int32_t{1});
    memory.Put(subject_title_ids, 0, kInitialTitle);
    memory.Put(title_registry_slot, 0, title_registry); memory.Put(title_fallback_slot, 0, fallback_title);
    memory.Put(title_registry, 0x20, title_slots); memory.Put(title_registry, 0x2C, std::uint32_t{4});
    memory.Put(title_slots, 0x10 + 8, title_a); memory.Put(title_slots, 0x20 + 8, title_b);
    memory.Put(title_slots, 0x30 + 8, initial_title);
    memory.Put(title_a, 0x10, kTitleA); memory.Put(title_b, 0x10, kTitleB);
    memory.Put(initial_title, 0x10, kInitialTitle); memory.Put(fallback_title, 0x10, kFallbackTitle);
    memory.Put(title_a, 0x130, std::uint8_t{1}); memory.Put(title_b, 0x130, std::uint8_t{0});
    memory.Put(initial_title, 0x130, std::uint8_t{1}); memory.Put(fallback_title, 0x130, std::uint8_t{1});
    memory.Put(initial_title, 0x330, kSecondId); memory.Put(fallback_title, 0x330, kSecondId);
    memory.Put(title_template, 0x64, std::int32_t{3});
    for (const auto title : {title_a, title_b, fallback_title}) {
      memory.Put(title, 0x48, title_template);
      memory.Put(title, 0x12C, std::int32_t{17});
      memory.Refuse(title, 0x12C, 4);
    }
    memory.Put(second_registry_slot, 0, second_registry); memory.Put(second_fallback_slot, 0, second_object);
    memory.Put(second_registry, 0x20, second_slots); memory.Put(second_registry, 0x2C, std::uint32_t{2});
    memory.Put(second_slots, 0x10 + 8, second_object); memory.Put(second_object, 0x10, kSecondId);
    memory.Put(second_object, 0x50, phase_b_ids); memory.Put(second_object, 0x5C, std::int32_t{3});
    memory.Put(phase_b_ids, 0, kTitleB); memory.Put(phase_b_ids, 4, kTitleA); memory.Put(phase_b_ids, 8, kTitleB);
    memory.Put(title_a, 0x228, composer_a); memory.Put(title_a, 0x234, std::int32_t{3});
    memory.Put(title_b, 0x228, composer_b); memory.Put(title_b, 0x234, std::int32_t{1});
    memory.Put(fallback_title, 0x228, composer_fallback); memory.Put(fallback_title, 0x234, std::int32_t{1});
    memory.Put(composer_a, 0, component_p); memory.Put(composer_a, 8, component_q); memory.Put(composer_a, 16, component_p);
    memory.Put(composer_b, 0, component_c); memory.Put(composer_fallback, 0, component_fallback);
    Property(Offset(component_p, 0xD8), p_keys, p_values, {0x22A, 0x333}, {100'000, -50'000});
    Property(Offset(component_q, 0xD8), q_keys, q_values, {0x22A, 0x444}, {-200'000, 300'000});
    Property(Offset(component_c, 0xD8), c_keys, c_values, {0x555}, {125'000});
    Property(Offset(component_fallback, 0xD8), fallback_keys, fallback_values, {0x777}, {75'000});
  }
  void Configure(FirstVectorKind kind) {
    switch (kind) {
    case FirstVectorKind::direct_b:
      memory.Put(receiver_context, 0x1B8, static_cast<std::uint32_t>(kSubject) + std::uint32_t{1});
      memory.Refuse(receiver_context, 0x1E0, 0x10);
      break;
    case FirstVectorKind::null_title_registry:
      memory.Put(title_registry_slot, 0, static_cast<void *>(nullptr));
      memory.Refuse(phase_a_ids, 0, 3 * 4); memory.Refuse(phase_b_ids, 0, 3 * 4);
      break;
    case FirstVectorKind::generation:
      memory.Put(title_a, 0x10, std::uint32_t{0x04000001U});
      memory.Refuse(title_a, 0x130, 1);
      break;
    case FirstVectorKind::pc_partial:
      memory.Refuse(p_values, 0, 2 * 8, false);
      break;
    case FirstVectorKind::negative_b:
      memory.Put(second_object, 0x5C, std::int32_t{-2});
      break;
    default: break;
    }
  }
};

void CheckFirstVectorElement(const native4::PersonFirstTitleVectorElement12004 &element,
                             const FirstVectorWorld &world, const void *title,
                             bool partial) {
  const bool is_a = title == world.title_a;
  const bool is_b = title == world.title_b;
  const std::size_t count = is_a ? std::size_t{3} : std::size_t{1};
  Require(element.identity == Address(title) && element.input_ready &&
              element.template_identity == Address(world.title_template) &&
              element.template_tier_i32 == std::int32_t{3} &&
              element.ready == !partial &&
              element.reason == (partial ? "composer_inputs_partial" : "") &&
              element.primary.ready && element.primary.known_empty == true &&
              element.primary.source_pcs.empty() &&
              element.supplemental.ready && element.supplemental.known_empty == true &&
              element.supplemental.rows.empty() &&
              element.composer.ready == !partial && element.composer.known_empty == false &&
              element.composer.count_i32 == static_cast<std::int32_t>(count) &&
              element.composer.source_pcs.size() == count,
          "direct emitted Title lost tier, independent family readiness or duplicate composer sources");
  for (std::size_t index = 0; index < count; ++index) {
    const bool is_p = is_a && index != std::size_t{1};
    const bool is_q = is_a && index == std::size_t{1};
    const auto component = is_p ? world.component_p : is_q ? world.component_q
        : is_b ? world.component_c : world.component_fallback;
    const auto &pc = element.composer.source_pcs[index];
    const bool pc_partial = partial && is_p;
    const std::vector<std::uint16_t> keys = is_p
        ? std::vector<std::uint16_t>{0x22A, 0x333}
        : is_q ? std::vector<std::uint16_t>{0x22A, 0x444}
        : is_b ? std::vector<std::uint16_t>{0x555} : std::vector<std::uint16_t>{0x777};
    const std::vector<std::int64_t> values = is_p
        ? std::vector<std::int64_t>{100'000, -50'000}
        : is_q ? std::vector<std::int64_t>{-200'000, 300'000}
        : is_b ? std::vector<std::int64_t>{125'000} : std::vector<std::int64_t>{75'000};
    Require(pc.identity == Address(component) + 0xD8 && pc.admitted == true &&
                pc.count_i32 == static_cast<std::int32_t>(keys.size()) &&
                pc.weight_q100000 == 100'000 && pc.ready == !pc_partial &&
                pc.reason == (pc_partial ? "pc_values_unread" : "") &&
                pc.properties && pc.properties->keys_u16 == keys &&
                static_cast<bool>(pc.properties->values_q64) == !pc_partial,
            "direct composer source lost actual PC pair, native order or fixed inner weight");
    if (!pc_partial)
      Require(pc.properties->values_q64 == values, "copied composer values changed");
  }
}

void ProduceFirstVector(const std::filesystem::path &directory,
                        const FirstVectorSpec &spec, std::uint64_t sequence) {
  FirstVectorWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_291e3a0_first_title_vector.has_value(),
          "same-query first Title-pointer vector missing");
  const auto &leaf = *person.following_291e3a0_first_title_vector;
  const bool negative = spec.kind == FirstVectorKind::negative_b;
  const bool partial = spec.kind == FirstVectorKind::pc_partial;
  const bool declined_a = spec.kind == FirstVectorKind::direct_b;
  const bool null_registry = spec.kind == FirstVectorKind::null_title_registry;
  const bool generation = spec.kind == FirstVectorKind::generation;
  Require(leaf.character_id == static_cast<std::uint32_t>(World::kSubject) &&
              leaf.character_identity == Address(world.subject) &&
              leaf.selected_model_identity == Address(world.model) &&
              leaf.destination_pc_identity == Address(world.destination_pc) &&
              leaf.build_version == native4::kGameVersion &&
              leaf.executable_sha256 == native4::kExecutableSha256 &&
              leaf.ready == !(negative || partial) &&
              leaf.source_inputs_ready == !negative && leaf.producer_ready == !negative &&
              leaf.family_input_ready == !negative && leaf.primary_ready == !negative &&
              leaf.composer_ready == !(negative || partial) &&
              leaf.supplemental_ready == !negative && leaf.family_known_zero == false &&
              !leaf.full_helper_ready &&
              leaf.full_helper_reason == "historical_post_callback_model_and_final_append_unobserved" &&
              leaf.reason == (negative ? "first_vector_source_inputs_partial"
                  : partial ? "composer_inputs_partial" : ""),
          "first-vector attribution, partial boundary or helper readiness changed");
  Require(leaf.receiver.ready && leaf.receiver.selection == "context_candidate" &&
              leaf.receiver.input_context_1c0_identity == Address(world.subject_context) &&
              leaf.receiver.input_link_1b8_identity == std::uintptr_t{0} &&
              leaf.receiver.context_link_1c0_identity == Address(world.liege_link) &&
              leaf.receiver.context_candidate_28_identity == Address(world.receiver) &&
              leaf.receiver.candidate_magic_1c_u32 == std::uint32_t{0x43686172U} &&
              leaf.receiver.candidate_full_id_18_u32 == FirstVectorWorld::kReceiverId &&
              leaf.receiver.selected_identity == Address(world.receiver) &&
              leaf.receiver.selected_identity != leaf.character_identity &&
              leaf.receiver_context_1c0_identity == Address(world.receiver_context) &&
              leaf.receiver_context_1b8_full_id_u32 ==
                  static_cast<std::uint32_t>(World::kSubject) + (declined_a ? std::uint32_t{1} : std::uint32_t{0}),
          "phaseA did not use the returned immediate-liege receiver independently of the subject");
  const auto &phase_a = leaf.phase_a;
  Require(phase_a.ready && phase_a.admitted == !declined_a && phase_a.reason.empty() &&
              phase_a.rows.size() == (declined_a ? std::size_t{0} : std::size_t{3}),
          "receiver owner admission or phaseA candidate count changed");
  if (declined_a) {
    Require(!phase_a.header_identity && !phase_a.array_identity && !phase_a.count_i32 &&
                !phase_a.title_registry_identity && !phase_a.title_fallback_identity,
            "declined phaseA demanded a list header or database input");
  } else {
    Require(phase_a.header_identity == Address(world.receiver_context) + 0x1E0 &&
                phase_a.array_identity == Address(world.phase_a_ids) &&
                phase_a.count_i32 == std::int32_t{3},
            "phaseA used the subject list instead of returned receiver list");
  }
  const auto &inputs = leaf.phase_b_inputs;
  Require(inputs.ready && inputs.selection == "context_first" &&
              inputs.subject_context_1c0_identity == Address(world.subject_context) &&
              inputs.context_count_1ec_i32 == std::int32_t{1} &&
              inputs.context_array_1e0_identity == Address(world.subject_title_ids) &&
              inputs.initial_title_full_id_u32 == FirstVectorWorld::kInitialTitle &&
              inputs.initial_title_resolution.ready &&
              inputs.initial_title_resolution.selection == (null_registry ? "fallback" : "mapped") &&
              inputs.second_requested_full_id_330_u32 == FirstVectorWorld::kSecondId &&
              inputs.second_resolution.ready && inputs.second_resolution.selection == "mapped" &&
              inputs.second_resolution.selected_identity == Address(world.second_object),
          "phaseB lost its mandatory first ID, second registry or full-generation source roots");
  const auto &phase_b = leaf.phase_b;
  Require(phase_b.ready == !negative && phase_b.admitted == true &&
              phase_b.header_identity == Address(world.second_object) + 0x50 &&
              phase_b.array_identity == Address(world.phase_b_ids) &&
              phase_b.count_i32 == (negative ? std::int32_t{-2} : std::int32_t{3}) &&
              phase_b.reason == (negative ? "phase_count_negative" : "") &&
              phase_b.rows.size() == (negative ? std::size_t{0} : std::size_t{3}),
          "phaseB signed count or ordered second-object header changed");
  std::vector<std::uintptr_t> expected_emitted;
  for (const auto *phase : {&phase_a, &phase_b}) {
    const bool is_a = phase == &phase_a;
    if (phase->rows.empty()) continue;
    Require(phase->title_registry_identity == (null_registry ? std::uintptr_t{0} : Address(world.title_registry)) &&
                phase->title_fallback_identity == Address(world.fallback_title),
            "producer did not retain both preloaded Title roots");
    for (std::size_t index = 0; index < phase->rows.size(); ++index) {
      const auto &row = phase->rows[index];
      const bool candidate_a = is_a ? index != std::size_t{1} : index == std::size_t{1};
      const bool fallback = null_registry || (generation && candidate_a);
      const auto selected = fallback ? world.fallback_title
          : candidate_a ? world.title_a : world.title_b;
      const auto requested = candidate_a ? FirstVectorWorld::kTitleA : FirstVectorWorld::kTitleB;
      const bool emitted = !is_a || fallback || candidate_a;
      Require(row.native_index == static_cast<std::uint32_t>(index) && row.ready && row.reason.empty() &&
                  row.id_demanded == !null_registry && row.resolution.ready &&
                  row.resolution.selection == (fallback ? "fallback" : "mapped") &&
                  row.resolution.selected_identity == Address(selected) && row.emitted == emitted,
              "candidate source order, null registry demand, generation fallback or emission changed");
      if (null_registry)
        Require(!row.requested_full_id_u32 && !row.resolution.requested_full_id_u32,
                "null Title registry demanded an intentionally unread list ID");
      else
        Require(row.requested_full_id_u32 == requested && row.resolution.requested_full_id_u32 == requested,
                "candidate full DWORD ID was truncated or collapsed");
      if (generation && candidate_a)
        Require(row.resolution.candidate_full_id_u32 == std::uint32_t{0x04000001U},
                "full Title generation mismatch was not preserved");
      if (is_a)
        Require(row.filter_byte_130_u8 == (emitted ? std::uint8_t{1} : std::uint8_t{0}),
                "phaseA must emit only the nonzero raw130 branch");
      else
        Require(!row.filter_byte_130_u8, "phaseB introduced a local raw130 exclusion");
      Require(row.element.has_value() == emitted, "nonemitted candidate invented a numerical element");
      if (emitted) {
        expected_emitted.push_back(Address(selected));
        CheckFirstVectorElement(*row.element, world, selected, partial && candidate_a);
      }
    }
  }
  if (negative)
    Require(!leaf.emitted_element_identities && expected_emitted.size() == std::size_t{2},
            "incomplete phaseB count fabricated a complete vector or discarded useful phaseA elements");
  else
    Require(leaf.emitted_element_identities == expected_emitted,
            "actual append order or duplicate Title-pointer occurrences changed");
  const auto request_id = std::string("person-first-title-vector-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_291e3a0_first_title_vector\":{") != std::string::npos,
          "real whole-command formatter omitted the first-vector domain leaf");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original first-vector whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_first_title_vector_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create first-vector packet output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kFirstVectorCases) ProduceFirstVector(directory, spec, ++sequence);
  std::cout << "person first Title-pointer vector: six fresh production whole-command packets\n";
  return 0;
}
