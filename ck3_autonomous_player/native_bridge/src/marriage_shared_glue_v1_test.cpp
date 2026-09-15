#include "xar_bridge/marriage_shared_glue_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <new>
#include <string_view>
#include <vector>

namespace bridge = xar::bridge;

namespace {

struct HookFixtureV1 {
  std::array<std::array<std::uint8_t, 15>,
             bridge::kMarriageResolutionHookCountV1>
      targets{};
  std::vector<void *> allocations{};
};

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

std::int32_t ReadTier(void *) { return 0; }

void Enumerate(void *, std::int32_t, bool, std::int32_t, void *) {}

void Score(void *, const void *, void *, void *) {}

void *InitializeScored(void *header) { return header; }

void Release(void *, void *, std::size_t) {}

void InitializeCandidate(void *, void **data, std::int32_t *capacity) {
  *data = reinterpret_cast<void *>(1);
  *capacity = 1;
}

bool ReadOption(void *, std::uint32_t) { return false; }

bool IsAllied(const void *, const void *) { return false; }

void *AllocateHook(void *context, std::size_t size, DWORD,
                   DWORD) noexcept {
  auto &fixture = *static_cast<HookFixtureV1 *>(context);
  auto *const result = new (std::nothrow) std::uint8_t[size];
  if (result != nullptr) {
    std::memset(result, 0, size);
    fixture.allocations.push_back(result);
  }
  return result;
}

bool FreeHook(void *context, void *address, std::size_t,
              DWORD) noexcept {
  auto &fixture = *static_cast<HookFixtureV1 *>(context);
  const auto found =
      std::find(fixture.allocations.begin(), fixture.allocations.end(),
                address);
  if (found == fixture.allocations.end()) return false;
  delete[] static_cast<std::uint8_t *>(address);
  fixture.allocations.erase(found);
  return true;
}

bool ProtectHook(void *, void *, std::size_t, DWORD desired,
                 DWORD &old) noexcept {
  old = desired == PAGE_EXECUTE_READ ? PAGE_READWRITE : PAGE_EXECUTE_READ;
  return true;
}

bool FlushHook(void *, const void *, std::size_t) noexcept { return true; }

bridge::MarriageSharedGlueInstallEnvironmentV1 Environment(
    HookFixtureV1 &fixture) {
  constexpr std::uintptr_t module_base = 0x10000000;
  const auto sha = bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  bridge::MarriageSharedGlueInstallEnvironmentV1 output{};
  output.binder.module_base = module_base;
  output.binder.exact_build_admitted = true;
  output.binder.admitted_executable_sha256 = sha;
  output.binder.offline_fixture = true;

  output.ranked.module_base = module_base;
  output.ranked.exact_build_admitted = true;
  output.ranked.admitted_executable_sha256 = sha;
  output.ranked.offline_fixture = true;
  output.ranked.read_memory = &ReadMemory;
  output.ranked.read_native_tier = &ReadTier;
  output.ranked.native_cap_table_slot = 1;
  output.ranked.enumerate_candidates = &Enumerate;
  output.ranked.score_candidates = &Score;
  output.ranked.initialize_scored_container = &InitializeScored;
  output.ranked.release_native_buffer = &Release;
  output.ranked.initialize_candidate_buffer = &InitializeCandidate;
  output.ranked.candidate_owner_vtable = 1;
  output.ranked.scored_owner_vtable = 2;
  output.ranked.scored_row_vtable = 3;
  output.ranked.candidate_backing_allocator = 4;
  output.ranked.scored_backing_allocator = 5;

  output.outcome.module_base = module_base;
  output.outcome.exact_build_admitted = true;
  output.outcome.admitted_executable_sha256 = sha;
  output.outcome.offline_fixture = true;
  output.outcome.read_memory = &ReadMemory;
  output.outcome.read_boolean_option = &ReadOption;
  output.outcome.grand_wedding_option_id_slot = 1;
  output.outcome.adult_threshold_zero_slot = 2;
  output.outcome.adult_threshold_one_slot = 3;

  output.alliance.module_base = module_base;
  output.alliance.exact_build_admitted = true;
  output.alliance.admitted_executable_sha256 = sha;
  output.alliance.offline_fixture = true;
  output.alliance.read_memory = &ReadMemory;
  output.alliance.is_allied_to = &IsAllied;

  output.resolution.module_base = module_base;
  output.resolution.exact_build_admitted = true;
  output.resolution.admitted_executable_sha256 = sha;
  output.resolution.primary_thread_suspended_proven = true;
  output.resolution.offline_fixture = true;
  for (std::size_t index = 0; index < fixture.targets.size(); ++index) {
    std::memcpy(fixture.targets[index].data(),
                bridge::kMarriageResolutionExpectedPrefixesV1[index].data(),
                fixture.targets[index].size());
    output.resolution.target_overrides[index] =
        reinterpret_cast<std::uintptr_t>(fixture.targets[index].data());
  }
  output.resolution.memory_context = &fixture;
  output.resolution.virtual_alloc_override = &AllocateHook;
  output.resolution.virtual_free_override = &FreeHook;
  output.resolution.virtual_protect_override = &ProtectHook;
  output.resolution.flush_instruction_cache_override = &FlushHook;
  return output;
}

bridge::MarriageProposalReceiptFrameV1 Frame(std::uint64_t revision) {
  bridge::MarriageProposalReceiptFrameV1 output{};
  output.available = true;
  output.paused = true;
  constexpr std::string_view snapshot = "native:17";
  std::copy(snapshot.begin(), snapshot.end(), output.snapshot_id.begin());
  output.public_revision = revision;
  output.native_revision = revision;
  output.proof_epoch = 9;
  output.date_raw = 73;
  return output;
}

bridge::MarriageProposalSubmissionV1 Submission() {
  bridge::MarriageProposalSubmissionV1 output{};
  output.subject_character_id = 303;
  output.candidate_character_id = 404;
  output.roles.actor_character_id = 101;
  output.roles.recipient_character_id = 202;
  output.roles.secondary_actor_character_id = 303;
  output.roles.secondary_recipient_character_id = 404;
  output.roles.intermediary_character_id = 505;
  return output;
}

} // namespace

