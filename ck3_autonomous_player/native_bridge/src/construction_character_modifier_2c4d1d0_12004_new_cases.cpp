#include "xar_bridge/construction_character_modifier_2c4d1d0_12004.hpp"
#include "xar_bridge/construction_character_modifier_2c4d1d0_12004_new_cases.hpp"

#include <cstring>
#include <iterator>
#include <map>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct CopiedMemory {
  static constexpr std::uintptr_t image = 0x10000000;
  static constexpr std::uintptr_t character = 0x21000000;
  static constexpr std::uintptr_t extension = 0x22000000;
  static constexpr std::uintptr_t model = 0x23000000;
  static constexpr std::uintptr_t keys = 0x24000000;
  static constexpr std::uintptr_t values = 0x25000000;
  static constexpr std::uintptr_t default_collection = image + 0x5D67B90;
  enum class Mutation { none, model_owner, physical_id, fallback_slot, default_values_count };

  std::map<std::uintptr_t, std::vector<unsigned char>> regions;
  Mutation mutation = Mutation::none;
  bool mutated = false;
  bool throw_on_read = false;
  std::uintptr_t failed_address = 0;
  std::size_t reads = 0;
  bool tag_read = false;

  CopiedMemory() {
    regions.emplace(character, std::vector<unsigned char>(0x1B8));
    regions.emplace(extension, std::vector<unsigned char>(0x260));
    regions.emplace(model, std::vector<unsigned char>(0x100));
    regions.emplace(keys, std::vector<unsigned char>(2));
    regions.emplace(values, std::vector<unsigned char>(8));
    regions.emplace(image + 0x5C67570, std::vector<unsigned char>(8));
    regions.emplace(image + 0x5D67B80, std::vector<unsigned char>(4));
    regions.emplace(default_collection, std::vector<unsigned char>(0xE0));
    Put(character + 0x18, std::uint32_t{5});
    Put(character + 0x1C, std::uint32_t{0});
    Put(character + 0x1B0, extension);
    Put(extension + 0x258, model);
    Put(model + 8, character);
    Put(image + 0x5C67570, character);
    Put(keys, std::uint16_t{0xA2});
    Put(values, std::int64_t{73});
    SeedCollection(model + 0x10, 1);
    SeedCollection(default_collection, 1);
  }

  template<class T> void Put(std::uintptr_t address, const T &value) {
    auto after = regions.upper_bound(address);
    Require(after != regions.begin(), "34c fixture write region");
    auto region = std::prev(after);
    const auto offset = address - region->first;
    Require(offset <= region->second.size() &&
        sizeof(T) <= region->second.size() - offset, "34c fixture write span");
    std::memcpy(region->second.data() + offset, &value, sizeof(T));
  }

  void SeedCollection(std::uintptr_t collection, std::int32_t count) {
    Put(collection + 0x68, keys);
    Put(collection + 0x70, std::int32_t{1});
    Put(collection + 0x74, count);
    Put(collection + 0xD0, values);
    Put(collection + 0xD8, std::int32_t{1});
    Put(collection + 0xDC, count);
  }

  void UseInitializedDefault() {
    Put(character + 0x1B0, std::uintptr_t{0});
    Put(image + 0x5D67B80, std::int32_t{1});
  }

  static bool Read(void *opaque, const void *pointer, void *output,
                   std::size_t size) {
    auto &memory = *static_cast<CopiedMemory *>(opaque);
    ++memory.reads;
    if (memory.throw_on_read) throw std::runtime_error("34c copy callback rejected");
    const auto address = reinterpret_cast<std::uintptr_t>(pointer);
    memory.tag_read = memory.tag_read || address == character + 0x1C;
    if (address == memory.failed_address) return false;
    auto after = memory.regions.upper_bound(address);
    if (after == memory.regions.begin()) return false;
    auto region = std::prev(after);
    const auto offset = address - region->first;
    if (offset > region->second.size() || size > region->second.size() - offset)
      return false;
    std::memcpy(output, region->second.data() + offset, size);
    if (address == values && size == sizeof(std::int64_t) && !memory.mutated) {
      memory.mutated = true;
      switch (memory.mutation) {
      case Mutation::model_owner:
        memory.Put(model + 8, std::uintptr_t{character + 0x1000}); break;
      case Mutation::physical_id:
        memory.Put(character + 0x18, std::uint32_t{6}); break;
      case Mutation::fallback_slot:
        memory.Put(image + 0x5C67570, std::uintptr_t{character + 0x1000}); break;
      case Mutation::default_values_count:
        memory.Put(default_collection + 0xDC, std::int32_t{0}); break;
      case Mutation::none: break;
      }
    }
    return true;
  }

  RawReceiverAccessV1 Access() {
    return {this, &Read, image, true};
  }
};
} // namespace

