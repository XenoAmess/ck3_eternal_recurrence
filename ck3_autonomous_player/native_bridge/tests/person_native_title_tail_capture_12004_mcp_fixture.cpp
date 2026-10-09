// Source preparation: six new historical capture worlds through the genuine
// observer, same-query reader and whole-command formatter. No old producer runs.
#define main PersonFollowing2922680HistoricalMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_title_tail_capture.hpp"

namespace {
enum class TailCaptureKind { unobserved, ordered, wrong_caller, wrong_owner, pc_partial, immutable };
struct TailCaptureSpec { const char *name; TailCaptureKind kind; };
constexpr TailCaptureSpec kTailCaptureCases[] = {
    {"unobserved", TailCaptureKind::unobserved},
    {"matching-final-tail-ordered-i64", TailCaptureKind::ordered},
    {"per-title-caller-ignored-original-once", TailCaptureKind::wrong_caller},
    {"other-owner-generation-not-borrowed", TailCaptureKind::wrong_owner},
    {"prepared-pc-values-unread", TailCaptureKind::pc_partial},
    {"immutable-capture-after-source-mutation", TailCaptureKind::immutable},
};
constexpr std::int64_t kWideValue = (std::numeric_limits<std::int64_t>::max)() - 8;
constexpr std::uintptr_t kOriginalReturn = std::uintptr_t{0xF123456789ABCDEFULL};
std::size_t original_calls = 0;
void *original_model = nullptr;
void *original_source = nullptr;
std::uintptr_t __fastcall CaptureOriginal(void *model, void *source_pc) {
  ++original_calls; original_model = model; original_source = source_pc;
  return kOriginalReturn;
}

struct TailCaptureWorld : World {
  void *prepared_pc = memory.Allocate(0x70);
  void *prepared_keys = memory.Allocate(4 * 2);
  void *prepared_values = memory.Allocate(4 * 8);
  void *aggregate_keys = memory.Allocate(2 * 2);
  void *aggregate_values = memory.Allocate(2 * 8);
  void *other_character = memory.Allocate(0x1D8);
  void *later_model = memory.Allocate(0xF0);
  void *capture_game_state_slot = memory.Allocate(sizeof(void *));
  void *captured_model = nullptr;
  native4::PersonTitleTailCaptureBindings12004 capture_bindings{};

