#define main SwayTerminationFixtureMainNotExecuted
#include "ck3_12002_sway_completion_termination_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp"

#include <new>

namespace {
std::int32_t scheme_identifier = 103, owner_identifier = 101, target_identifier = 102;
std::string global_toast_command = "send_interface_toast";
std::string global_tooltip_command = "custom_tooltip";
std::string global_description_command = "custom_description_no_bullet";
std::size_t global_getter_calls{}, native_lookup_calls{};
const std::string *ReasonGlobalKey(std::int32_t id) {
  ++global_getter_calls;
  return id == 7 ? &global_toast_command : id == 8 ? &global_tooltip_command :
      id == 9 ? &global_description_command : nullptr;
}
template <typename T> T GetFixture(const void *p, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + at, sizeof(value)); return value;
}
SwayInvalidationToken12002 *ReasonNativeLookup(const void *environment,
    SwayInvalidationToken12002 *out, std::int32_t id) {
  ++native_lookup_calls;
  const auto env_data = GetFixture<const std::byte *>(environment, 0);
  const auto env_count = GetFixture<std::int32_t>(environment, 0x0C);
  for (std::int32_t i = 0; i < env_count; ++i) {
    const auto *row = env_data + static_cast<std::size_t>(i) * 0x20;
    if (GetFixture<std::int32_t>(row, 0) == id) { *out = GetFixture<SwayInvalidationToken12002>(row, 8); return out; }
  }
  const auto *script = GetFixture<const std::byte *>(environment, 0x3D0);
  const auto *data = GetFixture<const std::byte *>(script, 0x18);
  const auto count = GetFixture<std::int32_t>(script, 0x24);
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *row = data + static_cast<std::size_t>(i) * 0x18;
    if (GetFixture<std::int32_t>(row, 0) == id) { *out = GetFixture<SwayInvalidationToken12002>(row, 8); return out; }
  }
  *out = {}; return out;
}
struct InvalidationReasonFixture {
  TerminationFixture core_fixture;
  std::array<std::byte, 0xC0> effect{};
  std::array<std::byte, 0x80> child{};
  std::array<std::byte, 0x50> scalar{};
  std::array<void *, 1> children{child.data()};
  std::array<std::byte, 0x400> environment{};
  std::array<std::byte, 0x28> script{};
  std::array<std::byte, 2 * 0x20> env_rows{};
  std::array<std::byte, 3 * 0x18> script_rows{};
  std::array<std::byte, 0x30> context{};
  SwayInvalidationToken12002 root{4, 0, 0, actor};
  std::string *title_key{}, *reason_key{};
  SwayInvalidationReasonBindings12002 bindings;
  SwayInvalidationReasonRecorder12002 recorder;
  std::size_t original_calls{};
  InvalidationReasonFixture() {
    Put(effect.data(), 0, base + 0x4837428);
    Put(effect.data(), 8, std::int32_t{7});
    Put(effect.data(), 0x0C, std::uint8_t{0});
    Put(effect.data(), 0x30, children.data());
    Put(effect.data(), 0x38, std::int32_t{1});
    Put(effect.data(), 0x3C, std::int32_t{1});
    Put(effect.data(), 0x60, base + 0x48BD0B0);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(scalar.data(), 0, base + 0x4929F08);
    title_key = ::new (scalar.data() + 0x30) std::string("sway_invalidated_title");
    Put(child.data(), 0, base + 0x4931918);
    Put(child.data(), 8, std::int32_t{8});
    reason_key = ::new (child.data() + 0x50) std::string("sway_invalidated_dead");
    Put(environment.data(), 0, env_rows.data());
    Put(environment.data(), 8, std::int32_t{2});
    Put(environment.data(), 0x0C, std::int32_t{2});
    Put(environment.data(), 0x3D0, script.data());
    Put(script.data(), 0x18, script_rows.data());
    Put(script.data(), 0x20, std::int32_t{3});
    Put(script.data(), 0x24, std::int32_t{3});
    Put(env_rows.data(), 0, owner_identifier);
    Put(env_rows.data(), 8, SwayInvalidationToken12002{4, 0, 0, actor});
    Put(env_rows.data(), 0x20, target_identifier);
    Put(env_rows.data(), 0x28, SwayInvalidationToken12002{4, 0, 0, target});
    Put(script_rows.data(), 0, scheme_identifier);
    Put(script_rows.data(), 8, SwayInvalidationToken12002{9, 0, 0, scheme});
    // Wrong older owner/target values prove native effective Env32 overrides.
    Put(script_rows.data(), 0x18, owner_identifier);
    Put(script_rows.data(), 0x20, SwayInvalidationToken12002{4, 0, 0, 0x70000005});
    Put(script_rows.data(), 0x30, target_identifier);
    Put(script_rows.data(), 0x38, SwayInvalidationToken12002{4, 0, 0, 0x70000006});
    Put(context.data(), 0, &root);
    Put(context.data(), 0x10, script.data());
    Put(context.data(), 0x18, environment.data());
    bindings = {true, base, core_fixture.bindings.core, &ReasonNativeLookup, &ReasonGlobalKey,
                &scheme_identifier, &owner_identifier, &target_identifier};
    // No live Scheme exists, yet inherited raw full-ID context remains valid.
    Put(core_fixture.scheme_slots.data(), 0xB8, static_cast<void *>(nullptr));
    std::memset(core_fixture.instance.data(), 0, core_fixture.instance.size());
  }
  ~InvalidationReasonFixture() { std::destroy_at(title_key); std::destroy_at(reason_key); }
  SwayInvalidationReasonQuery12002 Query(std::uint64_t after = 0) const { return {actor, target, scheme, after}; }
  SwayInvalidationReasonCapture12002 ExistingExecuteSink() {
    const auto result = CaptureAndRecordSwayInvalidationReason12002(bindings, effect.data(), context.data(), recorder);
    // Represents the existing wrapper's unchanged original forwarding. There
    // is deliberately no new installer or duplicate message pointer patch.
    ++original_calls;
    return result;
  }
};
void SaveReason(const std::filesystem::path &output, const char *name, const SwayInvalidationReasonQueryResult12002 &result) {
  std::ofstream file(output / name); file << SerializeSwayInvalidationReason12002(result) << '\n';
  Check(file.good(), "actual selected-source query wire saved");
}
} // namespace
#ifndef XAR_SWAY_INVALIDATION_REASON_FIXTURE_ENTRY
#define XAR_SWAY_INVALIDATION_REASON_FIXTURE_ENTRY main
#endif
int XAR_SWAY_INVALIDATION_REASON_FIXTURE_ENTRY(int argc, char **argv) {
  try {
    Check(argc == 2, "artifact directory supplied");
    const std::filesystem::path output{argv[1]};
    InvalidationReasonFixture f;
    SwayInvalidationReasonQueryResult12002 r;
    Check(!BindSwayInvalidationReasonImage12002(base, "old-build").enabled, "exact build binding required");
    f.recorder.SetObserverAttached(true);
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::captured, "dead actual single-child toast tuple captured");
    Check(f.recorder.Query(f.Query(), r) && r.records.size() == 1 &&
          r.records[0].source.branch == SwayInvalidationNotificationBranch12002::target_dead_notification_source &&
          r.records[0].source.scheme_id == scheme && r.records[0].source.actor_character_id == actor &&
          r.records[0].source.target_character_id == target, "native Env32 overlay and Script24 Scheme fallback join without live Scheme");
    SaveReason(output, "dead-notification-source-wire.json", r);
    *f.reason_key = "scheme_target_not_in_diplomatic_range";
    Put(f.child.data(), 0, base + 0x4931D10);
    Put(f.child.data(), 8, std::int32_t{9});
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::captured, "selected range description tuple captured");
    Check(f.recorder.Query(f.Query(1), r) && r.records.size() == 1 &&
          r.records[0].source.branch == SwayInvalidationNotificationBranch12002::out_of_range_notification_source,
          "independent range branch preserved as second source on same full SchemeID");
    SaveReason(output, "range-notification-source-wire.json", r);
    *f.reason_key = "sway_invalidated_war";
    Put(f.child.data(), 0, base + 0x4931918);
    Put(f.child.data(), 8, std::int32_t{8});
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::captured, "existing authored branch copied opaquely");
    Check(f.recorder.Query(f.Query(2), r) && r.records.size() == 1 &&
          r.records[0].source.branch == SwayInvalidationNotificationBranch12002::opaque_existing_stock_notification_source,
          "opaque branch has no new domain or inferred endcause");
    SaveReason(output, "opaque-notification-source-wire.json", r);
    Put(f.effect.data(), 0x3C, std::int32_t{2});
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::ignored, "multiple children do not establish selected reason");
    Put(f.effect.data(), 0x3C, std::int32_t{1});
    Put(f.child.data(), 0x3C, std::int32_t{1});
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::ignored, "nested children are not a selected unconditional reason source");
    Put(f.child.data(), 0x3C, std::int32_t{0});
    Put(f.effect.data(), 0x0C, std::uint8_t{1});
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::ignored, "nonstock command-key domain not looked up as global");
    Put(f.effect.data(), 0x0C, std::uint8_t{0});
    Put(f.script_rows.data(), 8, SwayInvalidationToken12002{});
    Check(f.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::ignored, "missing inherited Scheme token cannot produce source receipt");
    Check(f.original_calls == 7 && native_lookup_calls == 12 && global_getter_calls == 10,
          "sink original forwarding count and actual typed global/native lookup calls");
    Check(f.recorder.Query(f.Query(), r) && r.records.size() == 3, "ignored inputs do not fabricate records");
    std::memset(f.env_rows.data(), 0, f.env_rows.size());
    std::memset(f.script_rows.data(), 0, f.script_rows.size());
    Check(f.recorder.Query(f.Query(), r) && r.records.size() == 3 && r.records[0].source.scheme_id == scheme,
          "query retains only copied identity values after native context mutation");
    SaveReason(output, "copied-multiple-notification-source-wire.json", r);
    f.recorder.SetObserverAttached(false);
    Check(!f.recorder.Query(f.Query(), r), "detached sink cannot claim session source availability");
    SaveReason(output, "detached-reason-wire.json", r);
    std::cout << "PASS " << checks << " checks; selected toast tuple/native scope overlay/global command domain/copied query; no installer/no CK3\n";
    return 0;
  } catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
