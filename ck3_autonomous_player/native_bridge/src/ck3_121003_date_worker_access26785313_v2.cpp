#include "xar_bridge/ck3_121003_date_postday26785313_v1.hpp"
#include <Windows.h>
#include <intrin.h>

namespace xar::ck3_121003::build26785313 {
namespace {
using Sample=ck3_1210::DateWorkerGameAccessSampleV1;
using Result=ck3_1210::DateWorkerGameAccessResultV2;
using Acquisition=ck3_1210::DateWorkerAcquisitionV2;
using Release=ck3_1210::DateWorkerReleaseV2;
using Body=ck3_1210::DateWorkerBodyV2;
bool Same(const Sample &before,const Sample &now,std::uint8_t access) noexcept {
  return before.tls_block&&before.application&&now.tls_block==before.tls_block&&
      now.application==before.application&&before.command_scope==1&&
      now.command_scope==1&&now.native_access==access;
}
bool SampleCurrent(const DatePostdayImageBindings267V1 &b,Sample &out) {
  // This is read-only sampling. Native acquire/destructor alone may change TLS.
  if(*reinterpret_cast<const std::uint8_t *>(b.tls_initialized_flag)!=1)return false;
  const auto vector=__readgsqword(0x58);
  if(!vector)return false;
  const auto block=*reinterpret_cast<const std::uintptr_t *>(vector);
  if(!block)return false;
  out.tls_block=block;
  out.command_scope=*reinterpret_cast<const std::uint32_t *>(block+kDateCommandScopeOffset267V1);
  out.native_access=*reinterpret_cast<const std::uint8_t *>(block+kDateNativeAccessOffset267V1);
  out.application=*reinterpret_cast<const std::uintptr_t *>(b.application_slot);
  return out.application!=0;
}
bool Source(const DateWorkerAccessContext267V1 &context) noexcept {
  if(!context.image||!context.hook||
      !VerifyCurrentDatePostdayHookImage267V1(*context.image,*context.hook))return false;
  const auto status=ck3_1210::ReadDailyFinalHookStatusV1(*context.hook);
  return status.inflight!=0; // Actual callback lifetime, not worker-epoch proof.
}
void Run(const DateWorkerAccessContext267V1 &context,ck3_1210::DateWorkerGameBodyV1 body,
    void *body_context,Result &outcome) {
  if(!body||!Source(context))return;
  const auto &image=*context.image;
  Sample before{},now{};
  if(!SampleCurrent(image,before)||before.command_scope!=1||before.native_access>1)return;
  alignas(16) unsigned char descriptor[0x48]{};
  bool attempted=false;
  if(before.native_access==1) {
    outcome.acquisition=Acquisition::borrowed;
    outcome.release=Release::unknown;
  }
  __try {
    if(before.native_access==0) {
      attempted=true;
      outcome.acquisition=Acquisition::unknown;
      outcome.release=Release::unknown;
      image.acquire_worker_access();
      if(!SampleCurrent(image,now)||!Same(before,now,1))__leave;
      descriptor[0]=1;
      outcome.acquisition=Acquisition::owned;
    }
    if(!SampleCurrent(image,now)||!Same(before,now,1))__leave;
    outcome.body=Body::failed;
    if(body(body_context))outcome.body=Body::succeeded;
    outcome.scope_verified=SampleCurrent(image,now)&&Same(before,now,1);
  } __finally {
    // A fault before TLS commit is not a zero-acquisition proof. Never retry an
    // unknown destructor or synthesize an owned descriptor from a changed epoch.
    if(!descriptor[0]&&attempted&&SampleCurrent(image,now)&&Same(before,now,1)) {
      descriptor[0]=1;
      outcome.acquisition=Acquisition::owned;
    }
    if(descriptor[0]) {
      outcome.release=Release::unknown;
      image.destroy_worker_access(descriptor);
      if(SampleCurrent(image,now)&&Same(before,now,0))outcome.release=Release::owned_released;
    } else if(outcome.acquisition==Acquisition::borrowed) {
      if(SampleCurrent(image,now)&&Same(before,now,1))outcome.release=Release::borrowed_preserved;
    }
  }
}
} // namespace

ck3_1210::DateWorkerGameAccessResultV2 WithCurrentDateWorkerGameAccess267V2(
    void *actual,ck3_1210::DateWorkerGameBodyV1 body,void *body_context) noexcept {
  Result result{};
  if(!actual)return result;
  __try {Run(*static_cast<const DateWorkerAccessContext267V1 *>(actual),body,body_context,result);}
  __except(EXCEPTION_EXECUTE_HANDLER) {result.scope_verified=false;}
  return result;
}
} // namespace xar::ck3_121003::build26785313
