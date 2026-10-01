// Reuse only the existing source-input fixture. Its 26-case main is not run.
#define main SwayOriginalInstallerFixtureMainNotExecuted
#include "ck3_12002_sway_completion_execution_install_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp"

namespace {
std::int32_t sink_scheme_identifier = 203;
std::int32_t sink_owner_identifier = 201;
std::int32_t sink_target_identifier = 202;
template <typename T> T SinkGet(const void *p, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
SwayInvalidationToken12002 *SinkLookup(
    const void *environment, SwayInvalidationToken12002 *out, std::int32_t identifier) {
  const auto *rows = SinkGet<const std::byte *>(environment, 0);
  const auto count = SinkGet<std::int32_t>(environment, 0x0C);
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = rows + static_cast<std::size_t>(index) * 0x20;
    if (SinkGet<std::int32_t>(row, 0) == identifier) {
      *out = SinkGet<SwayInvalidationToken12002>(row, 8);
      return out;
    }
  }
  *out = {};
  return out;
}
struct SecondarySinkContext {
  SwayInvalidationReasonBindings12002 bindings;
  SwayInvalidationReasonRecorder12002 recorder;
  SwayExecutionRecorder12002 *hidden_recorder = nullptr;
  std::size_t calls = 0;
  bool same_native_arguments = true;
  bool hidden_capture_precedes_sink = false;
  SwayInvalidationReasonCapture12002 last_capture = SwayInvalidationReasonCapture12002::ignored;
};
SecondarySinkContext *original_sink_context{};
bool source_capture_precedes_original = true;
SwayInvalidationReasonQuery12002 SinkQuery() { return {actor, target, scheme, 0}; }
void SecondarySink(void *owner, const void *effect, const void *context) noexcept {
  auto &sink = *static_cast<SecondarySinkContext *>(owner);
  ++sink.calls;
  sink.same_native_arguments = sink.same_native_arguments &&
      effect == expected_effect && context == expected_context;
  if (sink.calls == 1) {
    SwayExecutionQueryResult12002 hidden;
    sink.hidden_capture_precedes_sink = sink.hidden_recorder->Query(Query(), hidden) &&
        hidden.records.size() == 1;
  }
  sink.last_capture = CaptureAndRecordSwayInvalidationReason12002(
      sink.bindings, effect, context, sink.recorder);
}
void SecondaryOriginal(std::size_t index, const void *effect, const void *context) {
  ++original_calls[index];
  original_arguments_match = original_arguments_match &&
      effect == expected_effect && context == expected_context;
  auto &sink = *original_sink_context;
  if (index == 0) {
    SwayExecutionQueryResult12002 hidden;
    source_capture_precedes_original = source_capture_precedes_original &&
        sink.calls == 1 && sink.hidden_recorder->Query(Query(), hidden) &&
        hidden.records.size() == 1;
  } else if (index == 1) {
    SwayInvalidationReasonQueryResult12002 reason;
    source_capture_precedes_original = source_capture_precedes_original &&
        sink.calls == 2 && sink.recorder.Query(SinkQuery(), reason) &&
        reason.records.size() == 1;
  }
}
void SecondaryOriginal0(const void *e, const void *c) { SecondaryOriginal(0, e, c); }
void SecondaryOriginal1(const void *e, const void *c) { SecondaryOriginal(1, e, c); }
void SecondaryOriginal2(const void *e, const void *c) { SecondaryOriginal(2, e, c); }
const std::array<SwayCompletionNativeExecute12002, 3> secondary_originals{
    &SecondaryOriginal0, &SecondaryOriginal1, &SecondaryOriginal2};

struct ReasonInput {
  alignas(8) std::array<std::byte, 0xC0> effect{};
  alignas(8) std::array<std::byte, 0x80> child{};
  alignas(8) std::array<std::byte, 0x50> scalar{};
  std::array<void *, 1> children{child.data()};
  std::string *title{};
  std::string *reason{};
  ReasonInput() {
    names[701] = "send_interface_toast";
    names[702] = "custom_tooltip";
    Put(effect.data(), 0, base + kSwayExecutionToastVtableRva12002);
    Put(effect.data(), 8, std::int32_t{701});
    Put(effect.data(), 0x30, children.data());
    Put(effect.data(), 0x38, std::int32_t{1});
    Put(effect.data(), 0x3C, std::int32_t{1});
    Put(effect.data(), 0x60, base + kSwayExecutionTitleWrapperVtableRva12002);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(scalar.data(), 0, base + kSwayExecutionScalarLocalizationVtableRva12002);
    title = ::new (scalar.data() + 0x30) std::string("sway_invalidated_title");
    Put(child.data(), 0, base + 0x4931918);
    Put(child.data(), 8, std::int32_t{702});
    reason = ::new (child.data() + 0x50) std::string("sway_invalidated_dead");
  }
  ~ReasonInput() { std::destroy_at(title); std::destroy_at(reason); }
};
void SaveSinkReason(const std::filesystem::path &directory,
                    const SwayInvalidationReasonQueryResult12002 &result) {
  std::ofstream file(directory / "secondary-dead-reason-wire.json");
  file << SerializeSwayInvalidationReason12002(result) << '\n';
  Check(file.good(), "installed secondary sink serializes its actual copied reason query");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "artifact directory supplied");
    const std::filesystem::path output{argv[1]};
    Fixture f;
    SecondarySinkContext sink;
    sink.hidden_recorder = &f.recorder;
    sink.bindings.enabled = true;
    sink.bindings.image_base = base;
    sink.bindings.core = f.bindings.core;
    sink.bindings.lookup = &SinkLookup;
    sink.bindings.global_key = &GlobalCommandKey;
    sink.bindings.scheme_identifier = &sink_scheme_identifier;
    sink.bindings.owner_identifier = &sink_owner_identifier;
    sink.bindings.target_identifier = &sink_target_identifier;
    original_sink_context = &sink;
    // Only fixture-owned initial pointers are changed; actual installation below
    // performs the production helper's three pointer replacements.
    DWORD previous{}, ignored{};
    Check(VirtualProtect(f.page, 4096, PAGE_READWRITE, &previous) != FALSE,
          "fixture slot initialization permitted");
    for (std::size_t index = 0; index < f.slots.size(); ++index)
      *f.slots[index] = secondary_originals[index];
    Check(VirtualProtect(f.page, 4096, previous, &ignored) != FALSE,
          "fixture slot initialization restores readonly protection");
    Check(InstallSwayCompletionExecutionFixtureWithSecondarySink12002(
        f.bindings, f.slots, secondary_originals, f.recorder, f.installation,
        &SecondarySink, &sink) && f.recorder.ObserverAttached() &&
        !sink.recorder.ObserverAttached(),
        "one shared three-slot install attaches hidden recorder; root owns reason attachment");
    sink.recorder.SetObserverAttached(true);
    (*f.slots[0])(f.effect.data(), f.context.data());
    Check(sink.calls == 1 && sink.hidden_capture_precedes_sink &&
        sink.last_capture == SwayInvalidationReasonCapture12002::ignored &&
        original_calls[0] == 1,
        "hidden message captured before secondary sink and typed original once");
    ReasonInput reason;
    expected_effect = reason.effect.data();
    (*f.slots[1])(reason.effect.data(), f.context.data());
    Check(sink.calls == 2 && sink.last_capture == SwayInvalidationReasonCapture12002::captured &&
        original_calls[0] == 1 && original_calls[1] == 1 && original_calls[2] == 0 &&
        sink.same_native_arguments && original_arguments_match && source_capture_precedes_original,
        "same installed toast wrapper captures selected reason then forwards same inputs once");
    SwayExecutionQueryResult12002 hidden;
    SwayInvalidationReasonQueryResult12002 selected_reason;
    Check(f.recorder.Query(Query(), hidden) && hidden.records.size() == 1 &&
        hidden.records[0].source.branch == SwayExecutionSourceBranch12002::hidden_phase_success_source &&
        sink.recorder.Query(SinkQuery(), selected_reason) && selected_reason.records.size() == 1 &&
        selected_reason.records[0].source.branch ==
            SwayInvalidationNotificationBranch12002::target_dead_notification_source &&
        selected_reason.records[0].source.scheme_id == scheme &&
        selected_reason.records[0].source.actor_character_id == actor &&
        selected_reason.records[0].source.target_character_id == target,
        "both independent copied queries join the actual full generation SchemeID");
    Save(output, "secondary-hidden-success-wire.json", hidden);
    SaveSinkReason(output, selected_reason);
    sink.recorder.SetObserverAttached(false);
    Check(UninstallSwayCompletionExecution12002(f.installation) &&
        !f.recorder.ObserverAttached() && !sink.recorder.ObserverAttached() &&
        f.installation.secondary_sink == nullptr &&
        f.installation.secondary_sink_context == nullptr &&
        *f.slots[0] == secondary_originals[0] && *f.slots[1] == secondary_originals[1] &&
        *f.slots[2] == secondary_originals[2],
        "root detach plus existing stop clears sink and restores all typed originals");
    Check(!sink.recorder.Query(SinkQuery(), selected_reason) && !selected_reason.available,
          "stopped reason query does not claim attached source observation");
    std::cout << "PASS " << checks << " checks; one shared three-slot installer; hidden then secondary sink then original once; "
                 "actual hidden/dead reason copied queries; root detach and exact slot restoration; old matrices not run; no CK3 touched\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
