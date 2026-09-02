#include "xar_bridge/raiktor_surrender_truce_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

using namespace xar::ck3_11906;

template <std::size_t Size, typename Value>
void Store(std::array<std::byte, Size> &storage, std::size_t offset,
           const Value &value) {
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<void *, 12> root_vtable{};
  std::array<void *, 1> scripted_vtable{};
  std::array<void *, 1> template_vtable{};
  std::array<void *, 1> hidden_vtable{};
  std::array<void *, 1> context_vtable{};
  std::array<void *, 1> truce_vtable{};
  std::array<void *, 1> unknown_vtable{};
  std::array<std::byte, 0x60> root{};
  std::array<std::byte, 0xA0> scripted{};
  std::array<std::byte, 0x128> scripted_template{};
  std::array<std::byte, 0x60> default_effect{};
  std::array<std::byte, 0x60> hidden{};
  std::array<std::byte, 0x80> context_effect{};
  std::array<std::byte, 0x110> truce{};
  std::array<std::byte, 0x10> unknown{};
  std::array<std::byte, 0xA0> private_scripted{};
  std::array<std::byte, 0x128> private_scripted_template{};
  std::array<std::byte, 0x60> private_default_effect{};
  std::array<std::byte, 0x60> private_hidden{};
  std::array<std::byte, 0x80> private_context_effect{};
  std::array<void *, 19> root_children{};
  std::array<void *, 6> default_children{};
  std::array<void *, 4> private_default_children{};
  std::array<void *, 1> private_hidden_children{};
  std::array<void *, 1> private_context_children{};
  std::array<void *, 1> hidden_children{};
  std::array<void *, 1> context_children{};
  std::array<std::byte, 1> war{};
  std::array<std::byte, 1> cb{};
  std::array<std::byte, 0x100> effect_context{};
  RaiktorSurrenderTruceFrameV1 frame;
  int frame_reads = 0;
  int evaluator_calls = 0;
  std::int32_t first_days = 1825;
  std::int32_t second_days = 1825;
  bool fail_first_frame = false;
  bool fail_second_frame = false;
  bool drift_second_frame = false;

  Fixture() {
    root_vtable[11] = reinterpret_cast<void *>(0x1);
    Store(unknown, 0x00, static_cast<void *>(unknown_vtable.data()));
    root_children.fill(unknown.data());
    root_children[9] = scripted.data();
    default_children.fill(unknown.data());
    default_children[2] = hidden.data();
    hidden_children[0] = context_effect.data();
    context_children[0] = truce.data();

    Store(root, 0x00, static_cast<void *>(root_vtable.data()));
    Store(root, 0x40, static_cast<void *>(root_children.data()));
    Store(root, 0x48, std::int32_t{19});
    Store(root, 0x4C, std::int32_t{14});
    Store(scripted, 0x00, static_cast<void *>(scripted_vtable.data()));
    Store(scripted, 0x60, static_cast<void *>(scripted_template.data()));
    Store(scripted, 0x94, std::int32_t{0});
    Store(scripted_template, 0x00,
          static_cast<void *>(template_vtable.data()));
    Store(scripted_template, 0x120,
          static_cast<void *>(default_effect.data()));
    Store(default_effect, 0x00, static_cast<void *>(root_vtable.data()));
    Store(default_effect, 0x40,
          static_cast<void *>(default_children.data()));
    Store(default_effect, 0x48, std::int32_t{6});
    Store(default_effect, 0x4C, std::int32_t{5});
    Store(hidden, 0x00, static_cast<void *>(hidden_vtable.data()));
    Store(hidden, 0x40, static_cast<void *>(hidden_children.data()));
    Store(hidden, 0x48, std::int32_t{1});
    Store(hidden, 0x4C, std::int32_t{1});
    Store(context_effect, 0x00,
          static_cast<void *>(context_vtable.data()));
    Store(context_effect, 0x40,
          static_cast<void *>(context_children.data()));
    Store(context_effect, 0x48, std::int32_t{1});
    Store(context_effect, 0x4C, std::int32_t{1});
    Store(context_effect, 0x6C, std::int32_t{1});
    Store(truce, 0x00, static_cast<void *>(truce_vtable.data()));

    private_default_children.fill(unknown.data());
    private_default_children[1] = private_hidden.data();
    private_hidden_children[0] = private_context_effect.data();
    private_context_children[0] = truce.data();
    Store(private_scripted, 0x00,
          static_cast<void *>(scripted_vtable.data()));
    Store(private_scripted, 0x60,
          static_cast<void *>(private_scripted_template.data()));
    Store(private_scripted, 0x94, std::int32_t{0});
    Store(private_scripted_template, 0x00,
          static_cast<void *>(template_vtable.data()));
    Store(private_scripted_template, 0x120,
          static_cast<void *>(private_default_effect.data()));
    Store(private_default_effect, 0x00,
          static_cast<void *>(root_vtable.data()));
    Store(private_default_effect, 0x40,
          static_cast<void *>(private_default_children.data()));
    Store(private_default_effect, 0x48, std::int32_t{4});
    Store(private_default_effect, 0x4C, std::int32_t{4});
    Store(private_hidden, 0x00, static_cast<void *>(hidden_vtable.data()));
    Store(private_hidden, 0x40,
          static_cast<void *>(private_hidden_children.data()));
    Store(private_hidden, 0x48, std::int32_t{1});
    Store(private_hidden, 0x4C, std::int32_t{1});
    Store(private_context_effect, 0x00,
          static_cast<void *>(context_vtable.data()));
    Store(private_context_effect, 0x40,
          static_cast<void *>(private_context_children.data()));
    Store(private_context_effect, 0x48, std::int32_t{1});
    Store(private_context_effect, 0x4C, std::int32_t{1});
    Store(private_context_effect, 0x6C, std::int32_t{1});

    frame.snapshot_revision = 73;
    frame.native_revision = 4;
    frame.date_raw = 53'175'816;
    frame.paused = true;
    frame.war_id = 16'777'290;
    frame.active_casus_belli_database_index = 411;
    frame.exact_raiktor_claim_cb = true;
    frame.primary_attacker_character_id = 29'829;
    frame.primary_defender_character_id = 17'116;
    frame.claimant_character_id = 29'829;
    frame.war = war.data();
    frame.active_casus_belli = cb.data();
    frame.attacker_defeat_root = root.data();
  }

  RaiktorSurrenderTruceNativeEnvironmentV1 Environment() const;
  RaiktorSurrenderTruceAccessV1 Access();
  RaiktorSurrenderTruceRequestV1 Request() {
    return {effect_context.data(), effect_context.data() + 0x28};
  }
};

