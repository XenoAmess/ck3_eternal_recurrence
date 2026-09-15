#include "xar_bridge/realm_law_native_shared_glue_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace bridge = xar::bridge;
namespace private_law = xar::ck3_11906::private_law;

using Disposition = bridge::RealmLawNativeSubmitDispositionV1;
using Failure = bridge::RealmLawNativeSharedGlueFailureV1;

constexpr std::string_view kSourceManifest =
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <typename Value>
Value Load(const void *source, std::size_t offset) {
  Value output{};
  std::memcpy(&output, static_cast<const std::byte *>(source) + offset,
              sizeof(output));
  return output;
}

struct Section {
  std::uint32_t virtual_address = 0;
  std::uint32_t mapped_size = 0;
  std::uint32_t raw_pointer = 0;
  std::uint32_t raw_size = 0;
};

class DiskPeImage {
public:
  explicit DiskPeImage(const char *path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    Require(input.good(), "could not open exact CK3 executable");
    const auto length = input.tellg();
    Require(length > 0, "exact CK3 executable is empty");
    bytes_.resize(static_cast<std::size_t>(length));
    input.seekg(0, std::ios::beg);
    input.read(reinterpret_cast<char *>(bytes_.data()), length);
    Require(input.good(), "could not read exact CK3 executable");

    Require(ReadU16(0) == 0x5A4D, "DOS signature mismatch");
    const std::size_t pe = ReadU32(0x3C);
    Require(ReadU32(pe) == 0x00004550, "PE signature mismatch");
    const std::size_t coff = pe + 4;
    Require(ReadU16(coff) == 0x8664, "PE machine mismatch");
    const auto section_count = ReadU16(coff + 2);
    const auto optional_size = ReadU16(coff + 16);
    const std::size_t optional = coff + 20;
    Require(ReadU16(optional) == 0x20B, "PE32+ header mismatch");
    preferred_base_ = ReadU64(optional + 24);
    image_size_ = ReadU32(optional + 56);
    headers_size_ = ReadU32(optional + 60);
    const std::size_t section_table = optional + optional_size;
    for (std::uint16_t index = 0; index < section_count; ++index) {
      const std::size_t entry = section_table + index * 40U;
      const auto virtual_size = ReadU32(entry + 8);
      const auto raw_size = ReadU32(entry + 16);
      sections_.push_back({ReadU32(entry + 12),
                           virtual_size > raw_size ? virtual_size : raw_size,
                           ReadU32(entry + 20), raw_size});
    }
  }

  std::uintptr_t preferred_base() const noexcept { return preferred_base_; }

  bool Read(std::uintptr_t rva, void *destination,
            std::size_t size) const noexcept {
    if (destination == nullptr || rva > image_size_ ||
        size > image_size_ - rva) {
      return false;
    }
    if (rva < headers_size_) {
      return Copy(static_cast<std::size_t>(rva), destination, size);
    }
    for (const auto &section : sections_) {
      if (rva < section.virtual_address) continue;
      const auto relative = rva - section.virtual_address;
      if (relative <= section.mapped_size &&
          size <= section.mapped_size - relative &&
          relative <= section.raw_size && size <= section.raw_size - relative) {
        return Copy(static_cast<std::size_t>(section.raw_pointer + relative),
                    destination, size);
      }
    }
    return false;
  }

private:
  template <typename Value>
  Value ReadValue(std::size_t offset) const {
    Require(offset <= bytes_.size() &&
                sizeof(Value) <= bytes_.size() - offset,
            "PE integer read out of range");
    Value output{};
    std::memcpy(&output, bytes_.data() + offset, sizeof(output));
    return output;
  }

  std::uint16_t ReadU16(std::size_t offset) const {
    return ReadValue<std::uint16_t>(offset);
  }
  std::uint32_t ReadU32(std::size_t offset) const {
    return ReadValue<std::uint32_t>(offset);
  }
  std::uint64_t ReadU64(std::size_t offset) const {
    return ReadValue<std::uint64_t>(offset);
  }

