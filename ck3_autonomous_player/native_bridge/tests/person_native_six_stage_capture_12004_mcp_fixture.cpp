// AUTHORED_NOTRUN: fresh natural-event graphs through the production capture,
// same-query Person reader and whole-command formatter. No prior producer runs.
#define main PersonFollowing2922680SixStageMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include <span>

namespace {
enum class SixCaptureKind {
  unobserved, ordered, incomplete, pc_partial, wrong_generation, immutable,
  wrong_caller_original_once,
};
struct SixCaptureSpec { const char *name; SixCaptureKind kind; };
constexpr SixCaptureSpec kSixCaptureCases[] = {
    {"unobserved", SixCaptureKind::unobserved},
    {"six-ordered-negative-zero-wrap-weight", SixCaptureKind::ordered},
    {"three-stages-incomplete", SixCaptureKind::incomplete},
    {"one-admitted-pc-values-unread", SixCaptureKind::pc_partial},
    {"full-generation-not-borrowed", SixCaptureKind::wrong_generation},
    {"owned-pcs-after-source-and-model-mutation", SixCaptureKind::immutable},
    {"other-caller-originals-once-rax-and-args", SixCaptureKind::wrong_caller_original_once},
};
constexpr std::int64_t kSixWideValue =
    (std::numeric_limits<std::int64_t>::max)() - 8;
constexpr std::uintptr_t kSixCountReturn = std::uintptr_t{0xF1234567FFFFFFFDULL};
constexpr std::uintptr_t kSixAppendReturn = std::uintptr_t{0xDEADBEEF13572468ULL};
constexpr std::array<std::int32_t, 6> kSixRawCounts{
    7, -3, 0, (std::numeric_limits<std::int32_t>::max)(), -1,
    (std::numeric_limits<std::int32_t>::min)()};
// These are independently supplied natural append arguments. The fixture does
// not infer the loaded offset, gate result or second weight from a raw count.
constexpr std::array<std::int64_t, 6> kSixFirstWeights{
    700'000, -300'000, 0, 214'748'364'700'000LL, -100'000,
    -214'748'364'800'000LL};
constexpr std::array<std::int64_t, 6> kSixSecondWeights{
    800'000, -200'000, 100'000, -214'748'364'800'000LL, 0,
    -214'748'364'700'000LL};
std::size_t six_count_calls = 0;
std::size_t six_append_calls = 0;
void *six_original_character = nullptr;
void *six_original_context = nullptr;
void *six_original_pc = nullptr;
std::uint32_t six_original_index = 0;
std::int64_t six_original_weight = 0;

std::uintptr_t __fastcall SixCountOriginal(
    void *character, void *context, std::uint32_t index) {
  ++six_count_calls;
  six_original_character = character;
  six_original_context = context;
  six_original_index = index;
  return kSixCountReturn;
}
std::uintptr_t __fastcall SixAppendOriginal(
    void *context, void *pc, std::int64_t weight) {
  ++six_append_calls;
  six_original_context = context;
  six_original_pc = pc;
  six_original_weight = weight;
  return kSixAppendReturn;
}

struct SixCaptureWorld : World {
  std::array<std::array<void *, 2>, 6> pcs{};
  std::array<std::array<void *, 2>, 6> keys{};
  std::array<std::array<void *, 2>, 6> values{};
  void *capture_game_state_slot = memory.Allocate(sizeof(void *));
  void *capture_character_storage_slot = memory.Allocate(sizeof(void *));
  void *historical_model = nullptr;
  void *historical_context = nullptr;
  void *later_model = memory.Allocate(0xF0);
  native4::PersonSixStageCaptureBindings12004 capture_bindings{};

