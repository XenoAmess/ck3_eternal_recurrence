#pragma once
#include "xar_bridge/ck3_12004_holy_site_snapshot.hpp"
#include <array>
namespace xar::ck3_12004::religion::holy_site {
using NativeCanConfirm = bool(__fastcall *)(void *);
using NativeConfirm = void(__fastcall *)(void *);
using NativeRequirementsSettings = void *(__fastcall *)();
using NativeConfirmTooltip = void *(__fastcall *)(void *,void *);
using NativeStringDestroy = void(__fastcall *)(void *);
using NativeDecisionCost = const void *(__fastcall *)(const void *);
using NativeCostEvaluate = void(__fastcall *)(const void *,const void *,std::int64_t *);
using NativeCostAffordable = bool(__fastcall *)(const void *,const void *,const void *,void *);
using NativeCooldownLookup = const std::int32_t *(__fastcall *)(const void *,const void *);
struct AdoptionDetailBindings {
  bool enabled=false;
  std::uintptr_t image_base=0;
  void **holy_site_storage=nullptr;
  const std::uint32_t *selected_item_token=nullptr;
  const std::uint32_t *current_actor_reference=nullptr;
  ReadMemory read_memory=nullptr;
  void *read_context=nullptr;
  NativeCanConfirm can_confirm=nullptr;
  NativeConfirm confirm=nullptr;
  NativeRequirementsSettings requirements_settings=nullptr;
  NativeConfirmTooltip confirm_tooltip=nullptr;
  NativeStringDestroy destroy_string=nullptr;
  NativeConfirmTooltip requirements_description=nullptr,cost_description=nullptr;
  NativeDecisionCost decision_cost=nullptr;
  NativeCostEvaluate evaluate_cost=nullptr;
  NativeCostAffordable affordable_cost=nullptr;
  NativeCooldownLookup cooldown_lookup=nullptr;
  void **character_storage=nullptr,**decision_clock=nullptr;
};
struct AdoptionDetailSnapshot {
  bool available=false;
  std::uint64_t capture_epoch=0;
  std::int32_t date_raw=0,played_character_id=-1;
  std::uint32_t requested_holy_site_id=0xFFFFFFFFU;
  bool detail_present=false,root_present=false;
  std::uint32_t detail_actor_id=0xFFFFFFFFU;
  std::uint32_t current_actor_id=0xFFFFFFFFU;
  std::int32_t decision_option_id=-1;
  std::string decision_key;
  std::int32_t selected_index=-1;
  std::uint32_t candidate_count=0;
  std::uint32_t selected_item_token=0;
  std::uint32_t parameter_holy_site_id=0xFFFFFFFFU,selected_holy_site_id=0xFFFFFFFFU;
  bool native_can_confirm=false;
  bool bypass_requirements_observed=false;
  std::uint8_t bypass_requirements_raw=0;
  bool confirm_tooltip_available=false;
  std::string confirm_tooltip;
  bool native_detail_context_verified=false;
  bool native_requirements_description_available=false,native_cost_description_available=false;
  std::string native_requirements_description,native_cost_description;
  bool native_resource_quote_available=false,native_affordable=false;
  std::array<std::int64_t,10> native_resource_vector_raw{};
  bool native_decision_cooldown_observed=false,native_decision_cooldown_present=false;
  std::int32_t native_decision_clock_raw=0,native_decision_expiry_raw=0;
  bool native_decision_cooldown_active=false;
  std::string native_planning_unavailable_reason;
  bool parameter_and_selection_match=false;
  // Provider-private owned-window pointers never cross the public wire.
  const void *owner=nullptr,*detail=nullptr,*root=nullptr,*controller=nullptr,*context=nullptr;
  std::string unavailable_reason;
};
inline constexpr std::string_view kAdoptionDetailQueryStep="query-player-holy-site-adoption-detail-v1";
AdoptionDetailBindings BindHolySiteAdoptionDetailImage12004(std::uintptr_t,std::string_view) noexcept;
bool ReadHolySiteAdoptionDetail12004(const AdoptionDetailBindings &,const void *jomini_owner,
    const ck3_12002::religion::Context &,std::uint32_t requested_id,AdoptionDetailSnapshot &) noexcept;
std::string SerializeHolySiteAdoptionDetail12004(const AdoptionDetailSnapshot &);
std::string SerializeHolySiteAdoptionDetailCommand12004(const AdoptionDetailSnapshot &,
    std::string_view request_id,std::uint64_t snapshot_revision,std::int64_t date_raw);
// Original Confirm revalidates native legality itself. Return is ACK only;
// callers require a visible exact detail and an independent Faith after-state.
bool ConfirmHolySiteAdoptionDetail12004(const AdoptionDetailBindings &,
    const AdoptionDetailSnapshot &,bool &native_attempted) noexcept;
}
