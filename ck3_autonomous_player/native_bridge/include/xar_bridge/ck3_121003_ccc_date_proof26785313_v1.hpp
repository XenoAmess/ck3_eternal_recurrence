#pragma once
// Closed internal CCC spec. Never a caller family/actor/allow-change parameter.
#include "xar_bridge/ck3_121003_ted_date_proof26785313_v1.hpp"
namespace xar::ck3_1210 {
using CccFixedDayStage267V1=TedFixedDayStage267V1;
using CccFixedDayProof267V1=TedFixedDayProof267V1;
ck3_11906::TacticalDailySentinelArmStatusV1 ArmCccFixedDay267V1(DateSentinelStateV1&,const ck3_11906::TacticalDailySentinelArmRequestV1&,std::uint64_t,CccFixedDayStage267V1)noexcept;
bool ReadCccFixedDayProof267V1(const DateSentinelStateV1&,std::uint64_t,CccFixedDayProof267V1&,ck3_11906::TacticalDailySentinelStatusV1&)noexcept;
bool ReadCccDeferredActorOnOwner267V1(DateSentinelStateV1&,const CccFixedDayProof267V1&,const ck3_11906::MainThreadExecutionStampV1&,DateSentinelObservationV1&,bool*busy=nullptr)noexcept;
}