  TailCaptureWorld() {
    model = memory.Allocate(0xF0);
    captured_model = model;
    memory.Put(model, 8, subject); memory.Put(scratch, 0x258, model);
    memory.Put(model, 0x10, static_cast<void *>(nullptr));
    memory.Put(context, 0x198 + 0xC, std::int32_t{0});
    Property(prepared_pc, prepared_keys, prepared_values,
             {125, 97, 125, 111}, {kWideValue, 0, -kWideValue, 4'294'967'296LL});
    Property(Offset(model, 0x78), aggregate_keys, aggregate_values,
             {125, 126}, {900'000, -700'000});
    memory.Put(later_model, 8, subject);
    memory.Put(later_model, 0x10, static_cast<void *>(nullptr));
    memory.Put(other_character, 0x18, std::uint32_t{0x04000004U});
    capture_bindings.memory = bindings.current_person_carrier_direct;
    memory.Put(capture_game_state_slot, 0, game_state);
    capture_bindings.game_state_slot = reinterpret_cast<void **>(capture_game_state_slot);
    original_calls = 0; original_model = original_source = nullptr;
    Require(native4::InitializePersonTitleTailCaptureFixture12004(capture_bindings, &CaptureOriginal),
            "production capture fixture initialization failed");
  }
  void Capture() {
    native4::ObservePersonTitleTailCapture12004(
        Address(model), Address(prepared_pc), kModule + native4::kPersonTitleTailReturnRva12004);
  }
  void Configure(TailCaptureKind kind) {
    switch (kind) {
    case TailCaptureKind::unobserved: break;
    case TailCaptureKind::wrong_caller: {
      native4::ObservePersonTitleTailCapture12004(
          Address(model), Address(prepared_pc), kModule + 0x291EF47);
      const auto bits = native4::XarPersonTitleTailHook12004V1(model, prepared_pc);
      Require(bits == kOriginalReturn && original_calls == std::size_t{1} &&
                  original_model == model && original_source == prepared_pc,
              "production hook changed original arguments, call count or RAX return bits");
      break;
    }
    case TailCaptureKind::wrong_owner: {
      memory.Put(model, 8, other_character);
      Capture();
      memory.Put(model, 8, subject);
      memory.Put(subject, 0x18, std::uint32_t{0x05000003U});
      Capture();
      memory.Put(subject, 0x18, static_cast<std::uint32_t>(kSubject));
      break;
    }
    case TailCaptureKind::pc_partial:
      memory.Refuse(prepared_values, 0, 4 * 8, false);
      Capture();
      break;
    case TailCaptureKind::immutable:
      memory.Refuse(aggregate_values, 0, 2 * 8, false);
      Capture();
      // A later current Model and rewritten source cannot replace owned history.
      memory.Put(scratch, 0x258, later_model);
      memory.Put(prepared_pc, 0xC, std::int32_t{0});
      memory.Put(prepared_keys, 0, std::uint16_t{999});
      memory.Put(prepared_values, 0, std::int64_t{42});
      memory.Put(model, 8, other_character);
      memory.Put(model, 0x84, std::int32_t{0});
      model = later_model;
      break;
    default: Capture(); break;
    }
  }
};

void ProduceTailCapture(const std::filesystem::path &directory,
                        const TailCaptureSpec &spec, std::uint64_t sequence) {
  TailCaptureWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_291e3a0_captured_tail.has_value(),
          "same-query native Title-tail capture leaf missing");
  const auto &leaf = *person.following_291e3a0_captured_tail;
  const bool observed = spec.kind == TailCaptureKind::ordered ||
      spec.kind == TailCaptureKind::pc_partial || spec.kind == TailCaptureKind::immutable;
  const bool partial = spec.kind == TailCaptureKind::pc_partial;
  const bool immutable = spec.kind == TailCaptureKind::immutable;
  Require(leaf.configured && leaf.capture_observed == observed &&
              leaf.ready == (observed && !partial) &&
              leaf.reason == (!observed ? "native_title_tail_unobserved"
                  : partial ? "prepared_pc_partial" : "") &&
              leaf.capture_sequence == (observed ? std::uint64_t{1} : std::uint64_t{0}) &&
              leaf.build_version == native4::kGameVersion &&
              leaf.executable_sha256 == native4::kExecutableSha256 &&
              leaf.weight_q100000 == std::int64_t{100'000} &&
              !leaf.actual_model_write_performed && !leaf.full_helper_ready,
          "capture observation, sequence, exact build or independent readiness changed");
  if (!observed) {
    Require(!leaf.capture_date_raw && !leaf.model_identity && !leaf.source_return_rva &&
                !leaf.inline_destination_identity && !leaf.prepared_pc.ready &&
                leaf.prepared_pc.reason == "pc_unobserved" &&
                !leaf.prepared_pc.identity && !leaf.prepared_pc.count_i32 &&
                !leaf.prepared_pc.properties,
            "unobserved owner/generation borrowed historical capture data");
  } else {
    Require(leaf.capture_date_raw == std::int32_t{World::kDate} &&
                leaf.character_id == static_cast<std::uint32_t>(World::kSubject) &&
                leaf.character_identity == Address(world.subject) &&
                leaf.model_identity == Address(world.captured_model) &&
                leaf.source_return_rva == native4::kPersonTitleTailReturnRva12004 &&
                leaf.inline_destination_identity == Address(world.captured_model) + 0x10,
            "historical stage attribution or native final caller changed");
    const auto &pc = leaf.prepared_pc;
    Require(pc.admitted == true && pc.identity == Address(world.prepared_pc) &&
                pc.count_i32 == std::int32_t{4} && pc.ready == !partial &&
                pc.reason == (partial ? "pc_values_unread" : "") &&
                pc.weight_q100000 == std::int64_t{100'000} && pc.properties &&
                pc.properties->keys_u16 == std::vector<std::uint16_t>{125, 97, 125, 111} &&
                static_cast<bool>(pc.properties->values_q64) == !partial,
            "prepared PC source order, duplicate/zero keys or partial pair changed");
    if (!partial)
      Require(pc.properties->values_q64 ==
                  std::vector<std::int64_t>{kWideValue, 0, -kWideValue, 4'294'967'296LL},
              "owned prepared PC lost full signed64, zero or immutable values");
    const auto &aggregate = leaf.model_aggregate_pc;
    Require(aggregate.identity == Address(world.captured_model) + 0x78 &&
                aggregate.count_i32 == std::int32_t{2} && aggregate.ready == !immutable &&
                aggregate.reason == (immutable ? "pc_values_unread" : "") &&
                aggregate.properties &&
                aggregate.properties->keys_u16 == std::vector<std::uint16_t>{125, 126} &&
                static_cast<bool>(aggregate.properties->values_q64) == !immutable,
            "diagnostic aggregate readiness gated or replaced the prepared capture");
    if (!immutable)
      Require(aggregate.properties->values_q64 == std::vector<std::int64_t>{900'000, -700'000},
              "diagnostic aggregate values changed");
    else
      Require(leaf.model_identity != person.following_2922680->selected_model_identity &&
                  person.following_2922680->selected_model_identity == Address(world.later_model),
              "later current Model was relabeled as the historical captured stage");
  }
  Require(original_calls == (spec.kind == TailCaptureKind::wrong_caller
              ? std::size_t{1} : std::size_t{0}),
          "fixture observer invoked the original wrapper or forwarded it more than once");
  const auto request_id = std::string("person-native-title-tail-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_291e3a0_captured_tail\":{") != std::string::npos,
          "production whole-command formatter omitted copied historical record");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original native Title-tail whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_native_title_tail_capture_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create native Title-tail output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kTailCaptureCases) ProduceTailCapture(directory, spec, ++sequence);
  std::cout << "person native Title-tail capture: six fresh production whole-command packets\n";
  return 0;
}
