#pragma once

#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <array>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {

// Exact CK3 1.19.0.6, EXE SHA-256 2D00FF31...83DB86. This private probe
// identifies the native GameSetup owner and selected-model indices; it never
// infers a bookmark character from repeated GUI widget order.
struct FrontendBookmarkModelProbeV1 {
  std::array<std::uint64_t, 3> gui_chain_vtable_rvas{};
  std::int32_t interface_application_chain_level = -1;
  std::uint64_t setup_view_vtable_rva = 0;
  std::uint64_t selected_bookmark_vtable_rva = 0;
  bool setup_view_matches_bookmarks_root = false;
  std::uint64_t selected_bookmark_group_vtable_rva = 0;
  std::string selected_bookmark_group_key;
  bool selected_bookmark_group_key_available = false;
  std::string selected_bookmark_key;
  bool selected_bookmark_key_available = false;
  std::uint64_t selected_date_raw = 0;
  bool selected_date_raw_available = false;
  std::int32_t selected_character_index = -1;
  std::int32_t hovered_character_index = -1;
  bool model_indices_available = false;
  // 0x3358EF0/0x3359030 initialize/copy this native collection layout;
  // 0x3346800 identifies the generic base/capacity/count/allocator fields.
  std::uint64_t bookmark_character_base_raw = 0;
  std::uint32_t bookmark_character_capacity_raw = 0;
  std::uint32_t bookmark_character_count_raw = 0;
  std::int32_t bookmark_character_allocator_raw = -1;
  std::int32_t bookmark_character_count = -1;
  std::array<std::string, 16> bookmark_character_keys{};
  bool bookmark_character_keys_available = false;
  std::array<std::string, 16> government_type_keys{};
  bool government_type_keys_available = false;
  // The source key identifies a candidate in the current native vector;
  // its runtime government/date and final selection are separate gates.
  std::int32_t supported_1066_candidate_index = -1;
  bool supported_1066_candidate_present = false;
  bool supported_1066_candidate_feudal = false;
  bool candidate_identity_ready = false;
  std::string unavailable_reason;
};

using FrontendBookmarkGovernmentGetterV1 =
    void *(*)(void *opaque_context,
              const void *bookmark_character) noexcept;

bool ProbeFrontendBookmarkModelV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *bookmarks_root,
    FrontendBookmarkModelProbeV1 &output,
    FrontendBookmarkGovernmentGetterV1 fixture_government_getter =
        nullptr) noexcept;

} // namespace xar::ck3_11906
