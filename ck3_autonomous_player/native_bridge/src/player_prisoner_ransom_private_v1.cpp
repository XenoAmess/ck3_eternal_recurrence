#include "xar_bridge/player_prisoner_ransom_private_v1.hpp"

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

namespace xar::ck3_11906 {
namespace {

constexpr std::string_view kRansom = "ransom_interaction";
constexpr std::string_view kRansomCost = "ransom_cost_value";
constexpr std::uint32_t kSlotMask = 0x00FFFFFFU;
constexpr std::size_t kContextSize = 0x338;
constexpr std::size_t kOptionCount = 7;
constexpr std::size_t kOptionDataOffset = 0x300;
constexpr std::size_t kOptionCountOffset = 0x30C;
constexpr std::size_t kDefinitionOptionCountOffset = 0x2554;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterExtensionOffset = 0x1A8;
constexpr std::size_t kGoldOffset = 0x100;
constexpr std::uintptr_t kCharacterStorageRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackRva = 0x570C138;
constexpr std::uintptr_t kNamedDatabaseGetterRva = 0x999AF0;
constexpr std::uintptr_t kNamedLookupRva = 0x9999B0;
constexpr std::uintptr_t kNamedVtableRva = 0x44C9EA0;
constexpr std::uintptr_t kNamedSecondaryVtableRva = 0x44C9F10;
constexpr std::uintptr_t kCloneScopeRva = 0x3358E00;
constexpr std::uintptr_t kSupport118ConstructorRva = 0x3354330;
constexpr std::uintptr_t kSupport2A8ConstructorRva = 0x3354280;
constexpr std::uintptr_t kEvaluateNamedFixedRva = 0x3369820;
constexpr std::uintptr_t kEvaluationFlagRva = 0x570C3F4;
constexpr std::uintptr_t kDestroyScopeTailRva = 0x81E900;
constexpr std::uintptr_t kDestroyRows48Rva = 0x81E980;
constexpr std::uintptr_t kDestroySupport2A8RowsRva = 0x969BA0;
constexpr std::uintptr_t kClearLocalOptionsRva = 0x2C405F0;
constexpr std::uintptr_t kSelectLocalOptionRva = 0x2C406D0;
constexpr std::uint16_t kCharacterScopeKind = 4;
constexpr std::int64_t kFixedScale = 100000;

using GetDatabase = void *(*)();
using LookupNamed = const void *(*)(void *, std::uint32_t);
using CloneScope = void *(*)(void *, const void *);
using ConstructContainer = void *(*)(void *);
using EvaluateNamed = std::int64_t *(*)(const void *, std::int64_t *, void *,
                                        void *, const void *);
using DestroyPart = void (*)(void *);
using Deallocate = void (*)(void *, void *, std::size_t);
using DefinitionIsValid = bool (*)(const void *);
using LocalOptionStep = void (*)(void *);
using SelectLocalOption = void (*)(void *, std::int32_t);

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

bool ValidNamedDefinition(std::uintptr_t module, const void *definition,
                          std::int32_t hash) noexcept {
  std::uintptr_t vtable = 0;
  std::uintptr_t secondary_vtable = 0;
  std::uintptr_t validity = 0;
  return DefinitionKey(definition, hash, kRansomCost) &&
         Read(definition, 0, vtable) &&
         vtable == module + kNamedVtableRva &&
         Read(definition, 0x88, secondary_vtable) &&
         secondary_vtable == module + kNamedSecondaryVtableRva &&
         Read(reinterpret_cast<const void *>(vtable), 0, validity) &&
         validity != 0 &&
         reinterpret_cast<DefinitionIsValid>(validity)(definition);
}

bool DeallocateRows(std::uintptr_t module, void *owner,
                    std::size_t data_offset, std::size_t capacity_offset,
                    std::size_t count_offset, std::size_t allocator_offset,
                    std::uintptr_t destroy_rva) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  if (!Read(owner, data_offset, data) || !Read(owner, count_offset, count) ||
      count < 0 || count > 1'048'576 || (count != 0 && data == nullptr))
    return false;
  if (data == nullptr) return count == 0;
  if (destroy_rva != 0)
    reinterpret_cast<DestroyPart>(module + destroy_rva)(
        static_cast<std::byte *>(owner) + data_offset);
  void *allocator = nullptr;
  void *vtable = nullptr;
  std::uintptr_t deallocate = 0;
  if (!Read(owner, allocator_offset, allocator) || allocator == nullptr ||
      !Read(allocator, 0, vtable) || vtable == nullptr ||
      !Read(vtable, 0x10, deallocate) || deallocate == 0)
    return false;
  const std::int32_t zero = 0;
  void *const null_data = nullptr;
  std::memcpy(static_cast<std::byte *>(owner) + data_offset, &null_data,
              sizeof(null_data));
  std::memcpy(static_cast<std::byte *>(owner) + capacity_offset, &zero,
              sizeof(zero));
  std::memcpy(static_cast<std::byte *>(owner) + count_offset, &zero,
              sizeof(zero));
  reinterpret_cast<Deallocate>(deallocate)(allocator, data, 8);
  return true;
}

bool DestroyValueState(std::uintptr_t module, void *scope, void *support118,
                       void *support2a8) noexcept {
  const bool a = DeallocateRows(module, support2a8, 0, 8, 0x0C, 0x10,
                                kDestroySupport2A8RowsRva);
  const bool b = DeallocateRows(module, support118, 0, 8, 0x0C, 0x10, 0);
  reinterpret_cast<DestroyPart>(module + kDestroyScopeTailRva)(
      static_cast<std::byte *>(scope) + 0x118);
  const bool c = DeallocateRows(module, scope, 0x100, 0x108, 0x10C, 0x110,
                                kDestroyRows48Rva);
  const bool d = DeallocateRows(module, scope, 0x18, 0x20, 0x24, 0x28, 0);
  return a && b && c && d;
}

template <std::size_t N>
void *Aligned(std::array<std::byte, N> &storage) noexcept {
  return reinterpret_cast<void *>(
      (reinterpret_cast<std::uintptr_t>(storage.data()) + 15U) &
      ~std::uintptr_t{15U});
}

bool ReadNamedRansomCost(std::uintptr_t module, const Bindings &bindings,
                         const void *interaction_scope,
                         std::int32_t prisoner_id,
                         std::int64_t &raw) noexcept {
  raw = 0;
  if (interaction_scope == nullptr || bindings.hash_stable_key == nullptr)
    return false;
  void *database = reinterpret_cast<GetDatabase>(module +
                                                 kNamedDatabaseGetterRva)();
  if (database == nullptr) return false;
  const auto hash = static_cast<std::uint32_t>(bindings.hash_stable_key(
      nullptr, kRansomCost.data(),
      static_cast<std::uint32_t>(kRansomCost.size())));
  const void *definition = reinterpret_cast<LookupNamed>(
      module + kNamedLookupRva)(database, hash);
  if (definition == nullptr ||
      !ValidNamedDefinition(module, definition,
                            static_cast<std::int32_t>(hash)))
    return false;

  std::array<std::byte, 0x168 + 15> scope_storage{};
  std::array<std::byte, 0x118 + 15> support118_storage{};
  std::array<std::byte, 0x2A8 + 15> support2a8_storage{};
  std::array<std::byte, 0x28 + 15> internal_storage{};
  void *const scope = Aligned(scope_storage);
  void *const support118 = Aligned(support118_storage);
  void *const support2a8 = Aligned(support2a8_storage);
  void *const internal = Aligned(internal_storage);
  if (reinterpret_cast<CloneScope>(module + kCloneScopeRva)(
          scope, interaction_scope) != scope)
    return false;
  const std::uint64_t prisoner_payload =
      static_cast<std::uint32_t>(prisoner_id);
  std::memcpy(static_cast<std::byte *>(scope), &kCharacterScopeKind,
              sizeof(kCharacterScopeKind));
  std::memcpy(static_cast<std::byte *>(scope) + 8, &prisoner_payload,
              sizeof(prisoner_payload));
  reinterpret_cast<ConstructContainer>(module + kSupport118ConstructorRva)(
      support118);
  reinterpret_cast<ConstructContainer>(module + kSupport2A8ConstructorRva)(
      support2a8);
  std::memset(internal, 0, 0x28);
  std::memcpy(static_cast<std::byte *>(internal), &scope, sizeof(scope));
  std::memcpy(static_cast<std::byte *>(internal) + 0x10, &scope,
              sizeof(scope));
  std::memcpy(static_cast<std::byte *>(internal) + 0x18, &support118,
              sizeof(support118));
  std::uint8_t evaluation_flag = 0;
  bool evaluated = Read(reinterpret_cast<const void *>(
                            module + kEvaluationFlagRva),
                        0, evaluation_flag);
  std::memcpy(static_cast<std::byte *>(internal) + 0x20,
              &evaluation_flag, sizeof(evaluation_flag));
  alignas(16) std::array<std::byte, 0x28> descriptor{};
  const char *const key = kRansomCost.data();
  const auto key_size = static_cast<std::uint32_t>(kRansomCost.size());
  const std::int32_t unknown_id = -1;
  const std::uint8_t source_valid = 1;
  std::memcpy(descriptor.data(), &key, sizeof(key));
  std::memcpy(descriptor.data() + 8, &key_size, sizeof(key_size));
  std::memcpy(descriptor.data() + 0x10, &unknown_id, sizeof(unknown_id));
  std::memcpy(descriptor.data() + 0x24, &source_valid,
              sizeof(source_valid));
  std::int64_t first = 0;
  std::int64_t second = 0;
  auto *const eval = reinterpret_cast<EvaluateNamed>(module +
                                                     kEvaluateNamedFixedRva);
  if (evaluated)
    evaluated = eval(definition, &first, internal, nullptr,
                     descriptor.data()) == &first &&
                eval(definition, &second, internal, nullptr,
                     descriptor.data()) == &second &&
                first == second && first > 0;
  const bool destroyed =
      DestroyValueState(module, scope, support118, support2a8);
  void *database_after = reinterpret_cast<GetDatabase>(
      module + kNamedDatabaseGetterRva)();
  const void *definition_after = database_after == nullptr
                                     ? nullptr
                                     : reinterpret_cast<LookupNamed>(
                                           module + kNamedLookupRva)(
                                           database_after, hash);
  if (!evaluated || !destroyed || database_after != database ||
      definition_after != definition)
    return false;
  raw = first;
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

bool ExactOneOption(const void *context, std::int32_t expected) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  const void *definition = nullptr;
  std::int32_t definition_count = 0;
  if (!Read(context, 0, definition) || definition == nullptr ||
      !Read(definition, kDefinitionOptionCountOffset, definition_count) ||
      !Read(context, kOptionDataOffset, data) || data == nullptr ||
      !Read(context, kOptionCountOffset, count) ||
      definition_count != static_cast<std::int32_t>(kOptionCount) ||
      count != definition_count)
    return false;
  for (std::int32_t i = 0; i < count; ++i) {
    std::uint8_t selected = 0;
    if (!Read(data, static_cast<std::size_t>(i), selected) ||
        selected != static_cast<std::uint8_t>(i == expected))
      return false;
  }
  return true;
}

std::string_view FailureName(PlayerPrisonerRansomQuoteFailureV1 value) {
  switch (value) {
  case PlayerPrisonerRansomQuoteFailureV1::none: return "none";
  case PlayerPrisonerRansomQuoteFailureV1::not_evaluated:
    return "not_evaluated";
  case PlayerPrisonerRansomQuoteFailureV1::binding_unavailable:
    return "binding_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::frame_changed:
    return "frame_changed";
  case PlayerPrisonerRansomQuoteFailureV1::definition_unavailable:
    return "definition_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::role_unavailable:
    return "role_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::option_unavailable:
    return "option_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::payer_below_one_gold:
    return "payer_below_one_gold";
  case PlayerPrisonerRansomQuoteFailureV1::extortionate_gold_option_requires_valuation:
    return "extortionate_gold_option_requires_valuation";
  case PlayerPrisonerRansomQuoteFailureV1::final_can_send_false:
    return "final_can_send_false";
  case PlayerPrisonerRansomQuoteFailureV1::final_legality_unavailable:
    return "final_legality_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::quote_unavailable:
    return "quote_unavailable";
  }
  return "binding_unavailable";
}

} // namespace

PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuotePrivateV1(
    const Bindings &bindings, std::uintptr_t module,
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
      bindings.destroy_character_interaction_context == nullptr)
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
  std::int32_t actor = jailer_id;
  std::int32_t payer_id = prisoner_id;
  std::int32_t secondary_actor = -1;
  std::int32_t secondary_recipient = -1;
  std::int32_t intermediary = -1;
  bindings.redirect_character_interaction_roles(
      definition, &actor, &payer_id, &secondary_actor,
      &secondary_recipient, &intermediary);
  void *const payer = ResolveCharacter(module, payer_id);
  if (actor != jailer_id || payer_id == jailer_id ||
      secondary_recipient != prisoner_id || payer == nullptr ||
      secondary_actor != -1 || intermediary != -1) {
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
    reinterpret_cast<LocalOptionStep>(module + kClearLocalOptionsRva)(context);
    reinterpret_cast<SelectLocalOption>(module + kSelectLocalOptionRva)(
        context, option);
    const bool roles_ok = ContextRolesMatch(
        context, definition, jailer_id, payer_id, prisoner_id);
    const bool selected = roles_ok && ExactOneOption(context, option);
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
                              prisoner_id, amount_raw)
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
  for (std::int32_t option : {0, 1}) {
    alignas(8) std::array<std::byte, kContextSize> storage{};
    void *const context = storage.data();
    if (bindings.construct_character_interaction_context_all_roles(
            context, definition, actor, payer_id, secondary_actor,
            secondary_recipient, intermediary, nullptr) != context) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::binding_unavailable;
      return result;
    }
    reinterpret_cast<LocalOptionStep>(module + kClearLocalOptionsRva)(context);
    reinterpret_cast<SelectLocalOption>(module + kSelectLocalOptionRva)(
        context, option);
    const bool selected =
        ContextRolesMatch(context, definition, jailer_id, payer_id,
                          prisoner_id) &&
        ExactOneOption(context, option);
    const bool can_send = selected &&
        bindings.validate_character_interaction_context(context, nullptr);
    bindings.destroy_character_interaction_context(context);
    if (can_send) {
      result.failure = PlayerPrisonerRansomQuoteFailureV1::
          extortionate_gold_option_requires_valuation;
      return result;
    }
  }
  std::int64_t payer_gold_raw = 0;
  result.failure = ReadPayerGold(payer, payer_gold_raw) &&
                           payer_gold_raw < kFixedScale
                       ? PlayerPrisonerRansomQuoteFailureV1::payer_below_one_gold
                       : PlayerPrisonerRansomQuoteFailureV1::option_unavailable;
  return result;
}

