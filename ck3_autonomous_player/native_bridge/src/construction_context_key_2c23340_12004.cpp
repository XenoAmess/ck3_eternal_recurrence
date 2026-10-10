#include "xar_bridge/construction_context_key_2c23340_12004.hpp"
#include "xar_bridge/conception_modifier_context_12004.hpp"
#include "xar_bridge/construction_actual_2c42930_return_12004.hpp"
#include "xar_bridge/title_selected_full_id_12004.hpp"
#include <cstring>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
constexpr auto kSha = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
struct ReadStamp {
  std::uintptr_t address = 0;
  std::size_t size = 0;
  std::array<std::byte, 8> bytes{};
};
struct ReadSet {
  const LoadedInputAccessV1 &original;
  std::vector<ReadStamp> stamps;
  static bool Copy(void *opaque, const void *source, void *out,
                   std::size_t size) noexcept {
    auto &set = *static_cast<ReadSet *>(opaque);
    if (size > 8 || set.original.read_memory == nullptr) return false;
    try {
      if (!set.original.read_memory(set.original.context, source, out, size))
        return false;
      ReadStamp stamp{reinterpret_cast<std::uintptr_t>(source), size, {}};
      std::memcpy(stamp.bytes.data(), out, size);
      set.stamps.push_back(stamp);
      return true;
    } catch (...) { return false; }
  }
  static bool CopyAddress(void *opaque, std::uintptr_t source, void *out,
                          std::size_t size) noexcept {
    return Copy(opaque, reinterpret_cast<const void *>(source), out, size);
  }
  bool StillCurrent() const noexcept {
    try {
      std::array<std::byte, 8> after{};
      for (const auto &stamp : stamps)
        if (!original.read_memory(original.context,
              reinterpret_cast<const void *>(stamp.address), after.data(), stamp.size) ||
            std::memcmp(after.data(), stamp.bytes.data(), stamp.size) != 0)
          return false;
      return true;
    } catch (...) { return false; }
  }
};

bool Resolve(const LoadedInputAccessV1 &a, std::uintptr_t store,
             std::uintptr_t fallback, std::uint32_t full_id,
             std::size_t id_offset, std::uintptr_t &out, bool &used_fallback) {
  used_fallback = true;
  out = fallback;
  if (store == 0) return true;
  std::uint32_t count = 0;
  if (!ReadOffsetV1(a, store, 0x2C, count)) return false;
  const auto index = full_id & 0xFFFFFFU;
  if (index >= count) return true;
  std::uintptr_t table = 0, candidate = 0;
  if (!ReadOffsetV1(a, store, 0x20, table) ||
      !ReadOffsetV1(a, table, static_cast<std::size_t>(index) * 16 + 8, candidate))
    return false;
  if (candidate == 0) return true;
  std::uint32_t actual_id = 0;
  if (!ReadOffsetV1(a, candidate, id_offset, actual_id)) return false;
  if (actual_id == full_id) { out = candidate; used_fallback = false; }
  return true;
}
} // namespace

std::int64_t SumContextNumericKey2C23340V1(
    std::int64_t first, std::int64_t second, std::int64_t third) noexcept {
  return SignedBitsV1(static_cast<std::uint64_t>(first) +
                      static_cast<std::uint64_t>(second) +
                      static_cast<std::uint64_t>(third));
}

