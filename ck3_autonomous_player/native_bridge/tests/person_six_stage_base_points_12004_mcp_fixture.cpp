// AUTHORED_NOTRUN: four new historical base/piety-source whole-command worlds.
// Reuse synthetic memory infrastructure only; the included producer never runs.
#define main PersonFollowing2922680BasePointsMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include <array>
#include <optional>
#include <span>

namespace {
enum class BasePointsKind { mutation, index2_unread, observe_bypass, recapture };
struct BasePointsSpec { const char *name; BasePointsKind kind; };
constexpr BasePointsSpec kBasePointsCases[] = {
    {"base-before-each-original-mutation", BasePointsKind::mutation},
    {"base-index2-unread-six-ready", BasePointsKind::index2_unread},
    {"base-observe-bypass-unobserved", BasePointsKind::observe_bypass},
    {"base-same-owner-new-capture-retained", BasePointsKind::recapture},
};
constexpr std::size_t kBasePointsOffset = 192;
constexpr std::size_t kBasePointsStride = 4;
constexpr std::array<std::int32_t, 6> kBasePointsFirst{
    std::int32_t{0}, std::int32_t{-7},
    (std::numeric_limits<std::int32_t>::max)(),
    (std::numeric_limits<std::int32_t>::min)(),
    std::int32_t{19}, std::int32_t{-1}};
constexpr std::array<std::int32_t, 6> kBasePointsSecond{
    (std::numeric_limits<std::int32_t>::min)(),
    (std::numeric_limits<std::int32_t>::max)(),
    std::int32_t{-11}, std::int32_t{0}, std::int32_t{23}, std::int32_t{-29}};
constexpr std::array<std::int32_t, 6> kBasePointsCounts{
    std::int32_t{7}, std::int32_t{-3}, std::int32_t{0},
    (std::numeric_limits<std::int32_t>::max)(), std::int32_t{-1},
    (std::numeric_limits<std::int32_t>::min)()};
constexpr std::array<std::int64_t, 6> kBasePointsFirstWeights{
    700'000LL, -300'000LL, 0LL, 214'748'364'700'000LL, -100'000LL,
    -214'748'364'800'000LL};
constexpr std::array<std::int64_t, 6> kBasePointsSecondWeights{
    800'000LL, -200'000LL, 100'000LL, -214'748'364'800'000LL, 0LL,
    -214'748'364'700'000LL};
constexpr std::array<std::int64_t, 6> kPietyScores{
    -1LL, 0LL, 99LL, 100LL, 200LL,
    (std::numeric_limits<std::int64_t>::max)()};
constexpr std::array<std::int32_t, 6> kPietyCaps{-1, -1, 1, 1, 2, -1};
constexpr std::array<std::int32_t, 6> kPietyCategories{0, 1, 1, 1, 0, 3};

std::uintptr_t BasePointsReturnBits(std::uint32_t index) {
  return std::uintptr_t{0xBADC0FFE00000000ULL} |
      static_cast<std::uint32_t>(kBasePointsCounts[index]);
}
std::array<std::optional<std::int32_t>, 6> BasePointsExpectedValues(
    const std::array<std::int32_t, 6> &values) {
  std::array<std::optional<std::int32_t>, 6> result{};
  for (std::size_t index = 0; index < result.size(); ++index)
    result[index] = values[index];
  return result;
}
struct BasePointsWorld;
BasePointsWorld *base_points_active_world = nullptr;
std::size_t base_points_original_calls = 0;
void *base_points_original_character = nullptr;
void *base_points_original_context = nullptr;
std::uint32_t base_points_original_index = 0;
std::uintptr_t __fastcall BasePointsOriginal(void *, void *, std::uint32_t);
std::uintptr_t __fastcall BasePointsAppendOriginal(void *, void *, std::int64_t) {
  return std::uintptr_t{0xDEADBEEF13572468ULL};
}

struct BasePointsWorld : World {
  BasePointsKind kind = BasePointsKind::mutation;
  std::array<std::int32_t, 6> expected_values = kBasePointsFirst;
  std::array<std::size_t, 6> base_read_attempts{};
  std::array<std::optional<std::int32_t>, 6> copied_base_values{};
  std::optional<std::uint32_t> active_index;
  void *historical_context = nullptr;
  void *aggregate_pc = nullptr;
  void *empty_pc = memory.Allocate(0x70);
  void *capture_game_slot = memory.Allocate(sizeof(void *));
  void *capture_character_slot = memory.Allocate(sizeof(void *));
  void *piety_key_table = memory.Allocate(48, kModule + 0x4807608);
  void *piety_threshold_slot = memory.Allocate(8, kModule + 0x54582D8);
  void *piety_threshold_count = memory.Allocate(4, kModule + 0x54582E4);
  void *piety_thresholds = memory.Allocate(24);
  native4::PersonSixStageCaptureBindings12004 capture_bindings{};

