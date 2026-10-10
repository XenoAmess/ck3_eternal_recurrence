#include "xar_bridge/construction_context_key_2c23340_12004.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
#include <map>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
constexpr std::uintptr_t kBase = 0x100000000ULL;
constexpr std::uintptr_t kContext = 0x20000000;
constexpr std::uintptr_t kRaw = 0x21000000;
constexpr std::uintptr_t kCharacter = 0x22000000;
constexpr std::uintptr_t kFallback = 0x23000000;
constexpr std::uintptr_t kCharacterStore = 0x24000000;
constexpr std::uintptr_t kCharacterTable = 0x25000000;
constexpr std::uintptr_t kPayload = 0x26000000;
constexpr std::uintptr_t kExtension = 0x27000000;
constexpr std::uintptr_t kModel = 0x28000000;
constexpr std::uint32_t kCharacterId = 0x02000001;
constexpr std::uint16_t kKey = 0x1E9;

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

struct Scene {
  std::map<std::uintptr_t, std::byte> bytes;
  std::vector<std::uintptr_t> reads;
  std::uintptr_t denied_address = 0;
  std::uintptr_t mutate_trigger = 0;
  bool mutated = false;

  template<class T> void Put(std::uintptr_t address, T value) {
    const auto *source = reinterpret_cast<const std::byte *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = source[i];
  }
  static bool Copy(void *opaque, const void *source, void *out,
                   std::size_t size) noexcept {
    auto &scene = *static_cast<Scene *>(opaque);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    try {
      scene.reads.push_back(address);
      if (address == scene.denied_address) return false;
      auto *destination = static_cast<std::byte *>(out);
      for (std::size_t i = 0; i < size; ++i) {
        const auto found = scene.bytes.find(address + i);
        if (found == scene.bytes.end()) return false;
        destination[i] = found->second;
      }
      if (!scene.mutated && address == scene.mutate_trigger) {
        scene.mutated = true;
        scene.Put<std::uint32_t>(kPayload + 0x3E0, 0x11223344);
      }
      return true;
    } catch (...) { return false; }
  }
  bool ReadAddress(std::uintptr_t address) const {
    return std::find(reads.begin(), reads.end(), address) != reads.end();
  }
  void Collection(std::uintptr_t collection, std::uintptr_t keys,
                  std::uintptr_t values, std::int64_t value,
                  std::uint16_t key = kKey) {
    Put<std::uintptr_t>(collection + 0x68, keys);
    Put<std::int32_t>(collection + 0x74, 1);
    Put<std::uintptr_t>(collection + 0xD0, values);
    Put<std::uint16_t>(keys, key);
    Put<std::int64_t>(values, value);
  }
  Scene() {
    // Raw context and object have no fabricated Province/full-ID admission.
    Put<std::uintptr_t>(kBase + 0x5D1DAF8, 0);
    Put<std::uintptr_t>(kBase + 0x5D1DAE0, kRaw);
    Put<std::uint8_t>(kRaw + 0x130, 1);
    Put<std::uint32_t>(kRaw + 0x128, kCharacterId);
    Put<std::uintptr_t>(kBase + 0x5C67568, kCharacterStore);
    Put<std::uintptr_t>(kBase + 0x5C67570, kFallback);
    Put<std::uint32_t>(kCharacterStore + 0x2C, 2);
    Put<std::uintptr_t>(kCharacterStore + 0x20, kCharacterTable);
    Put<std::uintptr_t>(kCharacterTable + 16 + 8, kCharacter);
    Put<std::uint32_t>(kCharacter + 0x18, kCharacterId);
    Put<std::uint32_t>(kCharacter + 0x1C, 0x43686172);
    Put<std::uintptr_t>(kCharacter + 0x1C0, 0);
    Put<std::uintptr_t>(kCharacter + 0x1B0, kExtension);
    Put<std::uintptr_t>(kExtension + 0x258, kModel);
    Put<std::uintptr_t>(kModel + 8, kCharacter);
    Put<std::uintptr_t>(kContext + 0x848, kPayload);
    Put<std::uint32_t>(kPayload + 0x3E0, 0x436F4461);
    Collection(kContext + 0x30, 0x29000000, 0x29000100, 100000);
    Collection(kPayload + 0x98, 0x2A000000, 0x2A000100, -30000);
    Collection(kModel + 0x10, 0x2B000000, 0x2B000100, 7000);
  }
  ContextNumericKey2C23340V1 Read(std::uint32_t key = kKey) {
    return ReadContextNumericKey2C23340V1({this, Copy, true}, kBase, kContext, key);
  }
  void FallbackCharacter() {
    Put<std::uintptr_t>(kBase + 0x5C67568, 0);
    Put<std::uint32_t>(kFallback + 0x18, 0xFFFFFFFFU);
    Put<std::uint32_t>(kFallback + 0x1C, 0x43686172);
    Put<std::uintptr_t>(kFallback + 0x1C0, 0);
    Put<std::uintptr_t>(kFallback + 0x1B0, kExtension);
    Put<std::uintptr_t>(kModel + 8, kFallback);
  }
};
} // namespace

