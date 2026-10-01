#include "xar_bridge/ck3_12002_realm_law_enact_command_v1.hpp"

#include <cassert>
#include <cstring>
#include <iostream>
#include <new>

namespace {
using namespace xar::ck3_12002::private_law;
using xar::bridge::RealmLawEnactSubmissionV1;
using xar::bridge::RealmLawNativeEnactTargetLeaseV1;
using xar::bridge::RealmLawNativeSubmitDispositionV1;

template <typename Value>
Value Load(const AddLawCommandV1 &command, std::size_t offset) {
  Value value{};
  std::memcpy(&value, command.bytes.data() + offset, sizeof(value));
  return value;
}

struct Fixture {
  AddLawCommandV1 submitted{};
  int validations = 0;
  int clones = 0;
  int queues = 0;
  int destructions = 0;
  bool legal = true;
  bool queue_accepts = true;
  bool clone_available = true;
  std::array<unsigned char, 5> padding{};
};

bool Validate(void *context, const AddLawCommandV1 &command) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validations;
  assert(Load<std::uintptr_t>(command, 0) == 0x140000000ULL +
      kAddLawCommandPrimaryVtableRvaV1);
  assert(Load<std::uintptr_t>(command, 0x18) == 0x140000000ULL +
      kAddLawCommandSecondaryVtableRvaV1);
  assert(Load<std::int32_t>(command, 0x20) == 0x02007485);
  assert(Load<std::uintptr_t>(command, 0x28) == 0x240080000ULL);
  for (std::size_t index = 8; index < 0x18; ++index) {
    assert(command.bytes[index] == 0);
  }
  return fixture.legal;
}

bool Clone(void *context, const AddLawCommandV1 &command,
            void *&owned) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.clones;
  if (!fixture.clone_available) return false;
  owned = new (std::nothrow) AddLawCommandV1(command);
  return owned != nullptr;
}

bool Queue(void *context, std::uintptr_t manager, void *&owned,
           std::uint32_t flags) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.queues;
  assert(manager == 0x140000000ULL + kCommandManagerRvaV1);
  assert(flags == 0x0E);
  assert(owned != nullptr);
  fixture.submitted = *static_cast<AddLawCommandV1 *>(owned);
  delete static_cast<AddLawCommandV1 *>(owned);
  owned = nullptr; // The native queue consumes ownership in either outcome.
  return fixture.queue_accepts;
}

void Destroy(void *context, void *owned) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.destructions;
  delete static_cast<AddLawCommandV1 *>(owned);
}

struct Inputs {
  Fixture fixture{};
  AddLawCommandOfflineCallsV1 calls{};
  AddLawCommandAccessV1 access{};
  RealmLawEnactSubmissionV1 submission{};
  RealmLawNativeEnactTargetLeaseV1 target{};

  Inputs() {
    calls = {&fixture, Validate, Clone, Queue, Destroy};
    access.module_base = 0x140000000ULL;
    access.mutation_abi_proof.verified = true;
    access.mutation_abi_proof.failure = RealmLawMutationAbiFailureV1::none;
    access.submit_enabled = true;
    access.offline_calls = &calls;
    submission.player_character_id = 0x02007485;
    submission.proof_epoch = 17;
    submission.group_key.size = 15;
    std::memcpy(submission.group_key.bytes.data(), "crown_authority", 15);
    submission.requested_law_key.size = 17;
    std::memcpy(submission.requested_law_key.bytes.data(), "crown_authority_1", 17);
    target.actor_identity_round_trip = true;
    target.actor_address = 0x240070000ULL;
    target.actor_character_id = submission.player_character_id;
    target.law_identity_round_trip = true;
    target.law_address = 0x240080000ULL;
    target.law_key = submission.requested_law_key;
    target.group_key = submission.group_key;
    target.proof_epoch = submission.proof_epoch;
  }
};

void TestQueueAcceptanceIsPending() {
  Inputs input;
  const auto result = SubmitAddLawCommandV1(input.access, input.submission,
                                           input.target);
  assert(result.disposition == RealmLawNativeSubmitDispositionV1::submitted);
  assert(result.failure == AddLawCommandFailureV1::none);
  assert(result.final_legality_called && result.native_queue_called);
  assert(input.fixture.validations == 1 && input.fixture.clones == 1);
  assert(input.fixture.queues == 1 && input.fixture.destructions == 0);
  // This ACK contains no effective-law/resource/succession success claim.
}

void TestFinalNativeDenialDoesNotQueue() {
  Inputs input;
  input.fixture.legal = false;
  const auto result = SubmitAddLawCommandV1(input.access, input.submission,
                                           input.target);
  assert(result.failure == AddLawCommandFailureV1::final_legality_denied);
  assert(result.disposition == RealmLawNativeSubmitDispositionV1::not_submitted);
  assert(input.fixture.validations == 1 && input.fixture.clones == 0);
  assert(input.fixture.queues == 0);
}

void TestNativeQueueRejectionIsNotAcknowledged() {
  Inputs input;
  input.fixture.queue_accepts = false;
  const auto result = SubmitAddLawCommandV1(input.access, input.submission,
                                           input.target);
  assert(result.failure == AddLawCommandFailureV1::queue_rejected);
  assert(result.disposition == RealmLawNativeSubmitDispositionV1::not_submitted);
  assert(input.fixture.clones == 1 && input.fixture.queues == 1);
  assert(input.fixture.destructions == 0);
}

void TestDisabledDefaultDoesNotInvokeNativeEntries() {
  Inputs input;
  input.access.submit_enabled = false;
  const auto result = SubmitAddLawCommandV1(input.access, input.submission,
                                           input.target);
  assert(result.failure == AddLawCommandFailureV1::submit_disabled);
  assert(input.fixture.validations == 0 && input.fixture.clones == 0);
  assert(input.fixture.queues == 0);
}
} // namespace

int main() {
  TestQueueAcceptanceIsPending();
  TestFinalNativeDenialDoesNotQueue();
  TestNativeQueueRejectionIsNotAcknowledged();
  TestDisabledDefaultDoesNotInvokeNativeEntries();
  std::cout << "realm-law-enact-12002 command fixtures: GREEN (4)\n";
  return 0;
}
