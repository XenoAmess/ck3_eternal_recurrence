#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge::character_skill_effect12004 {
inline constexpr std::string_view kExeSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::size_t kMaxBreakdownBytes = 32768;
struct Frame {
  std::uint64_t revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  bool owner_thread = false, paused = false, map_ready = false;
  friend bool operator==(const Frame &, const Frame &) = default;
};
struct SkillItem { std::int32_t skill = -1; std::uint32_t character_id = 0xFFFFFFFFU; };
static_assert(sizeof(SkillItem) == 8);
static_assert(offsetof(SkillItem, character_id) == 4);
using ReadMemory = bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
using ReadFrame = bool (*)(void *, Frame &) noexcept;
using ReadLevel = bool (*)(void *, std::uintptr_t actual_actor, std::int32_t &) noexcept;
using ReadBreakdown = bool (*)(void *, const SkillItem &, std::string &) noexcept;
enum class CallbackProvenance : std::uint8_t { unavailable, exact4_native, owned_fixture };
// Core callbacks are leaf seams. A future production factory must bind only the
// exact disk-proven native getter/owned-string/destructor chain. It must not
// expose fixture callbacks, claimed provenance, or arbitrary function pointers
// as an MCP/request argument. See NATIVE-BINDING-CONTRACT.json.
struct Environment {
  bool enabled = false;
  std::string_view executable_sha256{};
  std::uintptr_t image_base = 0;
  void *context = nullptr;
  ReadMemory read_memory = nullptr;
  ReadFrame read_frame = nullptr;
  ReadLevel read_level = nullptr;
  ReadBreakdown read_breakdown = nullptr;
  CallbackProvenance callback_provenance = CallbackProvenance::unavailable;
  bool allow_owned_fixture = false; // Never set by production factory.
};
struct Request {
  Frame expected{};
  std::uint32_t character_id = 0xFFFFFFFFU;
  std::int32_t skill = 0; // Diplomacy; finite six-skill enum only.
};
struct Result {
  bool available = false, two_pass_stable = false;
  std::string unavailable_reason = "not_read";
  Frame frame{};
  std::uint32_t character_id = 0xFFFFFFFFU;
  std::int32_t requested_skill = -1;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::array<std::int32_t, 6>> current_skill_points;
  std::optional<std::int32_t> effective_devotion_level;
  std::optional<std::int64_t> devotion_total_raw;
  std::optional<std::string> actual_skill_breakdown;
  CallbackProvenance callback_provenance = CallbackProvenance::unavailable;
  bool read_only = true, gameplay_command_submitted = false;
  bool skill_cache_refreshed = false, cache_generation_time_known = false;
  // This first slice reads actual actor values and original breakdown only.
  // Neither a definition, an expected coefficient nor a total is site evidence.
  bool site_attribution_observed = false;
  std::optional<std::int64_t> selected_site_contribution_raw;
};
bool Read(const Environment &, const Request &, Result &) noexcept;
} // namespace xar::bridge::character_skill_effect12004
