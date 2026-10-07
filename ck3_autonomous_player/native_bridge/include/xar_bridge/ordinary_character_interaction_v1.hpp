#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ordinary_interaction_request_v1.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12003::ordinary_interaction {

inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::int64_t kCostScale = 100000;
inline constexpr std::size_t kNativeContextBytes = 0x338;
inline constexpr std::size_t kNativeCommandBytes = 0x368;

using DatabaseGetter = void *(*)();
using StableHash = std::int32_t (*)(void *, const char *, std::uint32_t);
using DefinitionLookup = void *(*)(void *, std::int32_t);
using TwoRoleConstructor = void *(*)(void *, void *, std::int32_t,
                                    std::int32_t, void *, bool);
using MenuShown = bool (*)(void *);
using ReadOption = bool (*)(void *, std::uint32_t);
using OuterAnswer = std::uint8_t (*)(void *, std::uint8_t, std::uint8_t,
                                    void *, void *);
using DispatchFrameVerifier = bool (*)(void *) noexcept;

struct Bindings {
  bool enabled = false;
  ck3_12002::ContextBindings interaction{};
  DatabaseGetter get_database = nullptr;
  StableHash stable_hash = nullptr;
  DefinitionLookup lookup_definition = nullptr;
  TwoRoleConstructor construct_two_role = nullptr;
  MenuShown is_shown = nullptr;
  ReadOption read_option = nullptr;
  OuterAnswer outer_answer = nullptr;
  // Internal owner wrapper callback. Never sourced from a public request.
  void *dispatch_frame_context = nullptr;
  DispatchFrameVerifier verify_dispatch_frame = nullptr;
};

struct Observation {
  bool native_context_available = false;
  bool ordinary_context_supported = false;
  bool actor_binding_verified = false;
  bool recipient_binding_verified = false;
  std::optional<bool> actor_alive;
  std::optional<bool> recipient_alive;
  std::optional<std::uint32_t> definition_stable_hash;
  // Actor, recipient, secondary actor, secondary recipient, intermediary,
  // sixth role; -1 is absent, every other native ID is bit-preserved.
  std::array<std::optional<std::uint32_t>, 6> effective_roles{};
  std::optional<std::uint32_t> declared_option_count;
  std::optional<std::uint32_t> selected_option_count;
  std::optional<bool> special_payload_present;
  std::optional<bool> shown;
  std::optional<bool> can_send;
  std::optional<std::array<std::int64_t, 10>> costs_raw;
  std::optional<bool> auto_accept;
  std::optional<std::int64_t> recipient_score_raw;
  std::optional<std::int64_t> intermediary_score_raw;
  std::optional<std::uint8_t> outer_answer_status;
  const char *unavailable_reason = "not_sampled";
  const char *unsupported_reason = "not_sampled";
};

enum class QueueResult { not_attempted, unavailable, rejected, submitted };
struct SendObservation {
  Observation preflight_context{};
  bool native_call_completed = false;
  bool dispatch_invoked = false;
  QueueResult native_queue_result = QueueResult::not_attempted;
  const char *reason = "not_attempted";
};

// Address calculation only. Exact .3 core/context/command addresses are bound
// independently; no .2 executable gate, discovery, pipe or process attachment.
// Actual current code-pin, owner/TLS/frame verification belongs to the wrapper.
Bindings BindOrdinaryInteractionImage12003(std::uintptr_t module_base,
                                          std::string_view executable_sha256) noexcept;
// Actual .4 dependencies come from its own Core, interaction and command
// profiles. The .3 binder is never used for an actual .4 executable.
Bindings BindOrdinaryInteractionImage12004(std::uintptr_t module_base,
                                          std::string_view executable_sha256) noexcept;

// In-process, application-owner leaves. Callers must already hold the freshly
// verified owner/TLS/paused-frame gate. No capability/registry wiring here.
bool ReadOrdinaryInteractionContextV1(const Bindings &, const OrdinaryInteractionRequestV1 &,
                                     Observation &) noexcept;
// Rebuilds and evaluates the context, keeps it alive through native command
// construction, checks both vtables, invokes SubmitCommandCopy once (0x0E).
// Any invoked queue path is only pending; no gameplay outcome is claimed.
void InitiateOrdinaryInteractionV1(const Bindings &, const OrdinaryInteractionRequestV1 &,
                                   SendObservation &) noexcept;

#if defined(XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1)
// Trusted owner-only stock UI leaves. This path never constructs a command.
struct GrantWindowBindingsV1 {
  void *confirmation = nullptr, *handler = nullptr;
  void (*install_context)(void *, const void *) = nullptr;
  void (*open_window)(void *, std::int32_t, std::int32_t) = nullptr;
  void (*refresh_window)(void *) = nullptr;
};
struct GrantPrepareObservationV1 {
  Observation preflight{};
  bool dispatch_invoked = false, native_call_completed = false;
  const char *reason = "not_attempted";
};
void PrepareGrantTitlePickerWindowV1(const Bindings &, const OrdinaryInteractionRequestV1 &,
    const GrantWindowBindingsV1 &, GrantPrepareObservationV1 &) noexcept;
#endif

} // namespace xar::ck3_12003::ordinary_interaction
