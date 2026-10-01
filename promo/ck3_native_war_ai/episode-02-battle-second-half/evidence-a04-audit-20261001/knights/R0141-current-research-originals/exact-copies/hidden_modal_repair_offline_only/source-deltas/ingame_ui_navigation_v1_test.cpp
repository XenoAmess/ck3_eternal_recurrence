--- C:\w\e2cap1001c\ck3_autonomous_player\native_bridge\tests\ingame_ui_navigation_v1_test.cpp
+++ C:\w\e2research1001\ck3_autonomous_player\native_bridge\tests\ingame_ui_navigation_v1_test.cpp
@@ -57,6 +57,53 @@
   assert(!ComputeCombatUiFitTranslationV1({0,0,2560,1440},{0,0,-1,400},delta));
   assert(!ComputeCombatUiFitTranslationV1({0,0,2560,1440},{(std::numeric_limits<float>::quiet_NaN)(),0,800,400},delta));
   assert(JsonEscape("a\"b\\c\n")=="a\\\"b\\\\c\\u000A");
+  // Actual production modal helper uses ReadProcessMemory over offline buffers.
+  // Registered hidden receivers are not active blocking modals; a visible
+  // earlier entry must still refuse even when the absolute last entry is hidden.
+  std::array<unsigned char,0x300> modal_context{};
+  std::array<unsigned char,0xD1> hidden_receiver{},visible_receiver{};
+  hidden_receiver[0xD0]=0xB8;visible_receiver[0xD0]=0;
+  std::array<void *,256> modal_entries{};
+  const auto set_modal=[&](std::int32_t n,void *data){
+    std::memcpy(modal_context.data()+kZhongguoGuiModalReceiversOffset,&data,sizeof(data));
+    std::memcpy(modal_context.data()+kZhongguoGuiModalReceiverCountOffset,&n,sizeof(n));
+  };
+  IngameUiModalAdmissionV1 modal{};
+  set_modal(0,nullptr);
+  assert(ReadModalNavigationAdmission(modal_context.data(),modal) && modal.header_read && modal.receivers_verified && modal.receivers.empty());
+  set_modal(1,modal_entries.data());modal_entries[0]=hidden_receiver.data();
+  assert(ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receiver_count==1 && modal.receivers_verified && modal.effective_visible_count==0 && modal.receivers[0].flags_d0==0xB8);
+  modal_entries[0]=visible_receiver.data();
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receivers_verified && modal.effective_visible_count==1 && modal.unavailable_reason=="effective_visible_modal_receiver_blocks_navigation");
+  visible_receiver[0xD0]=0x10; // local hidden alone is not effective-hidden
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.effective_visible_count==1);
+  visible_receiver[0xD0]=0;
+  set_modal(2,modal_entries.data());modal_entries[0]=visible_receiver.data();modal_entries[1]=hidden_receiver.data();
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.effective_visible_count==1 && modal.receivers.size()==2);
+  modal_entries[0]=hidden_receiver.data();modal_entries[1]=visible_receiver.data();
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.effective_visible_count==1);
+  for(auto &entry:modal_entries)entry=hidden_receiver.data();set_modal(256,modal_entries.data());
+  assert(ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receivers.size()==256);
+  set_modal(-1,modal_entries.data());
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receiver_count==-1 && modal.unavailable_reason=="modal_receiver_count_out_of_bounds");
+  set_modal(257,modal_entries.data());assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receivers.empty());
+  set_modal(1,nullptr);assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_vector_missing");
+  set_modal(1,modal_entries.data());modal_entries[0]=nullptr;
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_entry_unreadable_or_null");
+  set_modal(1,reinterpret_cast<void *>(1));
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_entry_unreadable_or_null");
+  set_modal(1,modal_entries.data());modal_entries[0]=reinterpret_cast<void *>(1);
+  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_flags_unreadable");
+  assert(!ReadModalNavigationAdmission(nullptr,modal) && !modal.header_read && modal.unavailable_reason=="modal_receiver_header_unreadable");
+  assert(!ReadModalNavigationAdmission(reinterpret_cast<void *>(1),modal) && !modal.header_read);
+  IngameUiResultV1 modal_result{};modal_result.modal_admission=modal;
+  auto modal_json=SerializeIngameUiResultV1(r,modal_result,3);
+  assert(modal_json.find("\"receiver_count\":null")!=std::string::npos);
+  set_modal(1,modal_entries.data());modal_entries[0]=hidden_receiver.data();
+  assert(ReadModalNavigationAdmission(modal_context.data(),modal_result.modal_admission));
+  modal_json=SerializeIngameUiResultV1(r,modal_result,3);
+  assert(modal_json.find("\"receiver_count\":1")!=std::string::npos && modal_json.find("\"flags_d0\":184")!=std::string::npos);
+  std::cout<<"offline original modal helper: 15 bounded/hidden/visible/mixed/null/unreadable cases and 2 actual serializer checks PASS; no game calls\n";
   // Real ReadProcessMemory over offline buffers exercises storage indexing and
   // full generation identity; a low-24-bit match alone must fail.
   auto *image=static_cast<unsigned char *>(VirtualAlloc(nullptr,kImageSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
