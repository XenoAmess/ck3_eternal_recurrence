// The double sample uses the exact vector scanned by the stock 26785313 instance lookup.
bool SampleFull111EventQueue267V2(const ReadonlyBindings &bindings, std::uintptr_t owner_game,
    const Full111EventOptionTarget267V2 &target, Full111EventQueue267V2 &result) {
 struct Snapshot {
  full111_event_queue::Sample queue;
  Full111EventQueue267V2 data;
  std::uintptr_t target_definition=0;
 };
 const auto sample=[&](Snapshot &snapshot) {
  auto &queue=snapshot.queue;
  auto &data=snapshot.data;
  if (!full111_event_queue::Capture(bindings,owner_game,queue,true)) return false;
  for (std::int32_t index=0;index<queue.count;++index) {
   const auto row=queue.rows[static_cast<std::size_t>(index)];
   std::int32_t id=0;
   if (!lyd_common::At(row,0x1C4,id)||id<=0||
       std::find(data.instance_ids.begin(),data.instance_ids.end(),id)!=data.instance_ids.end()) return false;
   data.instance_ids.push_back(id);
   if (id!=target.instance_id) continue;
   std::int32_t recipient=-1;
   std::string definition;
   if (!lyd_common::At(row,0x1C0,recipient)||recipient!=target.recipient_character_id||
       !lyd_common::At(row,0x1B8,snapshot.target_definition)||!snapshot.target_definition||
       !lyd_common::Text(snapshot.target_definition+0x10,256,definition,true)||definition!=target.definition_key) return false;
   data.target_present=true;
  }
  return true;
 };
 Snapshot before, after;
 if (!sample(before)||!sample(after)||before.queue!=after.queue||
     before.data.instance_ids!=after.data.instance_ids||before.target_definition!=after.target_definition||
     before.data.target_present!=after.data.target_present) return false;
 result=std::move(after.data);
 return true;
}

LydRawCall267V1 CallFull111StockOption267V2(const ReadonlyBindings &bindings, std::uintptr_t option) noexcept {
 LydRawCall267V1 result;
 if (!option||!bindings.exact_image_admitted) return result;
 if (lyd_raw::NativeSelect(bindings.module_base,option,result.effect_entered,result.cleanup_known))
  result.status=LydRawCallStatus267V1::returned;
 else if (result.effect_entered||!result.cleanup_known)
  result.status=LydRawCallStatus267V1::indeterminate;
 return result;
}
