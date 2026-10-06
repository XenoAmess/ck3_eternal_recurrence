#include "xar_bridge/ck3_12003_player_seek_indulgences_terms.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <sstream>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::seek_indulgences {
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
bool DefinitionMatches(void *definition, std::int32_t hash) noexcept {
  std::int32_t stored_hash = 0;
  std::uint64_t size = 0, capacity = 0;
  if (!Read(definition, 0x14, stored_hash) || stored_hash != hash ||
      !Read(definition, 0x28, size) || !Read(definition, 0x30, capacity) ||
      size != kInteractionKey.size() || size > capacity) return false;
  const char *data = reinterpret_cast<const char *>(definition) + 0x18;
  if (capacity >= 16 && !Read(definition, 0x18, data)) return false;
  if (data == nullptr) return false;
  for (std::size_t i = 0; i < kInteractionKey.size(); ++i) {
    char value = 0;
    if (!Read(data, i, value) || value != kInteractionKey[i]) return false;
  }
  return true;
}
struct NativeContext {
  alignas(8) std::array<std::byte, 0x338> bytes{};
  ck3_12002::MarriageDestroyInteractionContext destroy = nullptr;
  bool constructed = false;
  ~NativeContext() {
    if (constructed) CallVoid(destroy, bytes.data());
  }
};
void Success(Sample &sample) noexcept {
  sample.available = true;
  sample.reason = "none";
}
void Unavailable(Context &out, const char *reason) noexcept {
  out.identity.reason = reason;
  out.options.reason = reason;
  out.shown.reason = reason;
  out.can_send.reason = reason;
  out.unavailable_reason = reason;
}
bool ReadRoles(const void *context, Identity &identity) noexcept {
  std::array<std::int32_t, 6> roles{};
  for (std::size_t i = 0; i < roles.size(); ++i)
    if (!Read(context, 0x2D8 + sizeof(std::int32_t) * i, roles[i])) return false;
  identity.effective_actor_id = roles[0];
  identity.effective_recipient_id = roles[1];
  identity.secondary_actor_id = roles[2];
  identity.secondary_recipient_id = roles[3];
  identity.intermediary_id = roles[4];
  identity.sixth_role_id = roles[5];
  return true;
}
void Quote(std::ostream &out, std::string_view text) {
  out << '"';
  for (const char value : text) {
    if (value == '"' || value == '\\') out << '\\';
    out << value;
  }
  out << '"';
}
template <typename T>
void Optional(std::ostream &out, const std::optional<T> &value) {
  if (!value) out << "null";
  else out << +*value;
}
void Optional(std::ostream &out, const std::optional<bool> &value) {
  if (!value) out << "null";
  else out << (*value ? "true" : "false");
}
void SampleFields(std::ostream &out, const Sample &sample) {
  out << "\"available\":" << (sample.available ? "true" : "false") <<
      ",\"reason\":";
  Quote(out, sample.reason);
}
void BoolFields(std::ostream &out, const BoolSample &sample) {
  SampleFields(out, sample);
  out << ",\"value\":";
  Optional(out, sample.available ? sample.value : std::optional<bool>{});
}
} // namespace

Bindings BindSeekIndulgencesTermsImage12003(std::uintptr_t base,
    std::string_view sha, const ck3_12002::ContextBindings &interaction) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.module_base = base;
  b.interaction = interaction;
  b.get_database = reinterpret_cast<DatabaseGetter>(base + 0x89DA60);
  b.stable_hash = reinterpret_cast<StableHash>(base + 0x3F7E240);
  b.lookup_definition = reinterpret_cast<DefinitionLookup>(base + 0xA055E0);
  b.construct_two_role = reinterpret_cast<TwoRoleConstructor>(base + 0x3076C90);
  b.is_shown = reinterpret_cast<MenuShown>(base + 0x30796B0);
  b.set_option = reinterpret_cast<SetOption>(base + 0x30788E0);
  b.read_option = reinterpret_cast<ReadOption>(base + 0x3078880);
  return b;
}

