#include "xar_bridge/m4_factor_actor_inner_init_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kActualExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

template <class T>
void Store(M4FactorActorInnerInit12004 &output, std::size_t offset, T value) noexcept {
  std::memcpy(output.raw.data() + offset, &value, sizeof(value));
  for (std::size_t i = offset; i != offset + sizeof(value); ++i)
    output.defined_bytes[i] = 1;
}

void SelfPointer(M4FactorActorInnerInit12004 &output,
                 std::uint16_t offset, std::uint16_t target) noexcept {
  output.self_pointer_patches[output.self_pointer_patch_count++] = {offset, target};
  // These bytes are defined by the relocation operation, applied by08c at its
  // final owned address. Zero raw placeholders are not an observed null field.
  for (std::size_t i = offset; i != offset + sizeof(std::uint64_t); ++i)
    output.defined_bytes[i] = 1;
}
} // namespace

bool ProjectM4FactorActorInnerInit12004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    std::uint64_t frame_key, M4FactorActorInnerInit12004 &output) noexcept {
  output = {};
  output.module_base = module_base;
  output.executable_sha256 = executable_sha256;
  output.frame_key = frame_key;
  if (module_base == 0 || executable_sha256 != kActualExecutableSha256 ||
      module_base > std::numeric_limits<std::uintptr_t>::max() - 0x54DE2E0)
    return false;
  output.executable_sha256 = kActualExecutableSha256;
  // Actual8558B0 sets data=self+20 and capacity8. Count remains zero from the
  // constructor's post-null-release QWORD+8 store. Inline payload is untouched.
  SelfPointer(output, 0x00, 0x20);
  Store(output, 0x08, std::uint32_t{8});
  Store(output, 0x0C, std::uint32_t{0});
  SelfPointer(output, 0x10, 0x18);
  Store(output, 0x18, static_cast<std::uint64_t>(module_base + 0x448D2A0));
  Store(output, 0xE0, static_cast<std::uint64_t>(module_base + 0x54DE2E0));
  output.complete_source = true;
  return true;
}
} // namespace xar::ck3_12004
