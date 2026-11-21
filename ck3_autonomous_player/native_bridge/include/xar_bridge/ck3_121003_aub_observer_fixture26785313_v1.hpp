#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <array>
#include <memory>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kAubObserverFixtureSchema267V1[]="ck3.private_fixture_inbox.current267_request.v1";
inline constexpr char kAubObserverFixtureResultSchema267V1[]="ck3.private_fixture_inbox.current267_result.v1";
inline constexpr char kAubObserverFixtureBackend267V1[]="ck3-1.21.0.3-native-headless-main-thread";
inline constexpr char kAubObserverFixtureStep267V1[]="run-current-aub-observer-fixture-v1";
inline constexpr char kAubObserverFixtureCapability267V1[]="game.command.run-current-aub-observer-fixture.v1";
inline constexpr char kAubObserverFixtureFilename267V1[]="xar_mcp_inbox.txt";
struct AubObserverFixtureRequest267V1 {
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t deadline_unix_ms=0;std::array<char,97> request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
enum class AubObserverFixtureStatus267V1 {unavailable,expired,stale_core,claim_consumed,source_changed,dispatched,indeterminate};
struct AubObserverFixtureResult267V1 {
 AubObserverFixtureStatus267V1 status=AubObserverFixtureStatus267V1::unavailable;
 bool effect_attempted=false,native_returned=false,native_accepted=false,cleanup_known=false;
 bool file_verified=false,file_verified_after=false,core_available=false;
 std::uint64_t claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix observed{};std::string inbox_sha256,reason;
};
class AubObserverFixtureSession267V1 {
 public:AubObserverFixtureSession267V1();~AubObserverFixtureSession267V1();
 AubObserverFixtureSession267V1(const AubObserverFixtureSession267V1&)=delete;
 AubObserverFixtureSession267V1&operator=(const AubObserverFixtureSession267V1&)=delete;
 private:struct State;std::unique_ptr<State> state_;
 friend bool ExecuteAubObserverFixtureInner267V1(struct AubObserverFixtureContext267V1&,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
 friend void BlockAubObserverFixtureUnknown267V1(AubObserverFixtureSession267V1&) noexcept;
 friend bool ExecuteAubObserverFixtureOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
};
struct AubObserverFixtureContext267V1 {
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};AubObserverFixtureRequest267V1 request{};
 AubObserverFixtureResult267V1 result{};AubObserverFixtureSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool resource_ownership_entered=false;
};
bool AubObserverFixtureRequestShape267V1(const AubObserverFixtureRequest267V1&) noexcept;
bool ParseAubObserverFixtureRequest267V1(std::string_view,AubObserverFixtureRequest267V1&) noexcept;
std::string SerializeAubObserverFixtureResult267V1(std::string_view,const AubObserverFixtureResult267V1&);
bool AubObserverFixtureRouteEnabled267V1(const game::AdapterDescriptor&) noexcept;
std::string DispatchAubObserverFixtureRequest267V1(const game::GameAdapter&,std::uint64_t,
 std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
void ArmAubObserverFixtureDeadline267V1(AubObserverFixtureContext267V1&) noexcept;
void BlockAubObserverFixtureUnknown267V1(AubObserverFixtureSession267V1&) noexcept;
bool ExecuteAubObserverFixtureOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ReadAubObserverFixtureCoreOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,ReadonlyObservation&) noexcept;
}
