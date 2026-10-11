#include "xar_bridge/ordinary_character_interaction_v1.hpp"
#include "xar_bridge/ck3_12004_interaction_context.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"
#include "xar_bridge/ck3_12004_phase.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_prisoner_ransom_action.hpp"

#include <bit>
#include <cstring>
#include <functional>
#include <limits>
#include <utility>

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
  const bool has_pair = r.child_full_id.has_value();
  const bool has_options = r.requested_option_keys.has_value();
  if (has_pair != r.guardian_full_id.has_value() ||
      ((has_pair || has_options) && r.interaction_key != "educate_child_interaction"))
    return false;
  if (has_pair && (*r.child_full_id == 0 || *r.child_full_id == UINT32_MAX ||
                   *r.guardian_full_id == 0 || *r.guardian_full_id == UINT32_MAX))
    return false;
  if (has_options) {
    for (const auto &key : *r.requested_option_keys) {
      if (key.empty() || key.size() > 128) return false;
      for (const unsigned char c : key)
        if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
              (c >= '0' && c <= '9') || c == '_')) return false;
    }
  }
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

template <typename T>
bool ReadEducationField(const void *base, std::size_t offset, T &value) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  const auto maximum = std::numeric_limits<std::uintptr_t>::max();
  if (address == 0 || offset > maximum - address ||
      sizeof(T) - 1 > maximum - (address + offset)) return false;
  return Read(base, offset, value);
}

// Read one admitted Character total-skill value through the existing actual4 binder.
// This source is a native API observation, separate from education expression identity.
bool ReadRequestGuardianTotalMartialCallback(std::uintptr_t base,
    const void *character, std::uint32_t full_id, std::int32_t &value) noexcept {
#if defined(_MSC_VER) && defined(_WIN32)
  if (base == 0 || character == nullptr) return false;
  const auto native = ck3_12004::BindCommanderImage12004(
      base, ck3_12004::kExecutableSha256);
  if (!native.enabled || !native.current_total_martial_observer_enabled ||
      native.get_current_total_skill == nullptr) return false;
  auto *target = const_cast<void *>(character);
  std::uint32_t observed_id = UINT32_MAX;
  bool alive = false;
  if (!ReadEducationField(character, 0x18, observed_id) || observed_id != full_id ||
      !Alive(target, alive) || !alive) return false;
  std::int32_t sampled = 0;
  if (!Call(native.get_current_total_skill, sampled, target, std::int32_t{1}))
    return false;
  alive = false;
  if (!ReadEducationField(character, 0x18, observed_id) || observed_id != full_id ||
      !Alive(target, alive) || !alive) return false;
  value = sampled;
  return true;
#else
  (void)base; (void)character; (void)full_id; (void)value;
  return false;
#endif
}

