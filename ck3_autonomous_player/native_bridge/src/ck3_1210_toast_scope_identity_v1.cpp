#include "xar_bridge/ck3_1210_toast_scope_identity_v1.hpp"
#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"
#include <cstring>
#include <limits>
namespace xar::ck3_1210 {
namespace {
constexpr std::uintptr_t kStoryStorageSlot=0x6A66700;
constexpr std::size_t kMaximumBytes=1024;
struct Reader {
  const ToastObjectMemoryReaderV1 &input;std::size_t used=0;
  template<class T>bool load(std::uintptr_t p,std::size_t offset,T &out) noexcept {
    if(!input.copy || !p || offset>(std::numeric_limits<std::uintptr_t>::max)()-p ||
        sizeof(T)>(std::numeric_limits<std::uintptr_t>::max)()-(p+offset) ||
        sizeof(T)>kMaximumBytes-used)return false;
    used+=sizeof(T);return input.copy(input.context,p+offset,&out,sizeof(out));
  }
};
bool Capture(Reader &r,std::uintptr_t base,std::uintptr_t slot,std::uint32_t id,
    std::size_t id_offset,std::size_t magic_offset,std::uint32_t magic,ToastScopeIdentityWitnessV1 &out) noexcept {
  if(!r.load(base,slot,out.storage) || !out.storage || !r.load(out.storage,0x20,out.slots) ||
      !r.load(out.storage,0x2C,out.capacity) || !out.slots || out.capacity==0 || out.capacity>0x1000000U)return false;
  const auto index=id&0xFFFFFFU;
  if(index>=out.capacity || !r.load(out.slots,static_cast<std::size_t>(index)*0x10+8,out.object) || !out.object ||
      !r.load(out.object,id_offset,out.full_id) || out.full_id!=id ||
      !r.load(out.object,magic_offset,out.magic) || out.magic!=magic)return false;
  return true;
}
} // namespace
bool ReadToastScopeIdentityV1(const ToastScopeIdentityBindingsV1 &bindings,
    const std::array<std::byte,16> &token,const ToastObjectMemoryReaderV1 &input,ToastScopeIdentityV1 &out) noexcept {
  out={};
  auto fail=[&](std::string_view reason) noexcept {out.status=ToastScopeIdentityStatusV1::unavailable;
    out.full_id=0;out.witness={};out.unavailable_reason=reason;return false;};
  if(!bindings.exact_build_admitted || !bindings.module_base ||
      bindings.module_base>(std::numeric_limits<std::uintptr_t>::max)()-kStoryStorageSlot-sizeof(void *) || !input.copy)
    return fail("scope_exact_binding_unavailable");
  std::uint64_t payload=0;std::memcpy(&out.observed_tag,token.data(),2);std::memcpy(&payload,token.data()+8,8);
  if(out.observed_tag!=4 && out.observed_tag!=0x16) {
    out.status=ToastScopeIdentityStatusV1::unsupported;out.unavailable_reason="scope_tag_not_admitted";return true;
  }
  out.kind=out.observed_tag==4?ToastScopeKindV1::character:ToastScopeKindV1::story;
  // The native resolver consumes the low32 ID. This stricter reader accepts
  // only its zero-extended form, never reducing a malformed payload modulo32.
  if(payload>0xFFFFFFFFULL || payload==0xFFFFFFFFULL)return fail("scope_id_noncanonical_or_invalid");
  const auto id=static_cast<std::uint32_t>(payload);
  const bool story=out.kind==ToastScopeKindV1::story;
  const auto slot=story?kStoryStorageSlot:kCharacterStorageSlotRva;
  const std::size_t id_offset=story?0x10:0x18,magic_offset=story?0x14:0x1C;
  const std::uint32_t magic=story?0x41635374U:0x43686172U;
  Reader reader{input};ToastScopeIdentityWitnessV1 first{},second{};
  if(!Capture(reader,bindings.module_base,slot,id,id_offset,magic_offset,magic,first) ||
      !Capture(reader,bindings.module_base,slot,id,id_offset,magic_offset,magic,second))return fail("scope_canonical_object_unavailable");
  if(first!=second)return fail("scope_canonical_object_changed");
  out.status=ToastScopeIdentityStatusV1::available;out.full_id=id;out.witness=second;out.unavailable_reason={};return true;
}
} // namespace xar::ck3_1210