  BasePointsWorld() {
    model = memory.Allocate(0xF0);
    historical_context = Offset(model, 0x10);
    aggregate_pc = Offset(historical_context, 0x68);
    memory.Put(model, 8, subject);
    memory.Put(model, 0x10, static_cast<void *>(nullptr));
    memory.Put(scratch, 0x258, model);
    memory.Put(context, 0x198 + 0xC, std::int32_t{0});
    Property(aggregate_pc, nullptr, nullptr, {}, {});
    Property(empty_pc, nullptr, nullptr, {}, {});
    capture_bindings.memory = bindings.current_person_carrier_direct;
    capture_bindings.memory.read_memory = &BasePointsWorld::Read;
    capture_bindings.memory.read_context = this;
    memory.Put(capture_game_slot, 0, game_state);
    capture_bindings.game_state_slot = reinterpret_cast<void **>(capture_game_slot);
    memory.Put(capture_character_slot, 0, character_storage);
    memory.Put(piety_threshold_slot, 0, piety_thresholds);
    memory.Put(piety_threshold_count, 0, std::int32_t{3});
    for (std::size_t index = 0; index < std::size_t{3}; ++index)
      memory.Put(piety_thresholds, index * sizeof(std::int64_t),
                 static_cast<std::int64_t>(index) * 100LL);
    for (std::size_t index = 0; index < std::size_t{6}; ++index)
      memory.Put(piety_key_table, index * std::size_t{8},
                 static_cast<std::uint16_t>(101U + index));
    base_points_original_calls = 0;
    base_points_original_character = base_points_original_context = nullptr;
    base_points_original_index = 0;
    base_points_active_world = this;
    Require(native4::InitializePersonSixStageCaptureFixture12004(
                capture_bindings, &BasePointsOriginal, &BasePointsAppendOriginal),
            "base-point production fixture initialization failed");
  }
  static bool Read(void *read_context, const void *source, void *destination,
                   std::size_t bytes) noexcept {
    auto &world = *static_cast<BasePointsWorld *>(read_context);
    const auto address = Address(source);
    if (world.kind == BasePointsKind::index2_unread &&
        world.active_index == std::uint32_t{2} &&
        address == Address(world.scratch) + 0x118 && bytes == sizeof(std::int64_t))
      return false;
    const auto first = Address(world.subject) + kBasePointsOffset;
    if (address >= first && address < first + kBasePointsFirst.size() * kBasePointsStride) {
      Require(bytes == sizeof(std::int32_t) &&
                  (address - first) % kBasePointsStride == std::size_t{0},
              "base operands were copied as more than one aligned DWORD");
      const auto index = (address - first) / kBasePointsStride;
      Require(world.active_index &&
                  static_cast<std::size_t>(*world.active_index) == index,
              "base operand was copied outside its exact current-stage Invoke");
      ++world.base_read_attempts[index];
      const bool copied = Memory::Read(&world.memory, source, destination, bytes);
      if (copied) {
        std::int32_t value{};
        std::memcpy(&value, destination, sizeof(value));
        world.copied_base_values[index] = value;
      }
      return copied;
    }
    return Memory::Read(&world.memory, source, destination, bytes);
  }
  void SetInputs(const std::array<std::int32_t, 6> &values) {
    expected_values = values;
    base_read_attempts = {};
    copied_base_values = {};
    // Only stage0 is initially correct. Each original callback seeds the next
    // stage; a six-slot snapshot taken before stage0 cannot satisfy this case.
    for (std::size_t index = 0; index < values.size(); ++index)
      memory.Put(subject, kBasePointsOffset + index * kBasePointsStride,
                 std::int32_t{500} + static_cast<std::int32_t>(index));
    memory.Put(subject, kBasePointsOffset, values.front());
    SetPietyInput(0);
  }
  void SetPietyInput(std::size_t index) {
    memory.Put(subject, 0x1B0, index == std::size_t{4} ? nullptr : scratch);
    memory.Put(scratch, 0x118, kPietyScores[index]);
    memory.Put(scratch, 0x120, kPietyCaps[index]);
  }
  void OriginalMutation(std::uint32_t index) {
    const auto slot = static_cast<std::size_t>(index);
    const bool unread = kind == BasePointsKind::index2_unread &&
        index == std::uint32_t{2};
    Require(base_read_attempts[slot] == std::size_t{1} &&
                copied_base_values[slot].has_value() == !unread &&
                (unread || copied_base_values[slot] == expected_values[slot]),
            "original callback ran without exactly one current-stage pre-read");
    memory.Put(subject, kBasePointsOffset + slot * kBasePointsStride,
               std::int32_t{700} + static_cast<std::int32_t>(index));
    if (slot + std::size_t{1} < expected_values.size())
      memory.Put(subject, kBasePointsOffset + (slot + std::size_t{1}) * kBasePointsStride,
                 expected_values[slot + std::size_t{1}]);
    if (slot + std::size_t{1} < expected_values.size())
      SetPietyInput(slot + std::size_t{1});
  }
  void Capture(bool bypass) {
    for (std::uint32_t index = 0; index < std::uint32_t{6}; ++index) {
      active_index = index;
      if (bypass) {
        native4::ObservePersonSixStageCapture12004(
            Address(subject), Address(historical_context), index,
            BasePointsReturnBits(index), kModule + native4::kPersonSixStageReturnRva12004);
      } else {
        const auto before = base_points_original_calls;
        const auto returned = native4::InvokePersonSixStageCapture12004(
            subject, historical_context, index,
            kModule + native4::kPersonSixStageReturnRva12004);
        Require(returned == BasePointsReturnBits(index) &&
                    base_points_original_calls == before + std::size_t{1} &&
                    base_points_original_character == subject &&
                    base_points_original_context == historical_context &&
                    base_points_original_index == index,
                "Invoke changed original call count, arguments or full RAX");
      }
      active_index.reset();
      if (index != std::uint32_t{2})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(empty_pc), kBasePointsFirstWeights[index],
            kModule + native4::kPersonSixStageFirstAppendReturnRva12004);
      if (index != std::uint32_t{4})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(empty_pc), kBasePointsSecondWeights[index],
            kModule + native4::kPersonSixStageSecondAppendReturnRva12004);
    }
    native4::CompletePersonSixStageCapture12004(
        Address(subject), static_cast<std::uint32_t>(kSubject),
        Address(historical_context));
  }
  void Configure(BasePointsKind selected) {
    kind = selected;
    if (kind == BasePointsKind::index2_unread)
      memory.Refuse(subject, kBasePointsOffset + std::size_t{2} * kBasePointsStride,
                    sizeof(std::int32_t), false);
    SetInputs(kBasePointsFirst);
    Capture(kind == BasePointsKind::observe_bypass);
    if (kind != BasePointsKind::recapture) return;
    const auto first = native4::ReadPersonSixStageCaptureForCharacter12004(
        Address(subject), static_cast<std::uint32_t>(kSubject));
    Require(first.capture_sequence == std::uint64_t{1} &&
                first.base_point_inputs.ready &&
                first.base_point_inputs.values_i32 == BasePointsExpectedValues(kBasePointsFirst),
            "first owner capture did not retain its six historical base operands");
    SetInputs(kBasePointsSecond);
    Capture(false);
    Require(first.capture_sequence == std::uint64_t{1} &&
                first.base_point_inputs.values_i32 == BasePointsExpectedValues(kBasePointsFirst) &&
                first.character_identity == Address(subject) &&
                first.context_identity == Address(historical_context),
            "same-owner recapture mutated the preceding owned base operands");
  }
  void MutateAfterQuery() {
    for (std::size_t index = 0; index < expected_values.size(); ++index)
      memory.Put(subject, kBasePointsOffset + index * kBasePointsStride,
                 std::int32_t{123'000} + static_cast<std::int32_t>(index));
    memory.Put(scratch, 0x118, std::int64_t{-9'000});
    memory.Put(scratch, 0x120, std::int32_t{0});
    memory.Put(piety_thresholds, 0, std::int64_t{9'999});
  }
};

std::uintptr_t __fastcall BasePointsOriginal(void *character, void *context,
                                           std::uint32_t index) {
  ++base_points_original_calls;
  base_points_original_character = character;
  base_points_original_context = context;
  base_points_original_index = index;
  Require(base_points_active_world != nullptr && index < std::uint32_t{6},
          "fixture original received an unexpected native index");
  base_points_active_world->OriginalMutation(index);
  return BasePointsReturnBits(index);
}

void ProduceBasePoints(const std::filesystem::path &directory,
                       const BasePointsSpec &spec, std::uint64_t sequence) {
  BasePointsWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const std::array<std::int32_t, 1> requested_ids{World::kSubject};
  const auto source_before = world.memory.Bytes();
  const auto captures = native4::CollectPersonSixStageQuery12004(
      reinterpret_cast<void **>(world.capture_character_slot),
      std::span<const std::int32_t>{requested_ids}, snapshot.snapshot_revision,
      snapshot.observed_date_raw);
  Require(world.memory.unexpected_reads == std::size_t{0} &&
              world.memory.Bytes() == source_before &&
              captures.character_captures.size() == std::size_t{1},
          "whole-query collection changed source bytes or requested cardinality");
  const auto &leaf = captures.character_captures.front();
  const bool bypass = spec.kind == BasePointsKind::observe_bypass;
  const bool unread = spec.kind == BasePointsKind::index2_unread;
  const bool recapture = spec.kind == BasePointsKind::recapture;
  const auto &base = leaf.base_point_inputs;
  auto expected_values = BasePointsExpectedValues(recapture ? kBasePointsSecond : kBasePointsFirst);
  std::array<bool, 6> expected_observed{};
  if (bypass) expected_values = {};
  else expected_observed.fill(true);
  if (unread) expected_values[2].reset();
  Require(leaf.ready && leaf.raw_counts_ready && leaf.capture_complete &&
              leaf.capture_sequence == (recapture ? std::uint64_t{2} : std::uint64_t{1}) &&
              leaf.character_identity == Address(world.subject) &&
              leaf.context_identity == Address(world.historical_context) &&
              leaf.pre_six_aggregate.observed == !bypass &&
              leaf.pre_six_aggregate.pc.ready == !bypass &&
              leaf.post_six_aggregate.observed && leaf.post_six_aggregate.pc.ready &&
              leaf.preparation_model.ready == !bypass &&
              leaf.aggregate_postimage_inputs_ready == !bypass &&
              leaf.aggregate_postimage_comparison_ready == !bypass &&
              !leaf.actual_model_write_performed && !leaf.full_helper_ready,
          "base availability changed independent native six-stage readiness");
  Require(base.observed == expected_observed && base.values_i32 == expected_values &&
              base.ready == (!bypass && !unread) &&
              base.reason == (bypass ? "base_point_unobserved" :
                              unread ? "base_point_unread" : ""),
          "historical base inputs lost signed values, availability or ownership");
  Require(base_points_original_calls == (bypass ? std::size_t{0} :
              recapture ? std::size_t{12} : std::size_t{6}),
          "base input publication replayed or skipped an original callback");
  for (std::size_t index = 0; index < leaf.stages.size(); ++index) {
    const auto &stage = leaf.stages[index];
    Require(stage.index == static_cast<std::uint32_t>(index) && stage.observed &&
                stage.raw_count_i32 == kBasePointsCounts[index] &&
                stage.first_append_observed == (index != std::size_t{2}) &&
                stage.second_append_observed == (index != std::size_t{4}) &&
                stage.first_pc.ready && stage.second_pc.ready &&
                world.base_read_attempts[index] == (bypass ? std::size_t{0} : std::size_t{1}),
            "base failure hid a later base, raw count or native append stage");
    const auto &category = leaf.piety_category_inputs[index];
    const bool category_unread = unread && index == std::size_t{2};
    Require(category.observed == !bypass && category.ready == (!bypass && !category_unread) &&
                category.category_i32 == (bypass || category_unread
                    ? std::nullopt : std::optional<std::int32_t>{kPietyCategories[index]}) &&
                category.property_key_u16 == (bypass ? std::nullopt
                    : std::optional<std::uint16_t>{static_cast<std::uint16_t>(101U + index)}) &&
                category.reason == (bypass ? "piety_category_unobserved"
                    : category_unread ? "piety_category_source_unread" : ""),
            "piety category lost its natural per-stage key, boundary, cap or availability");
    if (!bypass && index == std::size_t{4})
      Require(category.extension_identity == std::uintptr_t{0} &&
                  !category.score_q64 && !category.cap_i32 &&
                  !category.threshold_count_i32 && category.thresholds_used_q64.empty(),
              "native null piety extension fabricated resource operands");
  }
  if (spec.kind == BasePointsKind::mutation || recapture) {
    world.MutateAfterQuery();
    const auto mutated_source = world.memory.Bytes();
    const auto repeated = native4::CollectPersonSixStageQuery12004(
        reinterpret_cast<void **>(world.capture_character_slot),
        std::span<const std::int32_t>{requested_ids}, snapshot.snapshot_revision,
        snapshot.observed_date_raw);
    Require(repeated == captures && world.memory.Bytes() == mutated_source &&
                world.memory.unexpected_reads == std::size_t{0},
            "repeat whole query replaced owned pre-call bases with later memory");
  }
  const auto packet =
      xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultWithPersonSixStagesV1(
          std::string("person-six-stage-base-points-") + spec.name,
          World::kStep, sequence, snapshot, captures);
  Require(packet.find("\"base_point_inputs\":{") != std::string::npos &&
              packet.find("\"source_stage\":\"before_each_original_count\"") != std::string::npos &&
              packet.find("\"character_offset\":192") != std::string::npos &&
              packet.find("\"stride_bytes\":4") != std::string::npos,
          "whole production formatter omitted the historical base operand contract");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist historical base whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_six_stage_base_points_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create historical base whole-packet directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kBasePointsCases)
    ProduceBasePoints(directory, spec, ++sequence);
  std::cout << "person six-stage base inputs: four new whole-command packets\n";
  return 0;
}
