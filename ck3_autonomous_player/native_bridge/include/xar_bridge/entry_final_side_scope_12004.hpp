#pragma once

#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kEntryFinalSideRva12004 = 0x2651050;
inline constexpr std::uintptr_t kEntryFinalSideZeroReturn12004 = 0x247AB17;
inline constexpr std::uintptr_t kEntryFinalSideOneReturn12004 = 0x247AB26;
inline constexpr std::array<std::uint8_t, 20> kEntryFinalSidePrologue12004{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,
    0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xEC,0x20};

enum class EntryFinalSideBucket12004 { levy, men_at_arms };

struct EntryFinalSideIdentity12004 {
  PersonInstalledTransferEvent12004 occurrence;
  std::uintptr_t side_identity = 0;
  std::uintptr_t province_identity = 0;
  std::uintptr_t caller_return_rva = 0;
  std::uintptr_t caller_return_slot = 0;
  // Literal source return point only; not an inferred Combat invocation.
  std::optional<std::uint32_t> source_side_index;
};

struct EntryFinalSideBucketHeader12004 {
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> count_i32;
};

struct EntryFinalSidePhysicalSlot12004 {
  EntryFinalSideBucket12004 bucket = EntryFinalSideBucket12004::levy;
  std::size_t bucket_index = 0;
  std::size_t traversal_ordinal = 0;
  std::uintptr_t entry_identity = 0;
  std::uintptr_t writer_return_rva = 0;
  std::optional<std::array<std::uint8_t, 0x60>> raw_before;
};

struct EntryFinalSideScope12004 {
  EntryFinalSideIdentity12004 identity;
  EntryFinalSideBucketHeader12004 levy_header;
  EntryFinalSideBucketHeader12004 maa_header;
  std::vector<EntryFinalSidePhysicalSlot12004> physical_slots;
  bool copy_complete = false;
  std::string reason;
};

struct EntryFinalSideWriterScope12004 {
  EntryFinalSideIdentity12004 side;
  EntryFinalSidePhysicalSlot12004 slot;
  PersonInstalledTransferEvent12004 begin_event;
};

// Available only during the actual original Side call on this thread. Nested
// calls restore the previous scope; they never merge by ID or elapsed time.
const EntryFinalSideScope12004 *PeekActiveEntryFinalSideScope12004() noexcept;
const EntryFinalSideWriterScope12004 *
PeekActiveEntryFinalSideWriterScope12004() noexcept;

const EntryFinalSidePhysicalSlot12004 *FindEntryFinalSidePhysicalSlot12004(
    const EntryFinalSideScope12004 &, std::uintptr_t entry,
    std::uintptr_t province, std::uintptr_t writer_return_rva) noexcept;

class EntryFinalSideWriterSlotScope12004 {
public:
  EntryFinalSideWriterSlotScope12004(
      std::uintptr_t entry, std::uintptr_t province,
      std::uintptr_t writer_return_rva,
      const PersonInstalledTransferEvent12004 &begin_event);
  ~EntryFinalSideWriterSlotScope12004();
  EntryFinalSideWriterSlotScope12004(
      const EntryFinalSideWriterSlotScope12004 &) = delete;
  EntryFinalSideWriterSlotScope12004 &operator=(
      const EntryFinalSideWriterSlotScope12004 &) = delete;

private:
  const EntryFinalSideWriterScope12004 *previous_ = nullptr;
  std::optional<EntryFinalSideWriterScope12004> current_;
};

struct EntryFinalWriterCaptureRecord12004;
// Retain the immutable completed child in this current actual Side scope,
// including independently partial children. It does not qualify slot lineage.
void AppendEntryFinalSideWriterRecord12004(
    const EntryFinalWriterCaptureRecord12004 &) noexcept;

} // namespace xar::ck3_12004
