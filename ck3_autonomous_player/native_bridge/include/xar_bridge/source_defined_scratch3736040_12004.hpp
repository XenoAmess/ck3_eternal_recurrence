#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::size_t kSourceDefinedScratch3736040Bytes12004 = 0x128;
inline constexpr char kSourceDefinedScratch3736040ExecutableSha25612004[] =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

struct SourceDefinedScratchSelfPointer12004 {
  std::uint16_t field_offset = 0;
  std::uint16_t target_offset = 0;
};

struct SourceDefinedScratch373604012004 {
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
  std::array<std::uint8_t, kSourceDefinedScratch3736040Bytes12004> raw{};
  std::array<std::uint8_t, kSourceDefinedScratch3736040Bytes12004> source_defined{};
  std::array<std::uint8_t, kSourceDefinedScratch3736040Bytes12004> numeric_known{};
  std::array<SourceDefinedScratchSelfPointer12004, 2> self_pointer_relations{};
  std::size_t self_pointer_relation_count = 0;
  bool exact_build_admitted = false;
  bool source_complete = false;
  bool logical_return_is_self = false;
  bool actual_initializer_called = false;
  std::optional<std::uintptr_t> physical_scratch_identity;
  std::string_view unavailable_reason;
};

// Actual3736040 uses only RCX=self. Its actual zero-release chain and slot20
// leaf define40 bytes: header0..20 and backing pointer120..128. Inline payload
// and every other hole remain unknown. The two self-pointer operations define
// field0->self20 and field10->self18; their rawzero placeholders are not numeric
// nulls or observed physical pointers. Parent frame/context admission is kept
// by the owning caller. This projection performs no reads or native calls.
bool ProjectSourceDefinedScratch373604012004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    SourceDefinedScratch373604012004 &output) noexcept;

} // namespace xar::ck3_12004
