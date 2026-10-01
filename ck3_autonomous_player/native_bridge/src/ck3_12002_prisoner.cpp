#include "xar_bridge/ck3_12002_prisoner.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"
#include "xar_bridge/ck3_12002_prisoner_abi.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <string>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {

constexpr std::string_view kRansom = "ransom_interaction";
constexpr std::string_view kRansomCost = "normal_ransom_cost_value";
constexpr std::uint32_t kSlotMask = 0x00FFFFFFU;
constexpr std::size_t kContextSize = 0x338;
// The final authored option is the stock mass-action-only `invalid` fallback.
// It must be observed in the mask but is never a ransom quote candidate.
constexpr std::size_t kOptionCount = 9;
constexpr std::size_t kOptionDataOffset = 0x300;
constexpr std::size_t kOptionCountOffset = 0x30C;
constexpr std::size_t kDefinitionOptionCountOffset = 0x2264;
constexpr std::size_t kDefinitionOptionRowsOffset = 0x2258;
constexpr std::size_t kDefinitionOptionRowStride = 0x730;
constexpr std::size_t kDefinitionOptionFlagOffset = 0x368;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterExtensionOffset = 0x1B0;
constexpr std::size_t kGoldOffset = 0x100;
constexpr std::uintptr_t kCharacterStorageRva = 0x5C67568;
constexpr std::uintptr_t kCharacterFallbackRva = 0x5C67570;
constexpr std::int64_t kFixedScale = 100000;
constexpr std::array<std::string_view, kOptionCount> kOptionFlags{
    "extortionate_gold", "extortionate_current_gold", "gold",
    "current_gold", "favor", "influence_send_option",
    "herd_send_option", "current_herd", "invalid"};

struct NativeStringView {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::uint8_t owned = 0;
  std::array<std::byte, 3> padding{};
};
static_assert(sizeof(NativeStringView) == 0x10);

template <typename T>
bool Read(const void *base, std::size_t offset, T &out) noexcept {
  if (base == nullptr || reinterpret_cast<std::uintptr_t>(base) >
                             (std::numeric_limits<std::uintptr_t>::max)() - offset)
    return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&out, static_cast<const std::byte *>(base) + offset,
                sizeof(out));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

void *ResolveCharacter(std::uintptr_t module, std::int32_t id) noexcept {
  void *store = nullptr;
  void *fallback = nullptr;
  void *slots = nullptr;
  std::int32_t count = 0;
  if (module == 0 || id <= 0 ||
      !Read(reinterpret_cast<const void *>(module + kCharacterStorageRva),
            0, store) ||
      !Read(reinterpret_cast<const void *>(module + kCharacterFallbackRva),
            0, fallback) ||
      store == nullptr || !Read(store, 0x20, slots) || slots == nullptr ||
      !Read(store, 0x2C, count) || count <= 0 ||
      (static_cast<std::uint32_t>(id) & kSlotMask) >=
          static_cast<std::uint32_t>(count))
    return nullptr;
  void *character = nullptr;
  const auto slot = static_cast<std::uint32_t>(id) & kSlotMask;
  if (!Read(slots, static_cast<std::size_t>(slot) * 0x10 + 0x08,
            character) ||
      character == nullptr || character == fallback)
    return nullptr;
  std::int32_t observed = -1;
  return Read(character, kCharacterIdOffset, observed) && observed == id
             ? character
             : nullptr;
}

bool ReadMsvcString(const void *storage, std::string &out) noexcept {
  out.clear();
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!Read(storage, 0x10, size) || !Read(storage, 0x18, capacity) ||
      size == 0 || size > capacity || size > 96)
    return false;
  const char *data = static_cast<const char *>(storage);
  if (capacity >= 16 && !Read(storage, 0, data)) return false;
  if (data == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out.assign(data, static_cast<std::size_t>(size));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    out.clear();
    return false;
  }
#endif
}

bool DefinitionKey(const void *definition, std::int32_t hash,
                   std::string_view expected) noexcept {
  std::int32_t actual_hash = 0;
  std::string actual_key;
  return Read(definition, 0x14, actual_hash) && actual_hash == hash &&
         ReadMsvcString(static_cast<const std::byte *>(definition) + 0x18,
                        actual_key) &&
         actual_key == expected;
}