ContextNumericKey2C23340V1 ReadContextNumericKey2C23340V1(
    const LoadedInputAccessV1 &input, std::uintptr_t base,
    std::uintptr_t context, std::uint32_t key) {
  ContextNumericKey2C23340V1 r;
  r.raw_context = context;
  r.incoming_key_raw_u32 = key;
  r.property_key_u16 = static_cast<std::uint16_t>(key);
  const auto fail = [&](const char *name, std::uint32_t pc) {
    r.unavailable_input = name; r.source_pc = pc; return r;
  };
  if (!input.exact_12004_bound || input.read_memory == nullptr || base == 0 || context == 0)
    return fail("exact_bound_context_access", 0x2C23340);
  ReadSet reads{input, {}};
  const LoadedInputAccessV1 a{&reads, ReadSet::Copy, true};
  if (!ReadOffsetV1(a, base, 0x5D1DAF8, r.raw_store) ||
      !ReadOffsetV1(a, base, 0x5D1DAE0, r.raw_default_object))
    return fail("raw_object_store_or_default", 0x2C2335C);
  r.selected_raw_object = r.raw_default_object;
  if (r.raw_store != 0) {
    std::uint32_t requested = 0;
    if (!ReadOffsetV1(a, context, 0x738, requested))
      return fail("context_738_full_id", 0x2C2337C);
    r.context_738_full_id = requested;
    bool fallback = false;
    if (!Resolve(a, r.raw_store, r.raw_default_object, requested, 0x10,
                 r.selected_raw_object, fallback))
      return fail("raw_object_full_generation_resolution", 0x2C23384);
  }
  TitleSelectedFullIdAccess12004 child{&reads, ReadSet::CopyAddress, base, true};
  const RawTitleReturnAccessV1 return_access{&reads, ReadSet::Copy, base, true,
                                            &child, ReadTitleSelectedFullIdAdapter12004};
  const auto candidate = ReadActual2C42930ReturnV1(return_access, r.selected_raw_object);
  if (!candidate.observed) return fail("actual_2c42930_raw_return", 0x2C233AD);
  r.candidate_character = candidate.returned_pointer;
  std::uint32_t magic = 0;
  if (!ReadOffsetV1(a, context, 0x848, r.context_848_payload) ||
      !ReadOffsetV1(a, r.context_848_payload, 0x3E0, magic))
    return fail("context_848_payload_magic", 0x2C233BC);
  r.context_848_magic = magic;
  if (!AddOffsetV1(context, 0x30, r.collection_pointers[0]))
    return fail("context_inline_collection", 0x2C233B5);
  if (magic == 0x436F4461U &&
      !AddOffsetV1(r.context_848_payload, 0x98, r.collection_pointers[1]))
    return fail("context_848_collection", 0x2C233CD);
  if (!ReadOffsetV1(a, r.candidate_character, 0x1C, magic))
    return fail("candidate_character_magic", 0x2C233D8);
  std::uint32_t physical_id = 0xFFFFFFFFU;
  if (magic == 0x43686172U) {
    if (!ReadOffsetV1(a, r.candidate_character, 0x18, physical_id))
      return fail("candidate_character_full_id", 0x2C233E1);
    r.candidate_character_accepted = physical_id != 0xFFFFFFFFU;
  }
  if (r.candidate_character_accepted) {
    r.selected_character = r.candidate_character;
  } else {
    std::uint32_t requested = 0;
    if (!ReadOffsetV1(a, r.selected_raw_object, 0x128, requested))
      return fail("raw_object_128", 0x2C233EB);
    if (requested == 0xFFFFFFFFU) {
      std::uintptr_t kind_object = 0;
      std::uint32_t kind = 0;
      if (!ReadOffsetV1(a, r.selected_raw_object, 0x48, kind_object) ||
          !ReadOffsetV1(a, kind_object, 0x64, kind))
        return fail("raw_object_48_kind64", 0x2C233F7);
      if (kind == 1) {
        std::uintptr_t secondary = r.raw_default_object;
        if (r.raw_store != 0) {
          std::uint32_t secondary_id = 0;
          bool fallback = false;
          if (!ReadOffsetV1(a, r.selected_raw_object, 0xE8, secondary_id) ||
              !Resolve(a, r.raw_store, r.raw_default_object, secondary_id, 0x10,
                       secondary, fallback))
            return fail("raw_object_e8_resolution", 0x2C23406);
        }
        if (!ReadOffsetV1(a, secondary, 0x128, requested))
          return fail("secondary_raw_object_128", 0x2C23436);
      }
    }
    std::uintptr_t character_store = 0, character_default = 0;
    if (!ReadOffsetV1(a, base, 0x5C67568, character_store))
      return fail("character_store", 0x2C23443);
    // Native loads the fallback slot only after a failed resolution. Resolve
    // first with a marker; then copy the real fallback on that actual route.
    if (!Resolve(a, character_store, 0, requested, 0x18,
                 r.selected_character, r.used_final_character_default))
      return fail("character_full_generation_resolution", 0x2C2344A);
    if (r.used_final_character_default) {
      if (!ReadOffsetV1(a, base, 0x5C67570, character_default))
        return fail("character_default", 0x2C23475);
      r.selected_character = character_default;
    }
  }
  if (!ReadOffsetV1(a, r.selected_character, 0x18, physical_id))
    return fail("selected_character_physical_full_id", 0x2C2347C);
  r.selected_character_physical_full_id = physical_id;
  const auto modifier_bindings = BindConceptionModifierContext12004(
      base, "1.20.0.4", kSha, ReadSet::CopyAddress, &reads);
  const auto modifier = ResolveRawCharacterModifierContext12004(
      modifier_bindings, r.selected_character, physical_id,
      r.used_final_character_default);
  if (!modifier.ready) return fail("character_modifier_context", 0x2C2347C);
  r.collection_pointers[2] = modifier.context_address;
  std::array<std::int64_t, 3> contributions{};
  constexpr std::array<std::uint32_t, 3> pcs{0x2C234B1, 0x2C234DE, 0x2C2350B};
  for (std::size_t i = 0; i < contributions.size(); ++i) {
    if (r.collection_pointers[i] == 0) continue;
    r.collection_values[i] = ReadScaledCollectionKey12004(
        a, r.collection_pointers[i], r.property_key_u16, 100000, 0, 0);
    if (!r.collection_values[i]->ready || !r.collection_values[i]->scaled_value_raw_q64)
      return fail(i == 0 ? "context_collection_key" :
                  i == 1 ? "payload_collection_key" : "character_collection_key", pcs[i]);
    contributions[i] = *r.collection_values[i]->scaled_value_raw_q64;
  }
  std::string modifier_reason;
  if (!CheckRawCharacterModifierContextStillCurrent12004(
          modifier_bindings, modifier, physical_id,
          r.used_final_character_default, modifier_reason))
    return fail("character_modifier_context_changed", 0x2C23516);
  if (!reads.StillCurrent()) return fail("source_changed_during_read", 0x2C23516);
  r.signed_qword_raw = SumContextNumericKey2C23340V1(
      contributions[0], contributions[1], contributions[2]);
  r.source_pc = 0x2C23516;
  r.observed = true;
  return r;
}
} // namespace xar::ck3_12004::construction_owner_mode3
