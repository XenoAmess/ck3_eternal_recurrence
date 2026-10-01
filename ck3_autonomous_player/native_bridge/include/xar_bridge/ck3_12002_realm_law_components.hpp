#pragma once

#include "xar_bridge/realm_law_governance_snapshot_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002::private_law {

inline constexpr std::uintptr_t kRealmLawConstructActorScopeRva = 0xB17C70;
inline constexpr std::uintptr_t kRealmLawEvaluateCompiledTriggerRva = 0x372DF30;
inline constexpr std::size_t kRealmLawCanPassOffset = 0x3A0;
inline constexpr std::size_t kRealmLawCanHaveOffset = 0x540;
inline constexpr std::size_t kRealmLawCanKeepOffset = 0x610;
inline constexpr std::size_t kRealmLawSuccessionPolicyOffset = 0xBD8;
inline constexpr std::size_t kRealmLawActorScopeSize = 0x168;

struct RealmLawComponentBindings12002 {
  bool enabled = false;
  void *(*construct_actor_scope)(void *, const void *) = nullptr;
  bool (*evaluate_trigger)(const void *, const void *) = nullptr;
  void (*destroy_scope_tail)(void *) = nullptr;
  void (*destroy_scope_rows)(void *) = nullptr;
};

struct RealmLawComponents12002 {
  bool complete = false;
  bool can_have = false;
  bool can_pass = false;
  bool can_keep = false;
};

RealmLawComponentBindings12002 BindRealmLawComponentsImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// One synchronous paused-frame lease, using three independent native
// compiled trigger evaluations. No result is inferred from CanEnact.
RealmLawComponents12002 ReadRealmLawComponents12002(
    const void *law, const void *actor,
    const RealmLawComponentBindings12002 &bindings) noexcept;

// Value-only extraction of the reviewed native enum selectors and effective
// minimum share. Unset selectors are represented as absent, not failed reads.
bool ReadRealmLawSuccessionShape12002(
    const void *law, bridge::RealmLawGovernanceSuccessionShapeV1 &output) noexcept;

} // namespace xar::ck3_12002::private_law