bool ReadNamedRansomCost(std::uintptr_t module,
    const PrisonerRansomBindings &bindings, const void *scope,
    std::int32_t jailer, std::int32_t payer, std::int32_t prisoner,
    std::int64_t &raw) noexcept {
  return bindings.read_named_cost != nullptr &&
      bindings.read_named_cost(bindings.named_cost_context, module, scope,
          jailer, payer, prisoner, raw) && raw > 0;
}

bool ReadSnapshot(const PrisonerRansomBindings &bindings,
    game::Snapshot &out) noexcept {
  CoreSnapshotPrefix core{};
  if (!ReadCoreSnapshot(bindings.context.core, core)) return false;
  out = {};
  out.date_raw = core.clock.date_raw;
  out.paused = core.clock.paused;
  out.speed = core.clock.speed;
  out.map_ready = core.map_ready;
  out.has_played_character = core.has_played_character;
  out.played_character_id = core.played_character_id;
  out.played_character_alive = core.played_character_alive;
  return true;
}

bool ReadPayerGold(void *payer, std::int64_t &raw) noexcept {
  void *extension = nullptr;
  std::int64_t first = 0;
  std::int64_t second = 0;
  return Read(payer, kCharacterExtensionOffset, extension) &&
         extension != nullptr && Read(extension, kGoldOffset, first) &&
         Read(extension, kGoldOffset, second) && first == second &&
         (raw = first, true);
}

bool ReadCurrentGold(void *payer, std::int64_t &raw) noexcept {
  return ReadPayerGold(payer, raw) && raw >= kFixedScale;
}

bool ContextRolesMatch(const void *context, const void *definition,
                       std::int32_t jailer_id, std::int32_t payer_id,
                       std::int32_t prisoner_id) noexcept {
  std::int32_t observed_actor = -1;
  std::int32_t observed_payer = -1;
  std::int32_t observed_prisoner = -1;
  void *observed_definition = nullptr;
  return Read(context, 0, observed_definition) &&
         Read(context, 0x2D8, observed_actor) &&
         Read(context, 0x2DC, observed_payer) &&
         Read(context, 0x2E4, observed_prisoner) &&
         observed_definition == definition &&
         observed_actor == jailer_id &&
         observed_payer == payer_id &&
         observed_prisoner == prisoner_id;
}

bool LoadedOptionFlagsMatch(const PrisonerRansomBindings &bindings,
                            const void *definition) noexcept {
  if (bindings.get_script_identifier_table == nullptr ||
      bindings.lookup_script_identifier_id == nullptr)
    return false;
  void *rows = nullptr;
  void *const table = bindings.get_script_identifier_table();
  if (table == nullptr ||
      !Read(definition, kDefinitionOptionRowsOffset, rows) || rows == nullptr)
    return false;
  for (std::size_t index = 0; index < kOptionFlags.size(); ++index) {
    std::int32_t observed = -1;
    std::int32_t expected = -1;
    const auto key = kOptionFlags[index];
    const NativeStringView view{key.data(),
                                static_cast<std::int32_t>(key.size())};
    if (!Read(rows, index * kDefinitionOptionRowStride +
                        kDefinitionOptionFlagOffset, observed) ||
        bindings.lookup_script_identifier_id(table, &expected, &view) ==
            nullptr ||
        expected < 0 || observed != expected)
      return false;
  }
  return true;
}

enum class OptionMaskState : std::uint8_t {
  unreadable,
  none_selected,
  expected_only,
  unexpected,
};

