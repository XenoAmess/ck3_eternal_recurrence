#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {
inline constexpr std::string_view kTitleOwnLawsV1Capability =
    "game.command.query-title-own-laws-v1-ID";
inline constexpr std::string_view kTitleOwnLawsV1Schema =
    "xar.ck3.title-own-laws.v1";

struct TitleOwnLawV1 {
  std::uint32_t native_definition_id = 0;
  std::string key;
};

// Physical own-law rows. No effective-policy or scripted-trigger equivalence
// is implied by this snapshot, including when the complete array is empty.
struct TitleOwnLawsV1 {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::uint32_t title_id = UINT32_MAX;
  std::optional<std::int32_t> native_law_count;
  std::optional<std::vector<TitleOwnLawV1>> laws;
  std::optional<bool> single_heir_member;
};

enum class ReadTitleOwnLawsV1Result { unavailable, available };
} // namespace xar::game
