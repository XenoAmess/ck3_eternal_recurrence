#include "b11_five_flag_profile.hpp"
// Relative include resolves only in the final frozen B11 source snapshot.
#include "../src/ck3_12002_nonwar_router.cpp"
extern "C" unsigned B11RouterCompiledMask() noexcept {
  return b11_qualification::CompiledMask();
}
