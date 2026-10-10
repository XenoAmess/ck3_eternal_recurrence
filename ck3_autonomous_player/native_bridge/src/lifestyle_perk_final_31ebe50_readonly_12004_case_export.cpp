#include "xar_bridge/lifestyle_perk_final_31ebe50_readonly_12004.hpp"
#include "xar_bridge/lifestyle_perk_truth_producer_12004.hpp"
#include "xar_bridge/source_read_leaf_frame_12004.hpp"

#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004::lifestyle;
constexpr std::uintptr_t kImage = 0x10000000U;
constexpr std::uintptr_t kCharacter = 0x20000000U;
constexpr std::uintptr_t kExtension = 0x30000000U;
constexpr std::uintptr_t kPerk = 0x40000000U;
constexpr std::uintptr_t kPrerequisites = 0x50000000U;
constexpr std::uintptr_t kOwnedRows = 0x60000000U;

struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> fields;
  std::map<std::uintptr_t, std::size_t> reads;
  std::uintptr_t fail_second_address = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto &raw = fields[address];
    raw.resize(sizeof(value));
    std::memcpy(raw.data(), &value, sizeof(value));
  }
  static bool Read(void *opaque, std::uintptr_t address, void *out,
                   std::size_t bytes) {
    auto &self = *static_cast<Memory *>(opaque);
    const std::size_t occurrence = ++self.reads[address];
    if (address == self.fail_second_address && occurrence == 2U)
      return false;
    const auto found = self.fields.find(address);
    if (found == self.fields.end() || found->second.size() != bytes)
      return false;
    std::memcpy(out, found->second.data(), bytes);
    return true;
  }
  LifestylePerkReadonlyAccess12004 Access(
      const xar::ck3_12004::SourceReadFrame12004 *frame = nullptr) {
    return {kImage, this, &Memory::Read, std::nullopt, frame};
  }
  void EmptyOwned() {
    Put(kCharacter + 0x1B0U, kExtension);
    Put(kExtension + 0x220U, std::uintptr_t{0U});
    Put(kExtension + 0x22CU, std::int32_t{0});
  }
};

void Require(bool value, const char *reason) {
  if (!value)
    throw std::runtime_error(reason);
}
} // namespace

// Only new62 connector cases. The initial already-owned whole-command case
// belongs to16; no old62 or generic27 M4 case export is invoked here.
bool RunLifestylePerkFinalNaturalFocus12004() {
  {
    Memory memory;
    LifestylePerkTruthProducer37998D0Result12004 observation;
    observation.selected_perk_identity = kPerk;
    observation.source_projected_returned_raw_u8 = std::uint8_t{1U};
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter, std::uintptr_t{123U}, &observation);
    Require(!result.value && result.unavailable_reason ==
                "nonnull_diagnostic_writer_path_not_projected" &&
                memory.reads.empty() && observation.selected_perk_identity == 0U &&
                !observation.source_projected_returned_raw_u8,
            "62 nonnull writer keeps pointer scope and performs no null-path reads");
  }
  {
    Memory memory;
    memory.Put(kCharacter + 0x1B0U, std::uintptr_t{0U});
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter);
    Require(!result.value && result.unavailable_reason ==
                "initial_owned_perk_collection_unavailable" &&
                memory.reads[kPerk + 0x448U] == 0U,
            "62 missing actual thread TLS does not invent an empty collection");
  }
  {
    Memory memory;
    memory.EmptyOwned();
    memory.Put(kExtension + 0x22CU, std::int32_t{513});
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter);
    Require(!result.value && result.unavailable_reason ==
                "initial_owned_perk_membership_unavailable" &&
                memory.reads[kPerk + 0x448U] == 0U,
            "62 adapter uses existing M5 bound512 without granting native false");
  }
  {
    Memory memory;
    memory.EmptyOwned();
    memory.Put(kPerk + 0x448U, kPrerequisites);
    memory.Put(kPerk + 0x454U, std::int32_t{1});
    memory.Put(kPrerequisites, std::uintptr_t{0x8000000012345678ULL});
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter);
    Require(result.value.has_value() && !*result.value &&
                result.unavailable_reason.empty() &&
                memory.reads[kCharacter + 0x1B0U] == 2U &&
                memory.reads[kCharacter + 0x18U] == 0U,
            "62 absent prerequisite returns false after fresh getter, skips context");
  }
  {
    Memory memory;
    memory.EmptyOwned();
    memory.Put(kPerk + 0x448U, kPrerequisites);
    memory.Put(kPerk + 0x454U, std::int32_t{1});
    memory.Put(kPrerequisites, std::uintptr_t{0U});
    memory.fail_second_address = kCharacter + 0x1B0U;
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter);
    Require(!result.value && result.unavailable_reason ==
                "prerequisite_owned_perk_collection_unavailable" &&
                memory.reads[kCharacter + 0x1B0U] == 2U &&
                memory.reads[kCharacter + 0x18U] == 0U,
            "62 prerequisite does not reuse the previously read collection");
  }
  {
    Memory memory;
    memory.EmptyOwned();
    memory.Put(kExtension + 0x220U, kOwnedRows);
    memory.Put(kExtension + 0x22CU, std::int32_t{1});
    memory.Put(kOwnedRows, std::uintptr_t{0U});
    memory.Put(kPerk + 0x448U, kPrerequisites);
    memory.Put(kPerk + 0x454U, std::int32_t{2});
    memory.Put(kPrerequisites, std::uintptr_t{0U});
    memory.Put(kPrerequisites + 8U, std::uintptr_t{0U});
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter);
    Require(!result.value && result.unavailable_reason ==
                "character_scope_source_projection_unavailable" &&
                memory.reads[kCharacter + 0x1B0U] == 3U &&
                memory.reads[kCharacter + 0x18U] == 1U,
            "62 legal zero and duplicate keys retain all fresh prerequisite demands");
  }
  {
    Memory memory;
    memory.EmptyOwned();
    memory.Put(kPerk + 0x448U, std::uintptr_t{0U});
    memory.Put(kPerk + 0x454U, std::int32_t{-1});
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter);
    Require(!result.value && result.unavailable_reason ==
                "negative_prerequisite_count" &&
                memory.reads[kCharacter + 0x18U] == 0U,
            "62 negative extent stays unknown and does not construct context");
  }
  {
    Memory memory;
    memory.EmptyOwned();
    memory.Put(kPerk + 0x448U, std::uintptr_t{0U});
    memory.Put(kPerk + 0x454U, std::int32_t{0});
    memory.Put(kCharacter + 0x18U, std::uint32_t{0xAB000005U});
    LifestylePerkTruthProducer37998D0Result12004 observation;
    const auto result = ReadLifestylePerkFinal31EBE5012004(
        memory.Access(), kPerk, kCharacter, std::uintptr_t{0U}, &observation);
    Require(!result.value && result.unavailable_reason ==
                "lifestyle_truth_current_caller_frame_unavailable" &&
                memory.reads[kCharacter + 0x18U] == 1U &&
                memory.reads[kImage + 0x5D1DADCU] == 0U &&
                observation.selected_perk_identity == kPerk &&
                observation.context_projection_available &&
                observation.compiled_trigger_receiver_identity == kPerk + 0x80U &&
                observation.unavailable_reason == result.unavailable_reason &&
                !observation.source_projected_returned_raw_u8 &&
                !observation.trigger_vtable_raw &&
                !observation.root_kind_getter_slot58_raw &&
                !observation.root_mask_getter_slot60_raw &&
                !observation.final_evaluator_slotc8_raw,
            "62 empty prerequisites and ready context do not invent final truth");
  }
  return true;
}
