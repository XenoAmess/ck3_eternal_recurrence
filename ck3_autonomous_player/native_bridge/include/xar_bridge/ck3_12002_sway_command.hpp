#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_diplomacy.hpp"
#include "xar_bridge/active_scheme_semantic_action_v1_private.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kSwayDefinitionPrimaryVtableRva = 0x48C2218;
inline constexpr std::uintptr_t kSwayDefinitionSecondaryVtableRva = 0x48C2228;
inline constexpr std::size_t kSwayDefinitionSecondaryOffset = 0x2750;
inline constexpr std::size_t kSwayDatabaseRowsOffset = 0x50;
inline constexpr std::size_t kSwayDatabaseCountOffset = 0x5C;
inline constexpr std::uintptr_t kSwayShownRva = 0x30796B0;
inline constexpr std::uintptr_t kSwayValidityRva = 0x307AB70;

using SwayReadShownV1 = bool (*)(void *context);
using SwayReadValidityV1 = bool (*)(void *context, bool, bool, void *diagnostics);

struct SwayCommandBindingsV1 {
  bool enabled = false;
  ContextBindings context{};
  ConstructInteractionContext construct_two_roles = nullptr;
  SwayReadShownV1 shown = nullptr;
  SwayReadValidityV1 valid = nullptr;
  std::uintptr_t definition_primary_vtable = 0;
  std::uintptr_t definition_secondary_vtable = 0;
};

struct SwayCommandTermsV1 {
  bridge::ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
  bool final_legality_sampled = false;
  bool complete_can_send = false;
  std::array<std::int64_t, 10> send_costs_raw{};
};

enum class SwayCommandSubmitResultV1 { unavailable, rejected, submitted };

// Pure exact-build address binding. Owning mailbox supplies application-main
// thread confinement and its frame epoch; no process/pipe is discovered here.
SwayCommandBindingsV1 BindSwayCommandImage(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
bool ReadSwayCommandTermsV1(const SwayCommandBindingsV1 &,
    std::int64_t actor_character_id, std::int64_t target_character_id,
    std::uint64_t capture_epoch, SwayCommandTermsV1 &) noexcept;
SwayCommandSubmitResultV1 SubmitSwayCommandV1(const SwayCommandBindingsV1 &,
    const bridge::ActiveSchemeSemanticActionV1PrivateCommand &) noexcept;

} // namespace xar::ck3_12002
