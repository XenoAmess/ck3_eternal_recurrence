#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kPersonTransferBlockE0Rva12004 = 0x23060E0;
inline constexpr std::uintptr_t kPersonTransferBlockE0SelectedReturn12004 =
    0x291D030;
inline constexpr std::size_t kPersonTransferBlockE0Offset12004 = 0xE0;

using PersonTransferBlockE0ReadMemory12004 =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct PersonTransferBlockE0Bindings12004 {
  bool enabled = false;
  PersonTransferBlockE0ReadMemory12004 read_memory = nullptr;
  void *read_context = nullptr;
};

// Pure memory copies only. No allocator virtual method or original helper runs.
PersonTransferBlockE0Bindings12004 BindPersonTransferBlockE0Memory12004(
    std::string_view version, std::string_view executable_sha256,
    PersonTransferBlockE0ReadMemory12004 read_memory,
    void *read_context = nullptr) noexcept;

struct PersonTransferBlockE0Copy12004 {
  std::uintptr_t model_identity = 0;
  std::optional<std::uintptr_t> block_identity;
  std::optional<std::uintptr_t> allocator_receiver_identity;
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> capacity_i32;
  std::optional<std::int32_t> count_i32;
  std::optional<std::vector<std::int64_t>> values_q64;
  std::string values_reason;
  friend bool operator==(const PersonTransferBlockE0Copy12004 &,
                         const PersonTransferBlockE0Copy12004 &) = default;
};

// The caller supplies the actual A/B Model identities at original291CF30
// entry/return. This function does not resolve a current Model or Character.
// Header fields copy independently; missing capacity does not hide Q64 values.
PersonTransferBlockE0Copy12004 CopyPersonTransferBlockE0Storage12004(
    const PersonTransferBlockE0Bindings12004 &bindings,
    std::uintptr_t actual_model);

struct PersonTransferBlockE0Comparison12004 {
  bool model_pair_matches = false;
  std::optional<bool> a_values_equal_pre_b;
  std::optional<bool> b_values_equal_pre_a;
  std::optional<bool> copied_values_cross_equal;
  // Diagnostic equality to the outer-call entry header, not a branch verdict:
  // the actual matched-allocator path may reserve before its direct stores.
  std::optional<bool> entry_headers_cross_equal;
  std::string reason;
};

// Observe copied facts. All-path exchange semantics and natural transfer
// chronology remain separate. Independently copied sides stay independently
// visible if the other side is partial.
PersonTransferBlockE0Comparison12004 ComparePersonTransferBlockE0Copies12004(
    const PersonTransferBlockE0Copy12004 &pre_a,
    const PersonTransferBlockE0Copy12004 &pre_b,
    const PersonTransferBlockE0Copy12004 &post_a,
    const PersonTransferBlockE0Copy12004 &post_b);

struct PersonTransferBlockE0Header12004 {
  std::uintptr_t block_identity = 0;
  std::uintptr_t data_identity = 0;
  std::int32_t capacity_i32 = 0;
  std::int32_t count_i32 = 0;
  std::uintptr_t allocator_receiver_identity = 0;
  friend bool operator==(const PersonTransferBlockE0Header12004 &,
                         const PersonTransferBlockE0Header12004 &) = default;
};

struct PersonTransferBlockE0DirectHeaderPostimage12004 {
  PersonTransferBlockE0Header12004 a;
  PersonTransferBlockE0Header12004 b;
};

// Conditional source model of 2306248..2306269 only. The inputs must be the
// immediate pre-store state after any real B73FD0 calls, not function entry.
// Block and allocator receiver identities remain local; only data/cap/count
// cross. No material array, reserve, inline path or fallback is simulated.
PersonTransferBlockE0DirectHeaderPostimage12004
ProjectPersonTransferBlockE0DirectHeaderStores12004(
    const PersonTransferBlockE0Header12004 &immediate_pre_store_a,
    const PersonTransferBlockE0Header12004 &immediate_pre_store_b) noexcept;

} // namespace xar::ck3_12004
