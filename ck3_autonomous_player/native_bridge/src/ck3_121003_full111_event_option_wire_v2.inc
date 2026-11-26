namespace {
using EventOptionAction = Full111EventOptionAction267V2;
constexpr std::array<std::string_view, 3> kEventOptionActions{"prepare", "select", "query_queue"};

bool NullableId(Cursor &cursor, std::optional<std::string> &out) {
 cursor.Space();
 if (cursor.text.substr(cursor.pos, 4)=="null") { cursor.pos+=4; return true; }
 std::string_view value;
 if (!cursor.String(value)||!Id(value)) return false;
 out=std::string(value);return true;
}

bool EventOptionShape(const Full111EventOptionRequest267V2 &request) noexcept {
 const auto &target=request.target;
 const auto &lineage=request.lineage;
 if (!Id(request.request_id)||!request.deadline_unix_ms||!Prefix(request.expected)||
     target.instance_id<=0||target.recipient_character_id!=request.expected.played_character_id||
     target.authored_option_index<0||target.authored_option_index>=64||!KeyText(target.definition_key)||
     !lineage.source_revision||!lineage.renderer_provider_generation||!lineage.renderer_query_sequence||
     !Id(lineage.renderer_request_id)||lineage.renderer_request_id==request.request_id||
     (lineage.prepare_request_id && (*lineage.prepare_request_id==request.request_id ||
         *lineage.prepare_request_id==lineage.renderer_request_id)) ||
     (lineage.effect_request_id && (*lineage.effect_request_id==request.request_id ||
         *lineage.effect_request_id==lineage.renderer_request_id || lineage.effect_request_id==lineage.prepare_request_id))) return false;
 if (request.action==EventOptionAction::prepare)
  return !request.expected_revision && !lineage.prepare_request_id && !lineage.lease_sequence &&
      !lineage.effect_request_id && !lineage.claim_sequence;
 if (request.action==EventOptionAction::select)
  return request.expected_revision==lineage.source_revision && lineage.prepare_request_id && lineage.lease_sequence &&
      !lineage.effect_request_id && !lineage.claim_sequence;
 return request.action==EventOptionAction::query_queue && !request.expected_revision &&
     lineage.prepare_request_id && lineage.lease_sequence && lineage.effect_request_id &&
     lineage.claim_sequence>lineage.lease_sequence;
}

bool ParseEventOptionClaim(Cursor &cursor, Full111EventOptionRequest267V2 &request) {
 if (!cursor.Take('{')) return false;
 auto &target=request.target;
 auto &lineage=request.lineage;
 unsigned seen=0;
 bool first=true;
 while (!cursor.Take('}')) {
  if (!first&&!cursor.Take(',')) return false;
  first=false;
  std::string_view key, value;
  if (!cursor.String(key)||!cursor.Take(':')) return false;
  unsigned bit=0;
  bool good=false;
  if (key=="schema") { bit=1U<<0; good=cursor.Identity(kFull111EventOptionRequestSchema267V2); }
  else if (key=="game_version") { bit=1U<<1; good=cursor.Identity(kGameVersion); }
  else if (key=="executable_sha256") { bit=1U<<2; good=cursor.Identity(kExecutableSha256,true); }
  else if (key=="adapter_id") { bit=1U<<3; good=cursor.Identity(full111::kAdapterId); }
  else if (key=="backend") { bit=1U<<4; good=cursor.Identity(kLydBackend267V1); }
  else if (key=="action") { bit=1U<<5; good=EnumText(cursor,kEventOptionActions,request.action); }
  else if (key=="expected_core") { bit=1U<<6; good=Core(cursor,request.expected); }
  else if (key=="instance_id") { bit=1U<<7; good=cursor.Number(target.instance_id); }
  else if (key=="recipient_character_id") { bit=1U<<8; good=cursor.Number(target.recipient_character_id); }
  else if (key=="definition_key") { bit=1U<<9; good=cursor.String(value); if(good) target.definition_key.assign(value); }
  else if (key=="authored_option_index") { bit=1U<<10; good=cursor.Number(target.authored_option_index); }
  else if (key=="source_revision") { bit=1U<<11; good=UIntText(cursor,lineage.source_revision); }
  else if (key=="renderer_request_id") { bit=1U<<12; good=cursor.String(value); if(good) lineage.renderer_request_id.assign(value); }
  else if (key=="renderer_provider_generation") { bit=1U<<13; good=UIntText(cursor,lineage.renderer_provider_generation); }
  else if (key=="renderer_query_sequence") { bit=1U<<14; good=UIntText(cursor,lineage.renderer_query_sequence); }
  else if (key=="prepare_request_id") { bit=1U<<15; good=NullableId(cursor,lineage.prepare_request_id); }
  else if (key=="lease_sequence") { bit=1U<<16; good=UIntText(cursor,lineage.lease_sequence); }
  else if (key=="effect_request_id") { bit=1U<<17; good=NullableId(cursor,lineage.effect_request_id); }
  else if (key=="claim_sequence") { bit=1U<<18; good=UIntText(cursor,lineage.claim_sequence); }
  if (!bit||!good||(seen&bit)) return false;
  seen|=bit;
 }
 return seen==(1U<<19)-1;
}

bool QueueShape(const Full111EventQueue267V2 &queue, std::int32_t target) noexcept {
 if (queue.instance_ids.size()>32) return false;
 bool found=false;
 for (std::size_t i=0;i<queue.instance_ids.size();++i) {
  const auto id=queue.instance_ids[i];
  if (id<=0||std::find(queue.instance_ids.begin(),queue.instance_ids.begin()+i,id)!=queue.instance_ids.begin()+i) return false;
  found=found||id==target;
 }
 return found==queue.target_present;
}
}

