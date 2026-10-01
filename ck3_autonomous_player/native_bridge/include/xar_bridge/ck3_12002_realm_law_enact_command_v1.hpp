#pragma once

#include "xar_bridge/ck3_12002_realm_law_enact_mutation_abi_v1.hpp"
#include "xar_bridge/realm_law_native_shared_glue_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002::private_law {

inline constexpr std::size_t kAddLawCommandSizeV1 = 0x30;
inline constexpr std::uint32_t kAddLawCommandSubmitFlagsV1 = 0x0E;

struct alignas(std::uintptr_t) AddLawCommandV1 {
  std::array<unsigned char, kAddLawCommandSizeV1> bytes{};
};

// These typed overrides exercise the same clone/ownership/queue handoff in an
// offline fixture. A production adapter leaves this table null and invokes
// the verified native entries directly.
struct AddLawCommandOfflineCallsV1 {
  void *context = nullptr;
  bool (*validate)(void *, const AddLawCommandV1 &) noexcept = nullptr;
  bool (*clone)(void *, const AddLawCommandV1 &, void *&) noexcept = nullptr;
  bool (*queue)(void *, std::uintptr_t manager, void *&owned_command,
                std::uint32_t flags) noexcept = nullptr;
  void (*destroy)(void *, void *) noexcept = nullptr;
};

struct AddLawCommandAccessV1 {
  std::uintptr_t module_base = 0;
  RealmLawMutationAbiProofV1 mutation_abi_proof{};
  bool submit_enabled = false;
  const AddLawCommandOfflineCallsV1 *offline_calls = nullptr;
};

enum class AddLawCommandFailureV1 : std::uint8_t {
  none,
  submit_disabled,
  abi_unavailable,
  target_unavailable,
  final_legality_denied,
  clone_failed,
  queue_rejected,
};

struct AddLawCommandSubmitResultV1 {
  bridge::RealmLawNativeSubmitDispositionV1 disposition =
      bridge::RealmLawNativeSubmitDispositionV1::not_submitted;
  AddLawCommandFailureV1 failure = AddLawCommandFailureV1::submit_disabled;
  bool final_legality_called = false;
  bool native_queue_called = false;
};

AddLawCommandV1 BuildAddLawCommandV1(
    std::uintptr_t module_base, std::int32_t actor_character_id,
    std::uintptr_t law_address) noexcept;

// Called synchronously by the existing paused application-main LAW7/LAW8
// source operation after its frame and stable-key target recapture. No raw
// native pointer is retained in the returned result.
AddLawCommandSubmitResultV1 SubmitAddLawCommandV1(
    const AddLawCommandAccessV1 &access,
    const bridge::RealmLawEnactSubmissionV1 &submission,
    const bridge::RealmLawNativeEnactTargetLeaseV1 &target) noexcept;

const char *AddLawCommandFailureNameV1(AddLawCommandFailureV1 failure) noexcept;

} // namespace xar::ck3_12002::private_law
