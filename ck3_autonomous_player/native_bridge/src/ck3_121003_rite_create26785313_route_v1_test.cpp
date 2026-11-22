#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/ck3_121003_rite_create26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"
#include <algorithm>
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
using namespace xar::ck3_121003::build26785313;
struct SyntheticGame{const xar::game::AdapterDescriptor&descriptor()const noexcept{static const xar::game::AdapterDescriptor d{kAdapterId,kGameVersion,kExecutableSha256,"",{}};return d;}};
static int calls=0;static bool parsed=false,called_after_parse=false;static std::string observed;
namespace xar::ck3_121003::build26785313 {std::string DispatchRiteCreateRequest267V1(const SyntheticGame&,std::uint64_t,std::string_view,std::string_view step,std::string_view,int){++calls;called_after_parse=parsed;observed=step;return "SYNTHETIC_ROUTE_OBSERVER_ONLY_NO_NATIVE_BODY";}}
static bool write_frame(int,const std::string&){return true;}
static std::string CommandResultFrame(std::string_view,std::string_view,bool,std::string_view){return "SYNTHETIC_ROUTE_REFUSAL";}
static void trace_command_entry(std::string_view value){if(value=="step_parse_returned")parsed=true;}
static bool exercise(std::string payload){calls=0;parsed=false;called_after_parse=false;observed.clear();std::string step;SyntheticGame game;int pipe=0,g_main_thread_query_mailbox_v1=0;bool connected=true;std::string request_id="des-fixed-guard-route";struct{std::string payload;}incoming{std::move(payload)};struct{std::uint64_t connection_generation=1;}state;
        bool early_step_dispatched = false;
        if (!xar::bridge::JsonStringField(
                incoming.payload, "step", step,
                xar::ck3_11906::kTacticalDailySentinelMaximumArmStepBytesV1)) {
          connected = write_frame(
              pipe, CommandResultFrame(request_id, "", false,
                                       "native gameplay step is missing"));
          early_step_dispatched = true;
        }
        trace_command_entry("step_parse_returned");
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
        if(!early_step_dispatched&&step==xar::ck3_121003::build26785313::kRiteCreateStep267V1&&xar::game::IsCk3_121003Core26785313Descriptor(game.descriptor())){connected=write_frame(pipe,xar::ck3_121003::build26785313::DispatchRiteCreateRequest267V1(game,state.connection_generation,request_id,step,incoming.payload,g_main_thread_query_mailbox_v1));early_step_dispatched=true;}
#endif
 (void)connected;(void)early_step_dispatched;return calls==1&&called_after_parse;
}
int main(){for(const auto step:std::array<std::string_view,1>{kRiteCreateStep267V1}){const auto payload=std::string("{\"step\":\"")+std::string(step)+"\"}";assert(exercise(payload)&&observed==step);}assert(!exercise("{}")&&calls==0);assert(!exercise("{\"step\":7}")&&calls==0);assert(!exercise("{\"step\":\"unrelated-native-step\"}")&&calls==0);std::cout<<"PASS exact Bridge fragment and actual JsonStringField, one fixed decoded step/3zero-dispatch negatives; observer only, no Native effects\n";}
