// AUTHORED_NOTRUN: five new classified-piety historical whole-query worlds.
// Reuse source infrastructure only; the included producer main never runs.
#define main PersonFollowing2922680ClassifiedPietyMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include <array>
#include <optional>
#include <span>

namespace {
enum class ClassifiedKind { signed_rows, zero_selections, value_unread, recapture, bypass };
struct ClassifiedSpec { const char *name; ClassifiedKind kind; };
constexpr ClassifiedSpec kClassifiedCases[] = {
    {"classified-piety-signed-scaled-duplicates", ClassifiedKind::signed_rows},
    {"classified-piety-zero-selections", ClassifiedKind::zero_selections},
    {"classified-piety-selected-value-unread-later-ready", ClassifiedKind::value_unread},
    {"classified-piety-new-sequence-retained", ClassifiedKind::recapture},
    {"classified-piety-observe-bypass-unobserved", ClassifiedKind::bypass},
};
constexpr std::uintptr_t kClassifiedBadPc = 0xF00DU;
constexpr std::array<std::int32_t, 6> kClassifiedCounts{
    std::int32_t{7}, std::int32_t{-3}, std::int32_t{0},
    (std::numeric_limits<std::int32_t>::max)(), std::int32_t{-1},
    (std::numeric_limits<std::int32_t>::min)()};
constexpr std::array<std::int32_t, 6> kClassifiedBases{
    std::int32_t{0}, std::int32_t{-7},
    (std::numeric_limits<std::int32_t>::max)(),
    (std::numeric_limits<std::int32_t>::min)(), std::int32_t{19}, std::int32_t{-1}};
constexpr std::array<std::int64_t, 6> kClassifiedFirstWeights{
    700'000LL, -300'000LL, 0LL, 214'748'364'700'000LL, -100'000LL,
    -214'748'364'800'000LL};
constexpr std::array<std::int64_t, 6> kClassifiedSecondWeights{
    800'000LL, -200'000LL, 100'000LL, -214'748'364'800'000LL, 0LL,
    -214'748'364'700'000LL};
constexpr std::array<std::int64_t, 4> kClassifiedScales{
    100'000LL, -100'000LL, -150'000LL, 100'000LL};

std::array<std::int64_t, 3> ClassifiedValues(std::uint32_t index, bool second) {
  if (second && index == std::uint32_t{4})
    return {214'748'364'850'000LL, 0LL, 0LL};
  if (second && index == std::uint32_t{5})
    return {(std::numeric_limits<std::int64_t>::max)(),
            (std::numeric_limits<std::int64_t>::min)(), 1LL};
  const auto stage = static_cast<std::int64_t>(index);
  return {second ? 1'300'000LL + stage * 100'000LL : 300'000LL + stage * 100'000LL,
          second ? -700'000LL - stage * 10'000LL : -200'000LL - stage * 10'000LL,
          second ? -900'000LL + stage * 10'000LL : -500'000LL + stage * 10'000LL};
}
std::uintptr_t ClassifiedReturnBits(std::uint32_t index) {
  return std::uintptr_t{0xBADC0FFE00000000ULL} |
      static_cast<std::uint32_t>(kClassifiedCounts[index]);
}
struct ClassifiedWorld;
ClassifiedWorld *classified_active_world = nullptr;
std::size_t classified_original_calls = 0;
void *classified_original_character = nullptr;
void *classified_original_context = nullptr;
std::uint32_t classified_original_index = 0;
std::uintptr_t __fastcall ClassifiedOriginal(void *, void *, std::uint32_t);
std::uintptr_t __fastcall ClassifiedAppendOriginal(void *, void *, std::int64_t) {
  return std::uintptr_t{0xDEADBEEF13572468ULL};
}

struct ClassifiedWorld : World {
  ClassifiedKind kind = ClassifiedKind::signed_rows;
  bool second_capture = false;
  std::optional<std::uint32_t> active_index;
  std::array<std::size_t, 6> header_reads{};
  std::array<std::size_t, 6> a_value_reads{};
  void *historical_context = nullptr;
  void *aggregate_pc = nullptr;
  void *rows = memory.Allocate(4 * 16);
  void *pc_a = memory.Allocate(0x70);
  void *pc_b = memory.Allocate(0x70);
  void *pc_c = memory.Allocate(0x70);
  void *empty_pc = memory.Allocate(0x70);
  void *keys_a = memory.Allocate(4 * 2);
  void *keys_b = memory.Allocate(2);
  void *keys_c = memory.Allocate(2);
  void *values_a = memory.Allocate(4 * 8);
  void *values_b = memory.Allocate(8);
  void *values_c = memory.Allocate(8);
  void *capture_game_slot = memory.Allocate(sizeof(void *));
  void *capture_character_slot = memory.Allocate(sizeof(void *));
  void *piety_key_table = memory.Allocate(48, kModule + 0x4807608);
  void *piety_threshold_slot = memory.Allocate(8, kModule + 0x54582D8);
  void *piety_threshold_count = memory.Allocate(4, kModule + 0x54582E4);
  void *piety_thresholds = memory.Allocate(24);
  native4::PersonSixStageCaptureBindings12004 capture_bindings{};

