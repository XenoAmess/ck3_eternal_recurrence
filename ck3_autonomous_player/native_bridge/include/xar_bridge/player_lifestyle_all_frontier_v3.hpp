#pragma once
#include "xar_bridge/player_lifestyle_all_catalogue_v3.hpp"
#include "xar_bridge/player_lifestyle_formal_precondition_v1.hpp"
#include "xar_bridge/player_lifestyle_stock_perk_legality_v1.hpp"
#include <algorithm>
namespace xar::ck3_11906 {
inline bool LifestyleProgressObservedV3(const StockPerkLegalityResultV1 &p) noexcept {
  return (p.status == StockPerkLegalityStatusV1::observed_native_legal ||
          p.status == StockPerkLegalityStatusV1::observed_native_illegal) &&
         p.observed_unspent_points >= 0 && p.observed_used_points >= 0 &&
         p.observed_target_xp_total_raw >= 0 &&
         p.observed_target_xp_within_level_raw >= 0 &&
         p.observed_target_xp_per_level > 0;
}
// Progress is collected before any validator calls. Zero-point lifestyles
// never invoke CanPick; unavailable is distinct from zero/no legal frontier.
template<class Reader>
StockPerkLegalityResultV1 ReadAllLifestylePerkFrontierV3(
    const std::array<StockPerkLegalityResultV1,6> &progress,
    std::string_view current_lifestyle, Reader &&read) noexcept {
  using Status=StockPerkLegalityStatusV1;
  StockPerkLegalityResultV1 first_unknown{},last_negative{};
  bool unknown=false,negative=false;
  for(std::size_t i=0;i<progress.size();++i) {
    if (!LifestyleProgressObservedV3(progress[i])) {
      if(!unknown)first_unknown=progress[i];unknown=true;
    } else if(!negative) {last_negative=progress[i];negative=true;}
  }
  std::array<std::size_t,6> order{0,1,2,3,4,5};
  for(std::size_t i=0;i<6;++i)if(kAllLifestyleKeysV3[i]==current_lifestyle)
    std::rotate(order.begin(),order.begin()+i,order.begin()+i+1);
  for(auto i:order) {
    const auto &p=progress[i];
    if(!LifestyleProgressObservedV3(p)||p.observed_unspent_points==0)continue;
    for(const auto &entry:kAllLifestylePerksV3) {
      if(entry.lifestyle!=kAllLifestyleKeysV3[i])continue;
      auto candidate=read(entry.key);
      if(candidate.status==Status::observed_native_legal)return candidate;
      if(candidate.status==Status::observed_native_illegal) {
        last_negative=std::move(candidate);negative=true;
      } else {if(!unknown)first_unknown=std::move(candidate);unknown=true;}
    }
  }
  if(unknown)return first_unknown;
  return last_negative;
}
template<std::size_t N>
inline std::string_view LifestyleFixedV3(const std::array<char,N> &value) noexcept {
  const auto end=std::find(value.begin(),value.end(),'\0');
  return end==value.end()?std::string_view{}:std::string_view(value.data(),end-value.begin());
}
inline PlayerLifestyleFormalPreconditionResultV1 BuildAllLifestylePerkObservationV3(
    const game::PlayerLifestyleSnapshotV1 &snapshot,
    const StockPerkLegalityResultV1 &p,std::string_view episode,
    game::PlayerLifestyleSelectionStateObservationV1 &out) noexcept {
  using Result=PlayerLifestyleFormalPreconditionResultV1;out={};
  if(snapshot.status!=game::PlayerLifestyleSnapshotStatusV1::available ||
     !snapshot.readiness.current_focus_ready || !snapshot.readiness.owned_perks_ready ||
     !snapshot.readiness.same_frame_ready || !LifestyleProgressObservedV3(p))
    return Result::source_unavailable;
  if(LifestyleFixedV3(snapshot.snapshot_id).empty() ||
     LifestyleFixedV3(snapshot.snapshot_id)!=LifestyleFixedV3(p.frame.snapshot_id) ||
     snapshot.public_revision!=p.frame.public_revision ||
     snapshot.native_revision!=p.frame.native_revision ||
     snapshot.proof_epoch!=p.frame.proof_epoch || snapshot.date_raw!=p.frame.date_raw ||
     snapshot.player_character_id<=0 ||
     static_cast<std::uint32_t>(snapshot.player_character_id)!=p.frame.played_character_id ||
     snapshot.public_revision==0 || snapshot.native_revision==0 ||snapshot.proof_epoch==0 ||
     !p.frame.paused || !p.frame.map_ready || !p.frame.played_character_alive)
    return Result::frame_mismatch;
  if(episode.empty() || episode.size()>=out.episode_run_id.size() ||
     LifestyleFixedV3(p.frame.episode_run_id)!=episode)return Result::episode_unavailable;
  for(const auto c:episode)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||
      (c>='0'&&c<='9')||c=='-'))return Result::episode_unavailable;
  const auto &source=snapshot.state;
  if(source.owned_perk_count>game::kPlayerLifestyleWindowMaximumPerksV1 ||
     AllLifestylePerkLifestyleV3(PlayerLifestyleWindowStableKeyViewV1(p.target_key))!=
         PlayerLifestyleWindowStableKeyViewV1(p.lifestyle_key))return Result::invalid_source;
  out.has_current_focus=source.current_focus_presence==game::PlayerLifestyleFocusPresenceV1::present;
  if(!out.has_current_focus && source.current_focus_presence!=game::PlayerLifestyleFocusPresenceV1::absent)
    return Result::invalid_source;
  if(out.has_current_focus && !AssignPlayerLifestyleWindowStableKeyV1(
      PlayerLifestyleStableKeyViewV1(source.current_focus_key),out.current_focus_key))return Result::invalid_source;
  for(std::uint32_t i=0;i<source.owned_perk_count;++i)
    if(!AssignPlayerLifestyleWindowStableKeyV1(PlayerLifestyleStableKeyViewV1(source.owned_perk_keys[i]),out.owned_perk_keys[i]))return Result::invalid_source;
  out.available=true;out.paused=true;out.snapshot_id=p.frame.snapshot_id;
  std::copy(episode.begin(),episode.end(),out.episode_run_id.begin());
  out.public_revision=p.frame.public_revision;out.native_revision=p.frame.native_revision;
  out.proof_epoch=p.frame.proof_epoch;out.date_raw=p.frame.date_raw;
  out.player_character_id=p.frame.played_character_id;out.current_focus_known=true;
  out.owned_perks_fully_materialized=true;out.owned_perk_count=source.owned_perk_count;
  out.lifestyle_progress_fully_materialized=true;out.lifestyle_progress_count=1;
  out.lifestyle_progress[0]={p.lifestyle_key,p.observed_target_xp_total_raw,p.observed_unspent_points};
  return Result::ready;
}
inline PlayerLifestyleFormalPreconditionResultV1 BuildAllLifestylePerkPreconditionV3(
    const game::PlayerLifestyleSnapshotV1 &snapshot,
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    const StockPerkLegalityResultV1 &p,std::string_view episode,
    game::PlayerLifestyleSelectionPreconditionV1 &out) noexcept {
  using Result=PlayerLifestyleFormalPreconditionResultV1;out={};
  if(candidates.status!=game::PlayerLifestyleWindowCandidatesStatusV1::available ||
     !candidates.readiness.perk_candidates_ready || !candidates.readiness.final_legality_ready ||
     !candidates.readiness.same_frame_ready || candidates.perk_count!=1 ||
     candidates.perks[0].key!=p.target_key || candidates.perks[0].lifestyle_key!=p.lifestyle_key ||
     candidates.perks[0].can_select!=(p.status==StockPerkLegalityStatusV1::observed_native_legal))
    return Result::source_unavailable;
  if(candidates.snapshot_id!=p.frame.snapshot_id || candidates.public_revision!=p.frame.public_revision ||
     candidates.native_revision!=p.frame.native_revision || candidates.proof_epoch!=p.frame.proof_epoch ||
     candidates.date_raw!=p.frame.date_raw || candidates.player_character_id!=p.frame.played_character_id)
    return Result::frame_mismatch;
  const auto result=BuildAllLifestylePerkObservationV3(snapshot,p,episode,out.state);
  if(result==Result::ready)out.candidates=candidates;
  return result;
}
} // namespace xar::ck3_11906
