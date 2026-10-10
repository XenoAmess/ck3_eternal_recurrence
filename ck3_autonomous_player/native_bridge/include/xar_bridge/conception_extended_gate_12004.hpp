#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

using ConceptionExtendedGate12004ReadMemory =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;

struct ConceptionExtendedGate12004Bindings {
  bool enabled = false;
  ConceptionExtendedGate12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

struct ConceptionExtendedGate12004Read {
  std::string_view source = "native_conception_extended_gate";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_conception_extended_binding_unavailable";
  std::optional<bool> extended_data_present;
  // Actual qword+288, not an inferred pointer, pregnancy state or probability.
  // Absent for native null-extended skip and failed qword copy.
  std::optional<std::uint64_t> extended_288_raw_u64;
  std::optional<bool> blocks_pair_conception;
};

ConceptionExtendedGate12004Bindings BindConceptionExtendedGate12004(
    std::string_view build_version, std::string_view executable_sha256,
    ConceptionExtendedGate12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// Root supplies the current household row's resolved Character and complete ID
// in its existing application-thread frame. Reads neither pregnancy, traits,
// fertility nor the original pair function; applies only its +288 gate.
ConceptionExtendedGate12004Read ReadConceptionExtendedGateForCharacter12004(
    const ConceptionExtendedGate12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id) noexcept;

} // namespace xar::ck3_12004