OptionMaskState ReadOptionMaskState(
    const void *context, std::int32_t expected,
    PlayerPrisonerRansomQuoteFailureV1 &failure,
    std::optional<std::int32_t> &observed_definition_count,
    std::optional<std::int32_t> &observed_context_count,
    std::uint32_t *observed_mask = nullptr) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  const void *definition = nullptr;
  std::int32_t definition_count = 0;
  failure = PlayerPrisonerRansomQuoteFailureV1::none;
  if (!Read(context, 0, definition) || definition == nullptr) {
    failure = PlayerPrisonerRansomQuoteFailureV1::
        option_definition_pointer_unreadable;
    return OptionMaskState::unreadable;
  }
  if (!Read(definition, kDefinitionOptionCountOffset, definition_count)) {
    failure = PlayerPrisonerRansomQuoteFailureV1::
        option_definition_count_unreadable;
    return OptionMaskState::unreadable;
  }
  observed_definition_count = definition_count;
  if (definition_count != static_cast<std::int32_t>(kOptionCount)) {
    if (Read(context, kOptionCountOffset, count))
      observed_context_count = count;
    failure = PlayerPrisonerRansomQuoteFailureV1::
        option_definition_count_unexpected;
    return OptionMaskState::unreadable;
  }
  if (!Read(context, kOptionDataOffset, data)) {
    failure = PlayerPrisonerRansomQuoteFailureV1::
        option_data_pointer_unreadable;
    return OptionMaskState::unreadable;
  }
  if (data == nullptr) {
    failure = PlayerPrisonerRansomQuoteFailureV1::option_data_pointer_null;
    return OptionMaskState::unreadable;
  }
  if (!Read(context, kOptionCountOffset, count)) {
    failure = PlayerPrisonerRansomQuoteFailureV1::
        option_context_count_unreadable;
    return OptionMaskState::unreadable;
  }
  observed_context_count = count;
  if (count != definition_count) {
    failure = PlayerPrisonerRansomQuoteFailureV1::
        option_context_count_mismatch;
    return OptionMaskState::unreadable;
  }
  std::int32_t selected_count = 0;
  std::int32_t selected_index = -1;
  std::uint32_t mask_bits = 0;
  for (std::int32_t i = 0; i < count; ++i) {
    std::uint8_t selected = 0;
    if (!Read(data, static_cast<std::size_t>(i), selected)) {
      failure = PlayerPrisonerRansomQuoteFailureV1::option_byte_unreadable;
      return OptionMaskState::unreadable;
    }
    if (selected > 1) {
      failure = PlayerPrisonerRansomQuoteFailureV1::option_byte_out_of_range;
      return OptionMaskState::unreadable;
    }
    if (selected != 0) {
      ++selected_count;
      selected_index = i;
      mask_bits |= std::uint32_t{1} << i;
    }
  }
  if (observed_mask != nullptr) *observed_mask = mask_bits;
  if (selected_count == 0) return OptionMaskState::none_selected;
  return selected_count == 1 && selected_index == expected
             ? OptionMaskState::expected_only
             : OptionMaskState::unexpected;
}

} // namespace

PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuotePrivateV1(
    const PrisonerRansomBindings &bindings, std::uintptr_t module,
    std::int32_t jailer_id, std::int32_t prisoner_id) noexcept {
  PlayerPrisonerRansomQuoteV1 result{};
  if (!bindings.enabled || module == 0 || jailer_id <= 0 ||
      prisoner_id <= 0 || prisoner_id == jailer_id ||
      bindings.get_character_interaction_database == nullptr ||
      bindings.hash_stable_key == nullptr ||
      bindings.lookup_character_interaction == nullptr ||
      bindings.redirect_character_interaction_roles == nullptr ||
      bindings.construct_character_interaction_context_all_roles == nullptr ||
      bindings.validate_character_interaction_context == nullptr ||
      bindings.read_character_interaction_answer_score == nullptr ||
      bindings.evaluate_character_interaction_answer == nullptr ||
      bindings.destroy_character_interaction_context == nullptr ||
      bindings.clear_local_options == nullptr || bindings.select_local_option == nullptr)
    return result;
  game::Snapshot before{};
  if (!ReadSnapshot(bindings, before) || !before.paused ||
      !before.map_ready || !before.has_played_character ||
      !before.played_character_alive ||
      before.played_character_id != jailer_id) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::frame_changed;
    return result;
  }
  void *const jailer = ResolveCharacter(module, jailer_id);
  void *const prisoner = ResolveCharacter(module, prisoner_id);
  if (jailer == nullptr || prisoner == nullptr) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::role_unavailable;
    return result;
  }
  void *const database = bindings.get_character_interaction_database();
  const auto hash = bindings.hash_stable_key(
      database, kRansom.data(), static_cast<std::uint32_t>(kRansom.size()));
  void *const definition = database == nullptr
                               ? nullptr
                               : bindings.lookup_character_interaction(
                                     database, hash);
  if (definition == nullptr || !DefinitionKey(definition, hash, kRansom)) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::definition_unavailable;
    return result;
  }
  std::int32_t authored_option_count = 0;
  if (Read(definition, kDefinitionOptionCountOffset, authored_option_count) &&
      authored_option_count == static_cast<std::int32_t>(kOptionCount) &&
      !LoadedOptionFlagsMatch(bindings, definition)) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::
        option_flag_identity_unverified;
    return result;
  }
  std::int32_t actor = jailer_id;
  std::int32_t payer_id = prisoner_id;
  std::int32_t secondary_actor = -1;
  std::int32_t secondary_recipient = -1;
  std::int32_t intermediary = -1;
  std::int32_t added_role = -1;
  bindings.redirect_character_interaction_roles(
      definition, &actor, &payer_id, &secondary_actor,
      &secondary_recipient, &intermediary, &added_role);
  void *const payer = ResolveCharacter(module, payer_id);
  if (actor != jailer_id || payer_id == jailer_id ||
      secondary_recipient != prisoner_id || payer == nullptr ||
      secondary_actor != -1 || intermediary != -1 || added_role != -1) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::role_unavailable;
    return result;
  }

  bool any_option_selected = false;
  for (std::int32_t option : {2, 3}) {
    alignas(8) std::array<std::byte, kContextSize> storage{};
    void *const context = storage.data();
    if (bindings.construct_character_interaction_context_all_roles(
            context, definition, actor, payer_id, secondary_actor,
            secondary_recipient, intermediary, nullptr) != context) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::binding_unavailable;
      return result;
    }
    // Both routines operate on this stack-owned context only. No command is
    // allocated or submitted; the stock setter re-runs scope and option gates.
    bindings.clear_local_options(context);
    bindings.select_local_option(context, option);
    const bool roles_ok = ContextRolesMatch(
        context, definition, jailer_id, payer_id, prisoner_id);
    auto mask_failure = PlayerPrisonerRansomQuoteFailureV1::none;
    std::uint32_t observed_mask = 0;
    const auto mask = roles_ok ? ReadOptionMaskState(
                                     context, option, mask_failure,
                                     result.observed_definition_option_count,
                                     result.observed_context_option_count,
                                     &observed_mask)
                               : OptionMaskState::unreadable;
    // The stock exclusive-option finalizer can replace an unaffordable
    // ordinary gold selection with current_gold. Probe that option afresh;
    // its own final Can Send, answer and acceptance-time amount still decide.
    if (option == 2 && mask == OptionMaskState::unexpected &&
        observed_mask == (std::uint32_t{1} << 3)) {
      bindings.destroy_character_interaction_context(context);
      continue;
    }
    if (!roles_ok || mask == OptionMaskState::unreadable ||
        mask == OptionMaskState::unexpected) {
      bindings.destroy_character_interaction_context(context);
      result.failure = !roles_ok
                           ? PlayerPrisonerRansomQuoteFailureV1::
                                 option_context_roles_unverified
                           : mask == OptionMaskState::unreadable
                                 ? mask_failure
                                 : PlayerPrisonerRansomQuoteFailureV1::
                                       option_mask_unexpected;
      if (mask == OptionMaskState::unexpected) {
        result.requested_option_index = option;
        result.observed_option_mask_bits = observed_mask;
      }
      return result;
    }
    const bool selected = mask == OptionMaskState::expected_only;
    any_option_selected = any_option_selected || selected;
    const bool can_send = selected &&
        bindings.validate_character_interaction_context(context, nullptr);
    std::int64_t accept_raw = 0;
    const bool acceptance_read = can_send &&
        bindings.read_character_interaction_answer_score(
            context, &accept_raw) == &accept_raw;
    const auto answer = acceptance_read
                            ? bindings.evaluate_character_interaction_answer(
                                  context, 1, 1, nullptr, nullptr)
                            : std::uint8_t{3};
    std::int64_t amount_raw = 0;
    bool amount_read = false;
    if (can_send && acceptance_read && answer <= 2) {
      amount_read = option == 2
                        ? ReadNamedRansomCost(
                              module, bindings,
                              static_cast<const std::byte *>(context) + 8,
                              jailer_id, payer_id, prisoner_id, amount_raw)
                        : ReadCurrentGold(payer, amount_raw);
    }
    bindings.destroy_character_interaction_context(context);
    if (!selected || !can_send) continue;
    if (!acceptance_read || answer > 2) {
      result.failure =
          PlayerPrisonerRansomQuoteFailureV1::final_legality_unavailable;
      return result;
    }
    if (!amount_read) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::quote_unavailable;
      return result;
    }
    game::Snapshot after{};
    if (!ReadSnapshot(bindings, after) || after != before ||
        ResolveCharacter(module, jailer_id) != jailer ||
        ResolveCharacter(module, prisoner_id) != prisoner ||
        ResolveCharacter(module, payer_id) != payer ||
        bindings.get_character_interaction_database() != database ||
        bindings.lookup_character_interaction(database, hash) != definition) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::frame_changed;
      return result;
    }
    result.available = true;
    result.failure = PlayerPrisonerRansomQuoteFailureV1::none;
    result.jailer_character_id = jailer_id;
    result.payer_character_id = payer_id;
    result.prisoner_character_id = prisoner_id;
    result.selected_option = option == 2 ? "gold" : "current_gold";
    result.quoted_gold_raw = amount_raw;
    result.recipient_acceptance_raw = accept_raw;
    result.recipient_answer_status_raw = answer;
    result.would_accept_now = answer != 2;
    result.amount_is_acceptance_time_quote = option == 3;
    return result;
  }
  if (any_option_selected) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::final_can_send_false;
    return result;
  }
  // The first two authored options are the stock FP1 extortionate variants.
  // Their payment uses increased_ransom_cost_value, so the ordinary quote
  // cannot price them. Identify a legal opportunity without inventing value.
  bool any_extortionate_option_selected = false;
  for (std::int32_t option : {0, 1}) {
    alignas(8) std::array<std::byte, kContextSize> storage{};
    void *const context = storage.data();
    if (bindings.construct_character_interaction_context_all_roles(
            context, definition, actor, payer_id, secondary_actor,
            secondary_recipient, intermediary, nullptr) != context) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::binding_unavailable;
      return result;
    }
    bindings.clear_local_options(context);
    bindings.select_local_option(context, option);
    const bool roles_ok = ContextRolesMatch(
        context, definition, jailer_id, payer_id, prisoner_id);
    auto mask_failure = PlayerPrisonerRansomQuoteFailureV1::none;
    std::uint32_t observed_mask = 0;
    const auto mask = roles_ok ? ReadOptionMaskState(
                                     context, option, mask_failure,
                                     result.observed_definition_option_count,
                                     result.observed_context_option_count,
                                     &observed_mask)
                               : OptionMaskState::unreadable;
    if (!roles_ok || mask == OptionMaskState::unreadable ||
        mask == OptionMaskState::unexpected) {
      bindings.destroy_character_interaction_context(context);
      result.failure = !roles_ok
                           ? PlayerPrisonerRansomQuoteFailureV1::
                                 option_context_roles_unverified
                           : mask == OptionMaskState::unreadable
                                 ? mask_failure
                                 : PlayerPrisonerRansomQuoteFailureV1::
                                       option_mask_unexpected;
      if (mask == OptionMaskState::unexpected) {
        result.requested_option_index = option;
        result.observed_option_mask_bits = observed_mask;
      }
      return result;
    }
    const bool selected = mask == OptionMaskState::expected_only;
    any_extortionate_option_selected |= selected;
    const bool can_send = selected &&
        bindings.validate_character_interaction_context(context, nullptr);
    bindings.destroy_character_interaction_context(context);
    if (can_send) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::
          extortionate_gold_option_requires_valuation;
      return result;
    }
  }
  if (any_extortionate_option_selected) {
    result.failure =
        PlayerPrisonerRansomQuoteFailureV1::extortionate_final_can_send_false;
    return result;
  }
  std::int64_t payer_gold_raw = 0;
  if (!ReadPayerGold(payer, payer_gold_raw)) {
    result.failure =
        PlayerPrisonerRansomQuoteFailureV1::payer_gold_read_unavailable;
  } else if (payer_gold_raw < kFixedScale) {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::payer_below_one_gold;
  } else {
    result.failure = PlayerPrisonerRansomQuoteFailureV1::
        gold_options_not_selected_with_funded_payer;
  }
  return result;
}

