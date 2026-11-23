#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_decision26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
bool ExecuteCccOnOwner267V1([[maybe_unused]]void*opaque,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&stamp)noexcept{
#if (defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1)
 if(!opaque)return false;
 __try{auto&entry=*static_cast<CccOwnerInvocation267V1*>(opaque);if(entry.magic!=0x4343433236375631ULL||!entry.context)return false;
  switch(entry.kind){
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
  case CccInvocationKind267V1::transition:{auto&q=*static_cast<CccTransitionContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteCccTransitionOnOwner267V1(&q,stamp);}
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1
  case CccInvocationKind267V1::event:{auto&q=*static_cast<CccEventContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteCccEventOnOwner267V1(&q,stamp);}
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1
  case CccInvocationKind267V1::decision:{auto&q=*static_cast<CccDecisionContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteCccDecisionOnOwner267V1(&q,stamp);}
#endif
  default:return false;
  }
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 return false;
#endif
}
}
