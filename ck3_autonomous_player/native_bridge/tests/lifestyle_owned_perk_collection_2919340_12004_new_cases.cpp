#include "xar_bridge/lifestyle_owned_perk_collection_2919340_12004.hpp"

#include <cstring>
#include <limits>
#include <map>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12004::lifestyle;
struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::vector<std::uintptr_t> reads;
  std::uintptr_t denied = 0;
  template <typename T> void Put(std::uintptr_t at, T value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[at+i] = data[i];
  }
  static bool Read(void *context, std::uintptr_t at, void *out, std::size_t size) {
    auto &memory = *static_cast<Memory *>(context);
    memory.reads.push_back(at);
    if (at == memory.denied) return false;
    auto *data = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = memory.bytes.find(at+i);
      if (found == memory.bytes.end()) return false;
      data[i] = found->second;
    }
    return true;
  }
};
constexpr std::uintptr_t kBase = 0x10000000;
constexpr std::uintptr_t kCharacter = 0x2000;
constexpr std::uintptr_t kTlsArray = 0x3000;
constexpr std::uintptr_t kTlsZero = 0x4000;
} // namespace

// Called once by16's sole new selected-perk compound; there is no main or run.
bool RunLifestyleOwnedPerkCollection2919340NewCases12004(std::string &failure) {
  using namespace xar::ck3_12004::lifestyle;
  const auto require = [&](bool valid, const char *why) {
    if (!valid) failure = why;
    return valid;
  };
  Memory memory{};
  LifestylePerkReadonlyAccess12004 access{kBase, &memory, &Memory::Read};
  memory.Put(kCharacter+0x1B0, std::uintptr_t{0x5000});
  const auto first = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  if (!require(first.returned_collection_identity == std::uintptr_t{0x5220} &&
      first.branch == LifestyleOwnedPerkGetterBranch12004::character_extension &&
      memory.reads == std::vector<std::uintptr_t>{kCharacter+0x1B0},
      "nonnull extension must return220 and skip TLS/header reads")) return false;
  memory.Put(kCharacter+0x1B0, std::uintptr_t{0x6000});
  const auto repeated = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  if (!require(repeated.returned_collection_identity == std::uintptr_t{0x6220} &&
      memory.reads.size() == std::size_t{2},
      "every native demand must reread Character extension")) return false;
  memory.Put(kCharacter+0x1B0, std::numeric_limits<std::uintptr_t>::max()-std::uintptr_t{0x21F});
  const auto wrapped = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  if (!require(wrapped.returned_collection_identity == std::uintptr_t{0},
      "native return ADD bits must preserve zero wrap without dereference")) return false;

  memory.Put(kCharacter+0x1B0, std::uintptr_t{0});
  memory.reads.clear();
  const auto missing = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  if (!require(!missing.returned_collection_identity &&
      missing.extension_identity_raw == std::uintptr_t{0} &&
      missing.unavailable_reason == "owned_perk_same_thread_tls_array_unavailable" &&
      memory.reads == std::vector<std::uintptr_t>{kCharacter+0x1B0},
      "missing TLS must stay unknown and skip static header")) return false;
  access.current_thread_tls_array_identity = kTlsArray;
  memory.Put(kTlsArray, kTlsZero);
  memory.Put(kTlsZero+0x10, std::int32_t{-3});
  memory.Put(kBase+kLifestyleOwnedPerkStaticGuardRva12004, std::int32_t{-4});
  memory.reads.clear();
  const auto fast = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  if (!require(fast.returned_collection_identity == kBase+kLifestyleOwnedPerkStaticCollectionRva12004 &&
      fast.branch == LifestyleOwnedPerkGetterBranch12004::static_fast_return &&
      fast.tls_epoch_raw_i32 == std::int32_t{-3} && fast.static_guard_raw_i32 == std::int32_t{-4} &&
      memory.reads == std::vector<std::uintptr_t>{kCharacter+0x1B0,kTlsArray,kTlsZero+0x10,kBase+kLifestyleOwnedPerkStaticGuardRva12004},
      "null fast path must use signed guard comparison and literal load order")) return false;
  memory.Put(kBase+kLifestyleOwnedPerkStaticGuardRva12004, std::int32_t{-2});
  const auto slow = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  if (!require(!slow.returned_collection_identity &&
      slow.branch == LifestyleOwnedPerkGetterBranch12004::static_epoch_slow_path &&
      slow.static_guard_raw_i32 == std::int32_t{-2} &&
      slow.unavailable_reason == "owned_perk_static_epoch_slow_path_unmodeled",
      "epoch slow path must retain raw values without initializer or assumed collection")) return false;
  memory.denied = kTlsZero+0x10;
  const auto partial = ReadLifestyleOwnedPerkCollection291934012004(access, kCharacter);
  return require(!partial.returned_collection_identity && partial.tls_slot_zero_identity_raw == kTlsZero &&
      !partial.tls_epoch_raw_i32 && !partial.static_guard_raw_i32 &&
      partial.unavailable_reason == "owned_perk_tls_epoch_unavailable",
      "failed epoch read must preserve prefix and skip later guard");
}
