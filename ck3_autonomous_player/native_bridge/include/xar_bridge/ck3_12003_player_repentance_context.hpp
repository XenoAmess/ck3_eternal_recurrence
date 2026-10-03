#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_phase_character.hpp"
#include "xar_bridge/religion_rite_governance12002_head.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::repentance {

inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::string_view kSchema =
    "ck3_12003_player_repentance_context_v1";
inline constexpr std::string_view kInteractionKey = "declaration_of_repentance_interaction";
inline constexpr std::int64_t kRawScale = 100000;

using HeadBindings = ck3_12002::religion::head::Bindings;
using HeadContext = ck3_12002::religion::head::Context;
using HeadReader = bool (*)(const HeadBindings &, std::uint64_t,
                            HeadContext &) noexcept;
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

// Existing paused owner/core, fresh heads and single-trait readers are dependencies.
// No interaction send or command constructor is exposed by this leaf.
struct Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::ContextBindings interaction{};
  HeadBindings heads{};
  HeadReader read_heads = nullptr;
  ck3_12002::phase_character::Bindings traits{};
  DatabaseGetter get_database = nullptr;
  StableHash stable_hash = nullptr;
  DefinitionLookup lookup_definition = nullptr;
  TwoRoleConstructor construct_two_role = nullptr;
  MenuShown is_shown = nullptr;
  SetOption set_option = nullptr;
  ReadOption read_option = nullptr;
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
  std::optional<std::uint32_t> requested_recipient_character_id;
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
struct Context {
  const char *recipient_source = "faith_religious_head_holder_candidate";
  const char *candidate_scope = "faith_head_only";
  bool available = false;
  const char *unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> definition_stable_hash;
  BoolSample player_excommunication{};
  Identity identity{};
  Options options{};
  BoolSample shown{};
  BoolSample can_send{};
  DeclaredCosts declared_costs{};
  BoolSample auto_accept{};
  AcceptancePreview acceptance_preview{};
};

Bindings BindRepentanceImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256,
    const ck3_12002::ContextBindings &interaction, const HeadBindings &heads,
    HeadReader read_heads, const ck3_12002::phase_character::Bindings &traits) noexcept;
// Called only from the existing paused application-main query owner.
bool ReadRepentanceContext12003(const Bindings &, void *played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context &) noexcept;
// Read an actual role-derived candidate through the same final native context.
bool ReadRepentanceRecipientContext12003(const Bindings &, void *played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, std::int32_t requested_recipient_character_id,
    Context &) noexcept;
std::string SerializeRepentanceContext12003(const Context &);

} // namespace xar::ck3_12003::religion::repentance
