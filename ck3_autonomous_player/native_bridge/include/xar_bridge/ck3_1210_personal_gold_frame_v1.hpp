#pragma once
#include "xar_bridge/ck3_1210_personal_gold_v1.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
namespace xar::ck3_1210 {
inline constexpr char kPersonalGoldCapabilityV1[]="game.query.personal-gold-frame.v1";
inline constexpr char kPersonalGoldStepV1[]="query-personal-gold-frame-v1";
struct PersonalGoldMailboxContextV1 {
  const game::GameAdapter *game=nullptr;
  PersonalGoldBindingsV1 bindings{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  PersonalGoldObservationV1 observation{};
  bool application_main_observed=false;
};
bool ExecutePersonalGoldMailboxV1(void *,const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePersonalGoldCommandResultV1(std::string_view request_id,
    const PersonalGoldMailboxContextV1 &);
}
