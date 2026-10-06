#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ordinary_holy_war_cb_cost_v1.hpp"

namespace xar::ck3_12002 {
inline constexpr std::string_view kOrdinaryHolyWarDeclarationContextPrivateStep12003 =
    "query-player-ordinary-holy-war-declaration-context-v1";
inline constexpr std::string_view kOrdinaryHolyWarDeclarationContextDomainKey12003 =
    "player_ordinary_holy_war_declaration_context_v1";
inline constexpr std::string_view kOrdinaryHolyWarDeclarationContextBackend12003 =
    "ck3-1.20.0.3-native-player-ordinary-holy-war-declaration-context-v1";
struct OrdinaryHolyWarDeclarationContextRequest12003 {
  std::uint64_t expected_revision = 0, expected_public_revision = 0;
  std::string declaration_id;
  game::DeclarableWarSnapshot selected;
};
struct OrdinaryHolyWarDeclarationContextMailbox12003 {
  QueryMailboxEnvelope envelope{};
  OrdinaryHolyWarDeclarationContextRequest12003 request{};
  DeclarationsBindings declarations{};
  OrdinaryHolyWarCbCostBindingsV1 cost{};
  OrdinaryHolyWarDeclarationContextV1 observation{};
  bool completed = false;
  std::string failure;
};
bool IsOrdinaryHolyWarDeclarationContextPrivateStep12003(std::string_view) noexcept;
bool ParseOrdinaryHolyWarDeclarationContextRequest12003(std::string_view,
    OrdinaryHolyWarDeclarationContextRequest12003 &) noexcept;
bool ExecuteOrdinaryHolyWarDeclarationContextMailbox12003(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeOrdinaryHolyWarDeclarationContextResult12003(
    const OrdinaryHolyWarDeclarationContextMailbox12003 &, std::string_view request_id);
bool RunOrdinaryHolyWarDeclarationContextMailbox12003(OrdinaryHolyWarDeclarationContextMailbox12003 &,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;
bool HandleOrdinaryHolyWarDeclarationContextPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
} // namespace xar::ck3_12002
