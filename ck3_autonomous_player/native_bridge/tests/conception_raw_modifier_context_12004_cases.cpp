#include "xar_bridge/conception_modifier_context_12004.hpp"
#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include <cstdint>
#include <cstring>
#include <map>
#include <string>

namespace {
using namespace xar::ck3_12004;
using xar::ck3_12004::construction_owner_mode3::RawReceiverAccessV1;
constexpr std::uintptr_t kBase = 0x100000000ull;
constexpr std::uintptr_t kCharacter = 0x200000000ull;
constexpr std::uintptr_t kExtension = 0x300000000ull;
constexpr std::uintptr_t kModel = 0x400000000ull;
constexpr std::uintptr_t kDefault = kBase + 0x5D67B90;
constexpr std::string_view kSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

struct Memory {
  std::map<std::uintptr_t, unsigned char> bytes;
  std::size_t reads = 0;
  std::size_t fallback_slot_reads = 0;
  std::size_t default_guard_reads = 0;

  template<class T> void Set(std::uintptr_t address, const T &value) {
    unsigned char raw[sizeof(T)]{};
    std::memcpy(raw, &value, sizeof(T));
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = raw[i];
  }
  void InitializeFallback() {
    Set(kCharacter + 0x18, std::uint32_t{0xFFFFFFFFu});
    Set(kCharacter + 0x1B0, std::uintptr_t{0});
    Set(kBase + 0x5D67B80, std::int32_t{17});
    Set(kDefault + 0x68, kDefault + 0x88);
    Set(kDefault + 0x70, std::int32_t{32});
    Set(kDefault + 0x74, std::int32_t{0});
    Set(kDefault + 0xD0, kDefault + 0xF0);
    Set(kDefault + 0xD8, std::int32_t{32});
    Set(kDefault + 0xDC, std::int32_t{0});
  }
};

bool ReadConstAddress(void *context, const void *address, void *out,
                      std::size_t count) {
  auto &memory = *static_cast<Memory *>(context);
  const auto source = reinterpret_cast<std::uintptr_t>(address);
  ++memory.reads;
  if (source == kBase + 0x5C67570) ++memory.fallback_slot_reads;
  if (source == kBase + 0x5D67B80) ++memory.default_guard_reads;
  auto *destination = static_cast<unsigned char *>(out);
  for (std::size_t i = 0; i < count; ++i) {
    const auto found = memory.bytes.find(source + i);
    if (found == memory.bytes.end()) return false;
    destination[i] = found->second;
  }
  return true;
}

// The same mechanical const-void/uintptr callback join used by03/06 callers.
bool ReadIntegerAddress(void *context, std::uintptr_t address, void *out,
                        std::size_t count) noexcept {
  auto &access = *static_cast<RawReceiverAccessV1 *>(context);
  return access.exact_12004_bound && access.read_memory != nullptr &&
      access.read_memory(access.context, reinterpret_cast<const void *>(address),
                         out, count);
}
} // namespace

// Sole export, no main. Central10 adds this to the new connected compound.
bool VerifyRawCharacterModifierContext12004(std::string &failure) {
  using namespace xar::ck3_12004;
  failure.clear();
  const auto fail = [&](const char *text) { failure = text; return false; };
  Memory memory;
  memory.InitializeFallback();
  RawReceiverAccessV1 access{&memory, &ReadConstAddress, kBase, true};
  const auto bindings = BindConceptionModifierContext12004(
      access.module_base, "1.20.0.4", kSha, &ReadIntegerAddress, &access);
  if (!bindings.enabled) return fail("raw_access_binding");
  const auto unqualified = ResolveRawCharacterModifierContext12004(
      bindings, kCharacter, 0xFFFFFFFFu, false);
  const auto strict = ResolveConceptionModifierContext12004(bindings, kCharacter, -1);
  if (unqualified.ready || strict.ready || memory.reads != 0)
    return fail("unqualified_all_ones_or_changed_M7_admission");

  const auto observed = ResolveRawCharacterModifierContext12004(
      bindings, kCharacter, 0xFFFFFFFFu, true);
  if (!observed.ready || observed.context_address != kDefault ||
      observed.source != ConceptionModifierContextSource12004::InitializedDefault ||
      observed.full_character_id != -1 || observed.keys_stamp.count_raw != 0)
    return fail("source_qualified_all_ones_default");
  std::string reason;
  if (!CheckRawCharacterModifierContextStillCurrent12004(
          bindings, observed, 0xFFFFFFFFu, true, reason) ||
      CheckRawCharacterModifierContextStillCurrent12004(
          bindings, observed, 0xFFFFFFFFu, false, reason) ||
      CheckConceptionModifierContextStillCurrent12004(bindings, observed, reason))
    return fail("raw_recheck_admission_and_strict_M7");

  memory.Set(kCharacter + 0x18, std::uint32_t{0x01000001u});
  if (CheckRawCharacterModifierContextStillCurrent12004(
          bindings, observed, 0xFFFFFFFFu, true, reason))
    return fail("physical_identity_changed");
  memory.Set(kCharacter + 0x18, std::uint32_t{0xFFFFFFFFu});
  memory.Set(kDefault + 0xD0, std::uintptr_t{0});
  if (CheckRawCharacterModifierContextStillCurrent12004(
          bindings, observed, 0xFFFFFFFFu, true, reason))
    return fail("qualified_fallback_storage_destroyed");
  memory.Set(kDefault + 0xD0, kDefault + 0xF0);
  for (const std::int32_t guard : {std::int32_t{0}, std::int32_t{-1}}) {
    memory.Set(kBase + 0x5D67B80, guard);
    if (ResolveRawCharacterModifierContext12004(
            bindings, kCharacter, 0xFFFFFFFFu, true).ready)
      return fail("qualified_fallback_uninitialized_default");
  }

  // A fallback physical receiver can have an owned model. Native getter
  // selection still takes model+10 and does not inspect the default guard.
  memory.Set(kCharacter + 0x1B0, kExtension);
  memory.Set(kExtension + 0x258, kModel);
  memory.Set(kModel + 8, kCharacter);
  const auto guard_reads = memory.default_guard_reads;
  const auto owned = ResolveRawCharacterModifierContext12004(
      bindings, kCharacter, 0xFFFFFFFFu, true);
  if (!owned.ready || owned.context_address != kModel + 0x10 ||
      owned.source != ConceptionModifierContextSource12004::OwnedCharacter ||
      memory.default_guard_reads != guard_reads ||
      !CheckRawCharacterModifierContextStillCurrent12004(
          bindings, owned, 0xFFFFFFFFu, true, reason))
    return fail("qualified_fallback_owned_model_not_forced_default");
  memory.Set(kModel + 8, kCharacter + 0x1000);
  memory.Set(kBase + 0x5D67B80, std::int32_t{17});
  if (CheckRawCharacterModifierContextStillCurrent12004(
          bindings, owned, 0xFFFFFFFFu, true, reason))
    return fail("owned_receiver_changed_after_copy");

  memory.Set(kCharacter + 0x18, std::uint32_t{0xFEDCBA98u});
  memory.Set(kModel + 8, kCharacter);
  const auto high_generation = ResolveRawCharacterModifierContext12004(
      bindings, kCharacter, 0xFEDCBA98u, false);
  if (!high_generation.ready ||
      !CheckRawCharacterModifierContextStillCurrent12004(
          bindings, high_generation, 0xFEDCBA98u, false, reason))
    return fail("physical_high_generation_not_signed_positive_gate");
  if (memory.fallback_slot_reads != 0)
    return fail("adapter_read_caller_owned_fallback_slot");
  return true;
}