PlayerPrisonerRansomSubmitV1 SubmitPlayerPrisonerRansomPrivateV1(
    const PrisonerRansomBindings &bindings, std::uintptr_t module,
    const PlayerPrisonerRansomQuoteV1 &observed,
    std::uint64_t expected_native_revision,
    std::int64_t expected_date_raw) noexcept {
  using Result = PlayerPrisonerRansomSubmitV1;
  if (!bindings.enabled || module == 0 || !observed.available ||
      observed.failure != PlayerPrisonerRansomQuoteFailureV1::none ||
      observed.jailer_character_id <= 0 || observed.payer_character_id <= 0 ||
      observed.prisoner_character_id <= 0 || observed.quoted_gold_raw <= 0 ||
      (observed.selected_option != "gold" &&
       observed.selected_option != "current_gold") ||
      !observed.would_accept_now || observed.recipient_answer_status_raw > 1 ||
      expected_native_revision == 0 || expected_date_raw <= 0 ||
      !bindings.context.commands.enabled ||
      bindings.context.commands.command_manager == nullptr ||
      bindings.context.commands.queue_owned_command == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable !=
          module + kMarriageSendInteractionPrimaryVtableRva ||
      bindings.send_character_interaction_secondary_vtable !=
          module + kMarriageSendInteractionSecondaryVtableRva)
    return Result::unavailable;

  game::Snapshot before{};
  if (!ReadSnapshot(bindings, before) || !before.paused || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive ||
      before.played_character_id != observed.jailer_character_id ||
      before.date_raw != expected_date_raw)
    return Result::unavailable;

  // The observed value chooses an option; the engine decides whether it is
  // still the same legal offer at the actual application-main submit point.
  const auto fresh = ReadPlayerPrisonerRansomQuotePrivateV1(
      bindings, module, observed.jailer_character_id,
      observed.prisoner_character_id);
  if (!fresh.available || fresh.failure != observed.failure ||
      fresh.jailer_character_id != observed.jailer_character_id ||
      fresh.payer_character_id != observed.payer_character_id ||
      fresh.prisoner_character_id != observed.prisoner_character_id ||
      fresh.selected_option != observed.selected_option ||
      fresh.quoted_gold_raw != observed.quoted_gold_raw ||
      fresh.amount_is_acceptance_time_quote !=
          observed.amount_is_acceptance_time_quote ||
      !fresh.would_accept_now || fresh.recipient_answer_status_raw > 1)
    return Result::quote_changed;

  void *const database = bindings.get_character_interaction_database();
  if (database == nullptr) return Result::unavailable;
  const auto hash = bindings.hash_stable_key(
      database, kRansom.data(), static_cast<std::uint32_t>(kRansom.size()));
  void *const definition = bindings.lookup_character_interaction(database, hash);
  std::int32_t option_count = 0;
  if (definition == nullptr || !DefinitionKey(definition, hash, kRansom) ||
      !Read(definition, kDefinitionOptionCountOffset, option_count) ||
      option_count != static_cast<std::int32_t>(kOptionCount) ||
      !LoadedOptionFlagsMatch(bindings, definition))
    return Result::unavailable;

  const auto option = observed.selected_option == "gold" ? 2 : 3;
  alignas(8) std::array<std::byte, kContextSize> context_storage{};
  void *const context = context_storage.data();
  if (bindings.construct_character_interaction_context_all_roles(
          context, definition, observed.jailer_character_id,
          observed.payer_character_id, -1, observed.prisoner_character_id,
          -1, nullptr) != context)
    return Result::command_unavailable;
  bindings.clear_local_options(context);
  bindings.select_local_option(context, option);
  const auto context_ok = [&](const void *value) noexcept {
    auto failure = PlayerPrisonerRansomQuoteFailureV1::none;
    std::optional<std::int32_t> definition_count;
    std::optional<std::int32_t> context_count;
    return ContextRolesMatch(value, definition, observed.jailer_character_id,
                             observed.payer_character_id,
                             observed.prisoner_character_id) &&
           ReadOptionMaskState(value, option, failure, definition_count,
                               context_count) == OptionMaskState::expected_only;
  };
  if (!context_ok(context) ||
      !bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return Result::final_legality_changed;
  }
  game::Snapshot checked{};
  if (!ReadSnapshot(bindings, checked) || checked != before ||
      bindings.get_character_interaction_database() != database ||
      bindings.lookup_character_interaction(database, hash) != definition) {
    bindings.destroy_character_interaction_context(context);
    return Result::quote_changed;
  }

  alignas(8) std::array<std::byte, 0x368> command_storage{};
  void *const command = command_storage.data();
  void *const copied_context = command_storage.data() + 0x20;
  const auto destroy_copy_if_owned = [&]() noexcept {
    void *copied_definition = nullptr;
    if (Read(copied_context, 0, copied_definition) &&
        copied_definition == definition)
      bindings.destroy_character_interaction_context(copied_context);
  };
  if (bindings.construct_send_character_interaction_command(command, context) !=
          command) {
    destroy_copy_if_owned();
    bindings.destroy_character_interaction_context(context);
    return Result::command_unavailable;
  }
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  if (!Read(command, 0, primary) || !Read(command, 0x18, secondary) ||
      primary != bindings.send_character_interaction_primary_vtable ||
      secondary != bindings.send_character_interaction_secondary_vtable ||
      !context_ok(copied_context)) {
    destroy_copy_if_owned();
    bindings.destroy_character_interaction_context(context);
    return Result::command_unavailable;
  }
  const bool submitted = SubmitCommandCopy(
      bindings.context.commands, command, 0x0E) == CommandSubmitResult::submitted;
  destroy_copy_if_owned();
  bindings.destroy_character_interaction_context(context);
  return submitted ? Result::submitted_verification_pending
                   : Result::command_unavailable;
}

