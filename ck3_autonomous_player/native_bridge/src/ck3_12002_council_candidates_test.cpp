#include "ck3_12002_council_fixture.hpp"

#include <iostream>
#include <string>

namespace {
using namespace xar;
using namespace ck3_12002;
using Fixture = ck3_12002::test::CouncilCandidatesFixture12002;
using Result = ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1;
using Failure = game::CouncilCompositionStewardCandidatesFailureV1;
std::uint32_t checks = 0;
bool Check(bool condition, const char *name) {
  ++checks;
  if (!condition) std::cerr << "FAIL " << name << '\n';
  return condition;
}

void InitializeLeaf(void *allocator, std::uintptr_t *data, std::int32_t *capacity) {
  *data = reinterpret_cast<std::uintptr_t>(allocator) + 8;
  *capacity = 64;
}

bool Rejected(Fixture &f, Failure reason, std::uint32_t expected_producer,
              std::uint32_t expected_release, const char *name) {
  game::CouncilCompositionCandidatesPublicV1 output{};
  game::CouncilCompositionStewardCandidatesV1 source{};
  const auto result = ReadCouncilCandidates12002(f.environment, f.access, f.request, output, &source);
  return Check(result == Result::unavailable && output.candidate_count == 0 &&
      source.candidate_count == 0 && output.source_unavailable_reason == reason &&
      f.producer_calls == expected_producer && f.release_calls == expected_release, name);
}
}

