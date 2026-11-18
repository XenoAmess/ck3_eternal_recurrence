#pragma once
#include "xar_bridge/ck3_1210_personal_gold_v1.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_actor_foundation_v1.hpp"
namespace xar::ck3_1210 {
inline constexpr char kPersonalGoldCapabilityV1[]="game.query.personal-gold-frame.v1";
inline constexpr char kPersonalGoldStepV1[]="query-personal-gold-frame-v1";
inline constexpr char kActorFoundationFrameSchemaV1[]="ck3_1210_actor_foundation_frame_v1";
inline constexpr char kActorFoundationCapabilityV1[]="game.query.actor-foundation-frame.v1";
inline constexpr char kActorFoundationStepV1[]="query-actor-foundation-frame-v1";
struct PersonalCashMailboxContextV1;
enum class ActorObservationKindV1 {personal_gold,foundation,personal_cash};
// Both operations use one fixed paused-only actor reader; kind is chosen by
// the native step router, never by a caller-supplied memory address.
struct PersonalGoldMailboxContextV1 {
  ActorObservationKindV1 kind=ActorObservationKindV1::personal_gold;
  ActorFoundationObservationV1 foundation{};
  PersonalCashMailboxContextV1 *cash=nullptr;
  const game::GameAdapter *game=nullptr;
  PersonalGoldBindingsV1 bindings{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  PersonalGoldObservationV1 observation{};
  bool application_main_observed=false;
};
bool ExecutePersonalGoldMailboxV1(void *,const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeActorFoundationCommandResultV1(std::string_view request_id,
    const PersonalGoldMailboxContextV1 &);
std::string SerializePersonalGoldCommandResultV1(std::string_view request_id,
    const PersonalGoldMailboxContextV1 &);
}