// Consumed by Prepare on its existing owned context after validate returns.
// Does not invoke option getters, constructors or option setters.
void CopyEducationOptionRows(const Bindings &b, const void *storage, void *expected_definition,
    void *expected_option_data, std::int32_t expected_count,
    const std::array<std::optional<std::uint32_t>, 6> &expected_roles,
    EducationOptionRowsV1 &out) noexcept {
  out = {};
  out.unavailable_reason = "education_option_rows_copy_unavailable";
  try {
    void *definition = nullptr, *option_data = nullptr, *bank = nullptr;
    std::int32_t declared_count = -1, bank_count = -1;
    if (!ReadEducationField(storage, 0, definition) || definition != expected_definition ||
        !ReadEducationField(definition, 0x2258, option_data) || option_data != expected_option_data ||
        !ReadEducationField(definition, 0x2264, declared_count) || declared_count != expected_count ||
        declared_count < 0 || declared_count > 4096 ||
        !ReadEducationField(storage, 0x300, bank) ||
        !ReadEducationField(storage, 0x30C, bank_count) || bank_count < declared_count ||
        (declared_count != 0 && (bank == nullptr || option_data == nullptr))) return;
    auto roles_match = [&]() noexcept {
      for (std::size_t i = 0; i < expected_roles.size(); ++i) {
        std::int32_t id = -1;
        if (!ReadEducationField(storage, 0x2D8 + 4 * i, id)) return false;
        std::optional<std::uint32_t> copied;
        if (id != -1) copied = std::bit_cast<std::uint32_t>(id);
        if (copied != expected_roles[i]) return false;
      }
      return true;
    };
    if (!roles_match()) return;
    std::vector<EducationOptionRowV1> rows;
    rows.reserve(static_cast<std::size_t>(declared_count));
    for (std::int32_t i = 0; i < declared_count; ++i) {
      EducationOptionRowV1 row{};
      row.declared_ordinal = static_cast<std::uint32_t>(i);
      if (!ReadEducationField(option_data, static_cast<std::size_t>(i) * 0x730 + 0x368,
                              row.flag_full_u32) ||
          !ReadEducationField(bank, static_cast<std::size_t>(i), row.bank_value_u8)) return;
      row.ordinal_selected = row.bank_value_u8 == 1;
      rows.push_back(std::move(row));
    }
    for (auto &row : rows) {
      for (const auto &first : rows) {
        if (first.flag_full_u32 == row.flag_full_u32) {
          row.selected = first.ordinal_selected;
          break;
        }
      }
    }
    // Existing exact .4 forward lookup: all four views refer to NUL-terminated
    // string literals. BYTE+0xC is zero; no old native image is called.
    struct BorrowedScriptIdentifierView {
      const char *data;
      std::int32_t length;
      std::uint8_t owned;
      std::uint8_t padding[3];
    };
    static_assert(sizeof(BorrowedScriptIdentifierView) == 16);
    constexpr std::array<std::string_view, 4> keys{
        "convert_culture", "convert_faith", "send_to_university", "education_hook"};
    std::array<std::optional<std::uint32_t>, 4> actual_ids{};
    void *table = nullptr;
    if (Call(b.get_script_identifier_table, table) && table != nullptr) {
      for (std::size_t i = 0; i < keys.size(); ++i) {
        const BorrowedScriptIdentifierView view{keys[i].data(),
            static_cast<std::int32_t>(keys[i].size()), 0, {0, 0, 0}};
        std::int32_t id = -1;
        std::int32_t *returned = nullptr;
        if (Call(b.lookup_script_identifier_id, returned, table, &id,
                 static_cast<const void *>(&view)) && returned == &id && id != -1)
          actual_ids[i] = std::bit_cast<std::uint32_t>(id);
      }
    }
    for (auto &row : rows) {
      std::optional<std::size_t> matching_key;
      bool ambiguous = false;
      for (std::size_t i = 0; i < actual_ids.size(); ++i) {
        if (actual_ids[i] && *actual_ids[i] == row.flag_full_u32) {
          if (matching_key) ambiguous = true;
          else matching_key = i;
        }
      }
      if (matching_key && !ambiguous)
        row.canonical_flag_key = std::string(keys[*matching_key]);
    }
    void *definition_after = nullptr, *data_after = nullptr, *bank_after = nullptr;
    std::int32_t count_after = -1, bank_count_after = -1;
    if (!ReadEducationField(storage, 0, definition_after) || definition_after != definition ||
        !ReadEducationField(definition, 0x2258, data_after) || data_after != option_data ||
        !ReadEducationField(definition, 0x2264, count_after) || count_after != declared_count ||
        !ReadEducationField(storage, 0x300, bank_after) || bank_after != bank ||
        !ReadEducationField(storage, 0x30C, bank_count_after) || bank_count_after != bank_count ||
        !roles_match()) return;
    for (const auto &row : rows) {
      std::uint32_t flag_after = 0;
      std::uint8_t value_after = 0;
      if (!ReadEducationField(option_data, static_cast<std::size_t>(row.declared_ordinal) * 0x730 + 0x368,
                              flag_after) || flag_after != row.flag_full_u32 ||
          !ReadEducationField(bank, row.declared_ordinal, value_after) ||
          value_after != row.bank_value_u8) return;
    }
    out.rows = std::move(rows);
    out.available = true;
    out.unavailable_reason = nullptr;
  } catch (...) {
    out = {};
    out.unavailable_reason = "education_option_rows_copy_unavailable";
  }
}

bool ReadEffectiveEducationRoles(void *storage,
    std::array<std::optional<std::uint32_t>, 6> &roles) noexcept {
  for (std::size_t i = 0; i < roles.size(); ++i) {
    std::int32_t id = -1;
    if (!Read(storage, 0x2D8 + sizeof(id) * i, id)) return false;
    roles[i] = id == -1 ? std::optional<std::uint32_t>{} :
                         std::optional<std::uint32_t>{std::bit_cast<std::uint32_t>(id)};
  }
  return true;
}

bool HasEducationRequest(const OrdinaryInteractionRequestV1 &r) noexcept {
  return r.child_full_id.has_value() || r.requested_option_keys.has_value();
}

