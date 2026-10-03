#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::holy_order::selected_candidates {

inline constexpr std::string_view kExeSha256 =
    "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";

struct NativeTitleRefVector {
  std::uint32_t* data{};
  std::int32_t capacity{};
  std::int32_t count{};
  void* allocator{};
};
static_assert(offsetof(NativeTitleRefVector, capacity) == 0x08);
static_assert(offsetof(NativeTitleRefVector, count) == 0x0c);
static_assert(offsetof(NativeTitleRefVector, allocator) == 0x10);
static_assert(sizeof(NativeTitleRefVector) == 0x18);

using NativeProduce = void (*)(void* widget, void* actor,
                              NativeTitleRefVector* titles, void* params,
                              std::int32_t maximum_count);
using NativeSelectedValid = bool (*)(void* widget, void* params,
                                    void* reason_context);
using NativeInitializeVector = void (*)(void* allocator,
                                       std::uint32_t** data,
                                       std::int32_t* capacity);
using NativeReleaseVector = void (*)(void* allocator, void* data,
                                    std::size_t element_size);

struct Bindings {
  std::uintptr_t module_base{};
  std::uintptr_t military_vtable{};
  std::uintptr_t landed_title_vtable{};
  std::uintptr_t title_ref_allocator_vtable{};
  std::uintptr_t title_ref_fallback_allocator{};
  NativeProduce military_produce{};
  NativeProduce landed_title_produce{};
  NativeSelectedValid military_selected_valid{};
  NativeSelectedValid landed_title_selected_valid{};
  NativeInitializeVector initialize_vector{};
  NativeReleaseVector release_vector{};
  bool available{};
};

struct Widget {
  void* pointer{};
  std::uint32_t selected_name_key{};
  std::int32_t expected_tier{};
  bool military{};
  std::uint8_t configuration_type{};
  NativeProduce produce{};
  NativeSelectedValid selected_valid{};
};

Bindings BindHolyOrderSelectedCandidatesImage12003(
    std::uintptr_t module_base, std::string_view exe_sha256) noexcept;

// Reads already-created decision configuration; no DecisionView/UI is created.
bool GetHolyOrderDecisionWidget12003(const Bindings& bindings,
                                    const void* decision, Widget& output) noexcept;

// Caller supplies native params with named ruler/current actor, before selection.
// The game's controller applies title_valid and emits complete 32-bit TitleIDs.
// Empty output is a successful, available-empty candidate collection.
bool CollectHolyOrderTitleCandidates12003(
    const Bindings& bindings, const Widget& widget, void* actor, void* params,
    std::vector<std::uint32_t>& output) noexcept;

// Call after the native params setter installs the selected barony/title token.
// Returns read/call success separately from the legitimate false predicate.
bool ReadSelectedTitleValid12003(const Bindings& bindings, const Widget& widget,
                               void* params, bool& valid) noexcept;

}  // namespace xar::ck3_12003::religion::holy_order::selected_candidates
