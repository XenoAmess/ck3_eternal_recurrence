#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_decision26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_observation26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
bool ExecuteRmtmOnOwner267V1([[maybe_unused]]void*opaque,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&stamp)noexcept{
#if (defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1)
 if(!opaque)return false;
 __try{auto&entry=*static_cast<RmtmOwnerInvocation267V1*>(opaque);if(entry.magic!=0x524D544D32363731ULL||!entry.context)return false;
  switch(entry.kind){
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1
  case RmtmInvocationKind267V1::transition:{auto&q=*static_cast<RmtmTransitionContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteRmtmTransitionOnOwner267V1(&q,stamp);}
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1
  case RmtmInvocationKind267V1::event:{auto&q=*static_cast<RmtmEventContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteRmtmEventOnOwner267V1(&q,stamp);}
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1
  case RmtmInvocationKind267V1::decision:{auto&q=*static_cast<RmtmDecisionContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteRmtmDecisionOnOwner267V1(&q,stamp);}
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1
  case RmtmInvocationKind267V1::observation:{auto&q=*static_cast<RmtmObservationContext267V1*>(entry.context);if(&q.invocation!=&entry)return false;return ExecuteRmtmObservationOnOwner267V1(&q,stamp);}
#endif
  default:return false;
  }
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 return false;
#endif
}
}