  bool Copy(std::size_t offset, void *destination,
            std::size_t size) const noexcept {
    if (offset > bytes_.size() || size > bytes_.size() - offset) return false;
    std::memcpy(destination, bytes_.data() + offset, size);
    return true;
  }

  std::vector<unsigned char> bytes_;
  std::vector<Section> sections_;
  std::uintptr_t preferred_base_ = 0;
  std::uintptr_t image_size_ = 0;
  std::uintptr_t headers_size_ = 0;
};

struct ImageReader {
  const DiskPeImage *image = nullptr;
  bool corrupt = false;
  std::size_t reads = 0;
};

bool ReadImage(void *context, std::uintptr_t rva, void *destination,
               std::size_t size) noexcept {
  auto &reader = *static_cast<ImageReader *>(context);
  ++reader.reads;
  if (!reader.image->Read(rva, destination, size)) return false;
  if (reader.corrupt && rva == private_law::kGuiLawCanEnactReceiverRvaV1 &&
      size != 0) {
    *static_cast<unsigned char *>(destination) ^= 1U;
  }
  return true;
}

bridge::RealmLawGovernanceKeyV1 Key(std::string_view value) {
  bridge::RealmLawGovernanceKeyV1 output{};
  Require(bridge::AssignRealmLawGovernanceKeyV1(value, output),
          "law key did not fit");
  return output;
}

struct Fixture {
  explicit Fixture(const DiskPeImage &image) : image_reader{&image, false, 0} {
    proof.exact_build_admitted = true;
    Require(bridge::AssignRealmLawNativeDigestV1(
                bridge::kRealmLawNativeSharedGlueV1ExecutableSha256,
                proof.executable_sha256),
            "executable digest did not fit");
    proof.module_base = image.preferred_base();
    proof.signatures_complete = true;
    Require(bridge::AssignRealmLawNativeDigestV1(
                kSourceManifest, proof.signature_manifest_sha256),
            "source manifest did not fit");
    proof.signature_generation = 7;
    proof.connection_generation = 19;
    proof.proof_epoch = 33;
    proof.current_thread_id = 77;
    proof.application_main_thread_id = 77;
    proof.paused = true;
  }

  ImageReader image_reader;
  bridge::RealmLawNativeRuntimeProofV1 proof{};
  bool target_drift = false;
  bool proof_drift_after_target = false;
  bool validator_result = true;
  bool queue_result = true;
  std::size_t proof_reads = 0;
  std::size_t target_resolves = 0;
  std::size_t validator_calls = 0;
  std::size_t queue_calls = 0;
};

bool ReadProof(void *context,
               bridge::RealmLawNativeRuntimeProofV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.proof_reads;
  output = fixture.proof;
  return true;
}

bool CaptureFrame(void *, bridge::RealmLawGovernanceFrameV1 &) noexcept {
  return false;
}
bool ResolvePlayer(void *, std::int32_t,
                   bridge::RealmLawGovernanceSourcePlayerLeaseV1 &) noexcept {
  return false;
}
bool ResolveContainer(
    void *, const bridge::RealmLawGovernanceSourcePlayerLeaseV1 &,
    bridge::RealmLawGovernanceSourceContainerLeaseV1 &) noexcept {
  return false;
}
bool ReadGroup(void *,
               const bridge::RealmLawGovernanceSourcePlayerLeaseV1 &,
               const bridge::RealmLawGovernanceSourceContainerLeaseV1 &,
               std::size_t,
               bridge::RealmLawGovernanceSourceGroupLeaseV1 &) noexcept {
  return false;
}
bool ReadCandidate(
    void *, const bridge::RealmLawGovernanceSourcePlayerLeaseV1 &,
    const bridge::RealmLawGovernanceSourceContainerLeaseV1 &,
    const bridge::RealmLawGovernanceSourceGroupLeaseV1 &, std::size_t,
    bridge::RealmLawGovernanceCandidateV1 &) noexcept {
  return false;
}
bool ReadTitles(void *,
                const bridge::RealmLawGovernanceSourcePlayerLeaseV1 &,
                bridge::RealmLawGovernanceTitleBaselineV1 &) noexcept {
  return false;
}
bool ReadResources(void *, const bridge::RealmLawGovernanceSnapshotV1 &,
                   bridge::RealmLawNativeResourceSampleV1 &) noexcept {
  return false;
}

