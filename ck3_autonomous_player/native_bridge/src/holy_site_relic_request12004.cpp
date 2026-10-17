#include "xar_bridge/holy_site_relic_request12004.hpp"
#include "xar_bridge/protocol.hpp"
#include <array>

namespace xar::ck3_12004::religion::relic_actions {
namespace {
constexpr std::array<std::string_view,7>keys{"relic_artifact_id","relic_slot_index","relic_desired_selected",
 "relic_expected_effective_slot_index","relic_expected_replacing_empty","relic_expected_replacing_artifact_id","relic_expected_preview_sha256"};
bool Has(std::string_view json,std::string_view key){return json.find('"'+std::string(key)+'"')!=std::string_view::npos;}
bool UInt(std::string_view json,std::string_view key,std::uint32_t&out){
 std::uint64_t value=0;if(!bridge::JsonUnsignedField(json,key,value)||value>=absent)return false;
 out=static_cast<std::uint32_t>(value);return true;
}
}
bool HasRelicRequestFields12004(std::string_view json) noexcept {
 try{for(const auto key:keys)if(Has(json,key))return true;return false;}catch(...){return true;}
}
bool ParseRelicRequest12004(std::string_view json,std::uint32_t operation,std::uint32_t site,Request&out) noexcept {
 out={};try{
  if(!IsOperation(operation))return false;
  out.operation=static_cast<Operation>(operation);out.holy_site_id=site;
  const bool slot=out.operation==Operation::set_slot,select=out.operation==Operation::select_artifact;
  if(slot){
   std::uint32_t index=0;bool desired=false;
   if(!UInt(json,keys[1],index)||!bridge::JsonBooleanField(json,keys[2],desired))return false;
   out.slot_index=index;out.desired_selected=desired;
   for(std::size_t i=0;i<keys.size();++i)if(i!=1&&i!=2&&Has(json,keys[i]))return false;
  }else{
   if(!UInt(json,keys[0],out.artifact_id)||Has(json,keys[1])||Has(json,keys[2]))return false;
   if(select){for(std::size_t i=3;i<keys.size();++i)if(Has(json,keys[i]))return false;}
   else{
    bool empty=false;
    if(!bridge::JsonBooleanField(json,keys[4],empty)||!bridge::JsonStringField(json,keys[6],out.expected_preview_identity_sha256,64))return false;
    if(empty){if(Has(json,keys[5]))return false;}
    else{std::uint32_t replacement=0;if(!UInt(json,keys[5],replacement))return false;out.expected_replacing_artifact_id=replacement;}
    if(out.operation==Operation::enshrine){std::uint32_t index=0;if(!UInt(json,keys[3],index))return false;out.expected_effective_slot_index=index;}
    else if(Has(json,keys[3])||!empty)return false;
    out.frozen_preconditions=true;
   }
  }
  return ValidateRequest(out);
 }catch(...){return false;}
}
}
