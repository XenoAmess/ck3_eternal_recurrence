#pragma once

#include "xar_bridge/actor_cached_succession12004_v1.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

inline constexpr std::string_view kActorCachedSuccessionPrivateStepV1 =
    "query-actor-cached-succession-v1";
inline constexpr std::string_view kActorCachedSuccessionCapabilityV1 =
    "game.command.query-actor-cached-succession-v1";
inline constexpr std::string_view kActorCachedSuccessionDomainKeyV1 =
    "actor_cached_succession_v1";
inline constexpr std::string_view kActorCachedSuccessionBackendV1 =
    "ck3-1.20.0.4-native-actor-cached-succession-v1";

struct ActorCachedSuccessionMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  CoreBindings core{};
  actor_cached_succession::Bindings bindings{};
  actor_cached_succession::Snapshot observation{};
  bool completed = false;
  std::string failure;
};

bool IsActorCachedSuccessionPrivateStepV1(std::string_view) noexcept;
bool ParseActorCachedSuccessionRevisionV1(std::string_view,
                                         std::uint64_t &) noexcept;
bool ExecuteActorCachedSuccessionMailboxV1(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeActorCachedSuccessionResultV1(
    const ActorCachedSuccessionMailboxContextV1 &, std::string_view);
bool RunActorCachedSuccessionMailboxV1(ActorCachedSuccessionMailboxContextV1 &,
    std::string_view, std::string &, std::string &) noexcept;
bool HandleActorCachedSuccessionPrivateV1(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &,
    std::uint64_t, std::string_view, std::string_view, std::string_view,
    std::string &, std::string &) noexcept;

} // namespace xar::ck3_12004
