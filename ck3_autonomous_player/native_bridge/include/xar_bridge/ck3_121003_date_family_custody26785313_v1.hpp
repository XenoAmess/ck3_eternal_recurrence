#pragma once
#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Internal actual retained-session coordinator. No caller/public admission flags.
bool TedDatePredecessorResolved267V1(const ck3_1210::DateSentinelStateV1&)noexcept;
bool ClaimTedDateCustody267V1(const ck3_1210::DateSentinelStateV1&,bool recipient_continuation)noexcept;
void CompleteTedDateCustody267V1(const ck3_1210::DateSentinelStateV1&)noexcept;
void BlockTedDateCustodyUnknown267V1(const ck3_1210::DateSentinelStateV1&)noexcept;
}
