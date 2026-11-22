#pragma once
#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_v1.hpp"

namespace xar::ck3_121003::build26785313 {
inline constexpr char kXqolThresholdRequestSchema267V1[]="ck3.xqol_conversion_threshold.current267_request.v1";
inline constexpr char kXqolThresholdResultSchema267V1[]="ck3.xqol_conversion_threshold.current267_result.v1";
inline constexpr char kXqolThresholdSourceSchema267V1[]="ck3.xqol_conversion_threshold.current267_source.v1";
inline constexpr char kXqolThresholdBackend267V1[]="ck3-1.21.0.3-native-application-main-xqol-conversion-threshold";
inline constexpr std::array<std::string_view,2> kXqolThresholdSteps267V1{
 "query-xqol-conversion-threshold-current-v1","set-xqol-conversion-threshold-current-v1"};
inline constexpr std::array<std::string_view,2> kXqolThresholdCapabilities267V1{
 "game.query.current-xqol-conversion-threshold.v1","game.command.set-current-xqol-conversion-threshold.v1"};
enum class XqolThresholdAction267V1{query_threshold,set_threshold};
enum class XqolThresholdStatus267V1{unavailable,expired,stale_source,claim_consumed,available,threshold_route_dispatched,indeterminate};
struct XqolThresholdRequest267V1{
 XqolThresholdAction267V1 action=XqolThresholdAction267V1::query_threshold;
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::optional<std::int32_t> instance_id;
 std::uint32_t target_threshold=0;
 std::array<char,97> request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct XqolThresholdSource267V1{
 XqolPromptSource267V1 prompt{};
 bool scrollbar_found=false,handle_found=false,native_fixed_route_found=false,set_admissible=false;
 std::optional<bool> native_shown,native_valid;
 std::optional<std::uint32_t> value_bits_u32,minimum_bits_u32,maximum_bits_u32,step_bits_u32;
 std::uint32_t target_threshold=0;
 friend bool operator==(const XqolThresholdSource267V1&,const XqolThresholdSource267V1&)=default;
};
struct XqolThresholdResult267V1{
 XqolThresholdAction267V1 action=XqolThresholdAction267V1::query_threshold;
 XqolThresholdStatus267V1 status=XqolThresholdStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};
 std::optional<std::int32_t> instance_id;
 std::optional<XqolThresholdSource267V1> source;
 std::string reason;
};
bool XqolThresholdRequestShape267V1(const XqolThresholdRequest267V1&)noexcept;
bool ParseXqolThresholdRequest267V1(std::string_view,XqolThresholdRequest267V1&)noexcept;
std::string SerializeXqolThresholdResult267V1(std::string_view,const XqolThresholdResult267V1&);
}
