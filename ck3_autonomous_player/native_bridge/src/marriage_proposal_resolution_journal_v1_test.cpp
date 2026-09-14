#include "xar_bridge/marriage_proposal_resolution_journal_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

namespace bridge = xar::bridge;

namespace {

struct FixtureV1 {
  std::array<std::array<std::uint8_t, 15>,
             bridge::kMarriageResolutionHookCountV1>
      targets{};
  std::vector<void *> allocations{};
  std::uint32_t protect_calls = 0;
  std::uint32_t flush_calls = 0;
};

void *Allocate(void *context, std::size_t size, DWORD, DWORD) noexcept {
  auto &fixture = *static_cast<FixtureV1 *>(context);
  auto *const result = new (std::nothrow) std::uint8_t[size];
  if (result != nullptr) {
    std::memset(result, 0, size);
    fixture.allocations.push_back(result);
  }
  return result;
}

bool Free(void *context, void *address, std::size_t, DWORD) noexcept {
  auto &fixture = *static_cast<FixtureV1 *>(context);
  const auto found =
      std::find(fixture.allocations.begin(), fixture.allocations.end(),
                address);
  if (found == fixture.allocations.end()) {
    return false;
  }
  delete[] static_cast<std::uint8_t *>(address);
  fixture.allocations.erase(found);
  return true;
}

bool Protect(void *context, void *, std::size_t, DWORD desired,
             DWORD &old) noexcept {
  auto &fixture = *static_cast<FixtureV1 *>(context);
  ++fixture.protect_calls;
  old = desired == PAGE_EXECUTE_READ ? PAGE_READWRITE : PAGE_EXECUTE_READ;
  return true;
}

bool Flush(void *context, const void *, std::size_t) noexcept {
  ++static_cast<FixtureV1 *>(context)->flush_calls;
  return true;
}

bridge::MarriageProposalResolutionJournalInstallEnvironmentV1 Environment(
    FixtureV1 &fixture) {
  bridge::MarriageProposalResolutionJournalInstallEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.primary_thread_suspended_proven = true;
  output.offline_fixture = true;
  output.admitted_executable_sha256 =
      bridge::kMarriageProposalResolutionJournalExecutableSha256V1;
  output.module_base = 0x10000000;
  for (std::size_t index = 0; index < fixture.targets.size(); ++index) {
    std::memcpy(fixture.targets[index].data(),
                bridge::kMarriageResolutionExpectedPrefixesV1[index].data(),
                fixture.targets[index].size());
    output.target_overrides[index] = reinterpret_cast<std::uintptr_t>(
        fixture.targets[index].data());
  }
  output.memory_context = &fixture;
  output.virtual_alloc_override = &Allocate;
  output.virtual_free_override = &Free;
  output.virtual_protect_override = &Protect;
  output.flush_instruction_cache_override = &Flush;
  return output;
}

bridge::MarriageProposalSubmissionV1 Submission() {
  bridge::MarriageProposalSubmissionV1 output{};
  output.subject_character_id = 303;
  output.candidate_character_id = 404;
  output.native_rank = 1;
  output.roles.actor_character_id = 101;
  output.roles.recipient_character_id = 202;
  output.roles.secondary_actor_character_id = 303;
  output.roles.secondary_recipient_character_id = 404;
  output.roles.intermediary_character_id = 505;
  return output;
}

bridge::MarriageProposalResolutionIdentityV1 Identity() {
  return {0x12345678, 101, 202, 303, 404, 505};
}

void AssertResolution(
    bridge::MarriageProposalResolutionJournalDetourStateV1 &state,
    bridge::MarriageProposalNativeResolutionV1 expected) {
  bridge::MarriageProposalNativeResolutionV1 actual =
      bridge::MarriageProposalNativeResolutionV1::invalidated;
  assert(bridge::ReadMarriageProposalResolutionJournalV1(
      &state, 303, 404, actual));
  assert(actual == expected);
}

void AssertResolutionUnavailable(
    bridge::MarriageProposalResolutionJournalDetourStateV1 &state) {
  bridge::MarriageProposalNativeResolutionV1 actual =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  assert(!bridge::ReadMarriageProposalResolutionJournalV1(
      &state, 303, 404, actual));
  assert(actual == bridge::MarriageProposalNativeResolutionV1::pending);
}

} // namespace

