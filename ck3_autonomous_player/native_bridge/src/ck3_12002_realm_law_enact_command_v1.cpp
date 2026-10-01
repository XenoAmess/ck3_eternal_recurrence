#include "xar_bridge/ck3_12002_realm_law_enact_command_v1.hpp"

#include <cstring>
#include <type_traits>

namespace xar::ck3_12002::private_law {
namespace {

template <typename Value>
void Store(AddLawCommandV1 &command, std::size_t offset, Value value) noexcept {
  static_assert(std::is_trivially_copyable_v<Value>);
  std::memcpy(command.bytes.data() + offset, &value, sizeof(value));
}

#if defined(_MSC_VER)
using ValidateNative = bool(__fastcall *)(void *, void *);
using CloneNative = void **(__fastcall *)(void *, void **);
using QueueNative = bool(__fastcall *)(void *, void **, std::uint32_t,
                                       void *, void **);
using DestroyNative = void *(__fastcall *)(void *, std::uint32_t);
#else
using ValidateNative = bool (*)(void *, void *);
using CloneNative = void **(*)(void *, void **);
using QueueNative = bool (*)(void *, void **, std::uint32_t, void *, void **);
using DestroyNative = void *(*)(void *, std::uint32_t);
#endif

bool CompleteOfflineCalls(const AddLawCommandOfflineCallsV1 &calls) noexcept {
  return calls.validate != nullptr && calls.clone != nullptr &&
      calls.queue != nullptr && calls.destroy != nullptr;
}

} // namespace

static_assert(sizeof(AddLawCommandV1) == kAddLawCommandSizeV1);

AddLawCommandV1 BuildAddLawCommandV1(std::uintptr_t module_base,
                                    std::int32_t actor_character_id,
                                    std::uintptr_t law_address) noexcept {
  AddLawCommandV1 command{};
  Store(command, 0x00, module_base + kAddLawCommandPrimaryVtableRvaV1);
  Store(command, 0x18, module_base + kAddLawCommandSecondaryVtableRvaV1);
  Store(command, 0x20, actor_character_id);
  Store(command, 0x28, law_address);
  return command;
}

AddLawCommandSubmitResultV1 SubmitAddLawCommandV1(
    const AddLawCommandAccessV1 &access,
    const bridge::RealmLawEnactSubmissionV1 &submission,
    const bridge::RealmLawNativeEnactTargetLeaseV1 &target) noexcept {
  AddLawCommandSubmitResultV1 result{};
  if (!access.submit_enabled) return result;
  const auto &proof = access.mutation_abi_proof;
  if (access.module_base == 0 || !proof.verified ||
      proof.build != kRealmLawEnactMutationBuildV1 ||
      proof.executable_sha256 != kRealmLawEnactMutationExeSha256V1 ||
      (access.offline_calls != nullptr &&
       !CompleteOfflineCalls(*access.offline_calls))) {
    result.failure = AddLawCommandFailureV1::abi_unavailable;
    return result;
  }
  if (!target.actor_identity_round_trip || target.actor_address == 0 ||
      target.actor_character_id != submission.player_character_id ||
      submission.player_character_id == -1 ||
      !target.law_identity_round_trip || target.law_address == 0 ||
      target.law_key != submission.requested_law_key ||
      target.group_key != submission.group_key ||
      target.proof_epoch != submission.proof_epoch) {
    result.failure = AddLawCommandFailureV1::target_unavailable;
    return result;
  }
  auto command = BuildAddLawCommandV1(access.module_base,
                                     target.actor_character_id,
                                     target.law_address);
  result.final_legality_called = true;
  const bool legal = access.offline_calls != nullptr
      ? access.offline_calls->validate(access.offline_calls->context, command)
      : reinterpret_cast<ValidateNative>(access.module_base +
            kAddLawCommandValidatorRvaV1)(command.bytes.data(), nullptr);
  if (!legal) {
    result.failure = AddLawCommandFailureV1::final_legality_denied;
    return result;
  }
  void *owned_command = nullptr;
  if (access.offline_calls != nullptr) {
    if (!access.offline_calls->clone(access.offline_calls->context, command,
                                     owned_command) || owned_command == nullptr) {
      result.failure = AddLawCommandFailureV1::clone_failed;
      return result;
    }
  } else {
    reinterpret_cast<CloneNative>(access.module_base +
        kAddLawCommandCloneRvaV1)(command.bytes.data(), &owned_command);
    if (owned_command == nullptr) {
      result.failure = AddLawCommandFailureV1::clone_failed;
      return result;
    }
  }
  result.native_queue_called = true;
  const auto manager = access.module_base + kCommandManagerRvaV1;
  bool queued = false;
  if (access.offline_calls != nullptr) {
    queued = access.offline_calls->queue(access.offline_calls->context,
        manager, owned_command, kAddLawCommandSubmitFlagsV1);
    if (owned_command != nullptr) {
      access.offline_calls->destroy(access.offline_calls->context,
                                    owned_command);
    }
  } else {
    void *unused_result = nullptr;
    queued = reinterpret_cast<QueueNative>(access.module_base +
        kRealmLawLockedQueueRvaV1)(reinterpret_cast<void *>(manager),
          &owned_command, kAddLawCommandSubmitFlagsV1, nullptr, &unused_result);
    const auto destroy = reinterpret_cast<DestroyNative>(
        access.module_base + kAddLawCommandDestructorRvaV1);
    if (owned_command != nullptr) destroy(owned_command, 1);
    if (unused_result != nullptr) destroy(unused_result, 1);
  }
  if (!queued) {
    result.failure = AddLawCommandFailureV1::queue_rejected;
    return result;
  }
  result.disposition = bridge::RealmLawNativeSubmitDispositionV1::submitted;
  result.failure = AddLawCommandFailureV1::none;
  return result;
}

const char *AddLawCommandFailureNameV1(AddLawCommandFailureV1 failure) noexcept {
  switch (failure) {
  case AddLawCommandFailureV1::none: return "none";
  case AddLawCommandFailureV1::submit_disabled: return "submit_disabled";
  case AddLawCommandFailureV1::abi_unavailable: return "abi_unavailable";
  case AddLawCommandFailureV1::target_unavailable: return "target_unavailable";
  case AddLawCommandFailureV1::final_legality_denied:
    return "final_legality_denied";
  case AddLawCommandFailureV1::clone_failed: return "clone_failed";
  case AddLawCommandFailureV1::queue_rejected: return "queue_rejected";
  }
  return "unknown";
}

} // namespace xar::ck3_12002::private_law
