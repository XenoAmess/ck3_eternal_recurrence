// AUTHORED_NOTRUN: six new worlds through the production Invoke/capture/query.
// Reuse only the old synthetic World; its main and producer are never invoked.
#define main PersonFollowing2922680PreSixMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include <array>
#include <limits>
#include <span>

namespace {
enum class PreSixKind { mutation, empty, partial, bypass, wrong_caller, recapture };
struct PreSixSpec { const char *name; PreSixKind kind; };
constexpr PreSixSpec kPreSixCases[] = {
    {"baseline-before-original-mutation", PreSixKind::mutation},
    {"baseline-observed-empty", PreSixKind::empty},
    {"baseline-values-unread-six-ready", PreSixKind::partial},
    {"observe-bypass-lacks-baseline", PreSixKind::bypass},
    {"wrong-caller-original-once", PreSixKind::wrong_caller},
    {"same-owner-new-capture-fresh-baseline", PreSixKind::recapture},
};
constexpr std::int64_t kPreSixWide =
    (std::numeric_limits<std::int64_t>::max)() - 8;
constexpr std::array<std::int32_t, 6> kPreSixCounts{
    7, -3, 0, (std::numeric_limits<std::int32_t>::max)(), -1,
    (std::numeric_limits<std::int32_t>::min)()};
constexpr std::array<std::int64_t, 6> kPreSixFirstWeights{
    700'000, -300'000, 0, 214'748'364'700'000LL, -100'000,
    -214'748'364'800'000LL};
constexpr std::array<std::int64_t, 6> kPreSixSecondWeights{
    800'000, -200'000, 100'000, -214'748'364'800'000LL, 0,
    -214'748'364'700'000LL};
std::uintptr_t PreSixReturnBits(std::uint32_t index) {
  return std::uintptr_t{0xBADC0FFE00000000ULL} |
      static_cast<std::uint32_t>(kPreSixCounts[index]);
}
struct PreSixWorld;
PreSixWorld *pre_six_active_world = nullptr;
std::size_t pre_six_original_calls = 0;
void *pre_six_original_character = nullptr;
void *pre_six_original_context = nullptr;
std::uint32_t pre_six_original_index = 0;
std::uintptr_t __fastcall PreSixOriginal(void *, void *, std::uint32_t);
std::uintptr_t __fastcall PreSixAppendOriginal(void *, void *, std::int64_t) {
  return std::uintptr_t{0xDEADBEEF13572468ULL};
}

struct PreSixWorld : World {
  PreSixKind kind = PreSixKind::mutation;
  bool second_capture = false;
  std::array<std::array<void *, 2>, 6> pcs{};
  std::array<std::array<void *, 2>, 6> keys{};
  std::array<std::array<void *, 2>, 6> values{};
  void *historical_context = nullptr;
  void *aggregate_pc = nullptr;
  void *baseline_keys = memory.Allocate(4 * 2);
  void *baseline_values = memory.Allocate(4 * 8);
  void *post_keys = memory.Allocate(4 * 2);
  void *post_values = memory.Allocate(4 * 8);
  void *capture_game_slot = memory.Allocate(sizeof(void *));
  void *capture_character_slot = memory.Allocate(sizeof(void *));
  native4::PersonSixStageCaptureBindings12004 capture_bindings{};

