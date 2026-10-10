#pragma once

#include "xar_bridge/construction_owner_mode3_loaded_inputs_12004.hpp"
#include "xar_bridge/returned_selector_28c2df0_12004.hpp"
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::string_view kConstructionNumeric24CEF10SourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uintptr_t kConstructionNumeric24CEF10Rva12004 = 0x24CEF10;

enum class Numeric24CEF10FailureV1 : std::uint8_t {
  none, exact_build, read_callback, image_base, first_resolution,
  second_resolution, returned_object, flags_read, value_read, source_changed,
};

// Raw copied lookup operands. Optional fields retain the native lazy-read
// path: a null registry skips the requested ID, count and slot reads.
struct Numeric24CEF10ResolutionV1 {
  bool observed = false;
  bool used_fallback = false;
  std::uintptr_t registry_slot_rva = 0;
  std::uintptr_t fallback_slot_rva = 0;
  std::optional<std::uintptr_t> registry_pointer;
  std::optional<std::uint32_t> requested_full_id_u32;
  std::optional<std::uint32_t> registry_count_u32;
  std::optional<std::uintptr_t> slots_pointer;
  std::optional<std::uintptr_t> candidate_pointer;
  std::optional<std::uint32_t> candidate_full_id_u32;
  std::optional<std::uintptr_t> fallback_pointer;
  std::uintptr_t selected_pointer = 0;
};

struct ConstructionNumericChild24CEF10ObservationV1 {
  bool observed = false;
  Numeric24CEF10FailureV1 failure = Numeric24CEF10FailureV1::none;
  std::string_view source_pin = kConstructionNumeric24CEF10SourcePin12004;
  std::uint64_t frame_key = 0;
  std::uintptr_t receiver_pointer = 0;
  Numeric24CEF10ResolutionV1 first_resolution;
  Numeric24CEF10ResolutionV1 second_resolution;
  ReturnedObject28C2DF0Result12004 returned_object_source;
  std::optional<std::uint64_t> flags_qword_40;
  std::optional<bool> gate_bit35;
  std::optional<std::uint32_t> eax_raw_u32;
  std::optional<std::int32_t> eax_signed_i32;
  // Equal readonly copies do not prove values consumed by an original CALL.
  bool actual_original_consumed_values = false;
};

// RCX is the actual19c parent RDX (slots+F0 context+848). Reuse04's owned
// returned-object resolver on this reader's own resolved receiver. No native
// function is called, and neither38C nor unrelated4D6 is read on a clear gate.
ConstructionNumericChild24CEF10ObservationV1 ReadConstructionNumericChild24CEF10V1(
    const LoadedInputAccessV1 &access, std::uintptr_t image_base,
    std::uintptr_t original_receiver, std::uint64_t frame_key);

void VerifyConstructionNumericChild24CEF10OwnedCases12004();

} // namespace xar::ck3_12004::construction_owner_mode3