// Only this existing temporary context is modified. The native selector takes
// the original row ordinal, including every matching duplicate flag row.
bool ApplyEducationOptionIntent(const Bindings &b, void *storage,
    const OrdinaryInteractionRequestV1 &r, const EducationOptionRowsV1 &rows,
    bool &applied, const char *&reason) noexcept {
  applied = !r.requested_option_keys.has_value();
  reason = nullptr;
  if (applied) return true;
  if (!rows.available) {
    reason = rows.unavailable_reason;
    return true;
  }
  if (!b.clear_local_options || !b.select_local_option) {
    reason = "education_option_setters_unavailable";
    return true;
  }
  try {
    const auto &keys = *r.requested_option_keys;
    for (const auto &key : keys) {
      bool found = false;
      for (const auto &row : rows.rows)
        if (row.canonical_flag_key && *row.canonical_flag_key == key) found = true;
      if (!found) {
        reason = "requested_education_option_key_unavailable";
        return true;
      }
    }
    std::vector<std::int32_t> ordinals;
    for (const auto &row : rows.rows) {
      if (!row.canonical_flag_key) continue;
      bool requested = false;
      for (const auto &key : keys)
        if (*row.canonical_flag_key == key) requested = true;
      if (requested) ordinals.push_back(static_cast<std::int32_t>(row.declared_ordinal));
    }
    if (!CallVoid(b.clear_local_options, storage)) {
      reason = "education_option_clear_unavailable";
      return false;
    }
    for (const auto ordinal : ordinals) {
      if (!CallVoid(b.select_local_option, storage, ordinal)) {
        reason = "education_option_selection_unavailable";
        return false;
      }
    }
    if (!CallVoid(b.interaction.refresh, storage, true) ||
        !CallVoid(b.interaction.finalize, storage)) {
      reason = "education_option_finalization_unavailable";
      return false;
    }
    applied = true;
    return true;
  } catch (...) {
    reason = "education_option_intent_copy_unavailable";
    return false;
  }
}

void CompleteEducationRequestMaterialization(const OrdinaryInteractionRequestV1 &r,
    const std::array<std::optional<std::uint32_t>, 6> &roles,
    const EducationOptionRowsV1 &rows, bool options_applied,
    const char *option_reason, EducationRequestMaterializationV1 &out) noexcept {
  out = {};
  if (r.child_full_id)
    out.pair_matches = roles[2] == r.guardian_full_id && roles[3] == r.child_full_id;
  if (r.requested_option_keys && rows.available && options_applied) {
    bool match = true, known = true;
    for (const auto &row : rows.rows) {
      if (!row.ordinal_selected) continue;
      if (!row.canonical_flag_key) { known = false; continue; }
      bool requested = false;
      for (const auto &key : *r.requested_option_keys)
        if (*row.canonical_flag_key == key) requested = true;
      if (!requested) match = false;
    }
    for (const auto &key : *r.requested_option_keys) {
      bool selected = false;
      for (const auto &row : rows.rows)
        if (row.ordinal_selected && row.canonical_flag_key &&
            *row.canonical_flag_key == key) selected = true;
      if (!selected) match = false;
    }
    if (known) out.option_keys_match = match;
  }
  if (out.pair_matches && !*out.pair_matches)
    out.unavailable_reason = "education_requested_pair_changed";
  else if (r.requested_option_keys && !options_applied)
    out.unavailable_reason = option_reason ? option_reason : "education_option_intent_unavailable";
  else if (!rows.available)
    out.unavailable_reason = rows.unavailable_reason;
  else if (r.requested_option_keys && !out.option_keys_match)
    out.unavailable_reason = "selected_education_option_key_unavailable";
  else if (out.option_keys_match && !*out.option_keys_match)
    out.unavailable_reason = "education_requested_option_keys_changed";
  else {
    out.available = true;
    out.unavailable_reason = nullptr;
  }
}

