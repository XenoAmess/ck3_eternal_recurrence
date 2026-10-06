#include "xar_bridge/ordinary_character_interaction_v1.hpp"

#include <bit>
#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::ordinary_interaction {
namespace {

template <typename T>
bool Read(const void *base, std::size_t offset, T &value) noexcept {
  if (base == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename Result, typename... Args>
bool Call(Fn fn, Result &result, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename... Args>
bool CallVoid(Fn fn, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Valid(const OrdinaryInteractionRequestV1 &r) noexcept {
  if (r.interaction_key.empty() || r.interaction_key.size() > 128 ||
      r.recipient_id == 0 || r.recipient_id == UINT32_MAX ||
      r.expected_player_character_id <= 0 || r.expected_revision == 0 ||
      r.expected_game_pid == 0 || r.expected_connection_generation == 0) return false;
  for (const unsigned char c : r.interaction_key)
    if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
          (c >= '0' && c <= '9') || c == '_')) return false;
  return true;
}

// This is the reviewed current storage layout, with every dereference guarded.
// The low24 bits select a slot; they never become the returned identity.
void *Resolve(const ck3_12002::CoreBindings &b, std::uint32_t id) noexcept {
  if (!b.enabled || b.character_storage_slot == nullptr || id == 0 || id == UINT32_MAX)
    return nullptr;
  void *storage = nullptr, *slots = nullptr, *character = nullptr;
  std::int32_t capacity = 0;
  std::uint32_t actual = UINT32_MAX;
  const std::uint32_t index = id & 0x00FFFFFFU;
  if (!Read(b.character_storage_slot, 0, storage) ||
      !Read(storage, 0x2C, capacity) || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity) ||
      !Read(storage, 0x20, slots) ||
      !Read(slots, static_cast<std::size_t>(index) * 0x10 + 8, character) ||
      !Read(character, 0x18, actual) || actual != id) return nullptr;
  return character;
}
bool Alive(void *character, bool &alive) noexcept {
  void *death = nullptr;
  if (!Read(character, ck3_12002::kCharacterDeathDataOffset, death)) return false;
  alive = death == nullptr;
  return true;
}
bool DefinitionMatches(void *definition, std::int32_t hash,
                       std::string_view key) noexcept {
  std::int32_t stored_hash = 0;
  std::uint64_t size = 0, capacity = 0;
  if (!Read(definition, 0x14, stored_hash) || stored_hash != hash ||
      !Read(definition, 0x28, size) || !Read(definition, 0x30, capacity) ||
      size != key.size() || size > capacity) return false;
  const char *data = static_cast<const char *>(definition) + 0x18;
  if (capacity >= 16 && !Read(definition, 0x18, data)) return false;
  if (data == nullptr) return false;
  for (std::size_t i = 0; i < key.size(); ++i) {
    char value = 0;
    if (!Read(data, i, value) || value != key[i]) return false;
  }
  char terminator = 1;
  return Read(data, key.size(), terminator) && terminator == '\0';
}

struct NativeContext {
  alignas(8) std::array<std::byte, kNativeContextBytes> bytes{};
  ck3_12002::MarriageDestroyInteractionContext destroy = nullptr;
  bool constructed = false;
  ~NativeContext() {
    void *definition = nullptr;
    if (constructed || (Read(bytes.data(), 0, definition) && definition != nullptr))
      CallVoid(destroy, bytes.data());
  }
};
struct NativeCommand {
  alignas(8) std::array<std::byte, kNativeCommandBytes> bytes{};
  ck3_12002::MarriageDestroyInteractionContext destroy = nullptr;
  bool constructed = false;
  ~NativeCommand() {
    void *definition = nullptr;
    if (constructed || (Read(bytes.data(), 0x20, definition) && definition != nullptr))
      CallVoid(destroy, bytes.data() + 0x20);
  }
};

bool Fail(Observation &out, const char *reason) noexcept {
  // Incomplete native terms must not be mistaken for a complete context.
  const bool actor_verified = out.actor_binding_verified;
  const bool recipient_verified = out.recipient_binding_verified;
  out = {};
  out.actor_binding_verified = actor_verified;
  out.recipient_binding_verified = recipient_verified;
  out.unavailable_reason = reason;
  out.unsupported_reason = "native_context_unavailable";
  return false;
}

bool Prepare(const Bindings &b, const OrdinaryInteractionRequestV1 &r,
             NativeContext &context, Observation &out) noexcept {
  out = {};
  if (!Valid(r)) return Fail(out, "request_invalid");
  if (!b.enabled || !b.interaction.enabled || !b.interaction.core.enabled ||
      b.interaction.destroy == nullptr) return Fail(out, "bindings_unavailable");
  void *actor = Resolve(b.interaction.core,
      static_cast<std::uint32_t>(r.expected_player_character_id));
  if (actor == nullptr) return Fail(out, "actor_identity_unavailable");
  out.actor_binding_verified = true;
  void *recipient = Resolve(b.interaction.core, r.recipient_id);
  if (recipient == nullptr) return Fail(out, "recipient_identity_unavailable");
  out.recipient_binding_verified = true;
  bool actor_alive = false, recipient_alive = false;
  if (!Alive(actor, actor_alive) || !Alive(recipient, recipient_alive))
    return Fail(out, "character_life_sample_unavailable");
  void *database = nullptr, *definition = nullptr;
  std::int32_t hash = 0;
  if (!Call(b.get_database, database) || database == nullptr ||
      !Call(b.stable_hash, hash, database, r.interaction_key.data(),
            static_cast<std::uint32_t>(r.interaction_key.size())) ||
      !Call(b.lookup_definition, definition, database, hash) ||
      !DefinitionMatches(definition, hash, r.interaction_key))
    return Fail(out, "interaction_definition_unavailable");
  context.destroy = b.interaction.destroy;
  void *constructed = nullptr;
  if (!Call(b.construct_two_role, constructed, context.bytes.data(), definition,
            r.expected_player_character_id, std::bit_cast<std::int32_t>(r.recipient_id),
            static_cast<void *>(nullptr), true) || constructed != context.bytes.data())
    return Fail(out, "interaction_context_unavailable");
  context.constructed = true;
  void *storage = context.bytes.data();
  if (!CallVoid(b.interaction.refresh, storage, true) ||
      !CallVoid(b.interaction.finalize, storage))
    return Fail(out, "interaction_finalization_unavailable");
  std::array<std::optional<std::uint32_t>, 6> roles{};
  for (std::size_t i = 0; i < roles.size(); ++i) {
    std::int32_t id = -1;
    if (!Read(storage, 0x2D8 + sizeof(id) * i, id))
      return Fail(out, "effective_roles_unavailable");
    if (id != -1) roles[i] = std::bit_cast<std::uint32_t>(id);
  }
  void *option_data = nullptr, *special = nullptr;
  std::int32_t option_count = -1;
  if (!Read(definition, 0x2258, option_data) ||
      !Read(definition, 0x2264, option_count) || option_count < 0 ||
      option_count > 4096 || (option_count != 0 && option_data == nullptr) ||
      !Read(storage, 0x330, special))
    return Fail(out, "ordinary_shape_sample_unavailable");
  std::uint32_t selected_count = 0;
  for (std::int32_t i = 0; i < option_count; ++i) {
    std::uint32_t flag = 0;
    bool selected = false;
    if (!Read(option_data, static_cast<std::size_t>(i) * 0x730 + 0x368, flag) ||
        !Call(b.read_option, selected, storage, flag))
      return Fail(out, "ordinary_option_readback_unavailable");
    if (selected) ++selected_count;
  }
  bool shown = false, can_send = false, automatic = false;
  std::array<std::int64_t, 10> costs{};
  if (!Call(b.is_shown, shown, storage)) return Fail(out, "shown_unavailable");
  if (!CallVoid(b.interaction.evaluate_cost,
      static_cast<const void *>(static_cast<const std::byte *>(definition) + 0x40),
      static_cast<const void *>(context.bytes.data() + 8), costs.data()))
    return Fail(out, "costs_unavailable");
  void *trigger = nullptr;
  if (!Read(definition, 0x2290, trigger)) return Fail(out, "auto_accept_unavailable");
  if (trigger != nullptr) {
    if (!Call(b.interaction.evaluate_trigger, automatic, trigger,
              static_cast<const void *>(context.bytes.data() + 8)))
      return Fail(out, "auto_accept_unavailable");
  } else {
    std::uint8_t scalar = 0;
    if (!Read(definition, 0x2718, scalar)) return Fail(out, "auto_accept_unavailable");
    automatic = scalar != 0;
  }
  std::int64_t recipient_score = 0, intermediary_score = 0;
  std::int64_t *returned = nullptr;
  if (!Call(b.interaction.recipient_answer_score, returned, storage, &recipient_score) ||
      returned != &recipient_score) return Fail(out, "recipient_score_unavailable");
  returned = nullptr;
  if (!Call(b.interaction.intermediary_answer_score, returned, storage, &intermediary_score) ||
      returned != &intermediary_score) return Fail(out, "intermediary_score_unavailable");
  std::uint8_t outer_status = 0;
  if (!Call(b.outer_answer, outer_status, storage, std::uint8_t{1}, std::uint8_t{1},
            static_cast<void *>(nullptr), static_cast<void *>(nullptr)) || outer_status > 2)
    return Fail(out, "outer_answer_unavailable");
  if (!Call(b.interaction.validate, can_send, storage, static_cast<void *>(nullptr)))
    return Fail(out, "can_send_unavailable");
  out.actor_alive = actor_alive;
  out.recipient_alive = recipient_alive;
  out.definition_stable_hash = std::bit_cast<std::uint32_t>(hash);
  out.effective_roles = roles;
  out.declared_option_count = static_cast<std::uint32_t>(option_count);
  out.selected_option_count = selected_count;
  out.special_payload_present = special != nullptr;
  out.shown = shown;
  out.can_send = can_send;
  out.costs_raw = costs;
  out.auto_accept = automatic;
  out.recipient_score_raw = recipient_score;
  out.intermediary_score_raw = intermediary_score;
  out.outer_answer_status = outer_status;
  out.native_context_available = true;
  out.unavailable_reason = nullptr;
  out.ordinary_context_supported = option_count == 0 && special == nullptr;
  out.unsupported_reason = special != nullptr ? "special_payload_unsupported" :
      (option_count != 0 ? "declared_options_unsupported" : nullptr);
  return true;
}

} // namespace

Bindings BindOrdinaryInteractionImage12003(std::uintptr_t base,
                                         std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  auto &i = b.interaction;
  i.enabled = true;
  i.core.enabled = true;
  i.core.game_state_slot = reinterpret_cast<void **>(base + 0x5C68C50);
  i.core.jomini_state_slot = reinterpret_cast<void **>(base + 0x5C6A520);
  i.core.character_storage_slot = reinterpret_cast<void **>(base + 0x5C67568);
  i.core.get_local_player = reinterpret_cast<ck3_12002::GetLocalPlayer>(base + 0x383E2B0);
  i.commands.enabled = true;
  i.commands.command_manager = reinterpret_cast<void *>(base + 0x5CC1240);
  i.commands.queue_owned_command = reinterpret_cast<ck3_12002::QueueOwnedCommand>(base + 0x37F06F0);
  i.refresh = reinterpret_cast<ck3_12002::MarriageRefreshInteractionContext>(base + 0x3078A60);
  i.finalize = reinterpret_cast<ck3_12002::MarriageFinalizeInteractionContext>(base + 0x3078C90);
  i.validate = reinterpret_cast<ck3_12002::MarriageValidateInteractionContext>(base + 0x307C040);
  i.destroy = reinterpret_cast<ck3_12002::MarriageDestroyInteractionContext>(base + 0x30773A0);
  i.recipient_answer_score = reinterpret_cast<ck3_12002::MarriageReadInteractionAnswerScore>(base + 0x307C460);
  i.intermediary_answer_score = reinterpret_cast<ck3_12002::MarriageReadInteractionAnswerScore>(base + 0x307C360);
  i.evaluate_cost = reinterpret_cast<ck3_12002::MarriageEvaluateInteractionCost>(base + 0x310CEE0);
  i.evaluate_trigger = reinterpret_cast<ck3_12002::MarriageEvaluateInteractionTrigger>(base + 0x372DF30);
  i.construct_send_command = reinterpret_cast<ck3_12002::MarriageConstructSendInteractionCommand>(base + 0x2968170);
  i.send_primary_vtable = base + 0x448BCE0;
  i.send_secondary_vtable = base + 0x448BCB0;
  b.get_database = reinterpret_cast<DatabaseGetter>(base + 0x89DA60);
  b.stable_hash = reinterpret_cast<StableHash>(base + 0x3F7E240);
  b.lookup_definition = reinterpret_cast<DefinitionLookup>(base + 0xA055E0);
  b.construct_two_role = reinterpret_cast<TwoRoleConstructor>(base + 0x3076C90);
  b.is_shown = reinterpret_cast<MenuShown>(base + 0x30796B0);
  b.read_option = reinterpret_cast<ReadOption>(base + 0x3078880);
  b.outer_answer = reinterpret_cast<OuterAnswer>(base + 0x307BC80);
  return b;
}

bool ReadOrdinaryInteractionContextV1(const Bindings &b,
    const OrdinaryInteractionRequestV1 &r, Observation &out) noexcept {
  NativeContext context{};
  return Prepare(b, r, context, out);
}

#if defined(XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1)
void PrepareGrantTitlePickerWindowV1(const Bindings &b, const OrdinaryInteractionRequestV1 &r,
    const GrantWindowBindingsV1 &window, GrantPrepareObservationV1 &out) noexcept {
  out = {};
  NativeContext context{};
  if (r.interaction_key != "grant_titles_interaction" || !window.confirmation || !window.handler ||
      !window.install_context || !window.open_window || !window.refresh_window) {
    out.reason = "stock_grant_open_bindings_unavailable"; return;
  }
  if (!Prepare(b, r, context, out.preflight)) { out.reason = out.preflight.unavailable_reason; return; }
  if (!out.preflight.actor_alive.value_or(false) || !out.preflight.recipient_alive.value_or(false) ||
      !out.preflight.shown.value_or(false)) { out.reason = "stock_grant_not_shown_or_alive"; return; }
  void *definition = nullptr; std::uint8_t kind = 255;
  std::uint32_t actor = UINT32_MAX, recipient = UINT32_MAX, effective_actor = UINT32_MAX;
  if (!Read(context.bytes.data(), 0, definition) || !Read(definition, 0x26F9, kind) || kind != 2 ||
      !Read(context.bytes.data(), 0x2D8, actor) || actor != static_cast<std::uint32_t>(r.expected_player_character_id) ||
      !Read(context.bytes.data(), 0x2DC, recipient) || recipient != r.recipient_id ||
      !Read(context.bytes.data(), 0x2EC, effective_actor) || effective_actor != actor) {
    out.reason = "stock_grant_kind_or_roles_changed"; return;
  }
  // AF2810's false branch sends a command. Evaluate its exact embedded
  // confirmation trigger, then call only its true branch's UI leaves.
  bool confirmation_required = false;
  if (!Call(b.interaction.evaluate_trigger, confirmation_required,
      static_cast<const void *>(static_cast<const std::byte *>(definition) + 0x13D8),
      static_cast<const void *>(context.bytes.data() + 8)) || !confirmation_required) {
    out.reason = "stock_grant_confirmation_trigger_not_true"; return;
  }
  bool frame_matches = false;
  if (!b.dispatch_frame_context || !Call(b.verify_dispatch_frame, frame_matches, b.dispatch_frame_context) || !frame_matches) {
    out.reason = "stock_grant_prepare_dispatch_frame_changed"; return;
  }
  out.dispatch_invoked = true;
  // Copy keeps its own native context alive after this stack context is destroyed.
  // enum15 is handler+98+15*8=handler+110, the exact grant slot.
  out.native_call_completed = CallVoid(window.install_context, window.confirmation,
      static_cast<const void *>(context.bytes.data())) &&
      CallVoid(window.open_window, window.handler, std::int32_t{15}, std::int32_t{1}) &&
      CallVoid(window.refresh_window, window.confirmation);
  out.reason = out.native_call_completed ? nullptr : "stock_grant_prepare_result_unknown_no_retry";
}
#endif

void InitiateOrdinaryInteractionV1(const Bindings &b,
    const OrdinaryInteractionRequestV1 &r, SendObservation &out) noexcept {
  out = {};
  NativeContext context{};
  if (!Prepare(b, r, context, out.preflight_context)) {
    out.reason = out.preflight_context.unavailable_reason;
    return;
  }
  const auto &preflight = out.preflight_context;
  if (!preflight.ordinary_context_supported) { out.reason = preflight.unsupported_reason; return; }
  if (!preflight.actor_alive.value_or(false) || !preflight.recipient_alive.value_or(false)) {
    out.reason = "character_not_alive"; return;
  }
  if (!preflight.shown.value_or(false)) { out.reason = "interaction_not_shown"; return; }
  if (!preflight.can_send.value_or(false)) { out.reason = "native_can_send_false"; return; }
  if (b.interaction.construct_send_command == nullptr || !b.interaction.commands.enabled ||
      b.interaction.commands.command_manager == nullptr ||
      b.interaction.commands.queue_owned_command == nullptr ||
      b.interaction.send_primary_vtable == 0 || b.interaction.send_secondary_vtable == 0) {
    out.reason = "send_bindings_unavailable"; return;
  }
  // Final full-generation/life reread on this same owner immediately before
  // command construction. Owner/frame/control verification is held by caller.
  bool actor_alive = false, recipient_alive = false;
  if (!Alive(Resolve(b.interaction.core, static_cast<std::uint32_t>(r.expected_player_character_id)), actor_alive) ||
      !Alive(Resolve(b.interaction.core, r.recipient_id), recipient_alive) ||
      !actor_alive || !recipient_alive) { out.reason = "character_identity_changed"; return; }
  bool frame_matches = false;
  if (b.dispatch_frame_context == nullptr ||
      !Call(b.verify_dispatch_frame, frame_matches, b.dispatch_frame_context) || !frame_matches) {
    out.reason = "dispatch_frame_unavailable"; return;
  }
  NativeCommand command{};
  command.destroy = b.interaction.destroy;
  void *constructed = nullptr;
  if (!Call(b.interaction.construct_send_command, constructed, command.bytes.data(),
            static_cast<const void *>(context.bytes.data())) || constructed != command.bytes.data()) {
    out.reason = "send_constructor_unavailable"; return;
  }
  command.constructed = true;
  std::uintptr_t primary = 0, secondary = 0;
  if (!Read(command.bytes.data(), 0, primary) || primary != b.interaction.send_primary_vtable ||
      !Read(command.bytes.data(), 0x18, secondary) || secondary != b.interaction.send_secondary_vtable) {
    out.reason = "send_vtable_identity_mismatch"; return;
  }
  // Command construction also invokes native answer getters. Recheck the
  // actual owner frame after these calls, immediately before the single queue.
  frame_matches = false;
  if (!Call(b.verify_dispatch_frame, frame_matches, b.dispatch_frame_context) || !frame_matches) {
    out.reason = "dispatch_frame_changed"; return;
  }
  ck3_12002::CommandSubmitResult result = ck3_12002::CommandSubmitResult::unavailable;
  out.dispatch_invoked = true;
  out.native_call_completed = Call(ck3_12002::SubmitCommandCopy, result,
      b.interaction.commands, static_cast<const void *>(command.bytes.data()), std::uint32_t{0x0E});
  if (!out.native_call_completed) {
    out.native_queue_result = QueueResult::unavailable;
    out.reason = "native_dispatch_did_not_complete";
    return;
  }
  switch (result) {
  case ck3_12002::CommandSubmitResult::submitted:
    out.native_queue_result = QueueResult::submitted; out.reason = nullptr; break;
  case ck3_12002::CommandSubmitResult::rejected:
    out.native_queue_result = QueueResult::rejected; out.reason = "native_queue_rejected"; break;
  default:
    out.native_queue_result = QueueResult::unavailable; out.reason = "native_queue_unavailable"; break;
  }
}

} // namespace xar::ck3_12003::ordinary_interaction