int main() {
  bool ok = true;
  const auto binding = BindCouncilCandidates12002(0x140000000, kExecutableSha256);
  ok &= Check(binding.exact_build_admitted && !binding.offline_fixture_function_overrides &&
      reinterpret_cast<std::uintptr_t>(binding.produce_candidates) == 0x140000000 + kCouncilCandidatesProducerRva12002 &&
      reinterpret_cast<std::uintptr_t>(binding.initialize_vector) == 0x140000000 + kCouncilCandidatesInitializeRva12002 &&
      reinterpret_cast<std::uintptr_t>(binding.release_allocation) == 0x140000000 + kCouncilCandidatesReleaseRva12002,
      "exact production addresses");
  ok &= Check(!BindCouncilCandidates12002(0x140000000,
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86").exact_build_admitted,
      "old SHA rejected");
  ok &= Check(!BindCouncilCandidates12002(0, kExecutableSha256).exact_build_admitted,
      "zero base rejected");

  {
    Fixture f;
    f.characters[15].Put(0xDC, std::int32_t{99}); // Old field must not supply stewardship.
    game::CouncilCompositionCandidatesPublicV1 output{};
    game::CouncilCompositionStewardCandidatesV1 source{};
    const auto result = ReadCouncilCandidates12002(f.environment, f.access, f.request, output, &source);
    ok &= Check(result == Result::available && output.readiness.ready &&
        output.candidate_collection_complete && output.candidate_count == 2 &&
        output.owner_character_id == Fixture::kOwner &&
        output.incumbent_character_id == Fixture::kIncumbent &&
        output.incumbent_main_skill.value == 9 && !output.vacant &&
        output.action_route == game::CouncilCompositionCandidateActionRouteV1::replace,
        "occupied source-chain projection");
    ok &= Check(output.candidates[0].character_id == Fixture::kCandidate &&
        output.candidates[0].native_collection_ordinal == 1 &&
        output.candidates[0].eligible && output.candidates[0].main_skill.value == 22 &&
        output.candidates[1].character_id == Fixture::kCandidate + 1 &&
        output.candidates[1].native_collection_ordinal == 0 &&
        output.candidates[1].main_skill.value == 17,
        "full IDs canonical order native ordinals and new skill field");
    ok &= Check(f.capture_calls == 2 && f.producer_calls == 1 && f.release_calls == 1 &&
        f.allocator_shape_valid && f.producer_inputs_valid && source.temporary_vector_released,
        "native producer and allocator lifecycle");
    const auto wire = SerializeCouncilCandidates12002(output);
    ok &= Check(!wire.empty() && wire.find("\"game_version\":\"1.20.0.2\"") != std::string::npos &&
        wire.find(kExecutableSha256) != std::string::npos &&
        wire.find("1.19.0.6") == std::string::npos &&
        wire.find("\"native_collection_ordinal\":1") != std::string::npos,
        "actual new-build wire provenance");
  }
  {
    Fixture f;
    f.tasks[0].Put(0x40, std::int32_t{-1});
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::available &&
        output.vacant && output.incumbent_character_id == -1 &&
        output.action_route == game::CouncilCompositionCandidateActionRouteV1::assign &&
        output.candidates[0].action_route == game::CouncilCompositionCandidateActionRouteV1::assign,
        "vacancy source-derived assign route");
    const auto wire = SerializeCouncilCandidates12002(output);
    ok &= Check(wire.find("\"incumbent_character_id\":null") != std::string::npos &&
        wire.find("\"incumbent_main_skill\":null") != std::string::npos,
        "vacancy wire nulls");
  }
  {
    Fixture f; f.count = 0;
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::available &&
        output.candidate_count == 0 && output.candidate_collection_complete &&
        output.readiness.ready && f.producer_calls == 1 && f.release_calls == 1,
        "complete native empty collection");
  }
  {
    Fixture f; f.EnableChancellor();
    game::CouncilCompositionCandidatesPublicV1 output{};
    CouncilCandidatesFrameV1 frame{};
    ok &= Check(CaptureCouncilCandidatesFrame12002(f.environment, f.access, frame,
        f.request.position_key) && frame.active_task_id == Fixture::kTask + 1 &&
        frame.active_task == reinterpret_cast<std::uintptr_t>(f.tasks[1].Data()),
        "Chancellor task selected while Steward task remains present");
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::available &&
        output.readiness.ready && std::string_view(output.position_key.data()) == Fixture::kChancellorPosition &&
        output.incumbent_character_id == Fixture::kChancellorIncumbent &&
        std::string_view(output.incumbent_main_skill.key.data()) == "diplomacy" &&
        output.incumbent_main_skill.value == 14 && output.candidates[0].main_skill.value == 28 &&
        output.candidates[1].main_skill.value == 19 &&
        std::string_view(output.candidates[0].main_skill.key.data()) == "diplomacy" &&
        f.producer_inputs_valid && f.release_calls == 1,
        "Chancellor effective diplomacy differs from Steward skill fields");
    const auto wire = SerializeCouncilCandidates12002(output);
    ok &= Check(!wire.empty() && wire.find("councillor_chancellor") != std::string::npos &&
        wire.find("\"key\":\"diplomacy\"") != std::string::npos &&
        ck3_11906::SerializeCouncilCompositionCandidatesPublicV1(output).empty(),
        "new role codec with strict legacy default");
  }
  {
    Fixture f; f.EnableChancellor();
    f.request.position_key = kCouncilCandidatesStewardPosition12002;
    f.expected_task_index = 0;
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::available &&
        output.incumbent_character_id == Fixture::kIncumbent &&
        std::string_view(output.position_key.data()) == Fixture::kPosition &&
        std::string_view(output.incumbent_main_skill.key.data()) == "stewardship" &&
        output.incumbent_main_skill.value == 9 && output.candidates[0].main_skill.value == 22 &&
        f.producer_inputs_valid, "default Steward profile remains distinct with both tasks");
  }
  {
    Fixture f; f.request.position_key = "councillor_marshal";
    ok &= Rejected(f, Failure::position_outside_coverage, 0, 0, "undelegated role is outside query coverage");
  }
  {
    Fixture f; f.request.position_key = kCouncilCandidatesChancellorPosition12002;
    ok &= Rejected(f, Failure::active_steward_task_unavailable, 0, 0,
        "missing requested Chancellor task cannot reuse Steward task");
  }
  {
    Fixture f; f.EnableChancellor(); f.unreadable_candidate_skill = true;
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::unavailable &&
        output.unavailable_reason == game::CouncilCompositionCandidatesPublicFailureV1::candidate_main_skill_unready &&
        !output.readiness.ready && f.producer_calls == 1 && f.release_calls == 1,
        "missing Chancellor diplomacy cannot use available stewardship");
  }
  {
    Fixture f;
    const void *resolved = nullptr;
    ok &= Check(ResolveCouncilCharacter12002(f.environment, f.access, Fixture::kCandidate, resolved) &&
        resolved == f.characters[15].Data(), "shared full ID resolver");
    ok &= Check(!ResolveCouncilCharacter12002(f.environment, f.access, 0x02000010, resolved) &&
        resolved == nullptr, "resolver generation mismatch");
    CouncilCandidatesFrameV1 frame{};
    ok &= Check(CaptureCouncilCandidatesFrame12002(f.environment, f.access, frame) &&
        frame.active_task_identity_round_trip && frame.active_task_id == Fixture::kTask &&
        frame.active_task == reinterpret_cast<std::uintptr_t>(f.tasks[0].Data()) &&
        frame.played_character_identity_round_trip, "captured source frame resolves actual task");
  }
  {
    Fixture f; f.environment.admitted_executable_sha256 = "different";
    ok &= Rejected(f, Failure::exact_build_not_admitted, 0, 0, "wrong image stops before source callback");
  }
  {
    Fixture f; f.main_thread = false;
    ok &= Rejected(f, Failure::application_main_thread_required, 0, 0, "main-thread callback required");
  }
  {
    Fixture f; f.frame.paused = false;
    ok &= Rejected(f, Failure::not_paused, 0, 0, "paused source required");
  }
  {
    Fixture f; ++f.request.expected_native_revision;
    ok &= Rejected(f, Failure::revision_drift, 0, 0, "expected source revision required");
  }
  {
    Fixture f; f.tasks[0].Put(0x10, std::int32_t{0x02000001});
    ok &= Rejected(f, Failure::active_steward_task_unavailable, 0, 0, "task full generation required");
  }
  {
    Fixture f; f.tasks[0].Put(0x44, Fixture::kCandidate);
    ok &= Rejected(f, Failure::active_steward_task_unavailable, 0, 0, "task owner cannot be substituted");
  }
  {
    Fixture f; f.owner_extension.Put(0x23C, std::int32_t{2}); f.task_ids[1] = Fixture::kTask + 1;
    ok &= Rejected(f, Failure::active_steward_task_unavailable, 0, 0, "duplicate steward task unavailable");
  }
  {
    Fixture f; f.characters[17].Put(0x18, Fixture::kCandidate);
    f.rows[1] = reinterpret_cast<std::uintptr_t>(f.characters[17].Data());
    ok &= Rejected(f, Failure::candidate_generation_mismatch, 1, 1, "candidate exact pointer roundtrip");
  }
  {
    Fixture f; f.rows[1] = f.rows[0];
    ok &= Rejected(f, Failure::duplicate_candidate_id, 1, 1, "duplicate candidate releases vector");
  }
  {
    Fixture f; f.rows[1] = 0;
    ok &= Rejected(f, Failure::candidate_row_unreadable, 1, 1, "unreadable native row releases vector");
  }
  {
    Fixture f; f.count = 65; f.capacity = 96;
    ok &= Rejected(f, Failure::candidate_span_invalid, 1, 1, "grown native vector outside v1 bound is released");
  }
  {
    Fixture f; f.count = -1;
    ok &= Rejected(f, Failure::candidate_span_invalid, 1, 1, "invalid vector count releases allocation");
  }
  {
    Fixture f; f.capacity = 1;
    ok &= Rejected(f, Failure::candidate_span_invalid, 1, 1, "native count cannot exceed capacity");
  }
  {
    Fixture f; f.producer_ok = false;
    ok &= Rejected(f, Failure::candidate_collection_unavailable, 1, 1, "failed native producer releases allocation");
  }
  {
    Fixture f; f.initialize_ok = false;
    ok &= Rejected(f, Failure::candidate_collection_unavailable, 0, 1, "failed initialized vector cleaned once");
  }
  {
    Fixture f; f.release_ok = false;
    ok &= Rejected(f, Failure::temporary_vector_release_failed, 1, 1, "release failure blocks all publication");
  }
  {
    Fixture f; f.drift_revision_after_release = true;
    ok &= Rejected(f, Failure::revision_drift, 1, 1, "post-release source revision independently checked");
  }
  {
    Fixture f; f.drift_date_after_release = true;
    ok &= Rejected(f, Failure::date_drift, 1, 1, "post-release date independently checked");
  }
  {
    Fixture f; f.drift_incumbent_after_release = true;
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::unavailable &&
        output.candidate_count == 0 &&
        output.unavailable_reason == game::CouncilCompositionCandidatesPublicFailureV1::same_frame_binding_mismatch &&
        f.release_calls == 1, "independent incumbent requery");
  }
  {
    Fixture f; f.unreadable_candidate_skill = true;
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::unavailable &&
        output.candidate_count == 0 &&
        output.unavailable_reason == game::CouncilCompositionCandidatesPublicFailureV1::candidate_main_skill_unready &&
        f.producer_calls == 1 && f.release_calls == 1, "native main skill unavailable blocks readiness");
  }
  {
    Fixture f; f.tasks[0].Put(0x40, std::int32_t{0x02000002});
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::unavailable &&
        output.unavailable_reason == game::CouncilCompositionCandidatesPublicFailureV1::incumbent_invalid &&
        f.producer_calls == 0, "incumbent generation checked before producer");
  }
  {
    Fixture f;
    f.environment.initialize_vector = InitializeLeaf;
    f.access.initialize_vector = nullptr;
    // Exercise the production initialize path with a fixture-owned native leaf.
    f.access.invoke_producer = [](void *context, const CouncilCandidatesEnvironmentV1 &env,
        const void *owner, const void *task, bool gui, CouncilCandidatesNativeVectorV1 &vector) noexcept {
      auto &fixture = *static_cast<Fixture *>(context);
      fixture.allocator_address = vector.allocator; fixture.allocator_size = 0x210;
      return Fixture::Produce(context, env, owner, task, gui, vector);
    };
    game::CouncilCompositionCandidatesPublicV1 output{};
    ok &= Check(ReadCouncilCandidates12002(f.environment, f.access, f.request, output) == Result::available &&
        f.producer_calls == 1 && f.release_calls == 1, "production initializer callback path");
  }
  std::cout << (ok ? "GREEN" : "RED") << " council_candidates12002 checks=" << checks
            << " evidence=static-ready local_ck3_used=false\n";
  return ok ? 0 : 1;
}
