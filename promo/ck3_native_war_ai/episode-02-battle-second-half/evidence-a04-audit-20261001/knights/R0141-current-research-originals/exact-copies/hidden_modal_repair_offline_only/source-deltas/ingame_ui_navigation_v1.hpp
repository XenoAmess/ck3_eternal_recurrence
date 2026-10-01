--- C:\w\e2cap1001c\ck3_autonomous_player\native_bridge\include\xar_bridge\ingame_ui_navigation_v1.hpp
+++ C:\w\e2research1001\ck3_autonomous_player\native_bridge\include\xar_bridge\ingame_ui_navigation_v1.hpp
@@ -5,6 +5,7 @@
 #include <cstdint>
 #include <string>
 #include <string_view>
+#include <vector>
 
 namespace xar::ck3_11906 {
 
@@ -48,6 +49,22 @@
   friend bool operator==(const IngameUiGuiOwnerBindingV1 &,
                          const IngameUiGuiOwnerBindingV1 &) = default;
 };
+// Diagnostic raw observations only. A registered hidden receiver does not
+// imply a visible modal; no flags are read from caller-supplied game pointers.
+struct IngameUiModalReceiverV1 {
+  std::uintptr_t address = 0;
+  std::uint8_t flags_d0 = 0;
+};
+struct IngameUiModalAdmissionV1 {
+  bool attempted = false;
+  bool header_read = false;
+  bool receivers_verified = false;
+  std::int32_t receiver_count = 0;
+  std::uintptr_t vector_address = 0;
+  std::uint32_t effective_visible_count = 0;
+  std::vector<IngameUiModalReceiverV1> receivers;
+  std::string unavailable_reason;
+};
 // Application-event ownership comes from the original SDL/TLS mailbox proof.
 // The global RNG wrapper has its own scoped subsystem owner and is diagnostic.
 inline bool IsIngameUiPausedOwnerStampV1(
@@ -86,6 +103,7 @@
   std::uintptr_t gui_context_address = 0;
   std::uintptr_t gui_owner_address = 0;
   std::uint32_t rng_owner_thread_id = 0;
+  IngameUiModalAdmissionV1 modal_admission{};
   bool combat_knights_read_available = false;
   std::int32_t left_knight_count = -1;
   std::int32_t right_knight_count = -1;
