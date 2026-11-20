#include "xar_bridge/ck3_121003_save_mapped111.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <cstring>
#include <intrin.h>
#include <windows.h>
namespace xar::ck3_1210 { namespace {
#include "save_mapped_pins111.inc"
bool Copy(SaveImageRead111 a,std::uintptr_t p,void *out,std::size_t n) noexcept {
  if(!p || !out || !n)return false;
  if(a.copy)return a.copy(a.context,p,out,n);
  if(a.context)return false;
#if defined(_MSC_VER)
  __try {std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;
#endif
}
bool Image(std::uintptr_t base,SaveImageRead111 a) noexcept {
  if(!base || base>UINTPTR_MAX-0x6FE5000)return false;
  std::array<unsigned char,2048> bytes{};
  for(const auto &pin:kSavePins111) {
    if(pin.size>bytes.size() || !Copy(a,base+pin.rva,bytes.data(),pin.size) ||
       std::memcmp(bytes.data(),pin.data,pin.size))return false;
  }
  for(const auto &pin:kSavePointers111) {
    std::uintptr_t value=0;
    if(!Copy(a,base+pin.rva,&value,sizeof(value)) || value!=base+pin.target)return false;
  }
  return true;
}
bool Same(const CoreBindings&a,const CoreBindings&b) noexcept {
  return a.enabled && b.enabled && a.image_build==b.image_build &&
    a.game_state_slot==b.game_state_slot && a.jomini_state_slot==b.jomini_state_slot &&
    a.character_storage_slot==b.character_storage_slot && a.get_local_player==b.get_local_player;
}
[[maybe_unused]] bool Production(const CoreControlContextV1&c,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
  if(!SaveMailboxOwner111(c,s) || c.mailbox->offline_fixture)return false;
  const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto core=BindCoreImage(base,ck3_121003::full111::kExecutableSha256);
  const auto commands=BindCommandImage(base,ck3_121003::full111::kExecutableSha256);
  const auto &m=*c.mailbox;
  if(!base || !Same(c.core,core) || !commands.enabled || m.module_base!=base ||
    c.commands.command_manager!=commands.command_manager || c.commands.queue_owned_command!=commands.queue_owned_command ||
    c.commands.auto_save_primary_vtable!=commands.auto_save_primary_vtable ||
    c.commands.auto_save_secondary_vtable!=commands.auto_save_secondary_vtable ||
    m.game_state_slot!=reinterpret_cast<std::uintptr_t>(core.game_state_slot) ||
    m.jomini_state_slot!=reinterpret_cast<std::uintptr_t>(core.jomini_state_slot) ||
    m.tls_initialized_flag!=base+ck3_121003::build26785313::kTlsFlagRva ||
    s.tls_initialized_flag_address!=m.tls_initialized_flag ||
    reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+ck3_121003::build26785313::kTlsGetterRva)return false;
  // No lazy TLS getter call or write: inspect the already-warm native block.
  if(*reinterpret_cast<const unsigned char*>(m.tls_initialized_flag)!=1)return false;
  const auto slots=reinterpret_cast<void**>(__readgsqword(0x58));
  if(!slots || !slots[0])return false;
  const auto block=reinterpret_cast<std::uintptr_t>(slots[0]);
  if((*reinterpret_cast<const std::uint32_t*>(block+0x3620)&1U)==0 ||
    block+0x3628!=s.tls_context || *reinterpret_cast<const unsigned char*>(s.tls_context+0x20)!=1)return false;
  return Image(base,{});
}
} // namespace
bool VerifySaveImage111(std::uintptr_t base,SaveImageRead111 a) noexcept {return Image(base,a);}
bool SaveMailboxOwner111(const CoreControlContextV1&c,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
  if(!c.mailbox || !c.game || !game::IsCk3_121003Full111Descriptor(c.game->descriptor()) ||
    c.core.image_build!=ImageBuildV1::full11126785313 || !c.core.enabled || !c.commands.enabled ||
    !c.ticket.sequence || !s.thread_id || s.thread_id!=GetCurrentThreadId() || !s.pump_epoch ||
    s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || !s.tls_context || !s.paused)return false;
  const auto&m=*c.mailbox;
  return m.iat_hook_installed.load() && m.active_hook_calls.load()>0 &&
    !m.stop_requested.load() && !m.proof_reset_requested.load() && m.failure_flags.load()==0 &&
    m.pump_epochs.load()==s.pump_epoch && m.owner_thread_id.load()==s.thread_id &&
    m.paused_owner_verified_pump_epochs.load()>=ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
    m.state.load()==ck3_11906::MainThreadQueryMailboxStateV1::executing &&
    m.published_sequence.load()==c.ticket.sequence && m.executor_started_sequence.load()==c.ticket.sequence &&
    m.executor_started_pump_epoch.load()==s.pump_epoch && m.executor_context==&c &&
    m.executor.load()==&ExecuteCoreControlMailboxV1;
}
bool SaveAdmission111(const CoreControlContextV1&c,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
#if defined(XAR_CK3_ENABLE_121003_FULL111)
#if defined(XAR_CK3_SAVE111_OFFLINE_FIXTURE)
  // This symbol exists only in the separate NoGame object. It never enters DLL.
  extern bool SaveOfflineAdmission111(const CoreControlContextV1&,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
  return SaveMailboxOwner111(c,s) && SaveOfflineAdmission111(c,s);
#else
#if defined(_MSC_VER)
  __try {return Production(c,s);} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  return Production(c,s);
#endif
#endif
#else
  static_cast<void>(c);static_cast<void>(s);return false;
#endif
}
} // namespace xar::ck3_1210
