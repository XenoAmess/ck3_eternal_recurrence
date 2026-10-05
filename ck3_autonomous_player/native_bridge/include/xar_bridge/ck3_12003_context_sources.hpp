#pragma once

#include "xar_bridge/ck3_12003_context_locale.hpp"

#include "xar_bridge/battle_context_source_inputs_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

// Default reader copies in-process memory. An injected copy reader exercises
// exactly the production collector with caller-owned fake memory.
using ContextSourceReadMemoryV1 = bool (*)(void *context, const void *address,
                                         void *output, std::size_t bytes) noexcept;
struct ContextSourceTokenSliceV1 {
  const char *data = nullptr;
  std::int32_t length = 0;
  std::uint8_t flag = 0;
  std::uint8_t reserved[3]{};
};
struct ContextSourceTokenCursorV1 { void *node = nullptr; };
#include "xar_bridge/ck3_12003_middle_helper_sources.inc.hpp"
#include "xar_bridge/ck3_12003_trait_stage_sources.inc.hpp"
#include "xar_bridge/ck3_12003_absent_recipient_sources.inc.hpp"
#include "xar_bridge/ck3_12003_uncached_recipient_sources.inc.hpp"
#include "xar_bridge/ck3_12003_conference_sources.inc.hpp"
#include "xar_bridge/ck3_12003_provider_bucket_bindings.inc.hpp"
#include "xar_bridge/ck3_12003_qualifier_28bc0d0_sources.inc.hpp"
#include "xar_bridge/ck3_12003_list_predicate_2530dd0_sources.inc.hpp"
#include "xar_bridge/ck3_12003_gated_temporary_tail_sources.inc.hpp"
#include "xar_bridge/ck3_12003_after_gated_tail_sources.inc.hpp"
#include "xar_bridge/ck3_12003_provider192_and2920850_sources.inc.hpp"
#include "xar_bridge/ck3_12003_following_2920b50_sources.inc.hpp"
#include "xar_bridge/ck3_12003_following_2bca620_sources.inc.hpp"
#include "xar_bridge/ck3_12003_following_312a950_sources.inc.hpp"
static_assert(sizeof(ContextSourceTokenSliceV1) == 16);
static_assert(offsetof(ContextSourceTokenSliceV1, length) == 8);
static_assert(offsetof(ContextSourceTokenSliceV1, flag) == 0xC);
static_assert(sizeof(ContextSourceTokenCursorV1) == 8);
using ContextSourceExistingTokenLookupV1 = ContextSourceTokenCursorV1 *(*)(
    void *map_header, ContextSourceTokenCursorV1 *output,
    const ContextSourceTokenSliceV1 *slice);
