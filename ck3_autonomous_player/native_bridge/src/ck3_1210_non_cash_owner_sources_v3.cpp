#include "xar_bridge/ck3_1210_non_cash_owner_sources_v3.hpp"
#include <cstring>
#if defined(_MSC_VER)
#include <windows.h>
#endif
namespace xar::ck3_1210 {
namespace {
std::uintptr_t CurrentModule() noexcept {
#if defined(_MSC_VER)
  return reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
#else
  return 0; // No physical Win64 image witness on unsupported platforms.
#endif
}
bool SameCore(const CoreSnapshotPrefix &a,const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed &&
      a.clock.paused==b.clock.paused && a.local_player_id==b.local_player_id &&
      a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
      a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
void *ResolveSafe(const CoreBindings &b,std::int32_t id) noexcept {
#if defined(_MSC_VER)
  __try {return ResolveCoreCharacter(b,id);} __except(EXCEPTION_EXECUTE_HANDLER){return nullptr;}
#else
  return ResolveCoreCharacter(b,id);
#endif
}
bool Copy(void *,std::uintptr_t address,void *target,std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {std::memcpy(target,reinterpret_cast<const void *>(address),size);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)address;(void)target;(void)size;return false;
#endif
}
bool Fail(NonCashOwnerSourceObservationV3 &o,std::string_view reason) noexcept {
  o={};o.unavailable_reason=reason;return false;
}
bool ReadImpl(const ActorResourceLeafSourceInputV2 &input,NonCashOwnerSourceObservationV3 &o) noexcept {
  o={};
  // This reader obtains source DATA itself; a caller-populated formatter DTO
  // cannot supply before/after frames or amounts.
  if(!ReadActorResourceLeafV2(input,o.before))return Fail(o,"base_resource_source_unavailable");
  if(CurrentModule()==0 || CurrentModule()!=input.image_base)return Fail(o,"raw_getter_module_before_changed");
  const auto &core=input.gold_bindings.core;
  const auto first=ResolveSafe(core,o.before.before.played_character_id);
  if(first==nullptr)return Fail(o,"actor_generation_before_unavailable");
  const auto raw=BindNonCashDecodeImageV1(input.image_base,input.executable_sha256);
  if(!raw.exact_build_admitted)return Fail(o,"raw_source_image_unavailable");
  const auto actor=reinterpret_cast<std::uintptr_t>(first);
  (void)DecodeNonCashRawV1(raw,&Copy,nullptr,actor,o.before.before.played_character_id,
      NonCashResourceV1::dynasty_renown,o.renown);
  (void)DecodeNonCashRawV1(raw,&Copy,nullptr,actor,o.before.before.played_character_id,
      NonCashResourceV1::government_treasury,o.treasury);
  if(!ReadActorResourceLeafV2(input,o.after))return Fail(o,"base_resource_after_unavailable");
  const auto second=ResolveSafe(core,o.after.after.played_character_id);
  if(first!=second || second==nullptr)return Fail(o,"actor_generation_interval_changed");
  if(CurrentModule()==0 || CurrentModule()!=input.image_base)return Fail(o,"raw_getter_module_after_changed");
  if(!SameCore(o.before.before,o.after.after) || o.before.actor_character_id!=o.after.actor_character_id ||
      o.before.actor_gold_raw!=o.after.actor_gold_raw || o.before.prestige_raw!=o.after.prestige_raw ||
      o.before.piety_raw!=o.after.piety_raw)return Fail(o,"base_resource_interval_changed");
  o.owner_source_interval_verified=true;
  const bool any=o.renown.status==NonCashDecodeStatusV1::decoded || o.treasury.status==NonCashDecodeStatusV1::decoded;
  o.unavailable_reason=any?std::string_view{}:std::string_view{"additional_sources_unknown"};
  return any;
}
} // namespace
bool ReadNonCashOwnerSourcesV3(const ActorResourceLeafSourceInputV2 &input,
    NonCashOwnerSourceObservationV3 &out) noexcept {
#if defined(_MSC_VER)
  __try {return ReadImpl(input,out);} __except(EXCEPTION_EXECUTE_HANDLER){return Fail(out,"additional_source_memory_failed");}
#else
  return ReadImpl(input,out);
#endif
}
} // namespace xar::ck3_1210
