#pragma once
#include "xar_bridge/white_player_business_variables_v1.hpp"
#include "xar_bridge/white_rendered_text_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
namespace xar::ck3_11906 {
inline constexpr std::string_view kWhiteControlActionV1Step="click-white-control-v1";
inline constexpr std::string_view kWhiteControlActionV1Capability="game.command.click-white-control-v1";
inline constexpr std::string_view kWhiteNumericControlActionV1Step="click-white-numeric-control-v1";
inline constexpr std::string_view kWhiteNumericControlActionV1Capability="game.command.click-white-numeric-control-v1";
struct WhiteControlSpecV1 {
  std::string_view control,button;
  std::size_t variable_index=0,text_index=0;
  std::int32_t maximum=0;
  bool legacy_age=false;
};
inline constexpr std::array<WhiteControlSpecV1,7> kWhiteControlSpecsV1{{
  {"age_plus_1","ervc_cc_age_plus_1_button",1,0,120,true},
  {"diplomacy_plus_1","ervc_cc_diplomacy_plus_1_button",2,1,100,false},
  {"martial_plus_1","ervc_cc_martial_plus_1_button",3,2,100,false},
  {"stewardship_plus_1","ervc_cc_stewardship_plus_1_button",4,3,100,false},
  {"intrigue_plus_1","ervc_cc_intrigue_plus_1_button",5,4,100,false},
  {"learning_plus_1","ervc_cc_learning_plus_1_button",6,5,100,false},
  {"prowess_plus_1","ervc_cc_prowess_plus_1_button",7,6,100,false},
}};
constexpr const WhiteControlSpecV1 *FindWhiteControlSpecV1(std::string_view control) noexcept {
  for(const auto &spec:kWhiteControlSpecsV1)if(spec.control==control)return &spec;
  return nullptr;
}
struct WhiteControlActionResultV1 {
  std::string control="age_plus_1";
  std::int32_t expected_before_value=-1;bool before_price_bound=false;
  bool available=false,source_abi_pins_verified=false,receiver_qualified=false;
  bool gui_owner_binding_verified=false,frame_verified=false;
  bool dispatch_attempted=false,dispatch_invoked=false,native_handled=false,native_after_read=false;
  std::uint32_t game_pid=0;std::uint64_t native_revision=0,connection_generation=0;
  std::int32_t played_character_id=-1,date_raw=0,expected_before_age=-1;
  std::string target_child_path,unavailable_reason;
};
struct WhiteControlActionContextV1 {
  std::string control="age_plus_1",expected_before_price_text;
  std::int32_t expected_before_value=-1;
  const game::GameAdapter *game=nullptr;game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0,connection_generation=0;
  std::int32_t expected_before_age=-1;
  WhiteControlActionResultV1 result{};
};
// Fixed legacy age+1 and six skill+1 controls only. No arbitrary receiver/name,
// script execution API, direct ScriptedGui call or selected/down projection.
bool ExecuteWhiteControlActionV1(WhiteControlActionContextV1 &,MainThreadQueryMailboxV1 &,
    const MainThreadExecutionStampV1 &,const ZhongguoScoreboardNativeEnvironmentV1 &,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &) noexcept;
std::string SerializeWhiteControlActionV1(const WhiteControlActionResultV1 &);
}
