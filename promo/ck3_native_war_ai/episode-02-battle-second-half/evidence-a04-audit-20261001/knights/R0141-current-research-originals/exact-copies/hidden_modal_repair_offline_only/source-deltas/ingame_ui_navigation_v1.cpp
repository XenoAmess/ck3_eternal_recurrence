--- C:\w\e2cap1001c\ck3_autonomous_player\native_bridge\src\ingame_ui_navigation_v1.cpp
+++ C:\w\e2research1001\ck3_autonomous_player\native_bridge\src\ingame_ui_navigation_v1.cpp
@@ -55,6 +55,48 @@
   return Read(reinterpret_cast<const std::uint8_t *>(object)+offset,&value,sizeof(value));
 }
 template<class T> bool Slot(std::uintptr_t address,T &value) noexcept {return Read(reinterpret_cast<void *>(address),&value,sizeof(value));}
+// Original ShortcutManagerActivate 36E1C70..36E1CA6 scans receiver+D0 bit08
+// rather than treating nonzero registration count as an active modal. Global
+// typed navigation is conservatively stricter: any effective-visible receiver
+// refuses navigation, with no descendant allowance or exception by name.
+bool ReadModalNavigationAdmission(const void *context,
+                                 IngameUiModalAdmissionV1 &out) noexcept {
+  out={};out.attempted=true;
+  void **receivers=nullptr;
+  if(!Value(context,kZhongguoGuiModalReceiversOffset,receivers) ||
+     !Value(context,kZhongguoGuiModalReceiverCountOffset,out.receiver_count)) {
+    out.unavailable_reason="modal_receiver_header_unreadable";return false;
+  }
+  out.header_read=true;out.vector_address=reinterpret_cast<std::uintptr_t>(receivers);
+  if(out.receiver_count<0 || out.receiver_count>256) {
+    out.unavailable_reason="modal_receiver_count_out_of_bounds";return false;
+  }
+  if(out.receiver_count && !receivers) {
+    out.unavailable_reason="modal_receiver_vector_missing";return false;
+  }
+  for(std::int32_t index=0;index<out.receiver_count;++index) {
+    void *receiver=nullptr;std::uint8_t flags=0;
+    if(!Value(receivers,static_cast<std::size_t>(index)*sizeof(void *),receiver) || !receiver) {
+      out.unavailable_reason="modal_receiver_entry_unreadable_or_null";return false;
+    }
+    if(!Value(receiver,kZhongguoWidgetHiddenFlagsOffset,flags)) {
+      out.unavailable_reason="modal_receiver_flags_unreadable";return false;
+    }
+    out.receivers.push_back({reinterpret_cast<std::uintptr_t>(receiver),flags});
+    if((flags & kZhongguoWidgetEffectiveHiddenMask)==0)++out.effective_visible_count;
+  }
+  void **later_receivers=nullptr;std::int32_t later_count=0;
+  if(!Value(context,kZhongguoGuiModalReceiversOffset,later_receivers) ||
+     !Value(context,kZhongguoGuiModalReceiverCountOffset,later_count) ||
+     later_receivers!=receivers || later_count!=out.receiver_count) {
+    out.unavailable_reason="modal_receiver_header_changed_during_read";return false;
+  }
+  out.receivers_verified=true;
+  if(out.effective_visible_count) {
+    out.unavailable_reason="effective_visible_modal_receiver_blocks_navigation";return false;
+  }
+  return true;
+}
 bool Object(std::uintptr_t base,std::uintptr_t storage_rva,std::uint32_t id,std::size_t id_offset,void *&object) noexcept {
   object=nullptr;
   if (id==(std::numeric_limits<std::uint32_t>::max)()) return false;
@@ -494,12 +536,15 @@
     if(request.window_kind==IngameUiWindowKindV1::combat)ReadCombatHover(env,out);
     out.available=true;out.status="observed";return true;
   }
-  // Actions are refused behind modal receivers; they do not synthesize input.
-  ZhongguoScoreboardAccessV1 access{};void *context=nullptr;void *owner=nullptr;std::uint32_t modal_count=0;
+  // All actions, including semantic hover and fit, share the same original GUI
+  // context and conservative effective-visible modal admission.
+  ZhongguoScoreboardAccessV1 access{};void *context=nullptr;void *owner=nullptr;
   if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner) ||
-      context!=gui_binding.context || owner!=gui_binding.owner ||
-      !Value(context,kZhongguoGuiModalReceiverCountOffset,modal_count) || modal_count!=0) {
-    out.unavailable_reason="modal_context_blocks_navigation";return true;
+      context!=gui_binding.context || owner!=gui_binding.owner) {
+    out.unavailable_reason="modal_gui_context_binding_changed";return true;
+  }
+  if(!ReadModalNavigationAdmission(context,out.modal_admission)) {
+    out.unavailable_reason=out.modal_admission.unavailable_reason;return true;
   }
   const auto expected=request.operation==IngameUiOperationV1::open_knights ? static_cast<std::uint32_t>(snapshot.played_character_id):request.subject_id;
   if((request.operation==IngameUiOperationV1::open_character || request.operation==IngameUiOperationV1::open_combat ||
@@ -590,8 +635,20 @@
    <<"\",\"combat_roster_full_ids_available\":false,\"native_backend_id\":\"ck3-1.19.0.6-native-ingame-ui-v1\""
    <<",\"hover_state_available\":"<<v.hover_state_available<<",\"hovered_widget_name\":\""<<v.hovered_widget_name
    <<"\",\"hovered_ui_side\":\""<<v.hovered_ui_side<<"\",\"hovered_combat_id\":"<<v.hovered_combat_id
-   <<",\"hover_readback_is_pixels\":false"
-   <<",\"combat_geometry\":{\"available\":"<<v.combat_geometry.available
+   <<",\"hover_readback_is_pixels\":false";
+  const auto &m=v.modal_admission;
+  o<<",\"modal_admission\":{\"attempted\":"<<m.attempted<<",\"header_read\":"<<m.header_read
+   <<",\"receivers_verified\":"<<m.receivers_verified<<",\"receiver_count\":";
+  if(m.header_read)o<<m.receiver_count;else o<<"null";
+  o<<",\"vector_address\":"<<m.vector_address<<",\"effective_visible_count\":"<<m.effective_visible_count
+   <<",\"effective_hidden_mask\":8,\"policy\":\"refuse_any_effective_visible_receiver\""
+   <<",\"unavailable_reason\":\""<<JsonEscape(m.unavailable_reason)<<"\",\"receivers\":[";
+  for(std::size_t index=0;index<m.receivers.size();++index) {
+    if(index)o<<',';
+    o<<"{\"address\":"<<m.receivers[index].address<<",\"flags_d0\":"<<static_cast<unsigned>(m.receivers[index].flags_d0)<<'}';
+  }
+  o<<"]}";
+  o<<",\"combat_geometry\":{\"available\":"<<v.combat_geometry.available
    <<",\"combat_id\":"<<v.combat_geometry.combat_id<<",\"widget_count\":"<<v.combat_geometry.widget_count
    <<",\"coordinate_space\":\"native_gui_absolute\",\"scope\":\"visible_widget_union_and_verified_stock_background_margins\""
    <<",\"stock_margin_source_verified\":"<<v.combat_geometry.stock_margin_source_verified
