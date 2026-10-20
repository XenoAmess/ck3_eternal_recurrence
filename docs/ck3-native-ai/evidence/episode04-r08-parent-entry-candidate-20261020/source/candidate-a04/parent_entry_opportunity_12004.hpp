#pragma once
// SOURCE CANDIDATE ONLY. No public startup/command is connected to this API.
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <optional>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004::parent_entry {
inline constexpr std::uintptr_t kEntryRva = 0x28F7840;
inline constexpr std::array<std::uint8_t,16> kPrefix{
  0x48,0x8b,0xc4,0x53,0x55,0x48,0x81,0xec,0x98,0,0,0,0x4c,0x89,0x70,0xe0};
inline constexpr std::string_view kExeSha =
  "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

// All are raw ENTRY inputs; none is the function's return value or a payer.
struct EntryFrame {
  std::uint64_t rax,rcx,rdx,r8,r9,r10,r11,rbx,rbp,rsi,rdi,r12,r13,r14,r15;
  std::uint64_t rsp,rflags,native_return,tid,tsc_not_serialized;
};
struct alignas(64) WireState {
  volatile LONG64 enabled=0;
  std::uint64_t target_character=0,admitted_full_id=0,epoch=0,generation=0,window=0;
  std::uint64_t admission_date=0,admission_absolute_day=0;
  volatile LONG64 foreign_count=0,matching_pointer_count=0,dropped_matching_count=0;
  volatile LONG64 frame_state=0; // 0 empty;1 one producer writing;2 immutable ready
  EntryFrame frame{};
  volatile LONG64 active_thunks=0,counter_overflow=0;
};
static_assert(sizeof(EntryFrame)==160);
static_assert(offsetof(WireState,frame)==0x60);
static_assert(offsetof(WireState,active_thunks)==0x100);
static_assert(offsetof(WireState,counter_overflow)==0x108);

using Read = bool (*)(void*,std::uintptr_t,void*,std::size_t) noexcept;
struct Admission {
  std::string machine_id,executable_sha256;
  std::uintptr_t module_base=0,character=0,context=0,game_state=0;
  std::uint64_t process_create_time_100ns=0,generation=0,window=0,payment_epoch=0;
  std::uint64_t date_raw=0,absolute_day=0;
  std::uint32_t pid=0,full_id=0,local_player_id=0;
  bool ordinary_null_owner=false,explicit_entry_hook_admission=false;
};
struct Environment {
  void* context=nullptr;
  Read read=nullptr;
  // Existing startup may supply this ONLY while all possible executors of the
  // patched prefix are proved quiescent. A boolean is not that external proof.
  bool all_reachable_threads_quiescent=false;
};
struct Snapshot {
  enum class Status { not_owned,not_armed,busy,invalid_wire_state,stopped };
  Status status=Status::not_owned;
  std::optional<Admission> owner;
  std::optional<std::uint64_t> foreign_count,matching_pointer_count,dropped_matching_count;
  std::optional<std::uint64_t> raw_foreign_counter_bits,raw_matching_counter_bits,raw_dropped_counter_bits;
  std::optional<std::uint64_t> frame_state;
  std::optional<EntryFrame> frame;
  std::optional<bool> counter_overflow,producer_busy;
  bool identity_before_verified=false,identity_after_verified=false,stopped=false;
  // The entry thunk deliberately does not dereference Character or game state.
  // These remain false even if pre/post admission identity joins succeed.
  bool full_id_read_at_entry=false,native_clock_read_at_entry=false;
  std::optional<std::uint32_t> full_id_at_entry;
  std::optional<std::uint64_t> native_clock_at_entry;
  bool actual_payment=false,military_producer=false,payer_identified=false;
};
// One arm/window per process; no resetting an old frame under a possible entry.
// Default-off build and runtime. Install leaves enabled=0.
bool Install(const Admission&,const Environment&) noexcept;
bool ArmOnce() noexcept;
// OFF is attempted even when identity readback fails. A busy producer returns
// false with stopped=false; it must be read back, never guessed complete.
bool StopAndSnapshot(Snapshot&) noexcept;
// Optional restoration needs real global quiescence; on failure keep ownership,
// static thunk/trampoline and pinned module. Normal exit can retain OFF hook.
bool Uninstall(bool all_reachable_threads_quiescent) noexcept;
}

extern "C" {
extern xar::ck3_12004::parent_entry::WireState XarParentEntryState12004;
extern std::uintptr_t XarParentEntryContinuation12004;
void XarParentEntryThunk12004();
void XarParentEntryOriginalPrefix12004();
extern void (*const XarParentEntryOriginalPrefixTarget12004)();
}
