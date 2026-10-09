// AUTHORED_NOTRUN: eleven fresh stable synthetic worlds, real whole-query reader
// and formatter. Reuse only World setup/guarded memory from the prior fixture;
// its renamed main and Produce are never invoked here.
// Stable admitted descriptors are themselves in the original mapper header.
// Thus no-match/empty-header mapper branches remain source-qualified, without
// pretending a read-time header change is a coherent paused-frame fixture.
#define main PersonFollowing2922680HistoricalMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main

namespace {
enum class MappedKind {
  full_id_order, null_match, default_initialized, default_negative_epoch, default_guard_unread,
  default_uninitialized, values_partial, nested, unused_later, empty_pc,
  matched_pointer_unread
};
struct MappedSpec {
  const char *name;
  MappedKind kind;
  bool ready;
  const char *reason;
};
constexpr MappedSpec kMappedCases[] = {
    {"first-full-id-whole-order", MappedKind::full_id_order, true,
     "mapped_first_full_id_match"},
    {"first-null-stays-null", MappedKind::null_match, false,
     "mapped_first_full_id_match_null"},
    {"wrong-magic-default-initialized", MappedKind::default_initialized, true,
     "mapped_default_wrong_magic"},
    {"wrong-magic-default-negative-epoch", MappedKind::default_negative_epoch, true,
     "mapped_default_wrong_magic"},
    {"default-guard-unread", MappedKind::default_guard_unread, false,
     "mapped_default_guard_unread"},
    {"default-not-initialized", MappedKind::default_uninitialized, false,
     "mapped_default_not_initialized"},
    {"mapped-values-partial", MappedKind::values_partial, false,
     "mapped_first_full_id_match:pc_values_unread"},
    {"nested-mapped-interleaved", MappedKind::nested, true,
     "mapped_first_full_id_match"},
    {"first-match-unused-default-later", MappedKind::unused_later, true,
     "mapped_first_full_id_match"},
    {"mapped-empty-pc", MappedKind::empty_pc, true,
     "mapped_first_full_id_match"},
    {"matched-pc-pointer-unread", MappedKind::matched_pointer_unread, false,
     "mapped_matched_pc_pointer_unread"},
};

struct MappedWorld : World {
  static constexpr std::uintptr_t kDefault = kModule + 0x5DC21B0;
  static constexpr std::uintptr_t kDefaultGuard = kModule + 0x5DC21A4;
  static constexpr std::uint32_t kQueryId = 0x0100BEEF;
  void *mapped_descriptors = memory.Allocate(4 * 0x30);
  void *mapped_members = memory.Allocate(2 * 8);
  void *collision_key = memory.Allocate(0x40);
  void *earlier_key = memory.Allocate(0x40);
  void *query_a = memory.Allocate(0x40);
  void *query_b = memory.Allocate(0x40);
  void *first_pc = memory.Allocate(0x70);
  void *later_pc = memory.Allocate(0x70);
  void *first_keys = memory.Allocate(4 * 2);
  void *first_values = memory.Allocate(4 * 8);
  void *later_keys = memory.Allocate(2);
  void *later_values = memory.Allocate(8);
  void *default_pc = memory.Allocate(0x70, kDefault);
  void *default_guard = memory.Allocate(4, kDefaultGuard);
  void *default_keys = memory.Allocate(2);
  void *default_values = memory.Allocate(8);

