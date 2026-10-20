#include "b11_five_flag_profile.hpp"
static_assert(XAR_B11_PROFILE_MASK==0);
#include "../src/character_skill_effect12004_native.cpp"
extern "C" unsigned B11FactoryCompiledMask() noexcept {
  return b11_qualification::CompiledMask();
}
