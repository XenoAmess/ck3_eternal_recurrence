#pragma once
#include "xar_bridge/clerical_puppet_preview_context12004.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_11906 {
struct FaithPowerPresentationTargetV1 {
 std::uint32_t index=0;
 std::string kind,runtime_name;
 std::optional<std::string> definition_key,label;
 bool effective_visible=false,enabled=false;
};
struct FaithPowerPresentationTextV1 {
 std::string runtime_name,text,sha256;
};
struct FaithPowerHoldingTracksObservation12004 {
 bool available=false,owner_bound=false;
 std::string unavailable_reason;
 std::optional<bool> window_exists,root_exists,effective_visible;
 std::optional<std::int32_t> selection_category_id,selection_mode,selection_action_raw;
 std::optional<std::string> selected_building_key;
};
struct FaithPowerPresentationObservationV1 {
 bool requested=false,available=false;
 std::string status="not_requested",unavailable_reason;
 std::optional<std::uint32_t> subject_id,target_index;
 std::optional<std::string> active_tab,target_kind,receipt_id;
 std::optional<std::uint64_t> action_owner_epoch,observation_owner_epoch;
 std::optional<bool> post_window_visible;
 bool source_bound=false,tab_observed=false,picker_observed=false,preview_observed=false;
 std::optional<FaithPowerHoldingTracksObservation12004> holding_tracks;
 struct ClericalPreview {
   bool available=false,root_bound=false;
   std::optional<bool> window_visible;
   std::string phase="none";
   ck3_12004::clerical_preview::Context default_context{};
   std::optional<ck3_12004::clerical_preview::Context> window_context;
 };
 std::optional<ClericalPreview> clerical_preview;
 bool hover_source_matches=false,tooltip_stack_observed=false,tooltip_root_visible=false;
 std::optional<std::int32_t> tooltip_active_count,tooltip_top_locked;
 bool leave_observed=false,cache_complete=false,rendered_pixels_observed=false;
 std::vector<FaithPowerPresentationTextV1> cache_texts;
 std::vector<FaithPowerPresentationTargetV1> targets;
};
} // namespace xar::ck3_11906
