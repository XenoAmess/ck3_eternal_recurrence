#include "xar_bridge/realm_law_application_main_v1.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace {

namespace bridge = xar::bridge;
namespace native = xar::ck3_11906;
namespace private_law = xar::ck3_11906::private_law;

using Completion = bridge::RealmLawApplicationMainCompletionV1;
using Failure = bridge::RealmLawApplicationMainFailureV1;
using Candidate = bridge::RealmLawGovernanceCandidateV1;
using Container = bridge::RealmLawGovernanceSourceContainerLeaseV1;
using Group = bridge::RealmLawGovernanceSourceGroupLeaseV1;
using Player = bridge::RealmLawGovernanceSourcePlayerLeaseV1;
using Presence = bridge::RealmLawGovernancePresenceV1;

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

bridge::RealmLawGovernanceReasonV1 Reason(std::string_view value) {
  bridge::RealmLawGovernanceReasonV1 output{};
  Require(bridge::AssignRealmLawGovernanceReasonV1(value, output),
          "law reason did not fit");
  return output;
}

bridge::RealmLawGovernanceReasonV1 NoReason() {
  bridge::RealmLawGovernanceReasonV1 output{};
  output.presence = Presence::absent;
  return output;
}

bridge::RealmLawGovernanceOptionalKeyV1 OptionalKey(std::string_view value) {
  return {Presence::present, Key(value)};
}