int main() {
  {
    HookFixtureV1 fixture{};
    auto environment = Environment(fixture);
    environment.outcome.module_base += 1;
    bridge::MarriageSharedGlueStateV1 state{};
    assert(!bridge::InstallMarriageSharedGlueV1(state, environment));
    assert(bridge::ReadMarriageSharedGlueFailureV1(state) ==
           bridge::MarriageSharedGlueFailureV1::invalid_environment);
    assert(fixture.allocations.empty());
  }

  HookFixtureV1 fixture{};
  const auto environment = Environment(fixture);
  bridge::MarriageSharedGlueStateV1 state{};
  assert(bridge::InstallMarriageSharedGlueV1(state, environment));
  assert(state.installed.load() == 1);
  assert(state.binder.environment.ranked_container_lifecycle_certified);
  assert(state.binder.environment.outcome_classifier_certified);
  assert(state.binder.environment.alliance_readback_certified);
  assert(state.binder.environment.proposal_resolution_certified);
  assert(state.binder.environment.receipt_frame_context ==
         &state.receipt_frames);
  assert(state.binder.environment.capture_receipt_frame ==
         &bridge::CaptureMarriageSharedReceiptFrameV1);
  assert(fixture.allocations.size() ==
         bridge::kMarriageResolutionHookCountV1);

  bridge::MarriageProposalReceiptFrameV1 captured{};
  assert(!state.binder.environment.capture_receipt_frame(
      state.binder.environment.receipt_frame_context, captured));
  assert(!captured.available);

  const auto before = Frame(17);
  assert(bridge::PublishMarriageSharedReceiptFrameV1(state, before));
  assert(state.binder.environment.capture_receipt_frame(
      state.binder.environment.receipt_frame_context, captured));
  assert(captured == before);

  const auto submission = Submission();
  constexpr std::uintptr_t interaction = 0x12345678;
  assert(bridge::ArmMarriageSharedGlueV1(state, submission, interaction));

  // The preceding paused frame cannot be reused as receipt evidence between
  // arm/ACK and the first post-native-edge frame publication.
  captured = before;
  assert(!state.binder.environment.capture_receipt_frame(
      state.binder.environment.receipt_frame_context, captured));
  assert(!captured.available);
  bridge::MarriageProposalNativeResolutionV1 resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  assert(!state.binder.environment.read_proposal_resolution(
      state.binder.environment.proposal_resolution_context, 303, 404,
      resolution));

  const bridge::MarriageProposalResolutionIdentityV1 identity{
      interaction, 101, 202, 303, 404, 505};
  assert(bridge::CaptureMarriageResolutionImmediateFixtureV1(identity, 1));
  assert(state.binder.environment.read_proposal_resolution(
      state.binder.environment.proposal_resolution_context, 303, 404,
      resolution));
  assert(resolution == bridge::MarriageProposalNativeResolutionV1::accepted);

  const auto after = Frame(18);
  assert(bridge::PublishMarriageSharedReceiptFrameV1(state, after));
  assert(state.binder.environment.capture_receipt_frame(
      state.binder.environment.receipt_frame_context, captured));
  assert(captured == after);

  auto invalid = after;
  invalid.paused = false;
  assert(!bridge::PublishMarriageSharedReceiptFrameV1(state, invalid));
  assert(bridge::ReadMarriageSharedGlueFailureV1(state) ==
         bridge::MarriageSharedGlueFailureV1::invalid_receipt_frame);
  assert(state.binder.environment.capture_receipt_frame(
      state.binder.environment.receipt_frame_context, captured));
  assert(captured == after);

  assert(!bridge::RemoveMarriageSharedGlueV1(state, false));
  assert(bridge::ReadMarriageSharedGlueFailureV1(state) ==
         bridge::MarriageSharedGlueFailureV1::resolution_remove_failed);
  assert(state.binder.environment.capture_receipt_frame(
      state.binder.environment.receipt_frame_context, captured));

  assert(bridge::RemoveMarriageSharedGlueV1(state, true));
  assert(state.installed.load() == 0);
  assert(fixture.allocations.empty());
  assert(state.binder.environment.capture_receipt_frame == nullptr);
  assert(state.binder.environment.read_alliance_pair == nullptr);
  assert(state.binder.environment.read_proposal_resolution == nullptr);
  assert(!bridge::CaptureMarriageSharedReceiptFrameV1(
      &state.receipt_frames, captured));
  assert(bridge::RemoveMarriageSharedGlueV1(state, true));

  std::cout << "marriage shared glue v1 tests passed\n";
  return 0;
}