namespace {
bool ReadProductionNamedCost(void *, std::uintptr_t module, const void *scope,
    std::int32_t jailer, std::int32_t payer, std::int32_t prisoner,
    std::int64_t &raw) noexcept {
  const auto hash = reinterpret_cast<ck3_11906::HashStableKey>(
      module + kPrisonerHashStableKeyRva)(nullptr, kRansomCost.data(),
          static_cast<std::uint32_t>(kRansomCost.size()));
  return ReadNamedInteractionFixedExact12002(module, scope,
      static_cast<std::uint32_t>(prisoner), static_cast<std::uint32_t>(jailer),
      static_cast<std::uint32_t>(payer), kRansomCost,
      static_cast<std::uint32_t>(hash), raw);
}
} // namespace

PrisonerRansomBindings BindPrisonerRansomImage(std::uintptr_t module,
    std::string_view sha) noexcept {
  PrisonerRansomBindings bindings{};
  if (module == 0 || sha != kExecutableSha256) return bindings;
  bindings.context = BindContextImage(module, sha);
  if (!bindings.context.enabled) return bindings;
  bindings.get_character_interaction_database = reinterpret_cast<
      ck3_11906::GetCharacterInteractionDatabase>(module + kPrisonerGetInteractionDatabaseRva);
  bindings.hash_stable_key = reinterpret_cast<ck3_11906::HashStableKey>(module + kPrisonerHashStableKeyRva);
  bindings.lookup_character_interaction = reinterpret_cast<ck3_11906::LookupCharacterInteraction>(module + kPrisonerLookupInteractionRva);
  bindings.redirect_character_interaction_roles = bindings.context.redirect_roles;
  bindings.construct_character_interaction_context_all_roles = bindings.context.construct_all_roles;
  bindings.validate_character_interaction_context = bindings.context.validate;
  bindings.read_character_interaction_answer_score = bindings.context.recipient_answer_score;
  bindings.evaluate_character_interaction_answer = reinterpret_cast<ck3_11906::EvaluateCharacterInteractionAnswer>(module + kPrisonerEvaluateAnswerRva);
  bindings.destroy_character_interaction_context = bindings.context.destroy;
  bindings.get_script_identifier_table = reinterpret_cast<ck3_11906::GetScriptIdentifierTable>(module + kPrisonerGetScriptIdentifierTableRva);
  bindings.lookup_script_identifier_id = reinterpret_cast<ck3_11906::LookupScriptIdentifierId>(module + kPrisonerLookupScriptIdentifierIdRva);
  bindings.construct_send_character_interaction_command = bindings.context.construct_send_command;
  bindings.send_character_interaction_primary_vtable = bindings.context.send_primary_vtable;
  bindings.send_character_interaction_secondary_vtable = bindings.context.send_secondary_vtable;
  bindings.clear_local_options = reinterpret_cast<void (*)(void *)>(module + kPrisonerClearOptionsRva);
  bindings.select_local_option = reinterpret_cast<void (*)(void *, std::int32_t)>(module + kPrisonerSelectOptionRva);
  bindings.read_named_cost = &ReadProductionNamedCost;
  bindings.enabled = true;
  return bindings;
}

} // namespace xar::ck3_12002