int main() {
  {
    FixtureV1 bad_fixture{};
    auto environment = Environment(bad_fixture);
    bad_fixture.targets[2][0] ^= 0x01;
    bridge::MarriageProposalResolutionJournalDetourStateV1 bad_state{};
    assert(!bridge::InstallMarriageProposalResolutionJournalV1(
        bad_state, environment));
    assert((bad_state.failure_flags.load() &
            bridge::marriage_resolution_install_failure_anchor) != 0);
    assert(bad_fixture.allocations.empty());
  }

  FixtureV1 fixture{};
  auto environment = Environment(fixture);
  bridge::MarriageProposalResolutionJournalDetourStateV1 state{};
  assert(bridge::InstallMarriageProposalResolutionJournalV1(state,
                                                             environment));
  assert(state.installed.load() == 1);
  assert(fixture.allocations.size() ==
         bridge::kMarriageResolutionHookCountV1);
  assert(fixture.flush_calls >= bridge::kMarriageResolutionHookCountV1 * 2);

  for (std::size_t index = 0; index < fixture.targets.size(); ++index) {
    const auto patch_size = bridge::kMarriageResolutionPatchSizesV1[index];
    assert(fixture.targets[index][0] == 0xFF);
    assert(fixture.targets[index][1] == 0x25);
    assert(fixture.targets[index][2] == 0x00);
    assert(fixture.targets[index][3] == 0x00);
    assert(fixture.targets[index][4] == 0x00);
    assert(fixture.targets[index][5] == 0x00);
    if (patch_size == 15) {
      assert(fixture.targets[index][14] == 0x90);
    }
    const auto *const trampoline =
        static_cast<const std::uint8_t *>(state.trampolines[index]);
    assert(std::memcmp(
               trampoline,
               bridge::kMarriageResolutionExpectedPrefixesV1[index].data(),
               patch_size) == 0);
    assert(trampoline[patch_size] == 0xFF);
    assert(trampoline[patch_size + 1] == 0x25);
    std::uintptr_t resume = 0;
    std::memcpy(&resume, trampoline + patch_size + 6, sizeof(resume));
    assert(resume == environment.target_overrides[index] + patch_size);
  }

  bridge::MarriageProposalNativeBinderStateV1 binder{};
  assert(bridge::ConfigureMarriageProposalResolutionJournalV1(state,
                                                               binder));
  assert(binder.environment.proposal_resolution_certified);
  assert(binder.environment.proposal_resolution_context == &state);
  assert(binder.environment.read_proposal_resolution ==
         &bridge::ReadMarriageProposalResolutionJournalV1);

  const auto submission = Submission();
  const auto identity = Identity();
  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, submission, identity.interaction_definition));
  AssertResolutionUnavailable(state);
  bridge::MarriageProposalNativeResolutionV1 mismatched =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  assert(!bridge::ReadMarriageProposalResolutionJournalV1(
      &state, 303, 405, mismatched));

  assert(bridge::CaptureMarriageResolutionConstructFixtureV1(identity, 77));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::pending);
  assert(bridge::CaptureMarriageResolutionResponseFixtureV1(identity, 77, 0,
                                                             4));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::pending);
  assert(bridge::CaptureMarriageResolutionResponseFixtureV1(identity, 77, 0,
                                                             0));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::accepted);

  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, submission, identity.interaction_definition));
  assert(bridge::CaptureMarriageResolutionImmediateFixtureV1(identity, 0));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::refused);

  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, submission, identity.interaction_definition));
  assert(bridge::CaptureMarriageResolutionDispatchReturnFixtureV1(identity,
                                                                   false));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::invalidated);

  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, submission, identity.interaction_definition));
  assert(bridge::CaptureMarriageResolutionConstructFixtureV1(identity, 88));
  assert(!bridge::CaptureMarriageResolutionDeleteFixtureV1(
      88, bridge::kMarriageDeleteResponseCallerRvaV1));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::pending);
  assert(bridge::CaptureMarriageResolutionDeleteFixtureV1(
      88, bridge::kMarriageDeleteExpiredCallerRvaV1));
  AssertResolution(state,
                   bridge::MarriageProposalNativeResolutionV1::invalidated);

  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, submission, identity.interaction_definition));
  assert(bridge::CaptureMarriageResolutionConstructFixtureV1(identity, 89));
  assert(!bridge::CaptureMarriageResolutionResponseFixtureV1(identity, 89, 0,
                                                              2));
  AssertResolutionUnavailable(state);

  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, submission, identity.interaction_definition));
  auto wrong_identity = identity;
  wrong_identity.recipient_character_id = 999;
  assert(!bridge::CaptureMarriageResolutionImmediateFixtureV1(wrong_identity,
                                                               1));
  AssertResolutionUnavailable(state);

  auto signed_submission = submission;
  signed_submission.subject_character_id = 0x8800012FU;
  signed_submission.candidate_character_id = 0x99000194U;
  signed_submission.roles.secondary_actor_character_id =
      signed_submission.subject_character_id;
  signed_submission.roles.secondary_recipient_character_id =
      signed_submission.candidate_character_id;
  auto signed_identity = identity;
  std::memcpy(&signed_identity.subject_character_id,
              &signed_submission.subject_character_id,
              sizeof(signed_identity.subject_character_id));
  std::memcpy(&signed_identity.candidate_character_id,
              &signed_submission.candidate_character_id,
              sizeof(signed_identity.candidate_character_id));
  assert(bridge::ArmMarriageProposalResolutionJournalV1(
      state, signed_submission, signed_identity.interaction_definition));
  const std::int32_t signed_pending_id =
      static_cast<std::int32_t>(0x8800004DU);
  assert(bridge::CaptureMarriageResolutionConstructFixtureV1(
      signed_identity, signed_pending_id));
  bridge::MarriageProposalNativeResolutionV1 signed_resolution =
      bridge::MarriageProposalNativeResolutionV1::invalidated;
  assert(bridge::ReadMarriageProposalResolutionJournalV1(
      &state, signed_submission.subject_character_id,
      signed_submission.candidate_character_id, signed_resolution));
  assert(signed_resolution ==
         bridge::MarriageProposalNativeResolutionV1::pending);

  assert(bridge::RemoveMarriageProposalResolutionJournalV1(state, true));
  assert(state.installed.load() == 0);
  assert(state.active_calls.load() == 0);
  assert(fixture.allocations.empty());
  for (std::size_t index = 0; index < fixture.targets.size(); ++index) {
    assert(std::memcmp(
               fixture.targets[index].data(),
               bridge::kMarriageResolutionExpectedPrefixesV1[index].data(),
               bridge::kMarriageResolutionPatchSizesV1[index]) == 0);
  }
  bridge::MarriageProposalNativeResolutionV1 after_remove =
      bridge::MarriageProposalNativeResolutionV1::pending;
  assert(!binder.environment.read_proposal_resolution(
      binder.environment.proposal_resolution_context, 303, 404,
      after_remove));

  std::cout << "marriage proposal resolution journal v1 tests passed\n";
  return 0;
}
