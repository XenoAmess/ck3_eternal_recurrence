#pragma once

#include "xar_bridge/ck3_12002_context.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::seek_indulgences {

inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::string_view kSchema =
    "ck3_12003_player_seek_indulgences_terms_v1";
inline constexpr std::string_view kInteractionKey = "seek_indulgences_interaction";

using DatabaseGetter = void *(*)();
using StableHash = std::int32_t (*)(void *, const char *, std::uint32_t);
using DefinitionLookup = void *(*)(void *, std::int32_t);
using TwoRoleConstructor = void *(*)(void *, void *, std::int32_t,
                                     std::int32_t, void *, bool);
using MenuShown = bool (*)(void *);
using SetOption = void (*)(void *, std::uint32_t, bool);
using ReadOption = bool (*)(void *, std::uint32_t);

// A disposable native preview, using the cached .3 repentance/HoF ABI.
// This leaf has no interaction submission or resource/acceptance reader.
struct Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::ContextBindings interaction{};
  DatabaseGetter get_database = nullptr;
  StableHash stable_hash = nullptr;
  DefinitionLookup lookup_definition = nullptr;
  TwoRoleConstructor construct_two_role = nullptr;
  MenuShown is_shown = nullptr;
  SetOption set_option = nullptr;
  ReadOption read_option = nullptr;
};

struct Sample {
  bool available = false;
  const char *reason = "not_sampled";
};
struct BoolSample : Sample { std::optional<bool> value; };
struct Identity : Sample {
  std::uint32_t requested_recipient_character_id = UINT32_MAX;
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
};

Bindings BindSeekIndulgencesTermsImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256,
    const ck3_12002::ContextBindings &interaction) noexcept;
// Called only by the existing paused application-main query owner. Actor is
// the current played character; requested recipient is a complete uint32 ID.
bool ReadSeekIndulgencesTerms12003(const Bindings &, void *played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, std::uint32_t requested_recipient_character_id,
    Context &) noexcept;
std::string SerializeSeekIndulgencesTerms12003(const Context &);

} // namespace xar::ck3_12003::religion::seek_indulgences
