#pragma once
#include "xar_bridge/ck3_1210_actor_readonly_request_v1.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_personal_cash_v1.hpp"
namespace xar::ck3_1210 {
// New exact image only. No actor/address/source selector is wire input.
inline bool ParseHotfixPersonalCashRequestV2(std::string_view payload,std::string_view outer_id,
    ActorReadonlyRequestV1 &out) noexcept {
  ActorReadonlyRequestV1 parsed{};
  if(!ParseActorReadonlyRequestV1(payload,kPersonalCashStepV2,ActorReadonlyRevisionV1::positive,parsed) ||
      parsed.request_id!=outer_id)return false;
  out=std::move(parsed);return true;
}
} // namespace xar::ck3_1210
