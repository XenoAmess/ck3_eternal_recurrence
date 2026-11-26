namespace {
bool ReadFull111EventOptionCoreV2(ReadonlyContext &context, const RendererOwnerV1 &owner,
    const ck3_1210::CoreSnapshotPrefix &expected, ck3_1210::CoreSnapshotPrefix &actual) {
 if (!RendererOwnerV1::Current(&owner) || !Read(context,owner.stamp,owner.invocation) ||
     !context.observation.available || context.observation.offline_fixture ||
     !context.observation.main_owner_observed || !Same(context.observation.core,expected)) return false;
 actual=context.observation.core;
 return RendererOwnerV1::Current(&owner);
}
}

bool ReadFull111EventQueueOnOwner267V2(const ReadonlyBindings &bindings,
    ck3_11906::MainThreadQueryMailboxV1 *mailbox, const ck3_11906::MainThreadQueryTicketV1 &ticket,
    const ck3_11906::MainThreadExecutionStampV1 &stamp, void *invocation_context,
    const Full111EventOptionRequest267V2 &request, std::uint64_t mono,
    ck3_1210::CoreSnapshotPrefix &actual, Full111EventQueue267V2 &result) noexcept {
 try {
  if (!mailbox||mailbox->offline_fixture||!invocation_context||!bindings.exact_image_admitted) return false;
  ReadonlyContext context;
  context.bindings=bindings;context.mailbox=mailbox;context.ticket=ticket;context.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteLydOnOwner267V1,invocation_context};
  const RendererOwnerV1 owner{context,stamp,invocation,request.deadline_unix_ms,mono};
  return ReadFull111EventOptionCoreV2(context,owner,request.expected,actual) &&
      SampleFull111EventQueue267V2(bindings,stamp.game_state,request.target,result) &&
      ReadFull111EventOptionCoreV2(context,owner,request.expected,actual);
 } catch (...) { return false; }
}

LydRawCall267V1 SelectFull111RenderedOptionOnOwner267V2(const ReadonlyBindings &bindings,
    ck3_11906::MainThreadQueryMailboxV1 *mailbox, const ck3_11906::MainThreadQueryTicketV1 &ticket,
    const ck3_11906::MainThreadExecutionStampV1 &stamp, void *invocation_context, const LydFrame267V1 &frame,
    const Full111EventOptionRequest267V2 &request, std::uint64_t mono,
    const Full111EventRendererMaterial267V2::Option &option,
    const Full111EventRendererMaterial267V2 &material) noexcept {
 try {
  if (!mailbox||mailbox->offline_fixture||!invocation_context||!bindings.exact_image_admitted||
      !VerifyLetterImage267V1(bindings.module_base)) return {};
  ReadonlyContext context;
  context.bindings=bindings;context.mailbox=mailbox;context.ticket=ticket;context.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteLydOnOwner267V1,invocation_context};
  const RendererOwnerV1 owner{context,stamp,invocation,request.deadline_unix_ms,mono};
  ck3_1210::CoreSnapshotPrefix actual;
  const auto &target=request.target;
  if (!ReadFull111EventOptionCoreV2(context,owner,request.expected,actual) ||
      frame.scene.jomini!=stamp.jomini_state || option.authored_index!=target.authored_option_index) return {};
  std::int32_t id=0, recipient=-1, authored=-1;
  std::uintptr_t data=0, definition=0;
  std::uint8_t already_selected=0;
  full111_event_queue::Sample queue;
  if (!full111_event_queue::Capture(bindings,stamp.game_state,queue) || queue.game_data!=material.game_data ||
      queue.items!=material.queue_items || queue.count!=static_cast<std::int32_t>(material.queue_rows.size()) ||
      !std::equal(material.queue_rows.begin(),material.queue_rows.end(),queue.rows.begin()) ||
      !At(material.runtime,0x1C4,id) || id!=target.instance_id ||
      !At(material.runtime,0x1C0,recipient) || recipient!=target.recipient_character_id ||
      !At(material.runtime,0x1B8,definition) || definition!=material.definition ||
      !At(material.data,0,id) || id!=target.instance_id || !At(material.data,0x30,already_selected) || already_selected ||
      !At(option.model,0x160,data) || data!=material.data ||
      !At(option.model,0x1B0,authored) || authored!=target.authored_option_index || !RendererOwnerV1::Current(&owner)) return {};
  return CallFull111StockOption267V2(bindings,option.model);
 } catch (...) { return {}; }
}