  SixCaptureWorld() {
    model = memory.Allocate(0xF0);
    historical_model = model;
    historical_context = Offset(model, 0x10);
    memory.Put(model, 8, subject);
    memory.Put(model, 0x10, static_cast<void *>(nullptr));
    memory.Put(scratch, 0x258, model);
    memory.Put(context, 0x198 + 0xC, std::int32_t{0});
    memory.Put(later_model, 8, subject);
    memory.Put(later_model, 0x10, static_cast<void *>(nullptr));
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
        {kSixWideValue, 0, -kSixWideValue, 4'294'967'296LL});
    capture_bindings.memory = bindings.current_person_carrier_direct;
    memory.Put(capture_game_state_slot, 0, game_state);
    capture_bindings.game_state_slot =
        reinterpret_cast<void **>(capture_game_state_slot);
    memory.Put(capture_character_storage_slot, 0, character_storage);
    six_count_calls = six_append_calls = 0;
    six_original_character = six_original_context = six_original_pc = nullptr;
    six_original_index = 0;
    six_original_weight = 0;
    Require(native4::InitializePersonSixStageCaptureFixture12004(
                capture_bindings, &SixCountOriginal, &SixAppendOriginal),
            "six-stage production fixture initialization failed");
  }
  void Capture(std::size_t count = 6) {
    for (std::size_t index = 0; index < count; ++index) {
      const auto raw_bits = std::uintptr_t{0xAABBCCDD00000000ULL} |
          static_cast<std::uint32_t>(kSixRawCounts[index]);
      native4::ObservePersonSixStageCapture12004(
          Address(subject), Address(historical_context),
          static_cast<std::uint32_t>(index), raw_bits,
          kModule + native4::kPersonSixStageReturnRva12004);
      if (index != 2)
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(pcs[index][0]),
            kSixFirstWeights[index],
            kModule + native4::kPersonSixStageFirstAppendReturnRva12004);
      if (index != 4)
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(pcs[index][1]),
            kSixSecondWeights[index],
            kModule + native4::kPersonSixStageSecondAppendReturnRva12004);
    }
    const auto open = native4::ReadPersonSixStageCaptureForCharacter12004(
        Address(subject), static_cast<std::uint32_t>(kSubject));
    Require(open.capture_observed && !open.capture_complete && !open.ready &&
                open.raw_counts_ready == (count == 6),
            "last count incorrectly completed the still-open native sequence");
    if (count > 2)
      Require(!open.stages[2].first_append_observed &&
                  !open.stages[2].first_pc.ready &&
                  !open.stages[2].first_pc.admitted,
              "open missing append was invented as a known native gate skip");
  }
  void Configure(SixCaptureKind kind) {
    switch (kind) {
    case SixCaptureKind::unobserved: break;
    case SixCaptureKind::incomplete: Capture(3); break;
    case SixCaptureKind::pc_partial:
      memory.Refuse(values[3][1], 0, 2 * 8, false);
      Capture();
      break;
    case SixCaptureKind::wrong_generation:
      memory.Put(subject, 0x18, std::uint32_t{0x05000003U});
      for (std::uint32_t index = 0; index < 6; ++index)
        native4::ObservePersonSixStageCapture12004(
            Address(subject), Address(historical_context), index, 9,
            kModule + native4::kPersonSixStageReturnRva12004);
      native4::CompletePersonSixStageCapture12004(
          Address(subject), 0x05000003U, Address(historical_context));
      memory.Put(subject, 0x18, static_cast<std::uint32_t>(kSubject));
      break;
    case SixCaptureKind::immutable:
      Capture();
      native4::CompletePersonSixStageCapture12004(
          Address(subject), static_cast<std::uint32_t>(kSubject),
          Address(historical_context));
      for (std::size_t index = 0; index < pcs.size(); ++index) {
        for (std::size_t role = 0; role < pcs[index].size(); ++role) {
          memory.Put(pcs[index][role], 0xC, std::int32_t{0});
          memory.Put(keys[index][role], 0, std::uint16_t{999});
          memory.Put(values[index][role], 0, std::int64_t{42});
        }
      }
      memory.Put(scratch, 0x258, later_model);
      model = later_model;
      break;
    case SixCaptureKind::wrong_caller_original_once: {
      native4::ObservePersonSixStageCapture12004(
          Address(subject), Address(historical_context), 0, kSixCountReturn,
          kModule + 0x291CEA8);
      const auto count_bits = native4::XarPersonSixStageHook12004V1(
          subject, historical_context, 0xFEDCBA98U);
      Require(count_bits == kSixCountReturn && six_count_calls == 1 &&
                  six_original_character == subject &&
                  six_original_context == historical_context &&
                  six_original_index == 0xFEDCBA98U,
              "count hook changed original call count, arguments or full RAX bits");
      const auto append_bits = native4::XarPersonSixStageAppendHook12004V1(
          historical_context, pcs[0][0], -214'748'364'800'000LL);
      Require(append_bits == kSixAppendReturn && six_append_calls == 1 &&
                  six_original_context == historical_context &&
                  six_original_pc == pcs[0][0] &&
                  six_original_weight == -214'748'364'800'000LL,
              "append hook changed original call count, arguments or full RAX bits");
      break;
    }
    default: Capture(); break;
    }
  }
};

