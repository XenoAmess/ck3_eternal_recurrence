#pragma once

#include "xar_bridge/ck3_12003_player_repentance_context.hpp"
#include "xar_bridge/ck3_12003_repentance_fallback.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy.hpp"

#include <vector>

namespace xar::ck3_12003::religion::repentance_candidates {
using ObjectGetter = void *(*)(void *);
using LeaseLiege = std::int32_t *(*)(void *, std::int32_t *, std::int32_t);
using TopLiege = std::int32_t *(*)(std::int32_t *, std::int32_t);
using CapitalBarony = std::int32_t *(*)(void *, std::int32_t *);
struct Scope16 { std::uint32_t kind = 5; std::uint32_t padding = 0; std::uint64_t id = UINT32_MAX; };
static_assert(sizeof(Scope16) == 16);
using ClericalRegion = Scope16 *(*)(void *, Scope16 *, const Scope16 **);
using ClergyReader = bool (*)(const ck3_12002::religion::clergy::Bindings &,
    std::int32_t, ck3_12002::religion::clergy::CurrentClergySeat &) noexcept;

struct Bindings {
  bool enabled = false;
  ck3_12002::CoreBindings core{};
  ck3_12002::religion::clergy::Bindings clergy{};
  ClergyReader read_clergy = nullptr;
  void **game_state_slot = nullptr;
  void **title_storage_slot = nullptr;
  ObjectGetter authority = nullptr;
  LeaseLiege lease_liege = nullptr;
  TopLiege top_lease_liege_direct = nullptr;
  CapitalBarony capital_barony = nullptr;
  ClericalRegion clerical_region = nullptr;
};
struct Role : repentance::Sample {
  const char *source = "not_sampled";
  std::optional<std::int32_t> character_id;
};
struct Candidate {
  std::int32_t requested_recipient_character_id = -1;
  std::vector<const char *> sources;
  repentance::Context terms{};
};
struct Context {
  bool available = false;
  bool fallback_sources_sampled = false;
  bool fallback_source_traversal_complete = false;
  bool source_candidate_evaluation_complete = false;
  std::size_t fallback_new_candidate_count = 0;
  const char *unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::array<Role, 5> roles{};
  std::optional<std::int32_t> capital_barony_title_id;
  std::optional<std::int32_t> capital_county_title_id;
  std::optional<std::int32_t> capital_clerical_region_title_id;
  std::vector<Candidate> candidates;
  std::optional<std::int32_t> first_observed_ordinary_legal_recipient_character_id;
};
Bindings BindRepentanceRecipientCandidatesImage12003(std::uintptr_t,
    std::string_view, const ck3_12002::CoreBindings &,
    const ck3_12002::religion::clergy::Bindings &) noexcept;
bool ReadRepentanceRecipientCandidates12003(const Bindings &,
    const repentance::Bindings &, void *played_character,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    Context &) noexcept;
// Merge observed stock fallback roles; duplicate current IDs reuse their terms.
bool AppendRepentanceFallbackRecipients12003(const repentance::Bindings &,
    void *played_character, std::int32_t actor, std::int32_t date,
    std::uint64_t epoch, const repentance_fallback::Context &, Context &) noexcept;
std::string SerializeRepentanceRecipientCandidates12003(const Context &);
} // namespace xar::ck3_12003::religion::repentance_candidates
