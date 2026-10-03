#pragma once

#include "xar_bridge/ck3_12003_mercenary_candidates.hpp"
#include "xar_bridge/ck3_12003_mercenary_final_terms.hpp"
#include "xar_bridge/ck3_12003_mercenary_position.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::mercenary {

inline constexpr std::string_view kPlayerMercenaryContextSchema12003 =
    "ck3_12003_player_mercenary_context_v1";
inline constexpr std::string_view kPlayerMercenaryContextStep12003 =
    "query-player-mercenary-context-v1";
inline constexpr std::string_view kPlayerMercenaryContextExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";

struct ContextBindings {
  CandidateBindings candidates;
  FinalTermsBindings final_terms;
  xar::ck3_12003::MercenaryPositionBindingsV1 position;
  xar::ck3_12003::MercenaryPositionWorldV1 world;
};

struct Row {
  Candidate candidate;
  FinalTerms final_terms;
  xar::ck3_12003::MercenaryPositionObservationV1 location;
};

struct Context {
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::int32_t actor_character_id = -1;
  std::int32_t date_raw = -1;
  std::uint64_t capture_epoch = 0;
  std::vector<Row> rows;
};

// Owner thread, paused played-character frame. Rows contain copied values only;
// context availability describes enumeration, independently of each row field.
bool ReadPlayerMercenaryContext12003(const ContextBindings &, void *actor,
    std::int32_t actor_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context &) noexcept;

std::string SerializePlayerMercenaryContext12003(const Context &);

// The query completion envelope is distinct from availability of native data.
// The caller has already verified the paused frame and its native revision.
std::string SerializePlayerMercenaryContextResultV1(const Context &,
    std::string_view request_id, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision);

} // namespace xar::ck3_12003::mercenary