  PreSixWorld() {
    model = memory.Allocate(0xF0);
    historical_context = Offset(model, 0x10);
    aggregate_pc = Offset(historical_context, 0x68);
    memory.Put(model, 8, subject);
    memory.Put(model, 0x10, static_cast<void *>(nullptr));
    memory.Put(scratch, 0x258, model);
    memory.Put(context, 0x198 + 0xC, std::int32_t{0});
    for (std::size_t index = 0; index < pcs.size(); ++index) {
      for (std::size_t role = 0; role < pcs[index].size(); ++role) {
        pcs[index][role] = memory.Allocate(0x70);
        keys[index][role] = memory.Allocate(4 * 2);
        values[index][role] = memory.Allocate(4 * 8);
        Property(pcs[index][role], keys[index][role], values[index][role],
            {static_cast<std::uint16_t>(100 + index * 2 + role), 129},
            {static_cast<std::int64_t>(index * 10 + role), -17});
      }
    }
    Property(pcs[0][0], keys[0][0], values[0][0], {129, 97, 129, 111},
        {kPreSixWide, 0, -kPreSixWide, 4'294'967'296LL});
    SetBaselineA();
    capture_bindings.memory = bindings.current_person_carrier_direct;
    memory.Put(capture_game_slot, 0, game_state);
    capture_bindings.game_state_slot = reinterpret_cast<void **>(capture_game_slot);
    memory.Put(capture_character_slot, 0, character_storage);
    pre_six_original_calls = 0;
    pre_six_original_character = pre_six_original_context = nullptr;
    pre_six_original_index = 0;
    pre_six_active_world = this;
    Require(native4::InitializePersonSixStageCaptureFixture12004(
                capture_bindings, &PreSixOriginal, &PreSixAppendOriginal),
            "pre-six production fixture initialization failed");
  }
  void SetBaselineA() {
    Property(aggregate_pc, baseline_keys, baseline_values, {129, 97, 129, 111},
        {kPreSixWide, 0, -kPreSixWide, 4'294'967'296LL});
  }
  void SetBaselineB() {
    Property(aggregate_pc, baseline_keys, baseline_values, {222, 129, 222},
        {75, 0, -75});
  }
  void InstallPost() {
    if (kind == PreSixKind::empty)
      Property(aggregate_pc, post_keys, post_values, {}, {});
    else if (second_capture)
      Property(aggregate_pc, post_keys, post_values, {222, 129}, {-50, 25});
    else
      Property(aggregate_pc, post_keys, post_values, {129, 111, 129}, {44, 0, -44});
  }
  void OriginalMutation(std::uint32_t index) {
    if (index == std::uint32_t{0} && kind != PreSixKind::empty) {
      memory.Put(aggregate_pc, 0xC, std::int32_t{0});
      memory.Put(baseline_keys, 0, std::uint16_t{999});
      memory.Put(baseline_values, 0, std::int64_t{42});
    }
    if (index == std::uint32_t{5}) InstallPost();
  }
  void Capture(bool bypass_first = false) {
    for (std::uint32_t index = 0; index < std::uint32_t{6}; ++index) {
      if (bypass_first && index == std::uint32_t{0}) {
        native4::ObservePersonSixStageCapture12004(
            Address(subject), Address(historical_context), index,
            PreSixReturnBits(index), kModule + native4::kPersonSixStageReturnRva12004);
      } else {
        const auto before = pre_six_original_calls;
        const auto returned = native4::InvokePersonSixStageCapture12004(
            subject, historical_context, index,
            kModule + native4::kPersonSixStageReturnRva12004);
        Require(returned == PreSixReturnBits(index) &&
                    pre_six_original_calls == before + std::size_t{1} &&
                    pre_six_original_character == subject &&
                    pre_six_original_context == historical_context &&
                    pre_six_original_index == index,
                "Invoke changed original call count, arguments or full RAX");
      }
      if (index != std::uint32_t{2})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(pcs[index][0]),
            kPreSixFirstWeights[index],
            kModule + native4::kPersonSixStageFirstAppendReturnRva12004);
      if (index != std::uint32_t{4})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(pcs[index][1]),
            kPreSixSecondWeights[index],
            kModule + native4::kPersonSixStageSecondAppendReturnRva12004);
    }
  }
  void Complete() {
    native4::CompletePersonSixStageCapture12004(
        Address(subject), static_cast<std::uint32_t>(kSubject),
        Address(historical_context));
  }
  void MutateAfterCompletion() {
    memory.Put(aggregate_pc, 0xC, std::int32_t{0});
    memory.Put(post_keys, 0, std::uint16_t{60000});
    memory.Put(post_values, 0, std::int64_t{123456});
  }
  void Configure(PreSixKind selected) {
    kind = selected;
    if (kind == PreSixKind::mutation || kind == PreSixKind::empty) {
      for (std::size_t index = 0; index < pcs.size(); ++index)
        for (std::size_t role = 0; role < pcs[index].size(); ++role)
          Property(pcs[index][role], keys[index][role], values[index][role], {}, {});
    }
    if (kind == PreSixKind::empty)
      Property(aggregate_pc, baseline_keys, baseline_values, {}, {});
    if (kind == PreSixKind::partial)
      memory.Refuse(baseline_values, 0, 4 * 8, false);
    if (kind == PreSixKind::wrong_caller) {
      const auto result = native4::InvokePersonSixStageCapture12004(
          subject, historical_context, std::uint32_t{0},
          kModule + native4::kPersonSixStageReturnRva12004 - std::uintptr_t{1});
      Require(result == PreSixReturnBits(std::uint32_t{0}) &&
                  pre_six_original_calls == std::size_t{1} &&
                  pre_six_original_character == subject &&
                  pre_six_original_context == historical_context &&
                  pre_six_original_index == std::uint32_t{0},
              "wrong caller changed original forwarding or full return bits");
      return;
    }
    Capture(kind == PreSixKind::bypass);
    Complete();
    if (kind == PreSixKind::recapture) {
      const auto first = native4::ReadPersonSixStageCaptureForCharacter12004(
          Address(subject), static_cast<std::uint32_t>(kSubject));
      Require(first.capture_sequence == std::uint64_t{1} &&
                  first.pre_six_aggregate.pc.properties &&
                  first.post_six_aggregate.pc.properties &&
                  first.pre_six_aggregate.pc.properties->values_q64 ==
                      std::vector<std::int64_t>{kPreSixWide, 0, -kPreSixWide, 4'294'967'296LL},
              "first owner capture did not retain its baseline");
      second_capture = true;
      SetBaselineB();
      Capture();
      Complete();
      Require(first.post_six_aggregate.pc.properties->values_q64 ==
                  std::vector<std::int64_t>{44, 0, -44},
              "second capture mutated the first owned completion copy");
    }
    if (kind == PreSixKind::mutation || kind == PreSixKind::recapture)
      MutateAfterCompletion();
  }
};

std::uintptr_t __fastcall PreSixOriginal(void *character, void *context,
                                      std::uint32_t index) {
  ++pre_six_original_calls;
  pre_six_original_character = character;
  pre_six_original_context = context;
  pre_six_original_index = index;
  Require(pre_six_active_world != nullptr && index < std::uint32_t{6},
          "fixture original received an unexpected native index");
  pre_six_active_world->OriginalMutation(index);
  return PreSixReturnBits(index);
}

void ProducePreSix(const std::filesystem::path &directory, const PreSixSpec &spec,
                   std::uint64_t sequence) {
  PreSixWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const std::array<std::int32_t, 1> requested_ids{World::kSubject};
  const auto source_before = world.memory.Bytes();
  const auto captures = native4::CollectPersonSixStageQuery12004(
      reinterpret_cast<void **>(world.capture_character_slot),
      std::span<const std::int32_t>{requested_ids}, snapshot.snapshot_revision,
      snapshot.observed_date_raw);
  Require(world.memory.unexpected_reads == 0 && world.memory.Bytes() == source_before &&
              captures.character_captures.size() == std::size_t{1},
          "whole-query collection changed source bytes or requested cardinality");
  const auto &leaf = captures.character_captures.front();
  const bool wrong = spec.kind == PreSixKind::wrong_caller;
  const bool baseline_observed = !wrong && spec.kind != PreSixKind::bypass;
  const bool partial = spec.kind == PreSixKind::partial;
  const bool inputs_ready = baseline_observed && !partial;
  Require(leaf.ready == !wrong && leaf.capture_complete == !wrong &&
              leaf.raw_counts_ready == !wrong &&
              leaf.pre_six_aggregate.observed == baseline_observed &&
              leaf.pre_six_aggregate.pc.ready == inputs_ready &&
              leaf.post_six_aggregate.observed == !wrong &&
              leaf.post_six_aggregate.pc.ready == !wrong &&
              leaf.aggregate_postimage_inputs_ready == inputs_ready &&
              leaf.aggregate_postimage_comparison_ready == inputs_ready &&
              !leaf.actual_model_write_performed && !leaf.full_helper_ready,
          "baseline/completion readiness changed independent six-stage readiness");
  const auto expected_sequence = wrong ? std::uint64_t{0} :
      spec.kind == PreSixKind::recapture ? std::uint64_t{2} : std::uint64_t{1};
  const auto expected_calls = wrong ? std::size_t{1} :
      spec.kind == PreSixKind::bypass ? std::size_t{5} :
      spec.kind == PreSixKind::recapture ? std::size_t{12} : std::size_t{6};
  Require(leaf.capture_sequence == expected_sequence &&
              pre_six_original_calls == expected_calls,
          "capture reuse or original call count changed");
  if (baseline_observed) {
    const auto &pc = leaf.pre_six_aggregate.pc;
    Require(pc.identity == Address(world.aggregate_pc) && pc.properties &&
                pc.properties->keys_u16 &&
                static_cast<bool>(pc.properties->values_q64) == !partial,
            "baseline identity or independently copied arrays changed");
    if (partial)
      Require(pc.count_i32 == std::int32_t{4} && pc.reason == "pc_values_unread",
              "unread baseline values became a known empty baseline");
    else if (spec.kind == PreSixKind::empty)
      Require(pc.count_i32 == std::int32_t{0} && pc.properties->keys_u16->empty() &&
                  pc.properties->values_q64->empty(),
              "observed empty baseline became unavailable");
    else if (spec.kind == PreSixKind::recapture)
      Require(pc.properties->keys_u16 == std::vector<std::uint16_t>{222, 129, 222} &&
                  pc.properties->values_q64 == std::vector<std::int64_t>{75, 0, -75},
              "fresh owner capture borrowed the preceding baseline");
    else
      Require(pc.properties->keys_u16 == std::vector<std::uint16_t>{129, 97, 129, 111} &&
                  pc.properties->values_q64 == std::vector<std::int64_t>{
                      kPreSixWide, 0, -kPreSixWide, 4'294'967'296LL},
              "original callback mutation overwrote the before-original baseline");
  }
  if (!wrong) {
    const auto &post = leaf.post_six_aggregate.pc;
    Require(post.identity == Address(world.aggregate_pc) && post.properties &&
                post.properties->keys_u16 && post.properties->values_q64,
            "same-thread completion did not retain its copied PC");
    const auto expected_values = spec.kind == PreSixKind::empty
        ? std::vector<std::int64_t>{}
        : spec.kind == PreSixKind::recapture ? std::vector<std::int64_t>{-50, 25}
                                           : std::vector<std::int64_t>{44, 0, -44};
    Require(post.properties->values_q64 == expected_values,
            "repeat completion recaptured a mutated source postimage");
  }
  const auto packet =
      xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultWithPersonSixStagesV1(
          std::string("person-pre-six-baseline-") + spec.name,
          World::kStep, sequence, snapshot, captures);
  Require(packet.find("\"pre_six_aggregate\":{") != std::string::npos &&
              packet.find("\"post_six_aggregate\":{") != std::string::npos,
          "whole production formatter omitted aggregate observations");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist pre-six whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_pre_six_baseline_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create pre-six whole-packet directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kPreSixCases) ProducePreSix(directory, spec, ++sequence);
  std::cout << "person pre-six baseline: six new whole-command packets\n";
  return 0;
}
