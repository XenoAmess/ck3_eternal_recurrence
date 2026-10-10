#include "xar_bridge/source_defined_scratch3736040_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
bool ExactExecutable(std::string_view value) noexcept {
  constexpr std::string_view expected = kSourceDefinedScratch3736040ExecutableSha25612004;
  if (value.size() != expected.size()) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    char digit = value[i];
    if (digit >= 'A' && digit <= 'F') digit = static_cast<char>(digit - 'A' + 'a');
    if (digit != expected[i]) return false;
  }
  return true;
}

template <typename T>
void Store(SourceDefinedScratch373604012004 &out, std::size_t offset, T value) noexcept {
  std::memcpy(out.raw.data() + offset, &value, sizeof(value));
  for (std::size_t i = offset; i < offset + sizeof(value); ++i) {
    out.source_defined[i] = 1;
    out.numeric_known[i] = 1;
  }
}

void SelfPointer(SourceDefinedScratch373604012004 &out,
                 std::uint16_t field, std::uint16_t target) noexcept {
  out.self_pointer_relations[out.self_pointer_relation_count++] = {field, target};
  for (std::size_t i = field; i < static_cast<std::size_t>(field) + sizeof(std::uint64_t); ++i)
    out.source_defined[i] = 1;
}
} // namespace

bool ProjectSourceDefinedScratch373604012004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    SourceDefinedScratch373604012004 &output) noexcept {
  output = {};
  output.module_base = module_base;
  output.exact_build_admitted = ExactExecutable(executable_sha256);
  if (!output.exact_build_admitted) {
    output.unavailable_reason = "scratch3736040_executable_sha256_unbound";
    return false;
  }
  output.executable_sha256 = kSourceDefinedScratch3736040ExecutableSha25612004;
  if (module_base == 0) {
    output.unavailable_reason = "scratch3736040_module_base_unavailable";
    return false;
  }
  if (module_base > (std::numeric_limits<std::uintptr_t>::max)() - std::uintptr_t{0x54F2990}) {
    output.unavailable_reason = "scratch3736040_module_literal_address_overflow";
    return false;
  }
  // Actual8558B0 receives RCX=self18, so [RCX+8] is self20. Count remains
  // zero after the constructor's QWORD+8 reset, not a fabricated empty input.
  SelfPointer(output, 0x00, 0x20);
  Store(output, 0x08, std::uint32_t{8});
  Store(output, 0x0C, std::uint32_t{0});
  SelfPointer(output, 0x10, 0x18);
  Store(output, 0x18, static_cast<std::uint64_t>(module_base + std::uintptr_t{0x492B070}));
  Store(output, 0x120, static_cast<std::uint64_t>(module_base + std::uintptr_t{0x54F2990}));
  output.source_complete = true;
  output.logical_return_is_self = true;
  return true;
}

} // namespace xar::ck3_12004
