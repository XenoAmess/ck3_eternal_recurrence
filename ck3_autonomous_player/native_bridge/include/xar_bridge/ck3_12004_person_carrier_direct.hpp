#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr char kPersonCarrierDirect12004Schema[] =
    "xar.ck3.person-carrier-direct-12004-v1";
inline constexpr std::uintptr_t kPersonCarrierDefaultPcRva12004 = 0x5D71200;
inline constexpr std::uintptr_t kPersonCarrierDefaultGuardRva12004 = 0x5D711F0;
inline constexpr std::uintptr_t kPersonCarrierContextGetterRva12004 = 0x28C3AC0;
inline constexpr std::int64_t kPersonCarrierDirectWeight12004 = 100'000;

// Root supplies its guarded copy callback. No native getter, initializer,
// append, evaluator, or unguarded memcpy is installed by this binding.
using PersonCarrierDirect12004ReadMemory =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;

struct PersonCarrierDirect12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  // Exact4 getter identity; the memory-only owned branch below never invokes it.
  std::uintptr_t current_context_getter_identity = 0;
  PersonCarrierDirect12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

struct PersonCarrierDirect12004Properties {
  // These are physical arrays governed by the same signed PC count+C.
  // Independent failed copies remain null; order/duplicates/FFFF are retained.
  std::optional<std::vector<std::uint16_t>> keys_u16;
  std::optional<std::vector<std::int64_t>> values_q64;
  friend bool operator==(const PersonCarrierDirect12004Properties &,
                         const PersonCarrierDirect12004Properties &) = default;
};

struct PersonCarrierDirect12004DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> selected_model_identity;
  std::optional<std::uintptr_t> character_identity;
  // Model+10 is destination provenance only, never a source/baseline copy.
  std::optional<std::uintptr_t> destination_pc_identity;
  std::optional<bool> carrier_present;
  std::optional<std::uintptr_t> carrier_identity;
  std::optional<std::uintptr_t> definition_identity;
  std::optional<std::uint32_t> definition_magic_u32;
  std::optional<std::int32_t> rank_i32;
  std::optional<std::int32_t> row_count_i32;
  std::optional<std::uintptr_t> table_identity;
  std::string selection = "unavailable";
  std::optional<std::int32_t> default_guard_raw;
  std::optional<std::uintptr_t> selected_pc_identity;
  std::optional<std::int32_t> selected_pc_count_i32;
  std::optional<PersonCarrierDirect12004Properties> properties;
  std::optional<std::uint32_t> source_occurrence_count;
  std::int64_t weight_q100000 = kPersonCarrierDirectWeight12004;
  friend bool operator==(const PersonCarrierDirect12004DTO &,
                         const PersonCarrierDirect12004DTO &) = default;
};

// Only the existing exact 1.20.0.4 version/SHA pin is admitted; no old alias.
PersonCarrierDirect12004Bindings BindPersonCarrierDirect12004(
    std::uintptr_t module_base, std::string_view build_version,
    std::string_view executable_sha256,
    PersonCarrierDirect12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// The bounded model-receiver leaf used by the same-selected-person query hook.
// Ancillary full-ID copy failure is visible as null; it does not change the
// numerical branch's readiness or authorize attribution to another Character.
PersonCarrierDirect12004DTO ReadPersonCarrierDirect12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_model);

// The cached actual4 getter's owned branch: Character1B0 -> scratch258 ->
// Model, with Model8 == the requested Character. Its inline-default branch is
// not a model and is never substituted for an absent or differently owned model.
PersonCarrierDirect12004DTO ReadPersonCarrierDirectForCharacter12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_character);

// Returns a JSON leaf object. Signed Q64 elements are decimal JSON strings.
std::string SerializePersonCarrierDirect12004(
    const PersonCarrierDirect12004DTO &dto);

} // namespace xar::ck3_12004
