#pragma once
#include <atomic>
#include <cstdint>
#include <limits>
#include <optional>

namespace xar::ck3_12004 {
// The entry kind never substitutes for a nested writer's exact source caller.
enum class NativeInvocationParentKind12004 : std::uint32_t {
  periodic_supply_callback=1, county_entry_callback=2, regular_refill_core=3,
  residual_allocator=4,
};
struct NativeInvocationFrame12004 {
  NativeInvocationParentKind12004 parent_kind{};
  std::uint64_t invocation_token=0;
  std::uint32_t native_thread_id=0, nesting_depth=0;
  std::optional<std::uint64_t> parent_invocation_token;
  const void *typed_payload=nullptr; // Scoped owner only; never serialized here.
  const NativeInvocationFrame12004 *previous=nullptr;
};
namespace native_invocation_detail_12004 {
inline std::atomic<std::uint64_t> next_token{0};
inline thread_local const NativeInvocationFrame12004 *current=nullptr;
inline std::uint64_t AllocateToken(std::atomic<std::uint64_t> &counter) noexcept {
  auto value=counter.load(std::memory_order_relaxed);
  while(value!=std::numeric_limits<std::uint64_t>::max()){
    if(counter.compare_exchange_weak(value,value+1,std::memory_order_relaxed))return value+1;
  }
  return 0;
}
}
inline const NativeInvocationFrame12004 *CurrentNativeInvocationContext12004() noexcept {
  return native_invocation_detail_12004::current;
}
class NativeInvocationScope12004 final {
public:
  NativeInvocationScope12004(NativeInvocationParentKind12004 kind,
      std::uint32_t thread_id,const void *typed_payload) noexcept {
    const auto *previous=CurrentNativeInvocationContext12004();
    frame_.parent_kind=kind;
    frame_.invocation_token=native_invocation_detail_12004::AllocateToken(native_invocation_detail_12004::next_token);
    frame_.native_thread_id=thread_id;
    frame_.nesting_depth=previous==nullptr?1U:previous->nesting_depth+1U;
    if(previous!=nullptr&&previous->invocation_token!=0)frame_.parent_invocation_token=previous->invocation_token;
    frame_.typed_payload=typed_payload;frame_.previous=previous;
    native_invocation_detail_12004::current=&frame_;
  }
  NativeInvocationScope12004(const NativeInvocationScope12004 &)=delete;
  NativeInvocationScope12004 &operator=(const NativeInvocationScope12004 &)=delete;
  ~NativeInvocationScope12004() noexcept{native_invocation_detail_12004::current=frame_.previous;}
  const NativeInvocationFrame12004 &frame() const noexcept{return frame_;}
private:
  NativeInvocationFrame12004 frame_{};
};
}