Fixture *g_fixture = nullptr;

bool ReadFrame(void *context, RaiktorSurrenderTruceFrameV1 *output) {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_reads;
  if ((fixture.frame_reads == 1 && fixture.fail_first_frame) ||
      (fixture.frame_reads == 2 && fixture.fail_second_frame)) {
    return false;
  }
  *output = fixture.frame;
  if (fixture.frame_reads == 2 && fixture.drift_second_frame) {
    ++output->snapshot_revision;
  }
  return true;
}

std::int32_t Evaluate(void *script_value, void *effect_context,
                      void *evaluation_context) {
  if (g_fixture == nullptr ||
      script_value != g_fixture->truce.data() + 0x108 ||
      effect_context != g_fixture->effect_context.data() ||
      evaluation_context != g_fixture->effect_context.data() + 0x28) {
    return -1;
  }
  ++g_fixture->evaluator_calls;
  return g_fixture->evaluator_calls == 1 ? g_fixture->first_days
                                         : g_fixture->second_days;
}

RaiktorSurrenderTruceNativeEnvironmentV1 Fixture::Environment() const {
  return {
      true,
      true,
      0,
      reinterpret_cast<std::uintptr_t>(root_vtable.data()),
      reinterpret_cast<std::uintptr_t>(scripted_vtable.data()),
      reinterpret_cast<std::uintptr_t>(template_vtable.data()),
      reinterpret_cast<std::uintptr_t>(hidden_vtable.data()),
      reinterpret_cast<std::uintptr_t>(context_vtable.data()),
      reinterpret_cast<std::uintptr_t>(truce_vtable.data()),
      Evaluate,
  };
}

RaiktorSurrenderTruceAccessV1 Fixture::Access() {
  return {this, nullptr, ReadFrame};
}

bool ExpectFailure(const RaiktorSurrenderTruceObservationV1 &value,
                   RaiktorSurrenderTruceFailureV1 failure,
                   std::string_view label) {
  if (value.status != RaiktorSurrenderTruceStatusV1::unavailable ||
      value.failure != failure) {
    std::cerr << label << ": expected "
              << RaiktorSurrenderTruceFailureReasonV1(failure) << ", got "
              << RaiktorSurrenderTruceFailureReasonV1(value.failure) << '\n';
    return false;
  }
  return true;
}

template <typename Mutate>
bool ShapeDrift(Mutate mutate, RaiktorSurrenderTruceFailureV1 failure,
                std::string_view label) {
  Fixture fixture;
  g_fixture = &fixture;
  mutate(fixture);
  const auto value = ObserveRaiktorSurrenderTruceV1(
      fixture.Environment(), fixture.Access(), fixture.Request());
  return ExpectFailure(value, failure, label) &&
         fixture.evaluator_calls == 0;
}

} // namespace

