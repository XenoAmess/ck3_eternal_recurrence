// Included only in the exact Full111 ordinary observation profile.
namespace {
struct RendererOwnerV1 {
 ReadonlyContext &context;
 const ck3_11906::MainThreadExecutionStampV1 &stamp;
 const OwnerInvocationV1 &invocation;
 std::uint64_t wall, mono;

 static bool Current(const void *opaque) noexcept {
  const auto &state = *static_cast<const RendererOwnerV1 *>(opaque);
  const auto wall = std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count();
  return wall > 0 && static_cast<std::uint64_t>(wall) < state.wall &&
      GetTickCount64() < state.mono && Owner(state.context, state.stamp, state.invocation);
 }
};

bool ReadRendererSubtreeV1(std::uintptr_t image, const LydScene267V1 &scene,
 std::uintptr_t foreground, const RendererOwnerV1 &owner, std::vector<GuiWindowNodeV1> &nodes) {
 GuiWindowNodeV1 root;
 if (!GuiWindowNodeReadV1(image, foreground, scene.context, scene.events_layer, root)) return false;
 nodes.push_back(std::move(root));
 std::unordered_set<std::uintptr_t> seen{foreground};
 std::size_t name_bytes = nodes.front().name.size();
 for (std::size_t cursor = 0; cursor < nodes.size(); ++cursor) {
  const auto parent = nodes[cursor];
  if (parent.depth >= kGuiWindowMaxDepthV1) return false;
  for (std::int32_t i = 0; i < parent.child_count; ++i) {
   std::uintptr_t child = 0;
   GuiWindowNodeV1 node;
   if (nodes.size() >= kGuiWindowMaxNodesV1 || GetTickCount64() >= owner.mono ||
       !At(parent.children, static_cast<std::size_t>(i) * sizeof(child), child) ||
       !seen.insert(child).second ||
       !GuiWindowNodeReadV1(image, child, scene.context, parent.widget, node)) return false;
   name_bytes += node.name.size();
   if (name_bytes > 131072) return false;
   node.depth = parent.depth + 1;
   node.sibling_index = static_cast<std::uint32_t>(i);
   nodes.push_back(std::move(node));
  }
 }
 return RendererOwnerV1::Current(&owner);
}
}

bool ReadFull111EventRendererOnOwner267V1(const ReadonlyBindings &bindings,
 ck3_11906::MainThreadQueryMailboxV1 *mailbox, const ck3_11906::MainThreadQueryTicketV1 &ticket,
 const ck3_11906::MainThreadExecutionStampV1 &stamp, void *invocation_context,
 const LydFrame267V1 &frame, const LydRequest267V1 &request, std::uint64_t mono,
 Full111EventRendererSource267V1 &result, bool &native_read_entered, bool &cleanup_known, std::string &reason, Full111EventRendererMaterial267V2 *material) noexcept {
 result = {}; native_read_entered = false; cleanup_known = true;
 reason = "current111_renderer_original_owner_unavailable";
 Full111OrdinaryEventWitnessV1 witness;
 try {
  if (!request.instance_id || !frame.facts_verified || !invocation_context || !mailbox ||
      !bindings.exact_image_admitted || mailbox->offline_fixture) return false;
  ReadonlyContext context;
  context.bindings = bindings;
  context.mailbox = mailbox;
  context.ticket = ticket;
  const OwnerInvocationV1 invocation{&ExecuteLydOnOwner267V1, invocation_context};
  const RendererOwnerV1 owner{context, stamp, invocation, request.deadline_unix_ms, mono};
  const auto ready = ReadFull111OrdinaryEventOnOwnerV1(bindings, frame.core, stamp.game_state,
      frame.scene.jomini, request.deadline_unix_ms, mono, &owner, &RendererOwnerV1::Current, witness);
  native_read_entered = witness.raw.native_read_entered;
  cleanup_known = witness.raw.cleanup_known;
  if (!ready || !witness.raw.source.events) {
   reason = "current111_renderer_ordinary_world_unavailable";
   return false;
  }
  const auto image = bindings.module_base;
  const auto foreground = Full111ForegroundEventRootV1(witness);
  const auto &raw = witness.raw.event_rows;
  const auto selected = std::find_if(raw.begin(), raw.end(),
      [foreground](const auto &row) { return foreground && row.root == foreground; });
  if (selected == raw.end() || selected->instance_id != *request.instance_id) {
   reason = "current111_renderer_expected_foreground_changed";
   return false;
  }
  const auto &event = witness.raw.source.events->events[static_cast<std::size_t>(selected - raw.begin())];
  const full111_event_renderer::CopyReader reader{nullptr,
      [](void*, std::uintptr_t address, void *destination, std::size_t size) noexcept {
       return Copy(reinterpret_cast<const void *>(address), destination, size);
      }};
  const auto sample = [&]() -> std::optional<full111_event_renderer::Snapshot> {
   std::vector<GuiWindowNodeV1> nodes;
   if (!RendererOwnerV1::Current(&owner) ||
       !ReadRendererSubtreeV1(image, witness.scene, foreground, owner, nodes)) return {};
   return full111_event_renderer::Capture(reader, image, foreground, frame.core.played_character_id,
       *selected, event, nodes);
  };
  const auto first = sample();
  const auto stable = first ? full111_event_renderer::AcceptStable(first, sample()) : std::nullopt;
  full111_event_queue::Sample queue;
  if (!stable || !SameFull111ForegroundSourcesV1(image, witness) ||
      !full111_event_queue::Capture(bindings, stamp.game_state, queue) || queue != witness.queue ||
      !RendererOwnerV1::Current(&owner)) {
   reason = "current111_renderer_complete_widget_context_unavailable";
   return false;
  }
  Full111EventRendererSource267V1 source;
  source.instance_id = event.instance_id;
  source.recipient_character_id = event.recipient_character_id;
  source.authored_option_count = event.authored_option_count;
  source.definition_key = event.definition_key;
  for (const auto &row : stable->renderer_order) {
   const auto text = std::find_if(event.options.begin(), event.options.end(),
       [&row](const auto &option) { return option.authored_option_index == row.authored_index; });
   if (text == event.options.end()) return false;
   source.options.push_back({row.authored_index, row.native_valid, row.widget_visible,
       row.widget_enabled, text->text, text->disabled_reason});
  }
  if (material) {
   Full111EventRendererMaterial267V2 bound;
   bound.game_data=queue.game_data; bound.queue_items=queue.items;
   bound.controller=selected->controller; bound.root=selected->root; bound.data=selected->data;
   bound.runtime=selected->runtime; bound.definition=selected->definition; bound.grid=stable->grid;
   bound.queue_rows.assign(queue.rows.begin(),queue.rows.begin()+queue.count);
   for (const auto &row : stable->renderer_order)
    bound.options.push_back({row.placement.widget,row.option,row.context_thunk,row.authored_index});
   *material=std::move(bound);
  }
  result = std::move(source);
  reason.clear();
  return true;
 } catch (...) {
  native_read_entered = witness.raw.native_read_entered;
  cleanup_known = witness.raw.cleanup_known;
  reason = "current111_renderer_observation_exception";
  return false;
 }
}

#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
#include "ck3_121003_full111_event_option_reader_v2.inc"
#endif