int RunCharacterModifier2C4D1D012004NewCases() {
  // 1. Both actual getter selections reach the same qualified scalar leaf.
  {
    CopiedMemory owned;
    const auto out = ReadCharacterModifier2C4D1D012004(owned.Access(),
        CopiedMemory::character, 0xA2);
    Require(out.ready && out.value_raw_q64 == 73 &&
        out.context.source == ConceptionModifierContextSource12004::OwnedCharacter &&
        out.scalar.selection == ScaledCollectionKeySelection12004::mapped &&
        out.scalar.factor_raw_q64 == 100000, "34c owned getter/scalar join");
    CopiedMemory fallback_context;
    fallback_context.UseInitializedDefault();
    const auto default_out = ReadCharacterModifier2C4D1D012004(
        fallback_context.Access(), CopiedMemory::character, 0xA2);
    Require(default_out.ready && default_out.value_raw_q64 == 73 &&
        default_out.context.source == ConceptionModifierContextSource12004::InitializedDefault,
        "34c initialized default getter/scalar join");
  }
  // 2. Full physical DWORDs are bookends, not signed-ID or Char-tag gates.
  {
    CopiedMemory high_generation;
    high_generation.Put(CopiedMemory::character + 0x18, std::uint32_t{0x80000005u});
    const auto high = ReadCharacterModifier2C4D1D012004(high_generation.Access(),
        CopiedMemory::character, 0xA2);
    Require(high.ready && high.value_raw_q64 == 73 &&
        high.physical_character_id_raw_u32 == 0x80000005u && !high_generation.tag_read,
        "34c preserves negative high generation without tag gate");
    CopiedMemory all_ones;
    all_ones.Put(CopiedMemory::character + 0x18, std::uint32_t{0xFFFFFFFFu});
    const auto qualified = ReadCharacterModifier2C4D1D012004(all_ones.Access(),
        CopiedMemory::character, 0xA2);
    Require(qualified.ready && qualified.value_raw_q64 == 73 &&
        qualified.source_qualified_fallback && !all_ones.tag_read,
        "34c actual fallback all-ones receiver remains numerical");
    all_ones.Put(CopiedMemory::image + 0x5C67570, std::uintptr_t{0});
    const auto unqualified = ReadCharacterModifier2C4D1D012004(all_ones.Access(),
        CopiedMemory::character, 0xA2);
    Require(!unqualified.ready && !unqualified.value_raw_q64 &&
        unqualified.failure == CharacterModifierFailure2C4D1D012004::fallback_receiver_unqualified,
        "34c unobserved fallback route remains unknown");
  }
  // 3. Observed absence and numerical zero are accepted independently.
  {
    CopiedMemory absent;
    const auto missing_key = ReadCharacterModifier2C4D1D012004(absent.Access(),
        CopiedMemory::character, 0xA3);
    Require(missing_key.ready && missing_key.value_raw_q64 == 0 &&
        missing_key.scalar.selection == ScaledCollectionKeySelection12004::key_absent,
        "34c observed absent key yields known zero");
    CopiedMemory zero;
    zero.Put(CopiedMemory::values, std::int64_t{0});
    const auto selected_zero = ReadCharacterModifier2C4D1D012004(zero.Access(),
        CopiedMemory::character, 0xA2);
    Require(selected_zero.ready && selected_zero.value_raw_q64 == 0 &&
        selected_zero.scalar.selection == ScaledCollectionKeySelection12004::mapped,
        "34c selected numerical zero remains ready");
  }
  // 4. Negative Q64 values retain the actual scale result.
  {
    CopiedMemory negative;
    negative.Put(CopiedMemory::values, std::int64_t{-17});
    const auto out = ReadCharacterModifier2C4D1D012004(negative.Access(),
        CopiedMemory::character, 0xA2, 0, 200000);
    Require(out.ready && out.value_raw_q64 == -34 &&
        out.scalar.selected_value_raw_q64 == -17,
        "34c negative selected Q64 is not unavailable");
  }
  // 5. Access/context failure stays unknown, including factor0's getter.
  {
    CopiedMemory memory;
    auto bad_build = memory.Access();
    bad_build.exact_12004_bound = false;
    Require(!ReadCharacterModifier2C4D1D012004(bad_build,
        CopiedMemory::character, 0xA2).ready && memory.reads == 0,
        "34c exact token failure makes no copies");
    auto no_read = memory.Access();
    no_read.read_memory = nullptr;
    Require(!ReadCharacterModifier2C4D1D012004(no_read,
        CopiedMemory::character, 0xA2).ready,
        "34c callback absence remains unknown");
    memory.Put(CopiedMemory::character + 0x1B0, std::uintptr_t{0});
    const auto lazy_default = ReadCharacterModifier2C4D1D012004(memory.Access(),
        CopiedMemory::character, 0xA2, 0, 0);
    Require(!lazy_default.ready && !lazy_default.value_raw_q64 &&
        lazy_default.failure == CharacterModifierFailure2C4D1D012004::modifier_context,
        "34c factor0 does not bypass actual getter/default admission");
  }
  // 6. The sideeffect-bearing nonNULL detail branch is not represented.
  {
    CopiedMemory memory;
    const auto out = ReadCharacterModifier2C4D1D012004(memory.Access(),
        CopiedMemory::character, 0xA2, 1, 0);
    Require(!out.ready && !out.value_raw_q64 && memory.reads == 0 &&
        out.failure == CharacterModifierFailure2C4D1D012004::detail_branch_not_supplied,
        "34c nonNULL detail is explicit unknown before copies");
  }
  // 7. Changes after selected-value copy invalidate the returned value.
  {
    for (const auto mutation : {CopiedMemory::Mutation::model_owner,
                               CopiedMemory::Mutation::physical_id}) {
      CopiedMemory memory;
      memory.mutation = mutation;
      const auto changed = ReadCharacterModifier2C4D1D012004(memory.Access(),
          CopiedMemory::character, 0xA2);
      Require(!changed.ready && !changed.value_raw_q64 && changed.scalar.ready &&
          changed.failure == CharacterModifierFailure2C4D1D012004::modifier_context_changed,
          "34c receiver/context changes reject copied arithmetic value");
    }
    CopiedMemory default_stamp;
    default_stamp.UseInitializedDefault();
    default_stamp.mutation = CopiedMemory::Mutation::default_values_count;
    const auto stamp_changed = ReadCharacterModifier2C4D1D012004(default_stamp.Access(),
        CopiedMemory::character, 0xA2);
    Require(!stamp_changed.ready && !stamp_changed.value_raw_q64 &&
        stamp_changed.failure == CharacterModifierFailure2C4D1D012004::modifier_context_changed,
        "34c default lifetime stamp change invalidates value");
    CopiedMemory fallback_changed;
    fallback_changed.Put(CopiedMemory::character + 0x18, std::uint32_t{0xFFFFFFFFu});
    fallback_changed.mutation = CopiedMemory::Mutation::fallback_slot;
    const auto slot_changed = ReadCharacterModifier2C4D1D012004(fallback_changed.Access(),
        CopiedMemory::character, 0xA2);
    Require(!slot_changed.ready && !slot_changed.value_raw_q64 &&
        slot_changed.failure == CharacterModifierFailure2C4D1D012004::fallback_receiver_changed,
        "34c actual fallback slot gets an independent bookend");
  }
  // 8. Failed child copies cannot be converted into numerical zero.
  {
    CopiedMemory missing_value;
    missing_value.failed_address = CopiedMemory::values;
    const auto out = ReadCharacterModifier2C4D1D012004(missing_value.Access(),
        CopiedMemory::character, 0xA2);
    Require(!out.ready && !out.value_raw_q64 &&
        out.failure == CharacterModifierFailure2C4D1D012004::scaled_key &&
        out.scalar.failure == ScaledCollectionKeyFailure12004::selected_value_read,
        "34c unavailable scalar remains unknown");
    CopiedMemory throwing_copy;
    throwing_copy.throw_on_read = true;
    Require(!ReadCharacterModifier2C4D1D012004(throwing_copy.Access(),
        CopiedMemory::character, 0xA2).ready,
        "34c raw callback exception is a failed copy");
  }
  return 8;
}
} // namespace xar::ck3_12004::construction_owner_mode3