  ClassifiedWorld() {
    model = memory.Allocate(0xF0);
    historical_context = Offset(model, 0x10);
    aggregate_pc = Offset(historical_context, 0x68);
    memory.Put(model, 8, subject);
    memory.Put(model, 0x10, static_cast<void *>(nullptr));
    memory.Put(scratch, 0x258, model);
    memory.Put(context, 0x198 + 0xC, std::int32_t{0});
    Property(aggregate_pc, nullptr, nullptr, {}, {});
    Property(empty_pc, nullptr, nullptr, {}, {});
    memory.Put(piety_threshold_slot, 0, piety_thresholds);
    memory.Put(piety_threshold_count, 0, std::int32_t{3});
    for (std::size_t index = 0; index < std::size_t{3}; ++index)
      memory.Put(piety_thresholds, index * sizeof(std::int64_t),
                 static_cast<std::int64_t>(index) * 100LL);
    // The actual getter needs no PC access for FFFF and no arrays for count0.
    memory.Refuse(kClassifiedBadPc, 0x70);
    memory.Refuse(empty_pc, 0, sizeof(void *));
    memory.Refuse(empty_pc, 0x68, sizeof(void *));
    // Duplicate key129 must select its first physical occurrence only.
    memory.Refuse(values_a, 0, sizeof(std::int64_t));
    memory.Refuse(values_a, 2 * sizeof(std::int64_t), 2 * sizeof(std::int64_t));
    capture_bindings.memory = bindings.current_person_carrier_direct;
    capture_bindings.memory.read_memory = &ClassifiedWorld::Read;
    capture_bindings.memory.read_context = this;
    memory.Put(capture_game_slot, 0, game_state);
    capture_bindings.game_state_slot = reinterpret_cast<void **>(capture_game_slot);
    memory.Put(capture_character_slot, 0, character_storage);
    classified_original_calls = 0;
    classified_original_character = classified_original_context = nullptr;
    classified_original_index = 0;
    classified_active_world = this;
    Require(native4::InitializePersonSixStageCaptureFixture12004(
                capture_bindings, &ClassifiedOriginal, &ClassifiedAppendOriginal),
            "classified-piety production fixture initialization failed");
  }
  static bool Read(void *read_context, const void *source, void *destination,
                   std::size_t bytes) noexcept {
    auto &world = *static_cast<ClassifiedWorld *>(read_context);
    const auto address = Address(source);
    if (world.active_index) {
      const auto index = *world.active_index;
      if (address == Address(world.historical_context) + 0xC && bytes == sizeof(std::int32_t))
        ++world.header_reads[index];
      if (address >= Address(world.keys_a) && address < Address(world.keys_a) + 8)
        Require(bytes == sizeof(std::uint16_t), "classified lookup copied unrequested key arrays");
      if (address == Address(world.values_a) + 8 && bytes == sizeof(std::int64_t)) {
        ++world.a_value_reads[index];
        if (world.kind == ClassifiedKind::value_unread && index == std::uint32_t{2} &&
            world.a_value_reads[index] == std::size_t{1})
          return false;
      }
      if (world.kind == ClassifiedKind::zero_selections) {
        if (index == std::uint32_t{4} && address == Address(world.scratch) + 0x118 &&
            bytes == sizeof(std::int64_t))
          return false;
        if (index == std::uint32_t{5}) {
          if (address == kModule + 0x4807608 + 8 * index && bytes == sizeof(std::uint16_t))
            return false;
          Require(address != Address(world.historical_context),
                  "zero classified count demanded the row array pointer");
        }
      }
    }
    return Memory::Read(&world.memory, source, destination, bytes);
  }
  std::optional<std::uint16_t> ExpectedKey(std::uint32_t index) const {
    if (kind == ClassifiedKind::zero_selections) {
      if (index == std::uint32_t{5}) return std::nullopt;
      if (index == std::uint32_t{0} || index == std::uint32_t{3})
        return std::uint16_t{0xFFFF};
      if (index == std::uint32_t{2}) return std::uint16_t{130};
    }
    return std::uint16_t{129};
  }
  void InstallStage(std::uint32_t index) {
    const auto values = ClassifiedValues(index, second_capture);
    Property(pc_a, keys_a, values_a,
        {std::uint16_t{97}, std::uint16_t{129}, std::uint16_t{129}, std::uint16_t{200}},
        {111LL, values[0], -900'000LL, 222LL});
    Property(pc_b, keys_b, values_b, {std::uint16_t{129}}, {values[1]});
    Property(pc_c, keys_c, values_c, {std::uint16_t{129}}, {values[2]});
    const std::array<void *, 4> pcs{pc_a, pc_a, pc_b, pc_c};
    memory.Put(historical_context, 0, rows);
    memory.Put(historical_context, 0xC, std::int32_t{4});
    for (std::size_t row = 0; row < pcs.size(); ++row) {
      memory.Put(rows, row * 16, pcs[row]);
      memory.Put(rows, row * 16 + 8, kClassifiedScales[row]);
    }
    const auto key = ExpectedKey(index);
    memory.Put(piety_key_table, static_cast<std::size_t>(index) * 8,
               key.value_or(std::uint16_t{129}));
    memory.Put(scratch, 0x118, std::int64_t{100});
    memory.Put(scratch, 0x120, std::int32_t{-1});
    memory.Put(subject, 0xC0 + static_cast<std::size_t>(index) * 4, kClassifiedBases[index]);
    if (kind != ClassifiedKind::zero_selections) return;
    if (index == std::uint32_t{0} || index == std::uint32_t{3}) {
      memory.Put(historical_context, 0xC, std::int32_t{1});
      memory.Put(rows, 0, kClassifiedBadPc);
      memory.Put(rows, 8, std::int64_t{-100'000});
    } else if (index == std::uint32_t{1}) {
      memory.Put(historical_context, 0xC, std::int32_t{1});
      memory.Put(rows, 0, empty_pc);
      memory.Put(rows, 8, std::int64_t{200'000});
    } else if (index == std::uint32_t{2}) {
      memory.Put(historical_context, 0xC, std::int32_t{1});
      memory.Put(rows, 0, pc_a);
      memory.Put(rows, 8, std::int64_t{100'000});
    } else if (index == std::uint32_t{5}) {
      memory.Put(historical_context, 0xC, std::int32_t{0});
    }
  }
  void OriginalMutation(std::uint32_t index) {
    const bool full_rows = kind != ClassifiedKind::zero_selections || index == std::uint32_t{4};
    Require(header_reads[index] == std::size_t{1} &&
                a_value_reads[index] == (full_rows ? std::size_t{2} : std::size_t{0}),
            "original callback ran before its classified row inputs were copied");
    memory.Put(historical_context, 0xC, std::int32_t{0});
    memory.Put(rows, 8, std::int64_t{42});
    memory.Put(values_a, 8, std::int64_t{42'424'242});
    memory.Put(values_b, 0, std::int64_t{43'434'343});
    memory.Put(values_c, 0, std::int64_t{44'444'444});
    memory.Put(piety_key_table, static_cast<std::size_t>(index) * 8, std::uint16_t{65'534});
    memory.Put(scratch, 0x118, std::int64_t{10'000});
    memory.Put(scratch, 0x120, std::int32_t{0});
    memory.Put(subject, 0xC0 + static_cast<std::size_t>(index) * 4, std::int32_t{-999});
    if (index + std::uint32_t{1} < std::uint32_t{6})
      InstallStage(index + std::uint32_t{1});
  }
  void Capture(bool bypass) {
    header_reads = {};
    a_value_reads = {};
    InstallStage(std::uint32_t{0});
    for (std::uint32_t index = 0; index < std::uint32_t{6}; ++index) {
      active_index = index;
      if (bypass) {
        native4::ObservePersonSixStageCapture12004(
            Address(subject), Address(historical_context), index,
            ClassifiedReturnBits(index), kModule + native4::kPersonSixStageReturnRva12004);
      } else {
        const auto before = classified_original_calls;
        const auto returned = native4::InvokePersonSixStageCapture12004(
            subject, historical_context, index,
            kModule + native4::kPersonSixStageReturnRva12004);
        Require(returned == ClassifiedReturnBits(index) &&
                    classified_original_calls == before + std::size_t{1} &&
                    classified_original_character == subject &&
                    classified_original_context == historical_context && classified_original_index == index,
                "classified publication changed original forwarding, count or full RAX");
      }
      active_index.reset();
      if (index != std::uint32_t{2})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(empty_pc), kClassifiedFirstWeights[index],
            kModule + native4::kPersonSixStageFirstAppendReturnRva12004);
      if (index != std::uint32_t{4})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(empty_pc), kClassifiedSecondWeights[index],
            kModule + native4::kPersonSixStageSecondAppendReturnRva12004);
    }
    native4::CompletePersonSixStageCapture12004(
        Address(subject), static_cast<std::uint32_t>(kSubject), Address(historical_context));
  }
  void Configure(ClassifiedKind selected) {
    kind = selected;
    Capture(kind == ClassifiedKind::bypass);
    if (kind != ClassifiedKind::recapture) return;
    const auto first = native4::ReadPersonSixStageCaptureForCharacter12004(
        Address(subject), static_cast<std::uint32_t>(kSubject));
    Require(first.capture_sequence == std::uint64_t{1} &&
                first.classified_piety_inputs[0].ready &&
                first.classified_piety_inputs[0].rows[0].raw_value_q64 == std::int64_t{300'000} &&
                first.classified_piety_inputs[5].rows[0].raw_value_q64 == std::int64_t{800'000},
            "first sequence did not own each historical classified value");
    second_capture = true;
    Capture(false);
    Require(first.classified_piety_inputs[0].rows[0].raw_value_q64 == std::int64_t{300'000} &&
                first.classified_piety_inputs[5].rows[0].raw_value_q64 == std::int64_t{800'000},
            "new sequence mutated the preceding owned classified rows");
  }
  void MutateAfterQuery() {
    memory.Put(historical_context, 0xC, std::int32_t{-1});
    memory.Put(rows, 8, std::int64_t{-7});
    memory.Put(values_a, 8, std::int64_t{-8});
    memory.Put(values_b, 0, std::int64_t{-9});
    memory.Put(values_c, 0, std::int64_t{-10});
  }
};

std::uintptr_t __fastcall ClassifiedOriginal(void *character, void *context,
                                          std::uint32_t index) {
  ++classified_original_calls;
  classified_original_character = character;
  classified_original_context = context;
  classified_original_index = index;
  Require(classified_active_world != nullptr && index < std::uint32_t{6},
          "classified fixture original received an unexpected native index");
  classified_active_world->OriginalMutation(index);
  return ClassifiedReturnBits(index);
}

void CheckClassifiedStage(const ClassifiedWorld &world,
                         const native4::PersonSixStageClassifiedPietyStage12004 &stage,
                         std::uint32_t index) {
  const bool bypass = world.kind == ClassifiedKind::bypass;
  const bool zero = world.kind == ClassifiedKind::zero_selections;
  const bool partial = world.kind == ClassifiedKind::value_unread && index == std::uint32_t{2};
  Require(stage.index == index && stage.observed == !bypass,
          "classified stage lost its physical index or observation");
  if (bypass) {
    Require(!stage.ready && stage.reason == "classified_piety_unobserved" &&
                !stage.property_key_u16 && !stage.row_count_i32 &&
                !stage.row_array_identity && stage.rows.empty(),
            "legacy direct Observe fabricated pre-call classified operands");
    return;
  }
  const auto expected_count = zero ? index == std::uint32_t{5} ? std::int32_t{0}
      : index == std::uint32_t{4} ? std::int32_t{4} : std::int32_t{1} : std::int32_t{4};
  Require(stage.property_key_u16 == world.ExpectedKey(index) &&
              stage.row_count_i32 == expected_count && stage.ready == !partial &&
              stage.reason == (partial ? "classified_piety_rows_partial" : "") &&
              stage.rows.size() == static_cast<std::size_t>(expected_count),
          "classified stage lost zero, selected-value partial or later readiness");
  if (expected_count == 0) {
    Require(!stage.row_array_identity, "classified zero count fabricated a row-array demand");
    return;
  }
  Require(stage.row_array_identity == Address(world.rows), "classified row-array identity changed");
  if (zero && index != std::uint32_t{4}) {
    const auto &row = stage.rows.front();
    const bool sentinel = index == std::uint32_t{0} || index == std::uint32_t{3};
    const bool empty = index == std::uint32_t{1};
    Require(row.native_index == std::uint32_t{0} && row.ready && row.reason.empty() &&
                row.lookup_selection == (sentinel ? "sentinel" : empty ? "empty" : "absent") &&
                row.pc_identity == (sentinel ? kClassifiedBadPc :
                    empty ? Address(world.empty_pc) : Address(world.pc_a)) &&
                row.pc_count_i32 == (sentinel ? std::nullopt :
                    std::optional<std::int32_t>{empty ? std::int32_t{0} : std::int32_t{4}}) &&
                !row.selected_index_u32 && row.raw_value_q64 == std::int64_t{0} &&
                row.scale_q64 == (sentinel ? std::int64_t{-100'000} :
                    empty ? std::int64_t{200'000} : std::int64_t{100'000}),
            "sentinel, empty PC or residual absent lookup did not retain a proved zero");
    return;
  }
  const auto values = ClassifiedValues(index, world.second_capture);
  const std::array<std::int64_t, 4> raw{values[0], values[0], values[1], values[2]};
  const std::array<std::uintptr_t, 4> pcs{
      Address(world.pc_a), Address(world.pc_a), Address(world.pc_b), Address(world.pc_c)};
  for (std::size_t row_index = 0; row_index < stage.rows.size(); ++row_index) {
    const auto &row = stage.rows[row_index];
    const bool unread = partial && row_index == std::size_t{0};
    Require(row.native_index == static_cast<std::uint32_t>(row_index) && row.ready == !unread &&
                row.reason == (unread ? "classified_pc_value_unread" : "") &&
                row.lookup_selection == "mapped" && row.pc_identity == pcs[row_index] &&
                row.pc_count_i32 == (row_index < std::size_t{2} ? std::int32_t{4} : std::int32_t{1}) &&
                row.selected_index_u32 == (row_index < std::size_t{2} ? std::uint32_t{1} : std::uint32_t{0}) &&
                row.raw_value_q64 == (unread ? std::nullopt : std::optional<std::int64_t>{raw[row_index]}) &&
                row.scale_q64 == kClassifiedScales[row_index],
            "classified rows lost native order, duplicate first match or partial value");
  }
}

void ProduceClassified(const std::filesystem::path &directory,
                       const ClassifiedSpec &spec, std::uint64_t sequence) {
  ClassifiedWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const std::array<std::int32_t, 1> requested_ids{World::kSubject};
  const auto source_before = world.memory.Bytes();
  const auto captures = native4::CollectPersonSixStageQuery12004(
      reinterpret_cast<void **>(world.capture_character_slot), std::span<const std::int32_t>{requested_ids},
      snapshot.snapshot_revision, snapshot.observed_date_raw);
  Require(world.memory.unexpected_reads == std::size_t{0} && world.memory.Bytes() == source_before &&
              captures.character_captures.size() == std::size_t{1},
          "classified whole query changed source bytes, copied unrequested values or lost full ID");
  const auto &leaf = captures.character_captures.front();
  const bool bypass = spec.kind == ClassifiedKind::bypass;
  const bool recapture = spec.kind == ClassifiedKind::recapture;
  Require(leaf.ready && leaf.capture_complete && leaf.raw_counts_ready &&
              leaf.capture_sequence == (recapture ? std::uint64_t{2} : std::uint64_t{1}) &&
              leaf.character_identity == Address(world.subject) &&
              leaf.context_identity == Address(world.historical_context) &&
              leaf.base_point_inputs.ready == !bypass &&
              leaf.preparation_model.ready == !bypass &&
              leaf.aggregate_postimage_inputs_ready == !bypass &&
              leaf.aggregate_postimage_comparison_ready == !bypass &&
              !leaf.actual_model_write_performed && !leaf.full_helper_ready &&
              classified_original_calls == (bypass ? std::size_t{0} : recapture ? std::size_t{12} : std::size_t{6}),
          "classified input publication changed old six-stage readiness or original calls");
  for (std::uint32_t index = 0; index < std::uint32_t{6}; ++index) {
    CheckClassifiedStage(world, leaf.classified_piety_inputs[index], index);
    const auto &raw = leaf.stages[index];
    Require(raw.observed && raw.raw_count_i32 == kClassifiedCounts[index] &&
                raw.first_append_observed == (index != std::uint32_t{2}) &&
                raw.second_append_observed == (index != std::uint32_t{4}) &&
                raw.first_pc.ready && raw.second_pc.ready &&
                leaf.base_point_inputs.observed[index] == !bypass &&
                leaf.base_point_inputs.values_i32[index] == (bypass ? std::nullopt :
                    std::optional<std::int32_t>{kClassifiedBases[index]}),
            "classified partial source hid an independently captured base, raw count or append");
    const auto &category = leaf.piety_category_inputs[index];
    const bool category_unread = spec.kind == ClassifiedKind::zero_selections && index == std::uint32_t{4};
    const bool key_unread = spec.kind == ClassifiedKind::zero_selections && index == std::uint32_t{5};
    Require(category.observed == !bypass && category.ready == (!bypass && !category_unread && !key_unread) &&
                category.property_key_u16 == (bypass ? std::nullopt : world.ExpectedKey(index)) &&
                category.category_i32 == (bypass || category_unread ? std::nullopt :
                    std::optional<std::int32_t>{std::int32_t{2}}) &&
                category.reason == (bypass ? "piety_category_unobserved" :
                    category_unread ? "piety_category_source_unread" : key_unread ? "piety_property_key_unread" : ""),
            "classified observations changed the independently available piety category");
  }
  if (spec.kind == ClassifiedKind::signed_rows || recapture) {
    world.MutateAfterQuery();
    const auto mutated_source = world.memory.Bytes();
    const auto repeated = native4::CollectPersonSixStageQuery12004(
        reinterpret_cast<void **>(world.capture_character_slot), std::span<const std::int32_t>{requested_ids},
        snapshot.snapshot_revision, snapshot.observed_date_raw);
    Require(repeated == captures && world.memory.Bytes() == mutated_source &&
                world.memory.unexpected_reads == std::size_t{0},
            "repeat query replaced immutable pre-call classified inputs with current memory");
  }
  const auto packet =
      xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultWithPersonSixStagesV1(
          std::string("person-classified-piety-") + spec.name, World::kStep, sequence, snapshot, captures);
  Require(packet.find("\"classified_piety_inputs\":{") != std::string::npos,
          "whole production serializer omitted classified historical piety inputs");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist classified-piety whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_six_stage_classified_piety_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create classified-piety whole-packet directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kClassifiedCases) ProduceClassified(directory, spec, ++sequence);
  std::cout << "person classified piety inputs: five new whole-command packets\n";
  return 0;
}