bridge::RealmLawNativeBinderOperationsV1 SourceOperations() noexcept {
  return {&ReadProof,  &CaptureFrame, &ResolvePlayer, &ResolveContainer,
          &ReadGroup,  &ReadCandidate, &ReadTitles,    &ReadResources,
          nullptr};
}

bridge::RealmLawEnactSubmissionV1 Submission() {
  bridge::RealmLawEnactSubmissionV1 output{};
  output.player_character_id = 32'904;
  output.group_key = Key("succession_order_laws");
  output.previous_effective_law_key = Key("partition_succession_law");
  output.requested_law_key = Key("high_partition_succession_law");
  output.public_revision = 901;
  output.native_revision = 19'006;
  output.proof_epoch = 33;
  output.charge_count = 1;
  output.charges[0] = {Key("prestige"), 100, 500, 0};
  return output;
}

bool ResolveTarget(
    void *context, const bridge::RealmLawEnactSubmissionV1 &submission,
    bridge::RealmLawNativeEnactTargetLeaseV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.target_resolves;
  output = {};
  output.actor_identity_round_trip = true;
  output.actor_address = 0x71000;
  output.actor_character_id = submission.player_character_id;
  output.group_identity_round_trip = true;
  output.group_identity = 81;
  output.group_generation = 5;
  output.group_key = submission.group_key;
  output.law_identity_round_trip = true;
  output.law_address = 0x73000;
  output.law_identity = 91;
  output.law_generation = 6;
  output.law_key = submission.requested_law_key;
  output.connection_generation = fixture.proof.connection_generation;
  output.proof_epoch = fixture.proof.proof_epoch;
  if (fixture.target_drift && fixture.target_resolves == 2) {
    ++output.law_generation;
  }
  if (fixture.proof_drift_after_target && fixture.target_resolves == 1) {
    ++fixture.proof.proof_epoch;
  }
  return true;
}

bool ValidateCommand(void *context, const void *command,
                     std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validator_calls;
  const bool layout = size == bridge::kRealmLawNativeAddLawCommandSizeV1 &&
      Load<std::uintptr_t>(command, 0x00) ==
          fixture.proof.module_base +
              private_law::kAddLawCommandPrimaryVtableRvaV1 &&
      Load<std::uintptr_t>(command, 0x18) ==
          fixture.proof.module_base +
              private_law::kAddLawCommandSecondaryVtableRvaV1 &&
      Load<std::int32_t>(command, 0x20) == 32'904 &&
      Load<std::uintptr_t>(command, 0x28) == 0x73000;
  return fixture.validator_result && layout;
}

bool QueueCommand(void *context, std::uintptr_t manager,
                  const void *command, std::size_t size,
                  std::uint32_t flags) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.queue_calls;
  const bool contract =
      manager == fixture.proof.module_base + private_law::kCommandManagerRvaV1 &&
      flags == bridge::kRealmLawNativeSubmitFlagsV1 &&
      size == bridge::kRealmLawNativeAddLawCommandSizeV1 &&
      Load<std::int32_t>(command, 0x20) == 32'904 &&
      Load<std::uintptr_t>(command, 0x28) == 0x73000;
  return fixture.queue_result && contract;
}