int main() {
#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
  {
    Fixture fixture;
    g_fixture = &fixture;
    fixture.root_children[7] = fixture.private_scripted.data();
    Store(fixture.root, 0x48, std::int32_t{13});
    Store(fixture.root, 0x4C, std::int32_t{12});
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), fixture.Request());
    const auto &capture = LastRaiktorTrucePrivateShapeCaptureV1();
    if (!ExpectFailure(value,
                       RaiktorSurrenderTruceFailureV1::root_shape_drift,
                       "private targeted evaluator") ||
        capture.targeted_index7_status != "complete" ||
        capture.evaluator_capture_status != "complete" ||
        capture.duration_script_value !=
            reinterpret_cast<std::uintptr_t>(fixture.truce.data() + 0x108) ||
        capture.evaluator_function !=
            reinterpret_cast<std::uintptr_t>(Evaluate) ||
        capture.evaluator_effect_context != reinterpret_cast<std::uintptr_t>(
                                                fixture.effect_context.data()) ||
        capture.evaluator_evaluation_context !=
            reinterpret_cast<std::uintptr_t>(fixture.effect_context.data() +
                                             0x28) ||
        capture.evaluator_first_days != 1825 ||
        capture.evaluator_second_days != 1825 ||
        capture.evaluator_call_count != 2 ||
        !capture.evaluator_nonnegative || !capture.evaluator_stable ||
        fixture.evaluator_calls != 2 || fixture.frame_reads != 1) {
      std::cerr << "private targeted evaluator capture failed\n";
      return 1;
    }
  }
#endif
  {
    Fixture fixture;
    g_fixture = &fixture;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), fixture.Request());
    if (value.status != RaiktorSurrenderTruceStatusV1::available ||
        value.failure != RaiktorSurrenderTruceFailureV1::none ||
        value.owner_character_id != 29'829 ||
        value.toward_character_id != 17'116 || value.evaluated_days != 1825 ||
        !value.pointer_shape_verified ||
        !value.evaluator_double_read_stable || !value.same_frame_stable ||
        value.expiry_observable || fixture.frame_reads != 2 ||
        fixture.evaluator_calls != 2) {
      std::cerr << "available observation contract failed\n";
      return 1;
    }
  }
  if (!ShapeDrift(
          [](Fixture &fixture) { fixture.root_vtable[11] = nullptr; },
          RaiktorSurrenderTruceFailureV1::root_slot11_missing,
          "root slot11") ||
      !ShapeDrift(
          [](Fixture &fixture) { Store(fixture.root, 0x4C, std::int32_t{13}); },
          RaiktorSurrenderTruceFailureV1::root_shape_drift, "root span") ||
      !ShapeDrift(
          [](Fixture &fixture) {
            fixture.default_children[1] = fixture.hidden.data();
          },
          RaiktorSurrenderTruceFailureV1::caddtruce_not_unique,
          "duplicate hidden path") ||
      !ShapeDrift(
          [](Fixture &fixture) {
            Store(fixture.context_effect, 0x6C, std::int32_t{2});
          },
          RaiktorSurrenderTruceFailureV1::root_shape_drift,
          "context scope count") ||
      !ShapeDrift(
          [](Fixture &fixture) {
            Store(fixture.truce, 0x00,
                  static_cast<void *>(fixture.unknown_vtable.data()));
          },
          RaiktorSurrenderTruceFailureV1::caddtruce_not_unique,
          "truce vtable")) {
    return 1;
  }
  {
    Fixture fixture;
    g_fixture = &fixture;
    fixture.second_days = 1826;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), fixture.Request());
    if (!ExpectFailure(value,
                       RaiktorSurrenderTruceFailureV1::duration_unstable,
                       "duration drift") ||
        fixture.evaluator_calls != 2 || fixture.frame_reads != 1) {
      return 1;
    }
  }
  {
    Fixture fixture;
    g_fixture = &fixture;
    fixture.first_days = -1;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), fixture.Request());
    if (!ExpectFailure(value,
                       RaiktorSurrenderTruceFailureV1::duration_negative,
                       "negative duration")) {
      return 1;
    }
  }
  {
    Fixture fixture;
    g_fixture = &fixture;
    fixture.drift_second_frame = true;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), fixture.Request());
    if (!ExpectFailure(value, RaiktorSurrenderTruceFailureV1::frame_changed,
                       "frame drift")) {
      return 1;
    }
  }
  {
    Fixture fixture;
    g_fixture = &fixture;
    fixture.frame.paused = false;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), fixture.Request());
    if (!ExpectFailure(value,
                       RaiktorSurrenderTruceFailureV1::frame_not_paused,
                       "unpaused") ||
        fixture.evaluator_calls != 0) {
      return 1;
    }
  }
  {
    Fixture fixture;
    g_fixture = &fixture;
    auto environment = fixture.Environment();
    environment.module_base = 1;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        environment, fixture.Access(), fixture.Request());
    if (!ExpectFailure(value,
                       RaiktorSurrenderTruceFailureV1::unsupported_build,
                       "fixture admission")) {
      return 1;
    }
  }
  {
    Fixture fixture;
    g_fixture = &fixture;
    auto request = fixture.Request();
    request.evaluation_context = fixture.effect_context.data() + 0x30;
    const auto value = ObserveRaiktorSurrenderTruceV1(
        fixture.Environment(), fixture.Access(), request);
    if (!ExpectFailure(value,
                       RaiktorSurrenderTruceFailureV1::invalid_request,
                       "evaluation context")) {
      return 1;
    }
  }
  g_fixture = nullptr;
  return 0;
}