bool Prepare(const Bindings &b, const OrdinaryInteractionRequestV1 &r,
             NativeContext &context, Observation &out) noexcept {
  out = {};
  if (!Valid(r)) return Fail(out, "request_invalid");
  const bool education = b.education_rows_actual_12004 &&
      r.interaction_key == "educate_child_interaction";
  if (HasEducationRequest(r) && !education)
    return Fail(out, "education_request_bindings_unavailable");
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
  // Preserve the actual native redirect: the request's original recipient is
  // a candidate input, while the effective primary recipient may be its liege.
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
  if (education && r.child_full_id &&
      (roles[2] != r.guardian_full_id || roles[3] != r.child_full_id)) {
    // Reuse an already matching redirected context. Only a different requested
    // secondary pair needs reconstruction, using its observed primary roles.
    if (!roles[0] || !roles[1])
      return Fail(out, "education_default_primary_roles_unavailable");
    const auto primary_actor = std::bit_cast<std::int32_t>(*roles[0]);
    const auto primary_recipient = std::bit_cast<std::int32_t>(*roles[1]);
    const auto intermediary = roles[4] ? std::bit_cast<std::int32_t>(*roles[4]) :
                                       std::int32_t{-1};
    const bool destroyed = CallVoid(context.destroy, storage);
    context.constructed = false;
    context.bytes.fill(std::byte{0});
    if (!destroyed) return Fail(out, "education_default_context_cleanup_unavailable");
    constructed = nullptr;
    if (!Call(b.interaction.construct_all_roles, constructed, storage, definition,
              primary_actor, primary_recipient,
              std::bit_cast<std::int32_t>(*r.guardian_full_id),
              std::bit_cast<std::int32_t>(*r.child_full_id), intermediary,
              static_cast<void *>(nullptr)) || constructed != storage)
      return Fail(out, "education_requested_context_unavailable");
    context.constructed = true;
    if (!CallVoid(b.interaction.refresh, storage, true) ||
        !CallVoid(b.interaction.finalize, storage))
      return Fail(out, "education_requested_context_finalization_unavailable");
    if (!ReadEffectiveEducationRoles(storage, roles))
      return Fail(out, "education_requested_roles_unavailable");
  }
  void *option_data = nullptr, *special = nullptr;
  std::int32_t option_count = -1;
  if (!Read(definition, 0x2258, option_data) ||
      !Read(definition, 0x2264, option_count) || option_count < 0 ||
      option_count > 4096 || (option_count != 0 && option_data == nullptr) ||
      !Read(storage, 0x330, special))
    return Fail(out, "ordinary_shape_sample_unavailable");
  bool options_applied = !r.requested_option_keys.has_value();
  const char *option_reason = nullptr;
  if (education && r.requested_option_keys) {
    EducationOptionRowsV1 initial_rows{};
    CopyEducationOptionRows(b, storage, definition, option_data, option_count, roles, initial_rows);
    if (!ApplyEducationOptionIntent(b, storage, r, initial_rows, options_applied, option_reason))
      return Fail(out, option_reason);
    if (!ReadEffectiveEducationRoles(storage, roles) ||
        !Read(definition, 0x2258, option_data) ||
        !Read(definition, 0x2264, option_count) || option_count < 0 ||
        option_count > 4096 || (option_count != 0 && option_data == nullptr) ||
        !Read(storage, 0x330, special))
      return Fail(out, "education_option_materialization_readback_unavailable");
  }
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
  if (education) {
    if (!ReadEffectiveEducationRoles(storage, roles))
      return Fail(out, "education_final_roles_unavailable");
    if (!Read(storage, 0x330, special))
      return Fail(out, "education_final_payload_unavailable");
    CopyEducationOptionRows(b, storage, definition, option_data, option_count, roles,
                            out.education_option_rows);
    CompleteEducationRequestMaterialization(r, roles, out.education_option_rows,
        options_applied, option_reason, out.education_request_materialization);
    const ck3_12004::RequestGuardianSkillAccess12004 skill_access{
        const_cast<ck3_12002::CoreBindings *>(&b.interaction.core),
        [](void *opaque, std::uint32_t full_id) noexcept -> void * {
          return Resolve(*static_cast<const ck3_12002::CoreBindings *>(opaque), full_id);
        },
        [](void *, const void *character, std::size_t offset,
           std::int32_t &value) noexcept -> bool {
          return ReadEducationField(character, offset, value);
        }, b.module_base,
        [](std::uintptr_t base, const void *character, const char *key,
           bool &value) noexcept -> bool {
          if (base == 0) return false;
          const auto traits = ck3_12004::phase_character::BindImage(
              base, ck3_12004::kExecutableSha256);
          void *database = nullptr, *definition = nullptr;
          if (!traits.enabled ||
              !Read(reinterpret_cast<const void *>(base),
                    ck3_12004::phase_character::kTraitDatabaseSlotRva, database) ||
              database == nullptr ||
              !Call(&ck3_12002::phase_character::FindUniqueTraitDefinition,
                    definition, database, std::string_view{key}) ||
              definition == nullptr) return false;
          bool completed = false;
          return Call(&ck3_12002::phase_character::ReadTraitPresence, completed,
                      traits, const_cast<void *>(character),
                      std::span<void *const>{&definition, 1}, std::ref(value)) &&
                 completed;
        },
        [](std::uintptr_t base, const void *character, std::uint32_t full_id,
           ck3_12002::phase_culture::CharacterCultureParameterObservation &field) noexcept -> bool {
          if (base == 0) {
            field.unavailable_reason = "culture_parameter_bindings_unavailable";
            return false;
          }
          const auto phase = ck3_12004::BindPhaseImage12004(
              base, ck3_12004::kExecutableSha256);
          bool completed = false;
          return Call(&ck3_12002::phase_culture::ReadPhaseCharacterCultureParameter,
                      completed, std::cref(phase.culture), character, full_id,
                      std::string_view{"better_ward_education"}, std::ref(field)) &&
                 completed;
        }, b.education_rows_actual_12004 ? ReadRequestGuardianTotalMartialCallback : nullptr};
    out.request_guardian_skill_inputs = ck3_12004::ReadRequestGuardianSkillInputs12004(
        skill_access, roles[3], roles[2], r.expected_revision);
    // Additional getter calls must keep the original final request roles stable.
    // A failed bookend invalidates this optional observation alone.
    auto &total = out.request_guardian_skill_inputs->total_martial_callback_v1;
    if (total) {
      std::array<std::optional<std::uint32_t>, 6> roles_after{};
      if (!ReadEffectiveEducationRoles(storage, roles_after) || roles_after != roles) {
        total->available = false;
        total->value.reset();
        total->unavailable_reason = "total_martial_callback_roles_changed";
      }
    }
  }
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
  const bool request_materialized = !HasEducationRequest(r) ||
      out.education_request_materialization.available;
  const bool education_options_copy_supported = b.education_rows_actual_12004 &&
      r.interaction_key == "educate_child_interaction" &&
      out.education_option_rows.available && out.education_request_materialization.available;
  out.ordinary_context_supported = (option_count == 0 || education_options_copy_supported) &&
      special == nullptr && request_materialized;
  out.unsupported_reason = special != nullptr ? "special_payload_unsupported" :
      (!request_materialized ? out.education_request_materialization.unavailable_reason :
       (option_count != 0 && !education_options_copy_supported) ? "declared_options_unsupported" : nullptr);
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

Bindings BindOrdinaryInteractionImage12004(std::uintptr_t base,
                                          std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != ck3_12004::kExecutableSha256) return b;
  const auto context = ck3_12004::BindInteractionContext12004(base, sha);
  const auto commands = ck3_12004::BindCommandImage12004(base, sha);
  if (!context.enabled || !context.context.enabled || !commands.enabled) return b;
  b.interaction = context.context;
  auto &i = b.interaction;
  i.commands = commands;
  i.intermediary_answer_score = reinterpret_cast<ck3_12002::MarriageReadInteractionAnswerScore>(base + 0x307C340);
  i.construct_send_command = reinterpret_cast<ck3_12002::MarriageConstructSendInteractionCommand>(
      base + ck3_12004::kPrisonerRansomSendConstructorRva12004);
  i.send_primary_vtable = base + ck3_12004::kPrisonerRansomSendPrimaryVtableRva12004;
  i.send_secondary_vtable = base + ck3_12004::kPrisonerRansomSendSecondaryVtableRva12004;
  b.education_rows_actual_12004 = true;
  b.module_base = base;
  b.clear_local_options = context.clear_local_options;
  b.select_local_option = context.select_local_option;
  b.get_script_identifier_table = context.get_script_identifier_table;
  b.lookup_script_identifier_id = context.lookup_script_identifier_id;
  b.get_database = context.get_database;
  b.stable_hash = context.stable_hash;
  b.lookup_definition = context.lookup_definition;
  b.construct_two_role = context.construct_two_role;
  b.is_shown = reinterpret_cast<MenuShown>(base + 0x3079690);
  b.read_option = reinterpret_cast<ReadOption>(base + 0x3078860);
  b.outer_answer = reinterpret_cast<OuterAnswer>(base + ck3_12004::kInteractionEvaluateAnswerRva12004);
  b.enabled = true;
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
      static_cast<void *>(static_cast<std::byte *>(definition) + 0x13D8),
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
