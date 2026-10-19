#pragma once

#include "xar_bridge/ck3_12004_family.hpp"

namespace xar::ck3_12004::player_heir_candidate_v1 {

// Exact source: player-heir-h12004-source-closure-2026-10-19.json.
// Original native signature is CCharacter const*(CCharacter const*), RCX/RAX.
// SPromote at SType+20, not the separate boxed SFunction route at +48.
inline constexpr std::uintptr_t kGetPlayerHeirRva = 0x289DCC0;
using GetPlayerHeir = const void *(*)(const void *character);
using OnApplicationMain = bool (*)(void *context) noexcept;

struct Bindings {
  bool enabled = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  CoreBindings core{};
  ck3_12002::family_value::Bindings family{};
  GetPlayerHeir get_player_heir = nullptr;
  OnApplicationMain on_application_main = nullptr;
  void *thread_context = nullptr;
};

// Pure address calculation, default disabled. No CMake/adapter/mailbox route
// enables this new leaf. An explicit independent build opt-in is required:
// XAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1. This does not establish live
// qualification or authorization to deploy to any existing runtime.
Bindings BindImage(std::uintptr_t module_base,
                   std::string_view executable_sha256,
                   OnApplicationMain on_application_main,
                   void *thread_context = nullptr) noexcept;

struct Observation {
  // Complete coherent getter observation; NOT continuation legality or k1.
  // available + !candidate_present is observed null, never a full-pool proof.
  bool available = false;
  std::string_view unavailable_reason = "player_heir_not_read";
  bool source_fixture = false;
  bool original_getter_source_bound = false;
  CoreSnapshotPrefix before{};
  CoreSnapshotPrefix after{};
  bool getter_observed = false;
  bool candidate_present = false;
  std::int32_t actor_character_id = -1;
  std::int32_t candidate_character_id = -1;
  bool candidate_alive = false;
  bool identity_and_frame_stable = false;
  bool lineage_available = false;
  ck3_12002::family_value::Lineage candidate_lineage{};
  std::string_view lineage_unavailable_reason{};
};

// Owning application thread, paused current local living actor only. Calls the
// original getter ONCE, then copies full generation-checked identity/liveness
// and family lineage with frame, root-pointer and field bookends. Temporary
// native allocation is internal to the original getter; no gameplay command.
// SDK episode/revision/source epoch must be bound by the caller of the future
// query. This native core prefix cannot manufacture those outer identities.
// No candidate pointer escapes, no D0 comparison, no backup enumeration.
Observation Read(const Bindings &bindings) noexcept;

} // namespace xar::ck3_12004::player_heir_candidate_v1
