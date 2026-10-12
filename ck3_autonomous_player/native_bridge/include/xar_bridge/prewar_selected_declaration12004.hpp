#pragma once

#include "xar_bridge/ck3_12002_declarations.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Pointer-free observation of the common CWarDeclaration context. The actual4
// common CB scope publishes additional as named attacker and recipient as
// named defender. Its common War builder consumes these same two roles as the
// primary sides. Preserve the separate interaction actor and raw role fields.
struct PrewarSelectedDeclarationObservation12004 {
  bool available = false;
  bool finalized_selection_ready = false;
  bool finalized_roles_ready = false;
  std::optional<bool> final_can_send;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::string declaration_id;
  game::DeclarableWarSnapshot selected;
  std::optional<std::int32_t> context_actor_character_id;
  std::optional<std::int32_t> context_recipient_character_id;
  std::optional<std::int32_t> context_additional_role_character_id;
  std::optional<std::int32_t> context_claimant_character_id;
  std::optional<std::int32_t> native_cb_attacker_character_id;
  std::optional<std::int32_t> native_cb_defender_character_id;
  bool native_cb_role_names_ready = false;
  bool claimant_uses_native_fallback = false;
  bool consumer_invoked = false;
  // Hook completion is independent of each consumer's participant/force
  // coverage flags. A successful callback is not a complete coalition.
  bool consumer_completed = false;
  bool context_cleanup_completed = false;
  bool scratch_cleanup_completed = false;
  std::string failure;

  bool operator==(const PrewarSelectedDeclarationObservation12004 &) const = default;
};

// Borrowed only during the synchronous consumer call. Every pointer belongs
// to the same finalized selection. Never retain these pointers, construct a
// second context, submit a command, or dispatch another mailbox from here.
struct PrewarSelectedDeclarationNativeScope12004 {
  const void *finalized_context = nullptr;
  const void *war_declaration = nullptr;
  void *actual_cb = nullptr;
  void *context_actor = nullptr;
  void *context_recipient = nullptr;
  void *context_additional_role = nullptr;
  void *resolved_claimant = nullptr;
  const void *native_titles = nullptr;
};

using ConsumePrewarSelectedDeclaration12004 = bool (*)(
    void *context, const PrewarSelectedDeclarationNativeScope12004 &scope,
    const PrewarSelectedDeclarationObservation12004 &observation) noexcept;

// Borrow the actual4 declaration profile from the owning adapter. This
// generalizes its common construct/refresh/finalize/validate path for every
// native-enumerated CB, without modifying the existing holy-only query.
// True means the observation is available, including a native false final
// validator result. It does not assert complete participants or permission
// to declare. The caller owns the executing paused full-snapshot envelope,
// compares two complete observations/consumer DTOs, and finishes that frame.
bool ReadPrewarSelectedDeclaration12004(
    const ck3_12002::DeclarationsBindings &bindings,
    ck3_12002::QueryMailboxEnvelope &envelope,
    std::string_view declaration_id,
    const game::DeclarableWarSnapshot &selected,
    PrewarSelectedDeclarationObservation12004 &output,
    ConsumePrewarSelectedDeclaration12004 consume = nullptr,
    void *consumer_context = nullptr) noexcept;

} // namespace xar::ck3_12004
