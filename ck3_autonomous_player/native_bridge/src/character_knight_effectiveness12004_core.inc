// Included once by the existing character_skill_effect12004.cpp production TU.
#include "xar_bridge/character_knight_effectiveness12004.hpp"
namespace xar::bridge::character_skill_effect12004 {
namespace knight_detail {
struct Sample {
  std::uintptr_t actor=0,values=0,block=0,owner=0,rite=0,faith=0;
  std::uint32_t rite_id=absent,faith_id=absent;
  std::int64_t raw=0;
  std::string text;
  friend bool operator==(const Sample &,const Sample &)=default;
};
bool One(const KnightEnvironment &env,const KnightRequest &r,Sample &s) noexcept {
  const auto &e=env.actor;std::uint32_t magic=0;
  // 28C3AC0 otherwise returns a shared fallback context. Refuse that branch
  // before either native getter and verify the same owner-backed block after.
  if(!Resolve(e,0x5C67568,r.character_id,0x18,s.actor)||
      !At(e,s.actor,0x1C,magic)||magic!=0x43686172U||
      !At(e,s.actor,0x1B0,s.values)||!s.values||
      !At(e,s.values,0x258,s.block)||!s.block||
      !At(e,s.block,8,s.owner)||s.owner!=s.actor||
      !At(e,s.actor,0xB4,s.rite_id)||
      !Resolve(e,0x5D1E2F8,s.rite_id,8,s.rite)||
      !At(e,s.rite,0x4B8,s.faith_id)||
      !Resolve(e,0x5D1E300,s.faith_id,8,s.faith))return false;
  if(!env.read_knight(e.context,s.actor,s.raw,s.text)||s.text.size()>kMaxBreakdownBytes)return false;
  std::uintptr_t actor=0,values=0,block=0,owner=0;
  return Resolve(e,0x5C67568,r.character_id,0x18,actor)&&actor==s.actor&&
      At(e,actor,0x1B0,values)&&values==s.values&&
      At(e,values,0x258,block)&&block==s.block&&
      At(e,block,8,owner)&&owner==actor;
}
} // namespace knight_detail
bool ReadKnightEffectiveness(const KnightEnvironment &env,const KnightRequest &r,
                            KnightResult &out) noexcept {
  out={};out.frame=r.expected;out.character_id=r.character_id;
  const auto fail=[&](const char *reason) noexcept {
    out.available=false;out.two_pass_stable=false;out.own_actor_context_verified=false;
    out.rite_id.reset();out.faith_id.reset();out.knight_effectiveness_raw.reset();
    out.actual_knight_effectiveness_breakdown.reset();out.selected_site_contribution_raw.reset();
    out.site_attribution_observed=false;out.callback_provenance=CallbackProvenance::unavailable;
    out.unavailable_reason=reason;return false;
  };
  try{
    const auto &e=env.actor;
    if(!e.enabled||e.executable_sha256!=kExeSha||!e.image_base||!e.read_memory||
       !e.read_frame||!env.read_knight||
       (e.callback_provenance!=CallbackProvenance::exact4_native&&
        !(e.allow_owned_fixture&&e.callback_provenance==CallbackProvenance::owned_fixture)))
      return fail("exact4_knight_callbacks_unavailable");
    if(!FrameValid(r.expected)||r.character_id==absent)return fail("knight_request_or_frame_invalid");
    Frame before{},middle{},after{};knight_detail::Sample first{},second{};
    if(!e.read_frame(e.context,before)||before!=r.expected)return fail("knight_frame_changed_before");
    if(!knight_detail::One(env,r,first))return fail("knight_first_actor_context_or_getter_unavailable");
    if(!e.read_frame(e.context,middle)||middle!=r.expected)return fail("knight_frame_changed_between");
    if(!knight_detail::One(env,r,second))return fail("knight_second_actor_context_or_getter_unavailable");
    if(!e.read_frame(e.context,after)||after!=r.expected||first!=second)
      return fail("knight_actor_context_value_or_text_changed");
    out.rite_id=first.rite_id;out.faith_id=first.faith_id;
    out.knight_effectiveness_raw=first.raw;out.actual_knight_effectiveness_breakdown=first.text;
    out.callback_provenance=e.callback_provenance;out.two_pass_stable=true;
    out.own_actor_context_verified=true;out.available=true;out.unavailable_reason.clear();return true;
  }catch(...){return fail("knight_owned_copy_exception");}
}
} // namespace xar::bridge::character_skill_effect12004
