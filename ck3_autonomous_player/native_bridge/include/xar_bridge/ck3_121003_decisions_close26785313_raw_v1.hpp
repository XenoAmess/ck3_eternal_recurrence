#pragma once
#include "xar_bridge/ck3_121003_decisions_close26785313_v1.hpp"
#include "xar_bridge/ck3_121003_curated_decisions26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Pure DATA predicate is not authority: executor must retain/freshly reread the actual complete private source.
bool SameDecisionsCloseRawSource267V1(const CuratedDecisionRaw267V1&,const CuratedDecisionRaw267V1&)noexcept;
bool DecisionsCloseRawAdmissible267V1(const CuratedDecisionRaw267V1&)noexcept;
CuratedDecisionRawCall267V1 CloseDecisionsListRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CuratedDecisionScene267V1&,std::uint64_t monotonic_deadline,std::uint64_t wall_deadline,const CuratedDecisionRaw267V1&)noexcept;
}