bool ParseFull111EventOptionRequest267V2(std::string_view text, Full111EventOptionRequest267V2 &out) noexcept {
 out={};
 try {
  if (text.size()>16384) return false;
  Cursor cursor{text};
  Full111EventOptionRequest267V2 request;
  std::string_view step;
  unsigned seen=0;
  bool first=true;
  if (!cursor.Take('{')) return false;
  while (!cursor.Take('}')) {
   if (!first&&!cursor.Take(',')) return false;
   first=false;
   std::string_view key, value;
   if (!cursor.String(key)||!cursor.Take(':')) return false;
   unsigned bit=0;
   bool good=false;
   std::uint64_t version=0;
   if (key=="type") { bit=1; good=cursor.Identity("execute_step"); }
   else if (key=="protocol_version") { bit=2; good=cursor.Number(version)&&version==1; }
   else if (key=="request_id") { bit=4; good=cursor.String(value); if(good) request.request_id.assign(value); }
   else if (key=="step") { bit=8; good=cursor.String(step); }
   else if (key=="expected_revision") { bit=16; good=cursor.Number(request.expected_revision); }
   else if (key=="arguments") { bit=32; good=cursor.Take('{')&&cursor.Take('}'); }
   else if (key=="ordinary_event") { bit=64; good=ParseEventOptionClaim(cursor,request); }
   else if (key=="core_control_deadline_unix_ms") { bit=128; good=cursor.Number(request.deadline_unix_ms); }
   if (!bit||!good||(seen&bit)) return false;
   seen|=bit;
  }
  cursor.Space();
  if (seen!=255||cursor.pos!=text.size()||!EventOptionShape(request)||
      step!=kFull111EventOptionSteps267V2[static_cast<std::size_t>(request.action)]) return false;
  out=std::move(request);return true;
 } catch (...) { return false; }
}

std::string SerializeFull111EventOptionResult267V2(std::string_view id, EventOptionAction action,
    const LydResult267V1 &result, const Full111EventOptionResult267V2 &data) {
 using S=LydStatus267V1;
 const bool facts=result.facts_available&&Prefix(result.facts)&&result.connection_generation&&
     result.ticket_sequence&&result.pump_epoch&&result.thread_id;
 const bool selected=action==EventOptionAction::select;
 const bool queue=action==EventOptionAction::query_queue;
 const bool claim_qualified=data.lineage&&data.lineage->prepare_request_id&&data.lineage->lease_sequence&&
     ((selected||queue) ? data.lineage->effect_request_id&&data.lineage->claim_sequence>data.lineage->lease_sequence :
         data.lineage->prepare_request_id==id&&!data.lineage->effect_request_id&&!data.lineage->claim_sequence);
 const bool ok=facts&&result.cleanup_known&&result.source_available&&data.target&&claim_qualified&&
     data.target->recipient_character_id==result.facts.played_character_id&&
     result.effect_attempted==selected&&result.native_returned==selected&&
     (!selected||data.lineage->effect_request_id==id)&&
     (queue ? data.queue&&QueueShape(*data.queue,data.target->instance_id) : !data.queue)&&
     result.status==(selected?S::selection_dispatched:S::available);
 auto status=result.status;
 if (!ok) {
  if (!result.cleanup_known||result.effect_attempted) status=S::indeterminate;
  else if (status!=S::expired&&status!=S::stale_source&&status!=S::claim_consumed) status=S::unavailable;
 }
 Json j;
 j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";
 String(j.data,id);
 j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";
 String(j.data,kFull111EventOptionResultSchema267V2);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);
 j.str("backend",kLydBackend267V1);j.str("adapter_id",full111::kAdapterId);
 j.str("action",kEventOptionActions[static_cast<std::size_t>(action)]);j.str("status",Status(status));
 j.flag("source_available",ok);j.flag("cleanup_known",result.cleanup_known);
 j.flag("effect_attempted",result.effect_attempted);j.flag("native_returned",result.native_returned);
 WriteFactsAndOwner(j,result,facts);
 j.key("target");
 if (data.target) {
  j.data+="{\"instance_id\":"+std::to_string(data.target->instance_id);
  j.num("recipient_character_id",data.target->recipient_character_id);
  j.str("definition_key",data.target->definition_key);j.num("authored_option_index",data.target->authored_option_index);j.data+='}';
 } else j.data+="null";
 j.key("lineage");
 if (data.lineage) {
  j.data+="{\"source_revision\":";String(j.data,std::to_string(data.lineage->source_revision));
  j.str("renderer_request_id",data.lineage->renderer_request_id);
  j.u64("renderer_provider_generation",data.lineage->renderer_provider_generation);
  j.u64("renderer_query_sequence",data.lineage->renderer_query_sequence);
  j.nullable("prepare_request_id",data.lineage->prepare_request_id);j.u64("lease_sequence",data.lineage->lease_sequence);
  j.nullable("effect_request_id",data.lineage->effect_request_id);j.u64("claim_sequence",data.lineage->claim_sequence);j.data+='}';
 } else j.data+="null";
 j.key("queue");
 if (ok&&queue) {
  j.data+=R"({"complete":true)";j.num("count",static_cast<std::int64_t>(data.queue->instance_ids.size()));
  j.key("instance_ids");j.data+='[';
  for (std::size_t i=0;i<data.queue->instance_ids.size();++i) { if(i)j.data+=',';j.data+=std::to_string(data.queue->instance_ids[i]); }
  j.data+=']';j.str("target_state",data.queue->target_present?"present":"absent");j.data+='}';
 } else j.data+="null";
 j.flag("addresses_redacted",true);j.key("unavailable_reason");
 if (ok) j.data+="null";
 else String(j.data,result.reason.empty()?"current111_ordinary_event_option_unavailable":result.reason);
 j.data+="}}";return j.data;
}