// No main and no independent qualification.03/10 owns the single fresh
// connected construction compound that calls this export.
int RunConstructionContextKey2C23340Scenario12004() {
  int scenes = 0;
  {
    Scene s;
    const auto before = s.bytes;
    const auto r = s.Read(0xFFFF01E9U);
    Require(r.observed && r.signed_qword_raw == 77000, "three ordered raw contributions");
    Require(r.property_key_u16 == kKey && r.candidate_character_accepted,
            "low16 key and accepted actual returned Character");
    Require(!r.context_738_full_id && !s.ReadAddress(kContext + 0x10) &&
            !s.ReadAddress(kContext + 0x738), "null raw store bypasses identity fields");
    Require(s.bytes == before, "reader changed source bytes");
    ++scenes;
  }
  {
    Scene s;
    s.Put<std::uint32_t>(kPayload + 0x3E0, 0x11223344);
    s.denied_address = 0x2A000100;
    const auto r = s.Read();
    Require(r.observed && r.signed_qword_raw == 107000 &&
            r.collection_pointers[1] == 0 && !r.collection_values[1],
            "non-CoDa payload skips second collection");
    Require(!s.ReadAddress(0x2A000100), "unselected payload value was consumed");
    ++scenes;
  }
  {
    Scene s;
    s.denied_address = 0x29000100;
    const auto r = s.Read();
    Require(!r.observed && !r.signed_qword_raw &&
            r.unavailable_input == "context_collection_key", "failed value stayed unknown");
    Require(!s.ReadAddress(0x2A000100) && !s.ReadAddress(0x2B000100),
            "first unavailable value stops subsequent contributions");
    ++scenes;
  }
  {
    Scene s;
    s.Put<std::int32_t>(kContext + 0x30 + 0x74, 0);
    s.denied_address = 0x29000100;
    const auto r = s.Read();
    Require(r.observed && r.signed_qword_raw == -23000 &&
            !s.ReadAddress(0x29000100), "observed empty first collection contributes zero");
    ++scenes;
  }
  {
    Scene s;
    s.Put<std::uint16_t>(0x29000000, kKey + 1);
    const auto r = s.Read();
    Require(r.observed && r.signed_qword_raw == -23000 &&
            !s.ReadAddress(0x29000100), "observed absent key contributes zero");
    ++scenes;
  }
  {
    Scene s;
    s.Put<std::uintptr_t>(kBase + 0x5D1DAF8, 0x2C000000);
    s.Put<std::uint32_t>(kContext + 0x738, 0x03000001);
    s.Put<std::uint32_t>(0x2C000000 + 0x2C, 2);
    s.Put<std::uintptr_t>(0x2C000000 + 0x20, 0x2D000000);
    s.Put<std::uintptr_t>(0x2D000000 + 16 + 8, 0x2E000000);
    s.Put<std::uint32_t>(0x2E000000 + 0x10, 0x04000001);
    const auto r = s.Read();
    Require(r.observed && r.selected_raw_object == kRaw &&
            r.context_738_full_id == 0x03000001U,
            "raw same-low24 generation mismatch selects actual default");
    ++scenes;
  }
  {
    Scene s;
    s.FallbackCharacter();
    const auto r = s.Read();
    Require(r.observed && r.signed_qword_raw == 77000 &&
            r.used_final_character_default && r.selected_character == kFallback &&
            r.selected_character_physical_full_id == 0xFFFFFFFFU,
            "qualified FFFFFFFF Character retains actual owned modifier context");
    ++scenes;
  }
  {
    Scene s;
    s.FallbackCharacter();
    s.Put<std::uintptr_t>(kFallback + 0x1B0, 0);
    s.Put<std::int32_t>(kBase + 0x5D67B80, 0);
    const auto r = s.Read();
    Require(!r.observed && !r.signed_qword_raw &&
            r.unavailable_input == "character_modifier_context",
            "uninitialized default modifier context remains unavailable");
    Require(!s.ReadAddress(0x29000100), "unavailable receiver prefix precedes collection reads");
    ++scenes;
  }
  {
    Scene s;
    s.mutate_trigger = 0x2B000100;
    const auto r = s.Read();
    Require(s.mutated && !r.observed && !r.signed_qword_raw &&
            r.unavailable_input == "source_changed_during_read",
            "same-query source bookend rejects changed selected payload");
    ++scenes;
  }
  {
    Scene s;
    s.denied_address = kPayload + 0x3E0;
    const auto r = s.Read(0xFFFF);
    Require(!r.observed && !r.signed_qword_raw,
            "sentinel child key does not skip the actual receiver prefix");
    ++scenes;
  }
  {
    Scene s;
    s.denied_address = 0x29000100;
    const auto r = s.Read(0xFFFF);
    Require(r.observed && r.signed_qword_raw == 0 &&
            !s.ReadAddress(0x29000100), "sentinel contributes exact child zero after prefix");
    ++scenes;
  }
  {
    Scene s;
    s.Put<std::int64_t>(0x29000100, -1);
    s.Put<std::int64_t>(0x2A000100, 0);
    s.Put<std::int64_t>(0x2B000100, 0);
    const auto r = s.Read();
    Require(r.observed && r.signed_qword_raw == -1,
            "raw helper does not apply the caller floor or clamp");
    ++scenes;
  }
  Require(SumContextNumericKey2C23340V1(
              (std::numeric_limits<std::int64_t>::max)(), 1, 0) ==
              (std::numeric_limits<std::int64_t>::min)(), "positive sum wraps signed64");
  Require(SumContextNumericKey2C23340V1(
              (std::numeric_limits<std::int64_t>::min)(), -1, 0) ==
              (std::numeric_limits<std::int64_t>::max)(), "negative sum wraps signed64");
  return scenes;
}
} // namespace xar::ck3_12004::construction_owner_mode3