bridge::RealmLawGovernanceSuccessionShapeV1 SuccessionShape() {
  bridge::RealmLawGovernanceSuccessionShapeV1 output{};
  output.presence = Presence::present;
  output.order_of_succession = Key("inheritance");
  output.title_division = OptionalKey("partition");
  output.traversal_order = OptionalKey("children");
  output.rank = OptionalKey("oldest");
  output.primary_heir_minimum_share = {Presence::present, 50'000};
  return output;
}

Candidate Law(std::string_view key, bool active, bool can_enact) {
  Candidate output{};
  output.law_key = Key(key);
  output.is_active = active;
  output.evaluation_complete = true;
  output.can_have = true;
  output.can_pass = true;
  output.can_enact = can_enact;
  output.blocked_reason = can_enact ? NoReason() : Reason("already_enacted");
  output.costs_complete = true;
  output.cost_count = 1;
  output.costs[0] = {Key("prestige"), 100};
  output.succession = SuccessionShape();
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
    proof.current_thread_id = GetCurrentThreadId();
    proof.application_main_thread_id = proof.current_thread_id;
    proof.paused = true;

    frame.public_revision = 901;
    frame.native_revision = 19'006;
    frame.proof_epoch = proof.proof_epoch;
    frame.date_raw = 56'000'000;
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_id = 32'904;
    frame.played_character_alive = true;
    frame.played_character_identity_round_trip = true;

    player = {true, 0x1000, 32'904};
    container = {true, 0x2000, 71, 4, 32'904, 1};
    group.identity_round_trip = true;
    group.native_address = 0x3000;
    group.identity = 81;
    group.generation = 5;
    group.group_key = Key("succession_order_laws");
    group.active_law_key = Key("partition_succession_law");
    group.can_change_evaluated = true;
    group.can_change = true;
    group.candidate_count = 2;
    candidates[0] = Law("partition_succession_law", true, false);
    candidates[1] = Law("high_partition_succession_law", false, true);

    titles.primary_title_presence = Presence::present;
    titles.primary_title_id = 101;
    titles.primary_title_successor_count = 2;
    titles.primary_title_successor_character_ids[0] = 201;
    titles.primary_title_successor_character_ids[1] = 301;
    titles.held_title_count = 1;
    titles.held_titles[0].title_id = 101;
    titles.held_titles[0].primary = true;
    titles.held_titles[0].successor_count = 2;
    titles.held_titles[0].successor_character_ids[0] = 201;
    titles.held_titles[0].successor_character_ids[1] = 301;
  }

  ImageReader image_reader;
  bridge::RealmLawNativeRuntimeProofV1 proof{};
  bridge::RealmLawGovernanceFrameV1 frame{};
  Player player{};
  Container container{};
  Group group{};
  std::array<Candidate, 2> candidates{};
  bridge::RealmLawGovernanceTitleBaselineV1 titles{};
  std::int64_t prestige = 500;
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

bool CaptureFrame(void *context,
                  bridge::RealmLawGovernanceFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool ResolvePlayer(void *context, std::int32_t expected,
                   Player &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  if (expected != fixture.player.character_id) return false;
  output = fixture.player;
  return true;
}

bool ResolveContainer(void *context, const Player &player,
                      Container &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  if (player.native_address != fixture.player.native_address) return false;
  output = fixture.container;
  return true;
}

bool ReadGroup(void *context, const Player &player,
               const Container &container, std::size_t index,
               Group &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  if (index != 0 || player.native_address != fixture.player.native_address ||
      container.native_address != fixture.container.native_address) {
    return false;
  }
  output = fixture.group;
  return true;
}

bool ReadCandidate(void *context, const Player &player,
                   const Container &container, const Group &group,
                   std::size_t index, Candidate &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  if (index >= fixture.candidates.size() ||
      player.native_address != fixture.player.native_address ||
      container.native_address != fixture.container.native_address ||
      group.identity != fixture.group.identity) {
    return false;
  }
  output = fixture.candidates[index];
  return true;
}

bool ReadTitles(void *context, const Player &player,
                bridge::RealmLawGovernanceTitleBaselineV1 &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  if (player.native_address != fixture.player.native_address) return false;
  output = fixture.titles;
  return true;
}

bool ReadResources(void *context,
                   const bridge::RealmLawGovernanceSnapshotV1 &snapshot,
                   bridge::RealmLawNativeResourceSampleV1 &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  output = {};
  output.complete = true;
  output.public_revision = snapshot.public_revision;
  output.native_revision = snapshot.native_revision;
  output.connection_generation = fixture.proof.connection_generation;
  output.proof_epoch = snapshot.proof_epoch;
  output.date_raw = snapshot.date_raw;
  output.player_character_id = snapshot.played_character_id;
  output.resource_count = 1;
  output.resources[0] = {Key("prestige"), fixture.prestige};
  return true;
}

bridge::RealmLawNativeBinderOperationsV1 SourceOperations() noexcept {
  return {&ReadProof, &CaptureFrame, &ResolvePlayer, &ResolveContainer,
          &ReadGroup, &ReadCandidate, &ReadTitles,    &ReadResources,
          nullptr};
}

bool ResolveTarget(
    void *context, const bridge::RealmLawEnactSubmissionV1 &submission,
    bridge::RealmLawNativeEnactTargetLeaseV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.target_resolves;
  output = {};
  output.actor_identity_round_trip = true;
  output.actor_address = fixture.player.native_address;
  output.actor_character_id = submission.player_character_id;
  output.group_identity_round_trip = true;
  output.group_identity = fixture.group.identity;
  output.group_generation = fixture.group.generation;
  output.group_key = submission.group_key;
  output.law_identity_round_trip = true;
  output.law_address = 0x73000;
  output.law_identity = 91;
  output.law_generation = 6;
  output.law_key = submission.requested_law_key;
  output.connection_generation = fixture.proof.connection_generation;
  output.proof_epoch = fixture.proof.proof_epoch;
  return true;
}

bool ValidateCommand(void *context, const void *command,
                     std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validator_calls;
  return size == bridge::kRealmLawNativeAddLawCommandSizeV1 &&
      Load<std::uintptr_t>(command, 0x00) ==
          fixture.proof.module_base +
              private_law::kAddLawCommandPrimaryVtableRvaV1 &&
      Load<std::uintptr_t>(command, 0x18) ==
          fixture.proof.module_base +
              private_law::kAddLawCommandSecondaryVtableRvaV1 &&
      Load<std::int32_t>(command, 0x20) == fixture.player.character_id &&
      Load<std::uintptr_t>(command, 0x28) == 0x73000;
}

bool QueueCommand(void *context, std::uintptr_t manager, const void *command,
                  std::size_t size, std::uint32_t flags) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.queue_calls;
  return manager ==
             fixture.proof.module_base + private_law::kCommandManagerRvaV1 &&
      size == bridge::kRealmLawNativeAddLawCommandSizeV1 &&
      flags == bridge::kRealmLawNativeSubmitFlagsV1 &&
      Load<std::int32_t>(command, 0x20) == fixture.player.character_id &&
      Load<std::uintptr_t>(command, 0x28) == 0x73000;
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

bridge::RealmLawEnactActionRequestV1 Request(
    std::string_view id = "law8-test-1") {
  bridge::RealmLawEnactActionRequestV1 output{};
  output.request_id.assign(id);
  output.group_key = Key("succession_order_laws");
  output.law_key = Key("high_partition_succession_law");
  output.expected_public_revision = 901;
  output.expected_native_revision = 19'006;
  output.expected_proof_epoch = 33;
  output.expected_date_raw = 56'000'000;
  output.expected_player_character_id = 32'904;
  output.budget_count = 1;
  output.budgets[0] = {Key("prestige"), 100};
  return output;
}

native::MainThreadExecutionStampV1 Stamp(const Fixture &fixture) noexcept {
  native::MainThreadExecutionStampV1 output{};
  output.pump_epoch = 10;
  output.thread_id = GetCurrentThreadId();
  output.tls_initialized_flag_address = 0x1000;
  output.tls_initialized = 1;
  output.tls_context = 0x2000;
  output.tls_main_thread_marker = 1;
  output.jomini_state = 0x3000;
  output.game_state = 0x4000;
  output.date_raw = static_cast<std::int32_t>(fixture.frame.date_raw);
  output.paused = true;
  return output;
}

void PrepareMailbox(native::MainThreadQueryMailboxV1 &mailbox,
                    std::uintptr_t module_base) noexcept {
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::idle);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.executor_submission_enabled = true;
  mailbox.module_base = module_base;
  mailbox.permitted_executor_septentrigintary =
      &bridge::ExecuteRealmLawApplicationMainV1;
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      native::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
}

void ExecuteAndComplete(
    native::MainThreadQueryMailboxV1 &mailbox,
    bridge::RealmLawApplicationMainContextV1 &context,
    const native::MainThreadExecutionStampV1 &stamp,
    bool expected_result = true) {
  Require(mailbox.state.load() == native::MainThreadQueryMailboxStateV1::queued,
          "mailbox request was not queued");
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::executing);
  const bool result =
      bridge::ExecuteRealmLawApplicationMainV1(&context, stamp);
  Require(result == expected_result, "executor returned the wrong status");
  mailbox.executor_succeeded = result;
  mailbox.completed_sequence.store(context.ticket.sequence);
  mailbox.state.store(result
                          ? native::MainThreadQueryMailboxStateV1::completed
                          : native::MainThreadQueryMailboxStateV1::
                                executor_failed);
}

void Reclaim(bridge::RealmLawApplicationMainContextV1 &context) {
  Require(bridge::ReclaimRealmLawApplicationMainV1(context) ==
              native::MainThreadQueryReclaimResultV1::reclaimed,
          "mailbox ticket was not reclaimed");
}

void AdvanceToEnacted(Fixture &fixture) {
  ++fixture.frame.public_revision;
  ++fixture.frame.native_revision;
  ++fixture.proof.proof_epoch;
  fixture.frame.proof_epoch = fixture.proof.proof_epoch;
  fixture.group.active_law_key = Key("high_partition_succession_law");
  fixture.candidates[0] = Law("partition_succession_law", false, true);
  fixture.candidates[1] = Law("high_partition_succession_law", true, false);
  fixture.prestige = 400;
}

struct Harness {
  explicit Harness(Fixture &fixture) {
    PrepareMailbox(mailbox, fixture.proof.module_base);
    Require(bridge::ConfigureRealmLawApplicationMainV1(
                mailbox, Configuration(fixture), state, context),
            "LAW8 configuration failed");
  }

  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::RealmLawApplicationMainStateV1 state{};
  bridge::RealmLawApplicationMainContextV1 context{};
};

void QueueSubmit(Fixture &fixture, Harness &harness,
                 std::string_view id = "law8-test-1") {
  Require(bridge::PrepareRealmLawApplicationMainSubmitV1(
              harness.context, Request(id)),
          "submit preparation failed");
  Require(bridge::TryQueueRealmLawApplicationMainV1(harness.context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "submit ticket was not queued");
  ExecuteAndComplete(harness.mailbox, harness.context, Stamp(fixture));
}

void QueueReceipt(Fixture &fixture, Harness &harness) {
  Require(bridge::PrepareRealmLawApplicationMainReceiptV1(harness.context),
          "receipt preparation failed");
  Require(bridge::TryQueueRealmLawApplicationMainV1(harness.context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "receipt ticket was not queued");
  ExecuteAndComplete(harness.mailbox, harness.context, Stamp(fixture));
}

void TestSubmitAndIndependentFreshReceipt(const DiskPeImage &image) {
  Fixture fixture(image);
  auto harness = std::make_unique<Harness>(fixture);
  Require(!harness->state.initialized && fixture.image_reader.reads == 0,
          "native binding happened outside the application-main executor");
  QueueSubmit(fixture, *harness);
  Require(harness->context.completion ==
              Completion::submitted_verification_pending &&
              harness->state.initialized && harness->state.has_pending_ack &&
              harness->state.native_binder.submit_pending,
          "submit ACK did not remain verification-pending");
  Require(fixture.image_reader.reads != 0 && fixture.target_resolves == 2 &&
              fixture.validator_calls == 1 && fixture.queue_calls == 1,
          "exact LAW7 submit chain did not execute once");
  const auto submit_sequence = harness->state.pending_submit_sequence;
  Reclaim(harness->context);

  AdvanceToEnacted(fixture);
  QueueReceipt(fixture, *harness);
  Require(harness->context.ticket.sequence > submit_sequence,
          "receipt did not use an independent mailbox ticket");
  Require(harness->context.completion == Completion::receipt_enacted &&
              harness->context.receipt.effective_law_verified &&
              harness->context.receipt.resources_verified &&
              harness->context.receipt.succession_verified,
          "fresh law/resource/succession receipt did not verify");
  Require(!harness->state.has_pending_ack &&
              !harness->state.native_binder.submit_pending &&
              fixture.queue_calls == 1,
          "receipt retained pending state or submitted twice");
  Reclaim(harness->context);
}

void TestPendingAckSurvivesDuplicateAndStaleReceipt(
    const DiskPeImage &image) {
  Fixture fixture(image);
  auto harness = std::make_unique<Harness>(fixture);
  QueueSubmit(fixture, *harness, "law8-original");
  Reclaim(harness->context);
  const auto original_sequence = harness->state.pending_submit_sequence;

  QueueSubmit(fixture, *harness, "law8-duplicate");
  Require(harness->context.completion == Completion::action_red &&
              harness->context.failure == Failure::pending_ack &&
              harness->state.pending_ack.request_id == "law8-original" &&
              harness->state.pending_submit_sequence == original_sequence &&
              fixture.queue_calls == 1,
          "duplicate submit replaced the pending ACK");
  Reclaim(harness->context);

  QueueReceipt(fixture, *harness);
  Require(harness->context.completion == Completion::receipt_red &&
              harness->context.receipt_failure ==
                  bridge::RealmLawEnactActionReceiptFailureV1::
                      no_new_paused_snapshot &&
              harness->state.has_pending_ack &&
              harness->state.native_binder.submit_pending,
          "stale receipt cleared or hid the pending ACK");
  Reclaim(harness->context);
}

void TestActionAndBindingRedStayTyped(const DiskPeImage &image) {
  Fixture denied(image);
  auto denied_harness = std::make_unique<Harness>(denied);
  auto denied_request = Request("law8-denied");
  denied_request.budget_count = 0;
  Require(bridge::PrepareRealmLawApplicationMainSubmitV1(
              denied_harness->context, denied_request),
          "denied action preparation failed");
  Require(bridge::TryQueueRealmLawApplicationMainV1(
              denied_harness->context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "denied action did not queue");
  ExecuteAndComplete(denied_harness->mailbox, denied_harness->context,
                     Stamp(denied));
  Require(denied_harness->context.completion == Completion::action_red &&
              denied_harness->context.failure == Failure::action_rejected &&
              denied_harness->context.action_failure ==
                  bridge::RealmLawEnactActionFailureV1::
                      budget_not_authorized &&
              denied.queue_calls == 0,
          "authority denial did not remain typed action RED");
  Reclaim(denied_harness->context);

  Fixture corrupt(image);
  corrupt.image_reader.corrupt = true;
  auto corrupt_harness = std::make_unique<Harness>(corrupt);
  QueueSubmit(corrupt, *corrupt_harness, "law8-corrupt");
  Require(corrupt_harness->context.completion == Completion::binding_red &&
              corrupt_harness->context.failure == Failure::native_binding &&
              corrupt_harness->state.native_glue.failure ==
                  bridge::RealmLawNativeSharedGlueFailureV1::
                      mutation_abi_rejected &&
              corrupt.queue_calls == 0,
          "mutation ABI drift did not remain binding RED");
  Reclaim(corrupt_harness->context);
}

void TestMailboxIdentityAndStampMismatchStayRed(const DiskPeImage &image) {
  Fixture identity(image);
  auto identity_harness = std::make_unique<Harness>(identity);
  Require(bridge::PrepareRealmLawApplicationMainSubmitV1(
              identity_harness->context, Request("law8-identity")),
          "identity test preparation failed");
  Require(bridge::TryQueueRealmLawApplicationMainV1(
              identity_harness->context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "identity test did not queue");
  identity_harness->mailbox.executor_context = nullptr;
  ExecuteAndComplete(identity_harness->mailbox, identity_harness->context,
                     Stamp(identity), false);
  Require(identity_harness->context.completion ==
              Completion::infrastructure_red &&
              identity_harness->context.failure == Failure::mailbox_identity &&
              identity.image_reader.reads == 0 && identity.queue_calls == 0,
          "wrong mailbox identity reached native binding");
  Reclaim(identity_harness->context);

  Fixture stamp_fixture(image);
  auto stamp_harness = std::make_unique<Harness>(stamp_fixture);
  auto request = Request("law8-stamp");
  ++request.expected_date_raw;
  Require(bridge::PrepareRealmLawApplicationMainSubmitV1(
              stamp_harness->context, request),
          "stamp test preparation failed");
  Require(bridge::TryQueueRealmLawApplicationMainV1(stamp_harness->context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "stamp test did not queue");
  ExecuteAndComplete(stamp_harness->mailbox, stamp_harness->context,
                     Stamp(stamp_fixture));
  Require(stamp_harness->context.completion == Completion::action_red &&
              stamp_harness->context.failure == Failure::stamp_mismatch &&
              stamp_fixture.image_reader.reads == 0 &&
              stamp_fixture.queue_calls == 0,
          "request/stamp mismatch reached native binding");
  Reclaim(stamp_harness->context);

  Fixture receipt_stamp_fixture(image);
  auto receipt_stamp_harness =
      std::make_unique<Harness>(receipt_stamp_fixture);
  QueueSubmit(receipt_stamp_fixture, *receipt_stamp_harness,
              "law8-receipt-stamp");
  Reclaim(receipt_stamp_harness->context);
  AdvanceToEnacted(receipt_stamp_fixture);
  Require(bridge::PrepareRealmLawApplicationMainReceiptV1(
              receipt_stamp_harness->context),
          "receipt stamp preparation failed");
  Require(bridge::TryQueueRealmLawApplicationMainV1(
              receipt_stamp_harness->context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "receipt stamp test did not queue");
  auto wrong_receipt_stamp = Stamp(receipt_stamp_fixture);
  ++wrong_receipt_stamp.date_raw;
  ExecuteAndComplete(receipt_stamp_harness->mailbox,
                     receipt_stamp_harness->context,
                     wrong_receipt_stamp);
  Require(receipt_stamp_harness->context.completion ==
              Completion::receipt_red &&
              receipt_stamp_harness->context.failure ==
                  Failure::stamp_mismatch &&
              receipt_stamp_harness->state.has_pending_ack &&
              receipt_stamp_harness->state.native_binder.submit_pending,
          "receipt/stamp mismatch did not retain the pending transaction");
  Reclaim(receipt_stamp_harness->context);
}

} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2,
            "usage: realm_law_application_main_v1_test ck3.exe");
    const DiskPeImage image(argv[1]);
    TestSubmitAndIndependentFreshReceipt(image);
    TestPendingAckSurvivesDuplicateAndStaleReceipt(image);
    TestActionAndBindingRedStayTyped(image);
    TestMailboxIdentityAndStampMismatchStayRed(image);
    std::cout << "realm_law_application_main_v1_test: 4/4 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "realm_law_application_main_v1 RED: " << error.what()
              << '\n';
    return 1;
  }
}