  MappedWorld() {
    NumericInputs(false, false, false);
    for (const auto key : {collision_key, earlier_key, query_a, query_b}) {
      memory.Put(key, 0x10, kQueryId);
      memory.Put(key, 0x38, std::uint32_t{0x4744624F});
    }
    memory.Put(collision_key, 0x10, std::uint32_t{0x0200BEEF});
    Property(first_pc, first_keys, first_values, {0x22A, 0xFFFF, 0x22A, 0},
             {-100'000, (std::numeric_limits<std::int64_t>::min)(), 0,
              (std::numeric_limits<std::int64_t>::max)()});
    Property(later_pc, later_keys, later_values, {0x777}, {7'777'777});
    Property(default_pc, default_keys, default_values, {0x444}, {-444'444});
    memory.Put(default_guard, 0, std::int32_t{1});
    Descriptor(0, query_a, first_pc);
    Header(Offset(item_a, 0x3C0), 1);
    memory.Put(Offset(rite, 0x750), 0x50, mapped_members);
    memory.Put(Offset(rite, 0x750), 0x5C, std::int32_t{1});
    memory.Put(mapped_members, 0, query_a);
  }
  void Descriptor(std::size_t index, void *key, void *pc) {
    memory.Put(mapped_descriptors, index * 0x30 + 0x20, key);
    memory.Put(mapped_descriptors, index * 0x30 + 0x28, pc);
  }
  void Header(void *header, std::int32_t count) {
    memory.Put(header, 0, mapped_descriptors);
    memory.Put(header, 0xC, count);
  }
  void NoDefaultDemand() {
    memory.Refuse(kDefaultGuard, 4);
    memory.Refuse(kDefault, 0x70);
  }
  void Configure(MappedKind kind) {
    const bool use_default = kind == MappedKind::default_initialized ||
        kind == MappedKind::default_negative_epoch ||
        kind == MappedKind::default_guard_unread ||
        kind == MappedKind::default_uninitialized;
    if (use_default) {
      memory.Put(query_a, 0x38, std::uint32_t{0});
      memory.Refuse(query_a, 0x10, 4);
      memory.Refuse(mapped_descriptors, 0x28, 8);
      if (kind == MappedKind::default_guard_unread)
        memory.Refuse(kDefaultGuard, 4, false);
      if (kind == MappedKind::default_uninitialized)
        memory.Put(default_guard, 0, std::int32_t{0});
      if (kind == MappedKind::default_negative_epoch)
        memory.Put(default_guard, 0, std::int32_t{-42});
      if (kind != MappedKind::default_initialized &&
          kind != MappedKind::default_negative_epoch)
        memory.Refuse(kDefault, 0x70);
      return;
    }
    NoDefaultDemand();
    switch (kind) {
    case MappedKind::full_id_order:
      Descriptor(0, collision_key, later_pc);
      Descriptor(1, earlier_key, first_pc);
      Descriptor(2, query_a, later_pc);
      Descriptor(3, query_b, later_pc);
      Header(Offset(item_a, 0x3C0), 4);
      memory.Put(mapped_members, 8, query_b);
      memory.Put(Offset(rite, 0x750), 0x5C, std::int32_t{2});
      // Candidate magic and every unused PC pointer are not mapper operands.
      memory.Refuse(collision_key, 0x38, 4);
      memory.Refuse(earlier_key, 0x38, 4);
      memory.Refuse(mapped_descriptors, 0x28, 8);
      memory.Refuse(mapped_descriptors, 2 * 0x30 + 0x28, 8);
      memory.Refuse(mapped_descriptors, 3 * 0x30 + 0x28, 8);
      break;
    case MappedKind::null_match:
      Descriptor(0, earlier_key, nullptr);
      Descriptor(1, query_a, later_pc);
      Header(Offset(item_a, 0x3C0), 2);
      memory.Refuse(earlier_key, 0x38, 4);
      memory.Refuse(mapped_descriptors, 0x30 + 0x28, 8);
      break;
    case MappedKind::values_partial:
      memory.Refuse(first_values, 0, 4 * 8, false);
      break;
    case MappedKind::nested:
      Header(Offset(nested_a, 0x390), 1);
      break;
    case MappedKind::unused_later:
      Descriptor(1, earlier_key, later_pc);
      Header(Offset(item_a, 0x3C0), 2);
      memory.Refuse(earlier_key, 0x10, 4);
      memory.Refuse(earlier_key, 0x38, 4);
      memory.Refuse(mapped_descriptors, 0x30 + 0x28, 8);
      break;
    case MappedKind::empty_pc:
      Property(first_pc, nullptr, nullptr, {}, {});
      memory.Refuse(first_pc, 0, 8);
      memory.Refuse(first_pc, 0x68, 8);
      break;
    case MappedKind::matched_pointer_unread:
      memory.Refuse(mapped_descriptors, 0x28, 8, false);
      break;
    default: break;
    }
  }
};

void ProduceMapped(const std::filesystem::path &directory,
                   const MappedSpec &spec, std::uint64_t sequence) {
  MappedWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &leaf = *snapshot.character_observations->front()
                          .current_person_state->following_2922680;
  Require(leaf.ready == spec.ready && leaf.primary_ready && leaf.rows.size() == 1 &&
              leaf.rows[0].primary_ready && leaf.rows[0].sources.size() == 1,
          "mapped partial changed independent primary family or source order");
  const bool extended = spec.kind == MappedKind::full_id_order ||
                        spec.kind == MappedKind::nested;
  const std::vector<std::string_view> ordinary_order{
      "item_primary", "item_mapped", "nested_primary", "item_primary",
      "nested_primary", "item_primary", "item_mapped", "nested_primary"};
  const std::vector<std::string_view> duplicate_order{
      "item_primary", "item_mapped", "item_mapped", "nested_primary",
      "item_primary", "nested_primary", "item_primary", "item_mapped",
      "item_mapped", "nested_primary"};
  const std::vector<std::string_view> nested_order{
      "item_primary", "item_mapped", "nested_primary", "nested_mapped",
      "item_primary", "nested_primary", "item_primary", "item_mapped",
      "nested_primary", "nested_mapped"};
  const auto &order = spec.kind == MappedKind::full_id_order ? duplicate_order
      : spec.kind == MappedKind::nested ? nested_order : ordinary_order;
  Require(leaf.append_occurrences.size() == order.size(),
          "flat mapped/native occurrence cardinality changed");
  std::size_t mapped_count = 0;
  for (std::size_t index = 0; index < leaf.append_occurrences.size(); ++index) {
    const auto &append = leaf.append_occurrences[index];
    Require(append.kind == order[index] && append.outer_index == 0 &&
                append.source_index == 0 && append.admitted == true &&
                append.weight_q100000 == 100'000,
            "native interleaving, caller occurrence or fixed weight changed");
    if (append.kind != "item_mapped" && append.kind != "nested_mapped") {
      Require(append.ready, "mapped gap erased an independently copied primary PC");
      continue;
    }
    const auto mapped_index = mapped_count++;
    Require(append.ready == spec.ready && append.reason == spec.reason &&
                append.descriptor_index.has_value(),
            "mapped branch readiness, precise reason or descriptor ordinal changed");
    const auto descriptor = spec.kind == MappedKind::full_id_order
        ? 2U + static_cast<std::uint32_t>(mapped_index % 2)
        : spec.kind == MappedKind::null_match ? 1U : 0U;
    Require(append.descriptor_index == descriptor,
            "append ordinal was replaced with matched descriptor ordinal");
    if (spec.kind == MappedKind::null_match) {
      Require(append.identity == 0 && !append.count_i32 && !append.properties,
              "first null was replaced by a later match or default PC");
    } else if (spec.kind == MappedKind::matched_pointer_unread) {
      Require(!append.identity && !append.count_i32 && !append.properties,
              "unread selected pointer became a guessed PC");
    } else if (spec.kind == MappedKind::default_initialized ||
               spec.kind == MappedKind::default_negative_epoch) {
      Require(append.identity == MappedWorld::kDefault && append.count_i32 == 1 &&
                  append.properties && append.properties->keys_u16 &&
                  *append.properties->keys_u16 == std::vector<std::uint16_t>{0x444} &&
                  append.properties->values_q64 &&
                  *append.properties->values_q64 == std::vector<std::int64_t>{-444'444},
              "initialized inline default address or paired PC differs");
    } else if (spec.kind == MappedKind::default_guard_unread ||
               spec.kind == MappedKind::default_uninitialized) {
      Require(append.identity == MappedWorld::kDefault && !append.count_i32 &&
                  !append.properties,
              "uninitialized default was copied as post-initializer input");
    } else {
      Require(append.identity == Address(world.first_pc) && append.properties &&
                  append.properties->keys_u16 && append.count_i32 ==
                      (spec.kind == MappedKind::empty_pc ? 0 : 4),
              "mapper lost first full-ID match or selected later PC");
      Require(static_cast<bool>(append.properties->values_q64) == spec.ready,
              "mapped paired array partial did not retain independent keys");
    }
  }
  Require(mapped_count == (extended ? 4U : 2U),
          "duplicate item or matched nested mapped calls were collapsed");
  const auto &membership = leaf.rows[0].sources[0].items[0].membership;
  Require(membership.rows.size() == (spec.kind == MappedKind::full_id_order ? 4U
              : spec.kind == MappedKind::null_match ||
                    spec.kind == MappedKind::unused_later ? 2U : 1U),
          "whole original descriptors were filtered to admitted rows");
  if (spec.kind == MappedKind::full_id_order)
    Require(membership.rows[0].admitted == false &&
                membership.rows[1].admitted == false &&
                membership.rows[2].admitted == true &&
                membership.rows[3].admitted == true &&
                membership.rows[2].key_identity != membership.rows[3].key_identity,
            "full pointer admission or equal-ID/different-pointer rows changed");
  const auto request_id = std::string("person-mapped42127e0-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_2922680\":{") != std::string::npos &&
              packet.find(request_id) != std::string::npos,
          "real whole terminal formatter lost mapped leaf");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original mapped whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_mapped_pc_42127e0_mcp_test output_directory\n";
    return 2;
  }
  try {
    const std::filesystem::path directory(argv[1]);
    std::error_code error;
    std::filesystem::create_directories(directory, error);
    Require(!error, "cannot create mapped packet output directory");
    std::uint64_t sequence = 0;
    for (const auto &spec : kMappedCases) ProduceMapped(directory, spec, ++sequence);
    std::cout << "person mapped42127e0: eleven fresh production whole-command packets\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "person mapped42127e0: " << error.what() << '\n';
    return 1;
  }
}