bridge::RealmLawNativeSharedGlueConfigurationV1 Configuration(
    Fixture &fixture) noexcept {
  bridge::RealmLawNativeSharedGlueConfigurationV1 output{};
  output.enabled = true;
  output.offline_fixture = true;
  output.native_submit_enabled = true;
  output.module_base = fixture.proof.module_base;
  output.admitted_executable_sha256 =
      bridge::kRealmLawNativeSharedGlueV1ExecutableSha256;
  output.expected_source_signature_manifest_sha256 = kSourceManifest;
  output.mutation_abi_reader = {&fixture.image_reader, &ReadImage};
  output.source_context = &fixture;
  output.source_operations = SourceOperations();
  output.target_context = &fixture;
  output.resolve_target = &ResolveTarget;
  output.offline_call_context = &fixture;
  output.offline_calls = {&ValidateCommand, &QueueCommand};
  return output;
}

std::unique_ptr<bridge::RealmLawNativeSharedGlueStateV1> Prepare(
    Fixture &fixture) {
  auto state = std::make_unique<bridge::RealmLawNativeSharedGlueStateV1>();
  Require(bridge::PrepareRealmLawNativeSharedGlueV1(Configuration(fixture),
                                                    *state),
          "exact glue configuration was rejected");
  return state;
}

void TestExactAbiBuildsCompleteBinderTable(const DiskPeImage &image) {
  Fixture fixture(image);
  auto state = Prepare(fixture);
  Require(state->prepared && state->failure == Failure::none,
          "prepared glue retained a failure");
  Require(fixture.image_reader.reads != 0,
          "prepare did not verify the exact mutation ABI");

  const auto environment =
      bridge::MakeRealmLawNativeSharedGlueEnvironmentV1(*state);
  Require(environment.binding_enabled && environment.offline_fixture,
          "glue did not publish the binder environment");
  Require(environment.expected_signature_manifest_sha256 ==
              bridge::kRealmLawNativeSharedGlueV1MutationManifestSha256,
          "binder environment did not carry the mutation ABI manifest");
  auto binder = std::make_unique<bridge::RealmLawNativeBinderStateV1>();
  Require(bridge::BindRealmLawNativeV1(environment, *binder),
          "LAW5 rejected the LAW7 operation table");
  Require(binder->attached, "LAW5 binder was not attached");

  const auto reads_after_prepare = fixture.image_reader.reads;
  const auto disposition =
      environment.operations.submit_enact(environment.native_context,
                                           Submission());
  Require(disposition == Disposition::submitted,
          "exact offline command was not queued");
  Require(fixture.target_resolves == 2 && fixture.validator_calls == 1 &&
              fixture.queue_calls == 1,
          "submit did not use the double-resolve/validate/queue sequence");
  Require(fixture.image_reader.reads == reads_after_prepare,
          "steady-state glue rehashed the executable after preparation");
  Require(state->native_queue_calls == 1,
          "queue counter did not record the single handoff");
}

void TestAbiDriftAndSourceOverrideFailClosed(const DiskPeImage &image) {
  Fixture drift(image);
  drift.image_reader.corrupt = true;
  auto state = std::make_unique<bridge::RealmLawNativeSharedGlueStateV1>();
  Require(!bridge::PrepareRealmLawNativeSharedGlueV1(Configuration(drift),
                                                     *state),
          "corrupt mutation ABI prepared");
  Require(state->failure == Failure::mutation_abi_rejected &&
              state->abi_failure ==
                  private_law::RealmLawMutationAbiFailureV1::
                      instruction_span_mismatch,
          "corrupt mutation ABI returned the wrong typed failure");

  Fixture override_fixture(image);
  auto configuration = Configuration(override_fixture);
  configuration.source_operations.submit_enact =
      +[](void *, const bridge::RealmLawEnactSubmissionV1 &) noexcept {
        return Disposition::submitted;
      };
  state = std::make_unique<bridge::RealmLawNativeSharedGlueStateV1>();
  Require(!bridge::PrepareRealmLawNativeSharedGlueV1(configuration, *state) &&
              state->failure == Failure::source_submit_override_forbidden,
          "upstream submit override was not rejected");
}

