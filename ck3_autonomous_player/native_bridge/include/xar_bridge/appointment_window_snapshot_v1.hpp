#pragma once
#include <cstdint>
#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {
inline constexpr std::string_view kCurrentTitleAppointmentCapabilityV1="game.command.query-current-title-appointment-v1";
struct AppointmentWindowRequestV1 {
  std::uint32_t requested_title_id=0, candidate_offset=0, candidate_limit=32, breakdown_character_id=0;
};
// Private pure-reader boundary. Production creates callbacks only after the
// existing exact-build, paused application-owner and visible GUI admission.
// These addresses are never caller fields or public results.
struct AppointmentWindowAccessV1 {
  void *context=nullptr;
  bool (*read)(void *,std::uintptr_t,void *,std::size_t) noexcept=nullptr;
  bool (*title_key)(void *,std::uintptr_t,std::string &) noexcept=nullptr;
  bool (*breakdown)(void *,std::uintptr_t,std::uintptr_t,std::uintptr_t &) noexcept=nullptr;
  bool (*human_player)(void *,std::uint32_t,bool &) noexcept=nullptr;
  std::uintptr_t module_base=0,handler=0,window=0,gui_root=0;
};
struct AppointmentCandidateV1 {
  std::uint32_t character_id=0,list_index=0;
  std::int32_t native_rank=-1;
  std::int64_t score_raw=0;
  bool alive=false,is_human_player=false,is_ai=false;
  friend bool operator==(const AppointmentCandidateV1 &,const AppointmentCandidateV1 &)=default;
};
struct AppointmentScoreNodeV1 {
  std::string text0,text1,text2;
  std::int64_t value_raw=0,factor_raw=0;
  std::int32_t mode=0;
  std::uint8_t flags=0;
  std::vector<AppointmentScoreNodeV1> children;
};
struct AppointmentWindowSnapshotV1 {
  bool available=false,requested_resolves_to_current=false,breakdown_getter_invoked=false;
  std::uint32_t requested_title_id=0,requested_holder_character_id=0,group_first_title_id=0,resolved_title_id=0;
  std::uint32_t current_window_title_id=0,current_holder_character_id=0;
  std::string native_group_branch,current_title_key,resolved_title_key,effective_succession_law_key;
  std::uint32_t full_candidate_count=0,source_pool_count=0,candidate_offset=0,next_offset=0;
  std::string pool_consistency_token;
  std::vector<AppointmentCandidateV1> candidates;
  bool breakdown_available=false;
  std::uint32_t breakdown_character_id=0;
  AppointmentScoreNodeV1 breakdown;
  std::string breakdown_unavailable_reason,unavailable_reason;
};
bool ValidateAppointmentWindowRequestV1(const AppointmentWindowRequestV1 &) noexcept;
bool ReadAppointmentWindowSnapshotV1(const AppointmentWindowAccessV1 &,const AppointmentWindowRequestV1 &,AppointmentWindowSnapshotV1 &) noexcept;
std::string SerializeAppointmentWindowSnapshotV1(const AppointmentWindowSnapshotV1 &);
}