void ProduceSixCapture(const std::filesystem::path &directory,
                       const SixCaptureSpec &spec, std::uint64_t sequence) {
  SixCaptureWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &person =
      *snapshot.character_observations->front().current_person_state;
  const std::array<std::int32_t, 1> requested_ids{World::kSubject};
  const auto source_before_collection = world.memory.Bytes();
  const auto captures = native4::CollectPersonSixStageQuery12004(
      reinterpret_cast<void **>(world.capture_character_storage_slot),
      std::span<const std::int32_t>{requested_ids},
      snapshot.snapshot_revision, snapshot.observed_date_raw);
  Require(captures.snapshot_revision == snapshot.snapshot_revision &&
              captures.observed_date_raw == snapshot.observed_date_raw &&
              captures.character_captures.size() == 1 &&
              world.memory.unexpected_reads == 0 &&
              world.memory.Bytes() == source_before_collection,
          "typed query sibling changed source revision, date or requested cardinality");
  const auto &leaf = captures.character_captures.front();
  const bool observed = spec.kind == SixCaptureKind::ordered ||
      spec.kind == SixCaptureKind::incomplete ||
      spec.kind == SixCaptureKind::pc_partial ||
      spec.kind == SixCaptureKind::immutable;
  const bool incomplete = spec.kind == SixCaptureKind::incomplete;
  const bool partial = spec.kind == SixCaptureKind::pc_partial;
  Require(leaf.configured && leaf.capture_observed == observed &&
              leaf.raw_counts_ready == (observed && !incomplete) &&
              leaf.ready == (observed && !incomplete && !partial) &&
              leaf.capture_complete == (observed && !incomplete) && leaf.historical_capture &&
              leaf.capture_sequence == (observed ? std::uint64_t{1} : std::uint64_t{0}) &&
              leaf.build_version == native4::kGameVersion &&
              leaf.executable_sha256 == native4::kExecutableSha256 &&
              !leaf.actual_model_write_performed && !leaf.full_helper_ready,
          "six-stage observation, completion or independent readiness changed");
  if (!observed) {
    Require(leaf.character_id == static_cast<std::uint32_t>(World::kSubject) &&
                !leaf.character_identity && !leaf.context_identity &&
                !leaf.capture_date_raw && !leaf.source_return_rva,
            "other full generation or caller borrowed a captured sequence");
  } else {
    Require(leaf.character_id == static_cast<std::uint32_t>(World::kSubject) &&
                leaf.character_identity == Address(world.subject) &&
                leaf.context_identity == Address(world.historical_context) &&
                leaf.capture_date_raw == World::kDate &&
                leaf.source_return_rva == native4::kPersonSixStageReturnRva12004,
            "six-stage owner, historical context, date or physical caller changed");
  }
  for (std::size_t index = 0; index < leaf.stages.size(); ++index) {
    const auto &stage = leaf.stages[index];
    const bool stage_observed = observed && (!incomplete || index < 3);
    Require(stage.index == index && stage.observed == stage_observed &&
                static_cast<bool>(stage.raw_count_i32) == stage_observed,
            "fixed six native indices or observed/unobserved distinction changed");
    if (!stage_observed) continue;
    Require(stage.raw_count_i32 == kSixRawCounts[index],
            "signed low DWORD raw callback result was widened or replaced");
    for (std::size_t role = 0; role < 2; ++role) {
      const auto &pc = role == 0 ? stage.first_pc : stage.second_pc;
      const bool appended = role == 0 ? index != 2 : index != 4;
      const bool pc_partial = partial && index == 3 && role == 1;
      Require((role == 0 ? stage.first_append_observed : stage.second_append_observed) ==
                  appended,
              "actual first/second append occurrence moved between native stages");
      if (!appended) {
        Require(pc.ready == !incomplete &&
                    (incomplete ? !pc.admitted : pc.admitted == false) &&
                    !pc.identity && !pc.count_i32 && !pc.properties,
                "absent native append lost closure or invented source/count inputs");
        continue;
      }
      const auto expected_weight = role == 0
          ? kSixFirstWeights[index]
          : kSixSecondWeights[index];
      Require(pc.admitted == true && pc.identity == Address(world.pcs[index][role]) &&
                  pc.count_i32 == (index == 0 && role == 0 ? 4 : 2) &&
                  pc.weight_q100000 == expected_weight && pc.ready == !pc_partial &&
                  pc.properties && pc.properties->keys_u16 &&
                  static_cast<bool>(pc.properties->values_q64) == !pc_partial,
              "captured admitted PC, full signed weight or independent partial copy changed");
      if (index == 0 && role == 0)
        Require(pc.properties->keys_u16 ==
                    std::vector<std::uint16_t>{129, 97, 129, 111} &&
                    pc.properties->values_q64 ==
                    std::vector<std::int64_t>{kSixWideValue, 0, -kSixWideValue,
                        4'294'967'296LL},
                "owned PC lost order, duplicate keys, zero or full signed64 values");
      if (pc_partial)
        Require(pc.reason == "pc_values_unread",
                "failed admitted values were silently promoted to known empty");
    }
  }
  if (spec.kind == SixCaptureKind::immutable)
    Require(leaf.context_identity != person.following_2922680->destination_pc_identity &&
                person.following_2922680->selected_model_identity ==
                    Address(world.later_model),
            "current replacement Model overwrote historical captured context");
  const auto expected_calls =
      spec.kind == SixCaptureKind::wrong_caller_original_once ? 1U : 0U;
  Require(six_count_calls == expected_calls && six_append_calls == expected_calls,
          "source-only capture replayed an original native callback or append");
  const auto request_id = std::string("person-native-six-stage-") + spec.name;
  const auto packet =
      xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultWithPersonSixStagesV1(
          request_id, World::kStep, sequence, snapshot, captures);
  Require(packet.find("\"person_six_stage_captures\":{") !=
              std::string::npos &&
              packet.find(native4::kPersonSixStageCaptureSchema12004) != std::string::npos,
          "whole-command formatter omitted native six-stage leaf/schema");
  std::ofstream output(directory / (std::string(spec.name) + ".json"),
      std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist six-stage whole-command packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_native_six_stage_capture_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create native six-stage output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kSixCaptureCases)
    ProduceSixCapture(directory, spec, ++sequence);
  std::cout << "person native six-stage capture: seven fresh whole-command packets\n";
  return 0;
}