bool ReadSeekIndulgencesTerms12003(const Bindings &b, void *player,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    std::uint32_t requested, Context &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = date;
  out.played_character_id = actor;
  out.identity.requested_recipient_character_id = requested;
  Unavailable(out, "context_unavailable");
  if (!b.enabled) {
    Unavailable(out, "bindings_unavailable");
    return false;
  }
  std::int32_t actual_actor = -1;
  if (actor == -1 || !Read(player, 0x18, actual_actor) || actual_actor != actor) {
    Unavailable(out, "played_character_unavailable");
    return false;
  }
  if (requested == UINT32_MAX) {
    Unavailable(out, "requested_recipient_unavailable");
    return false;
  }
  void *database = nullptr, *definition = nullptr;
  std::int32_t definition_hash = 0;
  if (!Call(b.get_database, database) || database == nullptr ||
      !Call(b.stable_hash, definition_hash, database, kInteractionKey.data(),
            static_cast<std::uint32_t>(kInteractionKey.size())) ||
      !Call(b.lookup_definition, definition, database, definition_hash) ||
      !DefinitionMatches(definition, definition_hash)) {
    Unavailable(out, "interaction_definition_unavailable");
    return false;
  }
  out.definition_stable_hash = static_cast<std::uint32_t>(definition_hash);
  NativeContext context{};
  context.destroy = b.interaction.destroy;
  void *constructed = nullptr;
  std::int32_t native_recipient = -1;
  std::memcpy(&native_recipient, &requested, sizeof(native_recipient));
  if (context.destroy == nullptr ||
      !Call(b.construct_two_role, constructed, context.bytes.data(), definition,
          actor, native_recipient, static_cast<void *>(nullptr), true) ||
      constructed != context.bytes.data()) {
    Unavailable(out, "interaction_context_unavailable");
    return false;
  }
  context.constructed = true;
  void *storage = context.bytes.data();
  void *option_data = nullptr;
  std::int32_t option_count = -1;
  bool options_prepared = Read(definition, 0x2258, option_data) &&
      Read(definition, 0x2264, option_count) && option_count >= 0 &&
      (option_count == 0 || option_data != nullptr);
  if (options_prepared) {
    out.options.declared_count = static_cast<std::uint32_t>(option_count);
    for (std::int32_t i = 0; i < option_count; ++i) {
      std::uint32_t flag = 0;
      if (!Read(option_data, static_cast<std::size_t>(i) * 0x730 + 0x368, flag) ||
          !CallVoid(b.set_option, storage, flag, false)) {
        options_prepared = false;
        break;
      }
    }
  }
  if (!CallVoid(b.interaction.refresh, storage, true) ||
      !CallVoid(b.interaction.finalize, storage) ||
      !ReadRoles(storage, out.identity)) {
    Unavailable(out, "interaction_finalization_unavailable");
    return false;
  }
  Success(out.identity);
  out.options.reason = "ordinary_option_readback_unavailable";
  if (options_prepared) {
    std::uint32_t selected_count = 0;
    bool readback = true;
    for (std::int32_t i = 0; i < option_count; ++i) {
      std::uint32_t flag = 0;
      bool selected = false;
      if (!Read(option_data, static_cast<std::size_t>(i) * 0x730 + 0x368, flag) ||
          !Call(b.read_option, selected, storage, flag)) {
        readback = false;
        break;
      }
      if (selected) ++selected_count;
    }
    if (readback) {
      out.options.selected_count = selected_count;
      out.options.all_unselected = selected_count == 0;
      Success(out.options);
    }
  }
  bool shown = false, legal = false;
  out.shown.reason = "native_evaluation_unavailable";
  if (Call(b.is_shown, shown, storage)) {
    out.shown.value = shown;
    Success(out.shown);
  }
  // Native CanSend owns the overall cooldown, excommunication and all other
  // current rules. A false final result is a complete read-only observation.
  out.can_send.reason = "native_evaluation_unavailable";
  if (Call(b.interaction.validate, legal, storage, static_cast<void *>(nullptr))) {
    out.can_send.value = legal;
    Success(out.can_send);
  }
  out.available = out.identity.available && out.options.available &&
      out.options.all_unselected.value_or(false) && out.shown.available &&
      out.can_send.available;
  out.unavailable_reason = out.available ? "none" : "one_or_more_samples_unavailable";
  return out.available;
}

std::string SerializeSeekIndulgencesTerms12003(const Context &c) {
  std::ostringstream out;
  out << "{\"schema\":"; Quote(out, kSchema);
  out << ",\"game_version\":\"1.20.0.3\",\"executable_sha256\":";
  Quote(out, kExecutableSha256);
  out << ",\"read_only\":true,\"available\":" <<
      (c.available ? "true" : "false") << ",\"unavailable_reason\":";
  Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" <<
      c.date_raw << ",\"played_character_id\":" << c.played_character_id <<
      ",\"definition_key\":"; Quote(out, kInteractionKey);
  out << ",\"definition_stable_hash\":"; Optional(out, c.definition_stable_hash);
  out << ",\"identity\":{"; SampleFields(out, c.identity);
  out << ",\"requested_recipient_character_id\":" <<
      c.identity.requested_recipient_character_id;
#define XAR_INDULGENCE_ROLE(name) out << ",\"" #name "\":"; \
  Optional(out, c.identity.available ? c.identity.name : std::optional<std::int32_t>{})
  XAR_INDULGENCE_ROLE(effective_actor_id); XAR_INDULGENCE_ROLE(effective_recipient_id);
  XAR_INDULGENCE_ROLE(secondary_actor_id); XAR_INDULGENCE_ROLE(secondary_recipient_id);
  XAR_INDULGENCE_ROLE(intermediary_id); XAR_INDULGENCE_ROLE(sixth_role_id);
#undef XAR_INDULGENCE_ROLE
  out << "},\"options\":{"; SampleFields(out, c.options);
  out << ",\"declared_count\":";
  Optional(out, c.options.available ? c.options.declared_count : std::optional<std::uint32_t>{});
  out << ",\"selected_count\":";
  Optional(out, c.options.available ? c.options.selected_count : std::optional<std::uint32_t>{});
  out << ",\"all_unselected\":";
  Optional(out, c.options.available ? c.options.all_unselected : std::optional<bool>{});
  out << "},\"shown\":{"; BoolFields(out, c.shown);
  out << "},\"can_send\":{"; BoolFields(out, c.can_send);
  out << "}}";
  return out.str();
}

} // namespace xar::ck3_12003::religion::seek_indulgences
