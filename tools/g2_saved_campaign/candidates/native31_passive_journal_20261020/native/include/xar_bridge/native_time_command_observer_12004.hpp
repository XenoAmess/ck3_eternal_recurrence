#pragma once
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004::time_observer31 {
inline constexpr std::size_t kIdBytes=64, kRegistry=64, kEvents=128, kDumpEvents=64;
enum Gap:std::uint32_t { busy=1, full=2, pointer_reuse=4, unreadable=8,
  id_too_long=16, event_overwrite=32, no_token=64, identity_drift=128 };
enum class Kind:std::uint8_t { request=1, clone=2, queue_enter=3, insert_enter=4,
  insert_return=5, queue_return=6, execute_enter=7, execute_return=8,
  delete_enter=9, delete_return=10 };
enum class Role:std::uint8_t { unknown=0, bridge_root=1, recorder_copy=2, native_copy=3 };
struct Key { std::uint64_t connection{}; std::array<char,kIdBytes> id{};
  std::uint8_t desired_paused{}, valid{}; };
struct Token { std::uintptr_t address{}; std::uint64_t incarnation{};
  friend bool operator==(Token a,Token b) noexcept {
    return a.address==b.address && a.incarnation==b.incarnation;
  }
};
struct Scalar { std::uintptr_t game{},jomini{}; std::int32_t date{};
  std::uint8_t paused{}, valid{}; };
struct Event { std::uint64_t sequence{},qpc{},invocation{},identity_epoch{}; std::uint32_t thread{};
  Kind kind{}; Role role{}; std::uint8_t qualified{},accepted{};
  Token token{},parent{}; Key key{}; std::uintptr_t caller{},aux{};
  Scalar scalar{}; std::int32_t player{}; std::uint32_t native_sequence{};
  std::uint8_t command_paused{},payload_valid{}; };
struct Ticket { Token token{},parent{}; Key key{}; Role role{};
  std::uint64_t invocation{},identity_epoch{}; std::int32_t player{};
  std::uint32_t native_sequence{}; std::uint8_t valid{},payload_valid{},command_paused{},inserted{},qualified{}; };
struct CloneSeed { Ticket parent{}; Key key{}; Role role{}; };
struct Dump { std::uint64_t newest{},oldest{},lost{}; std::uint32_t gaps{},count{};
  std::uint32_t live_registry{}; std::array<Event,kDumpEvents> events{}; };
struct Environment { std::uintptr_t image_base{}; std::uint64_t process_birth{};
  std::uint32_t process_id{}; std::uint64_t qpc_frequency{};
  bool exact_build_admitted{}; };
void GapFlag(std::uint32_t) noexcept;
void InvalidateIdentity(std::uint32_t) noexcept;
std::uint64_t BeginConnection() noexcept;
struct RequestScope {
  Key previous{};
  RequestScope(std::uint64_t,std::string_view,bool) noexcept;
  ~RequestScope() noexcept;
  RequestScope(const RequestScope&)=delete;
};
struct BridgeCloneScope {
  const void* previous{};
  explicit BridgeCloneScope(const void*) noexcept;
  ~BridgeCloneScope() noexcept;
  BridgeCloneScope(const BridgeCloneScope&)=delete;
};
CloneSeed CloneEnter(const void*,std::uintptr_t) noexcept;
void CloneReturn(const CloneSeed&,const void*,std::uintptr_t) noexcept;
Ticket Lookup(const void*) noexcept;
Ticket Enter(Kind,const void*,std::uintptr_t,std::uintptr_t=0,bool=false) noexcept;
void Return(Kind,const Ticket&,std::uintptr_t,bool=false,bool=false) noexcept;
void Retire(const Ticket&) noexcept;
bool ReadDump(Dump&) noexcept;
std::string DiagnosticFrame(std::string_view) ;
enum class InstallResult:std::uint8_t { active=1, unavailable_clean=2, rollback_unsafe=3 };
InstallResult Install(const Environment&,std::string_view,bool primary_thread_suspended) noexcept;
bool Attached() noexcept;
Environment Identity() noexcept;
using CloneNative=void**(*)(const void*,void**);
using DeleteNative=void*(*)(void*,std::uint32_t);
using ExecuteNative=void(*)(void*);
using AppendNative=void**(*)(void*,void**);
void** ForwardClone(CloneNative,const void*,void**,std::uintptr_t);
void* ForwardDelete(DeleteNative,void*,std::uint32_t,std::uintptr_t);
void ForwardExecute(ExecuteNative,void*,std::uintptr_t);
void** ForwardAppend(AppendNative,void*,void**,std::uintptr_t);
bool ReadPointer(const void*,void*&) noexcept;
bool ExpectedContainer(const void*) noexcept;
// Windows-only helpers; no native game method is called by diagnostics.
bool IsPauseObject(const void*) noexcept;
bool ReadPayload(const void*,std::int32_t&,std::uint8_t&,std::uint32_t&) noexcept;
Scalar ReadScalar() noexcept;
std::uint64_t Clock() noexcept;
std::uint32_t Thread() noexcept;
} // namespace xar::ck3_12004::time_observer31
