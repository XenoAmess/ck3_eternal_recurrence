#include "xar_bridge/ck3_12003_player_hof_gold_context.hpp"

#include <cstddef>
#include <cstring>
#include <sstream>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::hof_gold {
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
bool ReadHeads(const Bindings &b, std::uint64_t epoch, HeadContext &heads) noexcept {
  if (b.read_heads == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return b.read_heads(b.heads, epoch, heads);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool NamedValue(const Bindings &b, const void *scope, std::uint32_t root,
                std::uint32_t actor, std::uint32_t hash,
                std::int64_t &value) noexcept {
  if (b.read_named_fixed == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return b.read_named_fixed(b.module_base, scope, root, actor, root,
                              kGoldValueKey, hash, value);
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
void ContextUnavailable(Context &out, const char *reason) noexcept {
  out.options.reason = reason;
  out.shown.reason = reason;
  out.can_send.reason = reason;
  out.declared_costs.reason = reason;
  out.auto_accept.reason = reason;
  out.acceptance_preview.recipient_score_reason = reason;
  out.acceptance_preview.intermediary_score_reason = reason;
  out.acceptance_preview.outer_reason = reason;
  out.gold_proceeds.reason = reason;
  out.acceptance_effect_consequence.reason = reason;
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
void SampleBool(MenuShown fn, void *context, BoolSample &out) noexcept {
  bool value = false;
  out.reason = "native_evaluation_unavailable";
  if (Call(fn, value, context)) { out.value = value; Success(out); }
}

void Quote(std::ostream &out, std::string_view text) {
  out << '"';
  for (const char value : text) {
    if (value == '"' || value == '\\') out << '\\';
    out << value;
  }
  out << '"';
}
template <typename T> void Optional(std::ostream &out, const std::optional<T> &v) {
  if (!v) out << "null";
  else out << +*v;
}
void Optional(std::ostream &out, const std::optional<bool> &v) {
  if (!v) out << "null";
  else out << (*v ? "true" : "false");
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

Bindings BindHeadOfFaithGoldImage12003(std::uintptr_t base, std::string_view sha,
    const ck3_12002::ContextBindings &interaction, const HeadBindings &heads,
    HeadReader read_heads, NamedFixedReader read_named_fixed) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.module_base = base;
  b.interaction = interaction;
  b.heads = heads;
  b.read_heads = read_heads;
  b.read_named_fixed = read_named_fixed;
  b.get_database = reinterpret_cast<DatabaseGetter>(base + 0x89DA60);
  b.stable_hash = reinterpret_cast<StableHash>(base + 0x3F7E240);
  b.lookup_definition = reinterpret_cast<DefinitionLookup>(base + 0xA055E0);
  b.construct_two_role = reinterpret_cast<TwoRoleConstructor>(base + 0x3076C90);
  b.is_shown = reinterpret_cast<MenuShown>(base + 0x30796B0);
  b.set_option = reinterpret_cast<SetOption>(base + 0x30788E0);
  b.read_option = reinterpret_cast<ReadOption>(base + 0x3078880);
  b.named_database = reinterpret_cast<DatabaseGetter>(base + 0xA07970);
  b.outer_answer = reinterpret_cast<OuterAnswer>(base + 0x307BC80);
  return b;
}

bool ReadHeadOfFaithGoldContext12003(const Bindings &b, void *player,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    Context &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = date;
  out.played_character_id = actor;
  ContextUnavailable(out, "context_unavailable");
  if (!b.enabled) { out.unavailable_reason = "bindings_unavailable"; return false; }
  std::int32_t actual_actor = -1;
  if (actor < 0 || !Read(player, 0x18, actual_actor) || actual_actor != actor) {
    out.identity.reason = "played_character_unavailable";
    out.unavailable_reason = out.identity.reason;
    return false;
  }
  HeadContext heads{};
  const bool heads_read = ReadHeads(b, epoch, heads);
  out.identity.actor_rite_id = heads.actor_rite_id;
  out.identity.faith_id = heads.faith_id;
  out.identity.faith_main_rite_id = heads.faith_main_rite_id;
  out.identity.head_title_id = heads.faith_religious_head_title_id;
  out.identity.requested_head_character_id =
      heads.faith_religious_head_holder_character_id;
  if (!heads_read || heads.capture_epoch != epoch || heads.date_raw != date ||
      heads.played_character_id != actor) {
    out.identity.reason = "head_identity_unavailable";
    out.unavailable_reason = out.identity.reason;
    return false;
  }
  if (!out.identity.requested_head_character_id ||
      *out.identity.requested_head_character_id == UINT32_MAX) {
    out.identity.reason = "faith_head_absent";
    out.unavailable_reason = out.identity.reason;
    return false;
  }
  void *database = nullptr, *definition = nullptr;
  std::int32_t definition_hash = 0;
  if (!Call(b.get_database, database) || database == nullptr ||
      !Call(b.stable_hash, definition_hash, database, kInteractionKey.data(),
            static_cast<std::uint32_t>(kInteractionKey.size())) ||
      !Call(b.lookup_definition, definition, database, definition_hash) ||
      !DefinitionMatches(definition, definition_hash)) {
    out.identity.reason = "interaction_definition_unavailable";
    out.unavailable_reason = out.identity.reason;
    return false;
  }
  out.definition_stable_hash = static_cast<std::uint32_t>(definition_hash);
  NativeContext context{};
  context.destroy = b.interaction.destroy;
  void *constructed = nullptr;
  if (context.destroy == nullptr ||
      !Call(b.construct_two_role, constructed, context.bytes.data(), definition,
          actor, static_cast<std::int32_t>(*out.identity.requested_head_character_id),
          static_cast<void *>(nullptr), true) || constructed != context.bytes.data()) {
    out.identity.reason = "interaction_context_unavailable";
    out.unavailable_reason = out.identity.reason;
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
    out.identity.reason = "interaction_finalization_unavailable";
    out.unavailable_reason = out.identity.reason;
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
          !Call(b.read_option, selected, storage, flag)) { readback = false; break; }
      if (selected) ++selected_count;
    }
    if (readback) {
      out.options.selected_count = selected_count;
      out.options.all_unselected = selected_count == 0;
      Success(out.options);
    }
  }
  SampleBool(b.is_shown, storage, out.shown);
  bool legal = false;
  out.can_send.reason = "native_evaluation_unavailable";
  if (Call(b.interaction.validate, legal, storage, static_cast<void *>(nullptr))) {
    out.can_send.value = legal;
    Success(out.can_send);
  }
  std::array<std::int64_t, 10> costs{};
  out.declared_costs.reason = "declared_cost_evaluation_unavailable";
  if (CallVoid(b.interaction.evaluate_cost,
      static_cast<const void *>(static_cast<const std::byte *>(definition) + 0x40),
      static_cast<const void *>(context.bytes.data() + 8), costs.data())) {
    out.declared_costs.raw = costs;
    Success(out.declared_costs);
  }
  void *trigger = nullptr;
  bool automatic = false;
  out.auto_accept.reason = "auto_accept_evaluation_unavailable";
  if (Read(definition, 0x2290, trigger)) {
    bool auto_read = false;
    if (trigger != nullptr)
      auto_read = Call(b.interaction.evaluate_trigger, automatic, trigger,
                      static_cast<const void *>(context.bytes.data() + 8));
    else {
      std::uint8_t scalar = 0;
      auto_read = Read(definition, 0x2718, scalar);
      automatic = scalar != 0;
    }
    if (auto_read) { out.auto_accept.value = automatic; Success(out.auto_accept); }
  }
  auto &answer = out.acceptance_preview;
  std::int64_t recipient_score = 0, intermediary_score = 0;
  std::int64_t *returned = nullptr;
  answer.recipient_score_reason = "recipient_score_unavailable";
  if (Call(b.interaction.recipient_answer_score, returned, storage, &recipient_score) &&
      returned == &recipient_score) {
    answer.recipient_score_available = true;
    answer.recipient_score_reason = "none";
    answer.recipient_score_raw = recipient_score;
  }
  returned = nullptr;
  answer.intermediary_score_reason = "intermediary_score_unavailable";
  if (Call(b.interaction.intermediary_answer_score, returned, storage, &intermediary_score) &&
      returned == &intermediary_score) {
    answer.intermediary_score_available = true;
    answer.intermediary_score_reason = "none";
    answer.intermediary_score_raw = intermediary_score;
  }
  std::uint8_t status = 0;
  answer.outer_reason = "outer_answer_unavailable";
  if (Call(b.outer_answer, status, storage, std::uint8_t{1}, std::uint8_t{1},
           static_cast<void *>(nullptr), static_cast<void *>(nullptr)) && status <= 2) {
    answer.outer_available = true;
    answer.outer_reason = "none";
    answer.outer_status = status;
  }
  auto &gold = out.gold_proceeds;
  gold.reason = "gold_value_evaluation_unavailable";
  if (*out.identity.effective_actor_id >= 0 && *out.identity.effective_recipient_id >= 0) {
    const auto effective_actor = static_cast<std::uint32_t>(*out.identity.effective_actor_id);
    const auto recipient = static_cast<std::uint32_t>(*out.identity.effective_recipient_id);
    gold.root_character_id = recipient;
    gold.actor_character_id = effective_actor;
    gold.recipient_character_id = recipient;
    void *named_db = nullptr;
    std::int32_t value_hash = 0;
    std::int64_t amount = 0;
    if (Call(b.named_database, named_db) && named_db != nullptr &&
        Call(b.stable_hash, value_hash, named_db, kGoldValueKey.data(),
              static_cast<std::uint32_t>(kGoldValueKey.size())) &&
        NamedValue(b, context.bytes.data() + 8, recipient, effective_actor,
                   static_cast<std::uint32_t>(value_hash), amount)) {
      gold.amount_raw = amount;
      Success(gold);
    }
  } else gold.reason = "effective_recipient_unavailable";
  auto &fee = out.acceptance_effect_consequence;
  fee.reason = "ordinary_options_not_unselected";
  if (out.options.available && out.options.all_unselected.value_or(false)) {
    fee.piety_raw = 25000000;
    fee.hook_selected = false;
    Success(fee);
  }
  out.available = out.identity.available && out.options.available &&
      out.options.all_unselected.value_or(false) && out.shown.available &&
      out.can_send.available && out.declared_costs.available && out.auto_accept.available &&
      answer.recipient_score_available && answer.intermediary_score_available &&
      answer.outer_available && gold.available && fee.available;
  out.unavailable_reason = out.available ? "none" : "one_or_more_samples_unavailable";
  return out.available;
}

std::string SerializeHeadOfFaithGoldContext12003(const Context &c) {
  std::ostringstream out;
  out << "{\"schema\":"; Quote(out, kSchema);
  out << ",\"game_version\":\"1.20.0.3\",\"executable_sha256\":";
  Quote(out, kExecutableSha256);
  out << ",\"raw_scale\":" << kRawScale << ",\"available\":" <<
      (c.available ? "true" : "false") << ",\"unavailable_reason\":";
  Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" <<
      c.date_raw << ",\"played_character_id\":" << c.played_character_id <<
      ",\"definition_key\":"; Quote(out, kInteractionKey);
  out << ",\"definition_stable_hash\":"; Optional(out, c.definition_stable_hash);
  out << ",\"identity\":{"; SampleFields(out, c.identity);
#define XAR_HOF_ID(name) out << ",\"" #name "\":"; Optional(out, c.identity.name)
  XAR_HOF_ID(actor_rite_id); XAR_HOF_ID(faith_id); XAR_HOF_ID(faith_main_rite_id);
  XAR_HOF_ID(requested_head_character_id); XAR_HOF_ID(head_title_id);
  XAR_HOF_ID(effective_actor_id); XAR_HOF_ID(effective_recipient_id);
  XAR_HOF_ID(secondary_actor_id); XAR_HOF_ID(secondary_recipient_id);
  XAR_HOF_ID(intermediary_id); XAR_HOF_ID(sixth_role_id);
#undef XAR_HOF_ID
  out << "},\"options\":{"; SampleFields(out, c.options);
  out << ",\"declared_count\":"; Optional(out, c.options.declared_count);
  out << ",\"selected_count\":"; Optional(out, c.options.selected_count);
  out << ",\"all_unselected\":"; Optional(out, c.options.all_unselected);
  out << "},\"shown\":{"; BoolFields(out, c.shown);
  out << "},\"can_send\":{"; BoolFields(out, c.can_send);
  out << "},\"declared_costs\":{"; SampleFields(out, c.declared_costs);
  out << ",\"raw\":";
  if (!c.declared_costs.available || !c.declared_costs.raw) out << "null";
  else {
    out << '[';
    for (std::size_t i = 0; i < c.declared_costs.raw->size(); ++i) {
      if (i != 0) out << ',';
      out << (*c.declared_costs.raw)[i];
    }
    out << ']';
  }
  out << ",\"raw_scale\":" << kRawScale << ",\"timing\":\"on_send\"}";
  out << ",\"auto_accept\":{"; BoolFields(out, c.auto_accept);
  const auto &a = c.acceptance_preview;
  out << "},\"acceptance_preview\":{\"recipient_score_available\":" <<
      (a.recipient_score_available ? "true" : "false") << ",\"recipient_score_reason\":";
  Quote(out, a.recipient_score_reason);
  out << ",\"recipient_score_raw\":"; Optional(out, a.recipient_score_raw);
  out << ",\"intermediary_score_available\":" <<
      (a.intermediary_score_available ? "true" : "false") << ",\"intermediary_score_reason\":";
  Quote(out, a.intermediary_score_reason);
  out << ",\"intermediary_score_raw\":"; Optional(out, a.intermediary_score_raw);
  out << ",\"outer_available\":" << (a.outer_available ? "true" : "false") <<
      ",\"outer_reason\":"; Quote(out, a.outer_reason);
  out << ",\"outer_status\":"; Optional(out, a.outer_status);
  out << ",\"raw_scale\":" << kRawScale << "},\"gold_proceeds\":{";
  SampleFields(out, c.gold_proceeds);
  out << ",\"key\":"; Quote(out, kGoldValueKey);
  out << ",\"root_character_id\":"; Optional(out, c.gold_proceeds.root_character_id);
  out << ",\"actor_character_id\":"; Optional(out, c.gold_proceeds.actor_character_id);
  out << ",\"recipient_character_id\":"; Optional(out, c.gold_proceeds.recipient_character_id);
  out << ",\"amount_raw\":"; Optional(out, c.gold_proceeds.amount_raw);
  out << ",\"raw_scale\":" << kRawScale << "},\"acceptance_effect_consequence\":{";
  SampleFields(out, c.acceptance_effect_consequence);
  out << ",\"source\":\"stock_qualified\",\"timing\":\"on_accept\",\"piety_raw\":";
  Optional(out, c.acceptance_effect_consequence.piety_raw);
  out << ",\"raw_scale\":" << kRawScale << ",\"hook_selected\":";
  Optional(out, c.acceptance_effect_consequence.hook_selected);
  out << "}}";
  return out.str();
}
} // namespace xar::ck3_12003::religion::hof_gold