std::string SerializePlayerPrisonerRansomQuotePrivateV1(
    const PlayerPrisonerRansomQuoteV1 &quote, std::uint64_t revision,
    std::int64_t date_raw, std::uint64_t proof_epoch) {
  std::string value =
      "{\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"action_surface_present\":false,\"status\":\"";
  value += quote.available ? "available" : "unavailable";
  value += "\",\"unavailable_reason\":";
  if (!quote.available) {
    value += '"';
    value += FailureName(quote.failure);
    value += '"';
    value += '}';
    return value;
  }
  if (revision == 0 || date_raw <= 0 || proof_epoch == 0 || quote.failure !=
                                             PlayerPrisonerRansomQuoteFailureV1::none ||
      quote.jailer_character_id <= 0 || quote.payer_character_id <= 0 ||
      quote.prisoner_character_id <= 0 || quote.quoted_gold_raw <= 0 ||
      (quote.selected_option != "gold" &&
       quote.selected_option != "current_gold") ||
      quote.recipient_answer_status_raw > 2)
    return {};
  value += "null,\"snapshot_id\":\"native:" +
           std::to_string(revision) + "\",\"public_revision\":" +
           std::to_string(revision) + ",\"native_revision\":" +
           std::to_string(revision) + ",\"proof_epoch\":" +
           std::to_string(proof_epoch) + ",\"date_raw\":" +
           std::to_string(date_raw) + ",\"definition_key\":\"ransom_interaction\","
           "\"jailer_character_id\":" + std::to_string(quote.jailer_character_id) +
           ",\"payer_character_id\":" + std::to_string(quote.payer_character_id) +
           ",\"prisoner_character_id\":" +
           std::to_string(quote.prisoner_character_id) +
           ",\"selected_option\":\"" + std::string(quote.selected_option) +
           "\",\"can_send\":true,\"quoted_gold_raw\":" +
           std::to_string(quote.quoted_gold_raw) +
           ",\"raw_scale\":100000,\"recipient_acceptance_raw\":" +
           std::to_string(quote.recipient_acceptance_raw) +
           ",\"recipient_answer_status_raw\":" +
           std::to_string(quote.recipient_answer_status_raw) +
           ",\"would_accept_now\":" +
           std::string(quote.would_accept_now ? "true" : "false") +
           ",\"amount_is_acceptance_time_quote\":" +
           std::string(quote.amount_is_acceptance_time_quote ? "true" : "false") +
           '}';
  return value;
}

} // namespace xar::ck3_11906
