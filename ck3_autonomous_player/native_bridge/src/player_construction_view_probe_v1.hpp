#pragma once

#include "domain_construction_candidate_identity_decoder_v1.hpp"
#include "xar_bridge/ck3_12004_construction_held.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3::shared {

// Private, read-only paused query. A populated view cache is evidence that a
// later item decoder can run; an empty cache is not an empty domain.
enum class PlayerConstructionViewProbeStatusV1 : std::uint8_t {
  unavailable = 0,
  view_candidate_cache_empty,
  view_candidate_cache_present,
};

enum class PlayerConstructionViewProbeFailureV1 : std::uint8_t {
  none = 0,
  exact_build,
  application_main,
  session,
  owner_path,
  view_missing,
  view_identity,
  candidate_span,
  source_read,
  frame_changed,
};

enum class PlayerConstructionHoldingViewVisibilityV1 : std::uint8_t {
  unavailable = 0,
  hidden,
  visible,
};

struct PlayerConstructionViewResolvedOwnerV1 final {
  std::uintptr_t root = 0U;
  std::uintptr_t idler_base = 0U;
  std::uintptr_t idler_gfx = 0U;
  std::uintptr_t handler = 0U;
  bool exact_idler_rtti_cast = false;
};

using ResolvePlayerConstructionViewOwnerV1 = bool (*)(
    void* context, std::uintptr_t module_base,
    PlayerConstructionViewResolvedOwnerV1& owner) noexcept;
using ReadPlayerConstructionHoldingViewVisibilityV1 = bool (*)(
    void* context, std::uintptr_t module_base,
    bool& effective_visible) noexcept;

struct PlayerConstructionViewProbeAdmissionV1 final {
  bool exact_build_admitted = false;
  bool application_main_thread = false;
  bool session_live = false;
  std::uintptr_t module_base = 0U;
};

struct PlayerConstructionViewProbeSourceV1 final {
  ResolvePlayerConstructionViewOwnerV1 resolve_owner = nullptr;
  void* owner_context = nullptr;
  research::DomainConstructionReadMemoryV1 read_memory = nullptr;
  void* read_context = nullptr;
  ReadPlayerConstructionHoldingViewVisibilityV1 read_holding_view_visibility =
      nullptr;
  void* visibility_context = nullptr;
};

struct PlayerConstructionViewProbeResultV1 final {
  PlayerConstructionViewProbeStatusV1 status =
      PlayerConstructionViewProbeStatusV1::unavailable;
  PlayerConstructionViewProbeFailureV1 failure =
      PlayerConstructionViewProbeFailureV1::none;
  bool view_present = false;
  std::int32_t candidate_capacity = 0;
  std::int32_t cached_candidate_count = 0;
  PlayerConstructionHoldingViewVisibilityV1 holding_view_visibility =
      PlayerConstructionHoldingViewVisibilityV1::unavailable;
  // Separate owned current12004 inputs. The attach helper clears every
  // borrowed pointer before this private query survives its callback.
  std::optional<ck3_12004::PlayerHeldConstructionMode3InputResultV1>
      native_mode3_inputs;
};

// The existing world receipt supplies the independent frame association.
// A mode3 failure remains local and never changes the old world/scalar result.
[[nodiscard]] bool AttachPlayerConstructionNativeMode3InputsV1(
    PlayerConstructionViewProbeResultV1& target,
    const ck3_12004::PlayerWorldBuildingSourceResultV1& world,
    ck3_12004::PlayerHeldConstructionMode3InputResultV1 inputs) noexcept;

// CK3 1.19.0.6; EXE SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// Reuses the LIFE3 portable root/idler/handler owner path, then freshly reads
// handler+0xD0 CHoldingView and its +0x118/+0x120/+0x124 model span.
[[nodiscard]] PlayerConstructionViewProbeResultV1
ProbePlayerConstructionViewCacheV1(
    const PlayerConstructionViewProbeAdmissionV1& admission,
    const PlayerConstructionViewProbeSourceV1& source) noexcept;

}  // namespace xar::ck3::shared