struct ContextSourceBindingsV1 {
  ContextSourceLocaleBindingsV1 current_locale{};
  bool enabled = false;
  // Reused Army slots/provider; only the second-object pair is a new binding.
  bool pre_291e210_1640_enabled = false;
  const void *army_internal_storage_slot = nullptr;
  const void *army_internal_fallback_slot = nullptr;
  const void *pre_291e210_second_storage_slot = nullptr;
  const void *pre_291e210_second_fallback_slot = nullptr;
  bool later_direct_enabled = false;
  const void *later_ordered_fallback_header = nullptr;
  const void *later_ordered_storage_slot = nullptr;
  const void *later_ordered_fallback_slot = nullptr;
  const void *later_guarded_fallback_slot = nullptr;
  bool helper_291f0a0_enabled = false;
  const void *helper_manager_slot = nullptr;
  const void *helper_third_storage_slot = nullptr;
  const void *helper_third_fallback_slot = nullptr;
  const void *helper_invalid_character_fallback_slot = nullptr;
  const void *helper_range_first_threshold_slot = nullptr;
  const void *helper_range_last_threshold_slot = nullptr;
  const void *helper_default_pc = nullptr;
  const void *helper_default_pc_guard_slot = nullptr;
  const void *helper_source_pointer_fallback_header = nullptr;
  const void *helper_source_pointer_fallback_guard_slot = nullptr;
  bool remaining_helpers_enabled = false;
  const void *remaining_character_storage_slot = nullptr;
  const void *remaining_character_fallback_slot = nullptr;
  const void *remaining_government_fallback_slot = nullptr;
  const void *remaining_government_default_pc = nullptr;
  const void *remaining_government_default_guard_slot = nullptr;
  const void *remaining_culture_mapped_default_pc = nullptr;
  const void *remaining_culture_mapped_default_guard_slot = nullptr;
  const void *remaining_nested_mapped_default_guard_slot = nullptr;
  bool tail_direct_enabled = false;
  const void *tail_weighted_storage_slot = nullptr;
  const void *tail_weighted_fallback_slot = nullptr;
  ContextSourceMiddleHelpersBindingsV1 middle_helpers{};
  ContextSourceTraitStageBindingsV1 trait_stage{};
  ContextSourceAbsentRecipientBindingsV1 absent_recipient{};
  ContextSourceUncachedRecipientBindingsV1 uncached_recipient{};
  bool tail_prefix_enabled = false;
  const void *tail_prefix_default_relation_slot = nullptr;
  bool helper_2922070_enabled = false;
  const void *helper_2922070_descendant_storage_slot = nullptr;
  const void *helper_2922070_descendant_fallback_slot = nullptr;
  const void *helper_2922070_descendant_fallback_header = nullptr;
  const void *helper_2922070_membership_storage_slot = nullptr;
  const void *helper_2922070_membership_fallback_slot = nullptr;
  const void *helper_2922070_membership_fallback_header = nullptr;
  ContextSourceConferenceBindingsV1 conference_24b1d00{};
  ProviderBucket291c5b2BindingsV1 provider_bucket_291c5b2{};
  ContextSourceQualifier28bc0d0BindingsV1 qualifier_28bc0d0{};
  ContextSourceListPredicate2530dd0BindingsV1 list_predicate_2530dd0{};
  ContextSourceGatedTemporaryTailBindingsV1 gated_temporary_tail{};
  ContextSourceAfterGatedTailBindingsV1 after_gated_tail{};
  ContextSourceProvider192And2920850BindingsV1 provider192_and2920850{};
  ContextSourceFollowing2920b50BindingsV1 following_2920b50{};
  ContextSourceFollowing2bca620BindingsV1 following_2bca620{};
  ContextSourceFollowing312a950BindingsV1 following_312a950{};
  void *(*provider)() = nullptr;
  bool post_291d7e0_sources_enabled = false;
  const void *post_ab_object_fallback_slot = nullptr;
  const void *post_ab_signed_character_threshold_slot = nullptr;
  const void *post_ab_static_inline_source_list_header = nullptr;
  const void *lifestyle_fallback_header = nullptr;
  const void *house_extra_fallback_header = nullptr;
  const void *first_storage_slot = nullptr;
  const void *first_fallback_slot = nullptr;
  const void *second_storage_slot = nullptr;
  const void *second_fallback_slot = nullptr;
  const void *source_fallback_header = nullptr;
  const void *conditional_a_fallback_properties = nullptr;
  const void *selector_a_storage_slot = nullptr;
  const void *selector_a_initial_fallback_slot = nullptr;
  const void *selector_a_second_storage_slot = nullptr;
  const void *selector_a_second_fallback_slot = nullptr;
  const void *selector_b_storage_slot = nullptr;
  const void *selector_b_fallback_slot = nullptr;
  void *(*government)(void *character) = nullptr;
  const void *condition_registry = nullptr;
  const void *condition_fallback_object = nullptr;
  const void *condition_registry_guard = nullptr;
  const void *condition_fallback_guard = nullptr;
  const void *token_manager_slot = nullptr;
  const void *prefix_classifier_locale_flag = nullptr;
  const void *prefix_classifier_table_slot = nullptr;
  ContextSourceExistingTokenLookupV1 existing_token_lookup = nullptr;
  ContextSourceReadMemoryV1 read_memory = nullptr;
  void *read_context = nullptr;
};

// Exact-build address binding only: no process discovery or native getter.
ContextSourceBindingsV1 BindContextSourceInputs12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Called from the owning-thread paused current-person query. Direct selected
// headers, full-ID generation resolution and Definition+40 property operands.
// It neither calls lazy initialization/writers nor reads an old final context.
game::BattleCurrentPersonContextSourceInputsSnapshotV1
ReadCurrentContextSourceInputs12003(const ContextSourceBindingsV1 &,
                                   const void *character,
                                   std::int32_t character_id) noexcept;

} // namespace xar::ck3_12002
