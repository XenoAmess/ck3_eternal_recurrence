namespace {
struct RendererEvidence267V2 {
 full111_event_effect::Evidence receipt;
 LydFrame267V1 frame;
 Full111EventRendererMaterial267V2 material;
 Full111EventRendererSource267V1 source;
};
full111_event_effect::Owner EventOptionOwner267V2(const LydContext267V1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
 return {stamp.game_state,stamp.jomini_state,context.connection_generation,context.ticket.sequence};
}

void SaveEventOptionCore267V2(LydContext267V1 &context, const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_1210::CoreSnapshotPrefix &core) noexcept {
 context.result.facts_available=true;
 context.result.facts=core;
 context.result.connection_generation=context.connection_generation;
 context.result.ticket_sequence=context.ticket.sequence;
 context.result.pump_epoch=stamp.pump_epoch;
 context.result.thread_id=stamp.thread_id;
}

const Full111EventRendererMaterial267V2::Option *QualifiedOption267V2(const Full111EventOptionTarget267V2 &target,
    const Full111EventRendererSource267V1 &source, const Full111EventRendererMaterial267V2 &material) noexcept {
 if (source.instance_id!=target.instance_id||source.recipient_character_id!=target.recipient_character_id||
     source.definition_key!=target.definition_key||!material.root||!material.runtime||!material.definition) return nullptr;
 const auto candidate=std::find_if(source.options.begin(),source.options.end(),[&](const auto &row) {
     return row.authored_option_index==target.authored_option_index;
 });
 if (candidate==source.options.end()||!candidate->native_can_select||!candidate->widget_visible||!candidate->widget_enabled)
  return nullptr;
 const auto option=std::find_if(material.options.begin(),material.options.end(),[&](const auto &row) {
     return row.authored_index==target.authored_option_index;
 });
 if (option==material.options.end()||!option->model||!option->widget||!option->cell_context_identity)
  return nullptr;
 using Storage=Full111OptionContextStorage267V2;
 return option->cell_context_storage==Storage::direct||option->cell_context_storage==Storage::typed_thunk
     ? &*option : nullptr;
}

bool ExecuteFull111EventOption267V2(LydContext267V1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp, full111_event_effect::State &state,
    const std::optional<RendererEvidence267V2> &renderer, std::atomic_bool &unknown) {
 using S=LydStatus267V1;
 using A=Full111EventOptionAction267V2;
 const auto &request=*context.event_option_request;
 auto &result=context.result;
 auto &data=context.event_option_result;
 const auto owner=EventOptionOwner267V2(context,stamp);
 const auto reject=[&](S status,const char *reason) { result.status=status;result.reason=reason;return true; };
 if (state.already_claimed(request.request_id)) return reject(S::claim_consumed,"current111_original_effect_claim_retained");
 if (unknown.load(std::memory_order_acquire)) {
  result.cleanup_known=false;return reject(S::indeterminate,"current111_original_native_completion_unknown");
 }
 if (!Time(context)) return reject(S::expired,"current111_original_operation_deadline_expired");
 if (request.action==A::query_queue) {
  if (!state.known_claim_for_read(request,owner)) return reject(S::stale_source,"current111_known_original_effect_missing");
  context.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
  Full111EventQueue267V2 queue;
  ck3_1210::CoreSnapshotPrefix core;
  if (!ReadFull111EventQueueOnOwner267V2(context.bindings,context.mailbox,context.ticket,stamp,&context,
      request,context.monotonic_deadline_ms,core,queue))
   return reject(Time(context)?S::unavailable:S::expired,"current111_complete_runtime_event_queue_unavailable");
  SaveEventOptionCore267V2(context,stamp,core);
  data.queue=std::move(queue);
  if (!data.queue->target_present) state.close_known_claim();
  result.source_available=true;
  return reject(S::available,"");
 }
 if (!renderer || context.published_revision!=request.lineage.source_revision ||
     renderer->receipt.lineage.source_revision!=request.lineage.source_revision)
  return reject(S::stale_source,"current111_original_full_renderer_revision_changed");
 const bool prepare=request.action==A::prepare;
 if (prepare ? !state.accepts_renderer(request,renderer->receipt,owner) : !state.accepts_selection(request,owner))
  return reject(S::stale_source,"current111_original_private_renderer_or_lease_changed");
 if (request.lineage.renderer_request_id!=renderer->receipt.lineage.renderer_request_id ||
     request.lineage.renderer_provider_generation!=renderer->receipt.lineage.renderer_provider_generation ||
     request.lineage.renderer_query_sequence!=renderer->receipt.lineage.renderer_query_sequence)
  return reject(S::stale_source,"current111_original_renderer_request_replaced");
 context.monotonic_deadline_ms=(std::min)(context.monotonic_deadline_ms,renderer->receipt.mono);
 if (!prepare) context.monotonic_deadline_ms=(std::min)(context.monotonic_deadline_ms,state.active_lease()->evidence.mono);
 if (!Time(context)) return reject(S::expired,"current111_original_renderer_or_lease_deadline_expired");
 LydFrame267V1 frame;
 LydRaw267V1 unused;
 if (!Frame(context,stamp,frame)||!Observe(context,frame,stamp,std::nullopt,unused)) {
  if (!result.cleanup_known) { unknown.store(true,std::memory_order_release); return reject(S::indeterminate,"current111_renderer_completion_unknown"); }
  return reject(Time(context)?S::unavailable:S::expired,"current111_exact_renderer_unavailable");
 }
 LydFrame267V1 after;
 if (!Frame(context,stamp,after)||!SameFrame(frame,after)||!SameFrame(frame,renderer->frame)||
     !result.renderer||*result.renderer!=renderer->source||context.renderer_material!=renderer->material)
  return reject(S::stale_source,"current111_renderer_or_foreground_changed");
 const auto *option=QualifiedOption267V2(request.target,*result.renderer,context.renderer_material);
 if (!option) return reject(S::unavailable,"current111_original_option_not_native_visible_and_enabled");
 if (!Time(context)) return reject(S::expired,"current111_original_preclaim_deadline_expired");
 if (prepare) {
  if (!state.prepare(request,renderer->receipt,owner,context.monotonic_deadline_ms))
   return reject(S::claim_consumed,"current111_prior_instance_or_lease_retained");
  data.lineage=state.active_lease()->evidence.lineage;
  result.source_available=true;
  return reject(S::available,"");
 }
 auto *claim=state.preclaim(request,owner);
 if (!claim) return reject(S::claim_consumed,"current111_original_effect_preclaim_consumed");
 data.lineage=claim->lease.evidence.lineage;
 const auto effect=SelectFull111RenderedOptionOnOwner267V2(context.bindings,context.mailbox,context.ticket,
     stamp,&context,frame,request,context.monotonic_deadline_ms,*option,context.renderer_material);
 result.effect_attempted=effect.effect_entered;
 result.native_returned=effect.status==LydRawCallStatus267V1::returned;
 result.cleanup_known=effect.cleanup_known;
 if (effect.status==LydRawCallStatus267V1::indeterminate||!effect.cleanup_known ||
     (effect.effect_entered&&!Time(context))) {
  unknown.store(true,std::memory_order_release);
  result.cleanup_known=false;
  return reject(S::indeterminate,"current111_original_effect_completion_unknown");
 }
 if (!result.native_returned) {
  state.close_known_claim();
  return reject(S::stale_source,"current111_native_refused_before_selection");
 }
 claim->dispatched=true;
 result.source_available=true;
 return reject(S::selection_dispatched,"");
}
}
