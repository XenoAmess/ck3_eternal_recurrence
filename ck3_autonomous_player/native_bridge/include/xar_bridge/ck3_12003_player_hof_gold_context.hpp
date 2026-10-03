#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"
#include "xar_bridge/religion_rite_governance12002_head.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::hof_gold {

inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::string_view kSchema =
    "ck3_12003_player_head_of_faith_gold_context_v1";
inline constexpr std::string_view kInteractionKey = "hof_ask_for_gold_interaction";
inline constexpr std::string_view kGoldValueKey = "hof_ask_for_gold_request_value";
inline constexpr std::int64_t kRawScale = 100000;

using HeadBindings = ck3_12002::religion::head::Bindings;
using HeadContext = ck3_12002::religion::head::Context;
using HeadReader = bool (*)(const HeadBindings &, std::uint64_t,
                            HeadContext &) noexcept;
using NamedFixedReader = bool (*)(std::uintptr_t, const void *, std::uint32_t,
    std::uint32_t, std::uint32_t, std::string_view, std::uint32_t,
    std::int64_t &) noexcept;
using DatabaseGetter = void *(*)();
using StableHash = std::int32_t (*)(void *, const char *, std::uint32_t);
using DefinitionLookup = void *(*)(void *, std::int32_t);
using TwoRoleConstructor = void *(*)(void *, void *, std::int32_t,
                                     std::int32_t, void *, bool);
using MenuShown = bool (*)(void *);
using SetOption = void (*)(void *, std::uint32_t, bool);
using ReadOption = bool (*)(void *, std::uint32_t);
using OuterAnswer = std::uint8_t (*)(void *, std::uint8_t, std::uint8_t,
                                     void *, void *);

// Existing main-owner/core, heads and named-value readers are dependencies.
// No interaction send or command constructor is exposed by this leaf.
struct Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::ContextBindings interaction{};
  HeadBindings heads{};
  HeadReader read_heads = nullptr;
  NamedFixedReader read_named_fixed = nullptr;
  DatabaseGetter get_database = nullptr;
  StableHash stable_hash = nullptr;
  DefinitionLookup lookup_definition = nullptr;
  TwoRoleConstructor construct_two_role = nullptr;
  MenuShown is_shown = nullptr;
  SetOption set_option = nullptr;
  ReadOption read_option = nullptr;
  DatabaseGetter named_database = nullptr;
  OuterAnswer outer_answer = nullptr;
};

struct Sample {
  bool available = false;
  const char *reason = "not_sampled";
};
struct BoolSample : Sample { std::optional<bool> value; };
struct Identity : Sample {
  std::optional<std::uint32_t> actor_rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> faith_main_rite_id;
  std::optional<std::uint32_t> requested_head_character_id;
  std::optional<std::uint32_t> head_title_id;
  std::optional<std::int32_t> effective_actor_id;
  std::optional<std::int32_t> effective_recipient_id;
  std::optional<std::int32_t> secondary_actor_id;
  std::optional<std::int32_t> secondary_recipient_id;
  std::optional<std::int32_t> intermediary_id;
  std::optional<std::int32_t> sixth_role_id;
};
struct Options : Sample {
  std::optional<std::uint32_t> declared_count;
  std::optional<std::uint32_t> selected_count;
  std::optional<bool> all_unselected;
};
struct DeclaredCosts : Sample {
  std::optional<std::array<std::int64_t, 10>> raw;
};
struct AcceptancePreview {
  bool recipient_score_available = false;
  const char *recipient_score_reason = "not_sampled";
  std::optional<std::int64_t> recipient_score_raw;
  bool intermediary_score_available = false;
  const char *intermediary_score_reason = "not_sampled";
  std::optional<std::int64_t> intermediary_score_raw;
  bool outer_available = false;
  const char *outer_reason = "not_sampled";
  std::optional<std::uint8_t> outer_status;
};
struct GoldProceeds : Sample {
  std::optional<std::uint32_t> root_character_id;
  std::optional<std::uint32_t> actor_character_id;
  std::optional<std::uint32_t> recipient_character_id;
  std::optional<std::int64_t> amount_raw;
};
struct AcceptanceEffectConsequence : Sample {
  std::optional<std::int64_t> piety_raw;
  std::optional<bool> hook_selected;
};
struct Context {
  bool available = false;
  const char *unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> definition_stable_hash;
  Identity identity{};
  Options options{};
  BoolSample shown{};
  BoolSample can_send{};
  DeclaredCosts declared_costs{};
  BoolSample auto_accept{};
  AcceptancePreview acceptance_preview{};
  GoldProceeds gold_proceeds{};
  AcceptanceEffectConsequence acceptance_effect_consequence{};
};

Bindings BindHeadOfFaithGoldImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256,
    const ck3_12002::ContextBindings &interaction, const HeadBindings &heads,
    HeadReader read_heads, NamedFixedReader read_named_fixed) noexcept;
// Called only from the existing paused application-main query owner.
bool ReadHeadOfFaithGoldContext12003(const Bindings &, void *played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context &) noexcept;
std::string SerializeHeadOfFaithGoldContext12003(const Context &);

} // namespace xar::ck3_12003::religion::hof_gold
