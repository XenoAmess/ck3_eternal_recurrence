#pragma once
#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kStockBookmarkRequestSchema267V1[]="ck3.stock_bookmark1070.current267_request.v1";
inline constexpr char kStockBookmarkSourceSchema267V1[]="ck3.stock_bookmark1070.current267_source.v1";
inline constexpr char kStockBookmarkResultSchema267V1[]="ck3.stock_bookmark1070.current267_result.v1";
inline constexpr char kStockBookmarkBackend267V1[]="ck3-1.21.0.3-native-application-main-stock-bookmark1070";
inline constexpr char kStockBookmarkDefinition267V1[]="bookmark.1070";
inline constexpr char kStockBookmarkOption267V1[]="bookmark.1070.c";
inline constexpr std::array<std::string_view,2> kStockBookmarkSteps267V1{"query-stock-bookmark1070-current-v1","select-stock-bookmark1070-c-current-v1"};
inline constexpr std::array<std::string_view,2> kStockBookmarkCaps267V1{"game.query.current-stock-bookmark1070.v1","game.command.select-current-stock-bookmark1070-c.v1"};
enum class StockBookmarkAction267V1{query,select_c};
enum class StockBookmarkStatus267V1{unavailable,expired,stale_source,claim_consumed,available,selection_dispatched,indeterminate};
struct StockBookmarkRequest267V1{
 StockBookmarkAction267V1 action=StockBookmarkAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<std::int32_t>instance_id;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct StockBookmarkSource267V1{
 LydEventSource267V1 event_census{};std::optional<std::int32_t>fixed_instance_id;
 bool select_c_admissible=false,sampled_twice=false;
 friend bool operator==(const StockBookmarkSource267V1&,const StockBookmarkSource267V1&)=default;
};
struct StockBookmarkResult267V1{
 StockBookmarkAction267V1 action=StockBookmarkAction267V1::query;StockBookmarkStatus267V1 status=StockBookmarkStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<std::int32_t>instance_id;
 std::optional<StockBookmarkSource267V1>source;std::string reason;
};
bool StockBookmarkRequestShape267V1(const StockBookmarkRequest267V1&)noexcept;
bool StockBookmarkSourceShape267V1(const StockBookmarkSource267V1&)noexcept;
bool ParseStockBookmarkRequest267V1(std::string_view,StockBookmarkRequest267V1&)noexcept;
std::string SerializeStockBookmarkResult267V1(std::string_view,const StockBookmarkResult267V1&);
}
