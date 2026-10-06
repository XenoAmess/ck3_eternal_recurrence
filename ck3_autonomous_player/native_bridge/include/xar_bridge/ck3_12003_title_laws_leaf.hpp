#pragma once

#include "xar_bridge/ck3_12003_title_properties_leaf.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// SOURCEONLY, not compiled/installed/executed. ROOT's owning-thread mailbox
// supplies the exact current paused revision and actual Faith-bound Title.
namespace xar::ck3_12003::title_laws {

inline constexpr std::uintptr_t kCLawPrimaryVtableRva = 0x48B8898;
inline constexpr std::uint32_t kCLawDatabaseObjectMagic = 0x4744624F;
inline constexpr std::string_view kExpectedLawKey =
    "temporal_head_of_faith_succession_law";
inline constexpr std::int32_t kMaximumLaws = 256;
inline constexpr std::uint64_t kMaximumKeyBytes = 256;

struct NamedLaw {
  std::uint32_t native_definition_id = 0;
  std::string key;
};

struct Observation {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::uint32_t requested_title_full_id = UINT32_MAX;
  std::optional<std::int32_t> native_count;
  std::optional<std::vector<NamedLaw>> complete_laws;
  std::optional<bool> temporal_head_of_faith_succession_law_member;
};

bool Read(const title_properties::Bindings &bindings,
          const game::Snapshot &paused_frame,
          std::uint32_t requested_title_full_id, Observation &output) noexcept;

} // namespace xar::ck3_12003::title_laws
