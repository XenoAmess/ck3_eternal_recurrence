#pragma once
#include "xar_bridge/ck3_1210_ingame_ready_v1.hpp"
#include "xar_bridge/ck3_1210_toast_scope_identity_v1.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <optional>
#include <vector>

namespace xar::ck3_1210 {
// Bounded raw provider behind the shared read-only public query. Its caller
// MUST already own exact Full + application-main/TLS custody. These are
// private memory operands, never fields accepted from a public request.
inline constexpr std::size_t kToastObjectMaximumQueueV1 = 64;
inline constexpr std::size_t kToastObjectMaximumNamedScopesV1 = 64;
inline constexpr std::size_t kToastObjectMaximumWidgetsV1 = 2048;
inline constexpr std::size_t kToastObjectReadBudgetV1 = 4 * 1024 * 1024;
enum class ToastObjectStageV1 { unavailable, empty, hidden, visible_pending_frame, visible };
struct ToastObjectBindingsV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  ToastScopeIdentityBindingsV1 scope_identities{};
};
struct ToastObjectMemoryReaderV1 {
  void *context = nullptr;
  bool (*copy)(void *, std::uintptr_t, void *, std::size_t) noexcept = nullptr;
};
// Complete scope token and canonical object witness are retained privately for
// stability checks. Only proved tags4/0x16 can yield typed identities.
struct ToastObjectNamedScopeV1 {
  std::uint32_t identifier = 0;
  std::string name;
  std::array<std::byte, 16> token{};
  ToastScopeIdentityV1 identity{};
  bool operator==(const ToastObjectNamedScopeV1 &) const = default;
};
struct ToastObjectScriptScopeV1 {
  std::string name;
  std::array<std::byte,16> token{};
  ToastScopeIdentityV1 identity{};
  bool operator==(const ToastObjectScriptScopeV1 &) const = default;
};
struct ToastObjectWidgetV1 {
  std::uintptr_t object = 0, parent = 0, children = 0, context = 0, vtable = 0;
  std::int32_t child_count = 0;
  std::uint8_t flags = 0;
  std::string name;
  bool operator==(const ToastObjectWidgetV1 &) const = default;
};
struct ToastObjectCaptureV1 {
  IngameReadyGraphV1 graph{};
  std::uintptr_t handler = 0, queue = 0, current_item = 0;
  std::uintptr_t context = 0, gui_root = 0, toast_widget = 0;
  std::int32_t queue_capacity = 0, queue_count = 0;
  std::array<std::byte, 0x11A0> semantic_base{};
  std::string title, description;
  std::vector<ToastObjectNamedScopeV1> saved_gui_scopes;
  std::vector<ToastObjectScriptScopeV1> saved_script_scopes;
  std::vector<ToastObjectWidgetV1> ancestry, subtree;
  bool effective_visible = false;
  bool operator==(const ToastObjectCaptureV1 &) const = default;
};
struct ToastObjectProviderV1 {
  bool has_previous = false;
  ToastObjectCaptureV1 previous;
};
struct ToastObjectScopeIdentityV1 {
  std::string name;
  ToastScopeKindV1 kind=ToastScopeKindV1::unsupported;
  std::uint16_t observed_tag=0;
  bool identity_available=false;
  std::optional<std::string> identity;
  std::string_view unavailable_reason;
  bool operator==(const ToastObjectScopeIdentityV1 &) const=default;
};
struct ToastObjectObservationV1 {
  ToastObjectStageV1 stage = ToastObjectStageV1::unavailable;
  std::uint64_t completed_application_frame = 0;
  std::int32_t queue_count = 0;
  std::string title, description;
  std::vector<ToastObjectScopeIdentityV1> saved_gui_scopes;
  std::vector<ToastObjectScopeIdentityV1> saved_script_scopes;
  // Deliberately distinct from a recipient or a correlated news event. A public
  // adapter must obtain viewer identity from its verified Full, not this graph.
  bool recipient_identity_available = false;
  bool news_origin_available = false;
  bool delivery_confirmed = false;
  std::string_view unavailable_reason;
};
// Binds only 1.21.0/26622941/2f2b... and verifies mapped source instructions.
// No game getter/initializer, GUI expression, lock, tick or mutation is called.
ToastObjectBindingsV1 BindToastObjectImageV1(std::uintptr_t,
    std::string_view executable_sha256) noexcept;
ToastObjectMemoryReaderV1 NativeToastObjectMemoryReaderV1() noexcept;
// Uses one exact Full's already-proven graph. Two complete captures must agree.
// A first visible capture is pending; a later completed application frame on the
// identical message and UI graph gives only `visible`, never correlated delivery.
bool ObservePublishedToastObjectV1(const ToastObjectBindingsV1 &,
    const IngameReadyGraphV1 &, const ToastObjectMemoryReaderV1 &,
    ToastObjectProviderV1 &, ToastObjectObservationV1 &) noexcept;
} // namespace xar::ck3_1210
