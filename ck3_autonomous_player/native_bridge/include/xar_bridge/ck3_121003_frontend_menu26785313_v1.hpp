#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <array>
#include <memory>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_121003::build26785313 {
inline constexpr char kFrontendMenuRequestSchema267V1[]="ck3.frontend_gui_route.current267_request.v1";
inline constexpr char kFrontendMenuResultSchema267V1[]="ck3.frontend_gui_route.current267_result.v1";
inline constexpr char kFrontendMenuBackend267V1[]="ck3-1.21.0.3-native-application-main-frontend";
inline constexpr char kFrontendMenuQueryStep267V1[]="query-current-frontend-menu-v1";
inline constexpr char kFrontendMenuQuitStep267V1[]="quit-current-frontend-menu-v1";
inline constexpr char kFrontendOpenBookmarksStep267V1[]="open-current-frontend-bookmarks-v1";
inline constexpr char kFrontendSelectBookmarkStep267V1[]="select-current-frontend-bookmark1066-v1";
inline constexpr char kFrontendRobertSelectStep267V1[]="select-current-frontend-robert1066-v1";
inline constexpr char kFrontendRobertStartStep267V1[]="start-current-frontend-robert1066-v1";
inline constexpr char kFrontendMenuQueryCapability267V1[]="game.command.query-current-frontend-menu.v1";
inline constexpr char kFrontendMenuQuitCapability267V1[]="game.command.quit-current-frontend-menu.v1";
inline constexpr char kFrontendOpenBookmarksCapability267V1[]="game.command.open-current-frontend-bookmarks.v1";
inline constexpr char kFrontendSelectBookmarkCapability267V1[]="game.command.select-current-frontend-bookmark1066.v1";
inline constexpr char kFrontendRobertSelectCapability267V1[]="game.command.select-current-frontend-robert1066.v1";
inline constexpr char kFrontendRobertStartCapability267V1[]="game.command.start-current-frontend-robert1066.v1";
inline constexpr char kFrontendRobertBookmark267V1[]="bm_1066_rags_to_riches";
inline constexpr char kFrontendRobertCharacter267V1[]="bookmark_rags_to_riches_duke_robert";
enum class FrontendMenuAction267V1 {query_menu,quit_menu,select_robert_1066,start_robert_1066,open_bookmarks,select_1066_bookmark};
enum class FrontendMenuRoute267V1 {unavailable,main_menu,bookmarks,lobby};
enum class FrontendMenuStatus267V1 {unavailable,available,expired,source_changed,query_consumed,
 claim_consumed,capacity_exhausted,exit_requested,selection_dispatched,start_dispatched,indeterminate,bookmarks_opened,bookmark_selected};
constexpr std::string_view FrontendMenuStep267V1(FrontendMenuAction267V1 a) noexcept {
 switch(a){case FrontendMenuAction267V1::query_menu:return kFrontendMenuQueryStep267V1;
 case FrontendMenuAction267V1::quit_menu:return kFrontendMenuQuitStep267V1;
 case FrontendMenuAction267V1::select_robert_1066:return kFrontendRobertSelectStep267V1;
 case FrontendMenuAction267V1::start_robert_1066:return kFrontendRobertStartStep267V1;
 case FrontendMenuAction267V1::open_bookmarks:return kFrontendOpenBookmarksStep267V1;
 case FrontendMenuAction267V1::select_1066_bookmark:return kFrontendSelectBookmarkStep267V1;}return {};
}
constexpr std::array<std::string_view,6> kFrontendAllSteps267V1{kFrontendMenuQueryStep267V1,kFrontendMenuQuitStep267V1,kFrontendRobertSelectStep267V1,kFrontendRobertStartStep267V1,kFrontendOpenBookmarksStep267V1,kFrontendSelectBookmarkStep267V1};
constexpr std::array<std::string_view,6> kFrontendAllCaps267V1{kFrontendMenuQueryCapability267V1,kFrontendMenuQuitCapability267V1,kFrontendRobertSelectCapability267V1,kFrontendRobertStartCapability267V1,kFrontendOpenBookmarksCapability267V1,kFrontendSelectBookmarkCapability267V1};
struct FrontendMenuRequest267V1 {
 std::array<char,97> request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
 FrontendMenuAction267V1 action=FrontendMenuAction267V1::query_menu;
 std::uint64_t deadline_unix_ms=0,provider_generation=0,query_sequence=0;
};
struct FrontendMenuFacts267V1 {
 FrontendMenuRoute267V1 route=FrontendMenuRoute267V1::unavailable;
 bool application_verified=false,gui_context_verified=false,global_root_verified=false;
 bool route_root_visible=false,no_world=false;
 std::optional<std::string> selected_bookmark_key,selected_character_key;
 bool robert_source_verified=false,start_admissible=false;
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
};
struct FrontendMenuResult267V1 {
 FrontendMenuAction267V1 action=FrontendMenuAction267V1::query_menu;
 FrontendMenuStatus267V1 status=FrontendMenuStatus267V1::unavailable;
 FrontendMenuFacts267V1 facts{};
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0;
 bool effect_attempted=false,native_returned=false,post_selection_verified=false;
 std::string reason;
};
bool FrontendMenuRequestShape267V1(const FrontendMenuRequest267V1&) noexcept;
bool ParseFrontendMenuRequest267V1(std::string_view,FrontendMenuRequest267V1&) noexcept;
std::string SerializeFrontendMenuResult267V1(std::string_view,const FrontendMenuResult267V1&);
class FrontendMenuSession267V1 {
 public:FrontendMenuSession267V1();~FrontendMenuSession267V1();
 FrontendMenuSession267V1(const FrontendMenuSession267V1&)=delete;
 FrontendMenuSession267V1&operator=(const FrontendMenuSession267V1&)=delete;
 private:struct State;std::unique_ptr<State> state_;
 friend bool ExecuteFrontendMenuInner267V1(struct FrontendMenuContext267V1&,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
 friend void BlockFrontendMenuUnknown267V1(FrontendMenuSession267V1&) noexcept;
};
struct FrontendMenuContext267V1 {
 ReadonlyBindings bindings{};const game::GameAdapter *game=nullptr;
 ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};
 FrontendMenuRequest267V1 request{};FrontendMenuResult267V1 result{};
 FrontendMenuSession267V1 *session=nullptr;
 bool seed_readback_only=false;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
};
void ArmFrontendMenuDeadline267V1(FrontendMenuContext267V1&) noexcept;
void BlockFrontendMenuUnknown267V1(FrontendMenuSession267V1&) noexcept;
bool ExecuteFrontendMenuOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool FrontendMenuStepEnabled267V1(const game::AdapterDescriptor&,std::string_view) noexcept;
std::string DispatchFrontendMenuRequest267V1(const game::GameAdapter&,std::uint64_t,
 std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace xar::ck3_121003::build26785313