void TestPreflightFailuresNeverReachQueue(const DiskPeImage &image) {
  Fixture disabled(image);
  auto configuration = Configuration(disabled);
  configuration.native_submit_enabled = false;
  auto state = std::make_unique<bridge::RealmLawNativeSharedGlueStateV1>();
  Require(bridge::PrepareRealmLawNativeSharedGlueV1(configuration, *state),
          "disabled-submit fixture did not prepare");
  auto environment =
      bridge::MakeRealmLawNativeSharedGlueEnvironmentV1(*state);
  Require(environment.operations.submit_enact(environment.native_context,
                                              Submission()) ==
              Disposition::not_submitted &&
              state->failure == Failure::native_submit_disabled &&
              disabled.target_resolves == 0 && disabled.queue_calls == 0,
          "disabled submit reached native preflight");

  Fixture target_drift(image);
  target_drift.target_drift = true;
  state = Prepare(target_drift);
  environment = bridge::MakeRealmLawNativeSharedGlueEnvironmentV1(*state);
  Require(environment.operations.submit_enact(environment.native_context,
                                              Submission()) ==
              Disposition::not_submitted &&
              state->failure == Failure::target_sample_drift &&
              target_drift.validator_calls == 0 && target_drift.queue_calls == 0,
          "drifting native target reached validation or queue");

  Fixture proof_drift(image);
  proof_drift.proof_drift_after_target = true;
  state = Prepare(proof_drift);
  environment = bridge::MakeRealmLawNativeSharedGlueEnvironmentV1(*state);
  Require(environment.operations.submit_enact(environment.native_context,
                                              Submission()) ==
              Disposition::not_submitted &&
              state->failure == Failure::runtime_proof_mismatch &&
              proof_drift.target_resolves == 1 && proof_drift.queue_calls == 0,
          "proof drift after target resolution reached queue");

  Fixture denied(image);
  denied.validator_result = false;
  state = Prepare(denied);
  environment = bridge::MakeRealmLawNativeSharedGlueEnvironmentV1(*state);
  Require(environment.operations.submit_enact(environment.native_context,
                                              Submission()) ==
              Disposition::not_submitted &&
              state->failure == Failure::final_legality_denied &&
              denied.validator_calls == 1 && denied.queue_calls == 0,
          "final legality denial reached queue");

  Fixture rejected(image);
  rejected.queue_result = false;
  state = Prepare(rejected);
  environment = bridge::MakeRealmLawNativeSharedGlueEnvironmentV1(*state);
  Require(environment.operations.submit_enact(environment.native_context,
                                              Submission()) ==
              Disposition::not_submitted &&
              state->failure == Failure::native_queue_rejected &&
              rejected.validator_calls == 1 && rejected.queue_calls == 1,
          "queue rejection returned the wrong state");
}

void TestFailureNames() {
  Require(bridge::RealmLawNativeSharedGlueFailureNameV1(
              Failure::mutation_abi_rejected) == "mutation_abi_rejected",
          "mutation failure name changed");
  Require(bridge::RealmLawNativeSharedGlueFailureNameV1(
              Failure::native_queue_rejected) == "native_queue_rejected",
          "queue failure name changed");
}

} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2,
            "usage: realm_law_native_shared_glue_v1_test ck3.exe");
    const DiskPeImage image(argv[1]);
    TestExactAbiBuildsCompleteBinderTable(image);
    TestAbiDriftAndSourceOverrideFailClosed(image);
    TestPreflightFailuresNeverReachQueue(image);
    TestFailureNames();
    std::cout << "realm_law_native_shared_glue_v1_test: 4/4 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "realm_law_native_shared_glue_v1 RED: " << error.what()
              << '\n';
    return 1;
  }
}
