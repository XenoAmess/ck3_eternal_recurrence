#ifdef NDEBUG
#error B11 factory assertions must remain enabled
#endif
#include "b11_five_flag_profile.hpp"
#include "xar_bridge/character_skill_effect12004_native.hpp"
#include <cassert>
#include <cstdio>
#include <string_view>
extern "C" unsigned B11FactoryCompiledMask() noexcept;
int main() {
  static_assert(XAR_B11_PROFILE_MASK==0);
  namespace core=xar::bridge::character_skill_effect12004;
  assert(B11FactoryCompiledMask()==0);
  core::NativeContext context{};
  const auto environment=core::BindNative(context);
  assert(!environment.enabled&&environment.context==nullptr);
  assert(environment.read_memory==nullptr&&environment.read_frame==nullptr);
  assert(environment.read_level==nullptr&&environment.read_breakdown==nullptr);
  assert(environment.callback_provenance==core::CallbackProvenance::unavailable);
  assert(!environment.allow_owned_fixture);
  assert(std::string_view(context.failure)=="native_context_not_bound");
  assert(!core::NativeSourceStillBound(context));
  assert(context.level_calls==0&&context.breakdown_calls==0&&context.string_destroy_calls==0);
  std::puts("b11_actor_factory_off compile_and_invalid_context_guard");
}
