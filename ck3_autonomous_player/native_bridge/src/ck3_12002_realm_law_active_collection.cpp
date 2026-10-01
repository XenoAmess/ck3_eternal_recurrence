#include "xar_bridge/ck3_12002_realm_law_active_collection.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_12002::private_law {
namespace {

constexpr std::uintptr_t kCharacterLawContextOffset = kCharacterLawContextOffset12002;
constexpr std::uintptr_t kLawCollectionOffset = kLawCollectionOffset12002;
constexpr std::uintptr_t kLawKeyOffset = kLawNativeKeyOffset12002;
constexpr std::size_t kMsvcStringInlineCapacity = 15;

template <typename T>
bool Read(const RealmLawActiveCollectionAccess &access,
          std::uintptr_t address, T &output) noexcept {
  return access.read_memory(access.context, address, &output, sizeof(output));
}

bool CopyKey(const RealmLawActiveCollectionAccess &access,
             std::uintptr_t key_storage_address,
             RealmLawActiveKey &output) noexcept {
  std::array<std::byte, 32> storage{};
  if (!access.read_memory(access.context, key_storage_address,
                          storage.data(), storage.size())) {
    return false;
  }
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  std::memcpy(&size, storage.data() + 0x10, sizeof(size));
  std::memcpy(&capacity, storage.data() + 0x18, sizeof(capacity));
  if (size == 0 || size >= kRealmLawActiveCollectionKeyCapacity ||
      capacity < size) {
    return false;
  }
  if (capacity <= kMsvcStringInlineCapacity) {
    std::memcpy(output.bytes.data(), storage.data(),
                static_cast<std::size_t>(size));
  } else {
    std::uintptr_t data_address = 0;
    std::memcpy(&data_address, storage.data(), sizeof(data_address));
    if (data_address == 0 ||
        !access.read_memory(access.context, data_address, output.bytes.data(),
                            static_cast<std::size_t>(size))) {
      return false;
    }
  }
  output.size = static_cast<std::uint16_t>(size);
  return true;
}

} // namespace

bool ReadRealmLawNativeKey12002(
    const RealmLawActiveCollectionAccess &access,
    std::uintptr_t key_storage_address,
    RealmLawActiveKey &output) noexcept {
  if (access.admitted_executable_sha256 !=
          kRealmLawActiveCollectionExeSha25612002 ||
      access.read_memory == nullptr || key_storage_address == 0) {
    return false;
  }
  return CopyKey(access, key_storage_address, output);
}

bool ReadRealmLawActiveCollection12002(
    const RealmLawActiveCollectionAccess &access,
    RealmLawActiveCollection &output) noexcept {
  output = {};
  if (access.admitted_executable_sha256 !=
      kRealmLawActiveCollectionExeSha25612002) {
    output.failure = RealmLawActiveCollectionFailure::exact_build_mismatch;
    return false;
  }
  if (access.read_memory == nullptr) {
    output.failure = RealmLawActiveCollectionFailure::reader_unavailable;
    return false;
  }
  if (access.played_character_address == 0) {
    output.failure = RealmLawActiveCollectionFailure::actor_unavailable;
    return false;
  }
  std::uintptr_t law_context = 0;
  if (!Read(access, access.played_character_address +
                        kCharacterLawContextOffset,
            law_context) ||
      law_context == 0) {
    output.failure = RealmLawActiveCollectionFailure::law_context_unavailable;
    return false;
  }
  const auto collection = law_context + kLawCollectionOffset;
  std::uintptr_t law_slots = 0;
  std::int32_t count = -1;
  if (!Read(access, collection, law_slots) ||
      !Read(access, collection + 0x0C, count)) {
    output.failure = RealmLawActiveCollectionFailure::collection_unavailable;
    return false;
  }
  if (count < 0 ||
      count > static_cast<std::int32_t>(kRealmLawActiveCollectionMaximumLaws) ||
      (count != 0 && law_slots == 0)) {
    output.failure = RealmLawActiveCollectionFailure::count_invalid;
    return false;
  }
  for (std::int32_t i = 0; i < count; ++i) {
    std::uintptr_t law = 0;
    if (!Read(access, law_slots + static_cast<std::uintptr_t>(i) * 8,
              law) ||
        law == 0) {
      output.failure = RealmLawActiveCollectionFailure::law_unavailable;
      return false;
    }
    auto &key = output.keys[static_cast<std::size_t>(i)];
    if (!ReadRealmLawNativeKey12002(access, law + kLawKeyOffset, key)) {
      output.failure = RealmLawActiveCollectionFailure::key_invalid;
      return false;
    }
    for (std::int32_t j = 0; j < i; ++j) {
      if (output.keys[static_cast<std::size_t>(j)] == key) {
        output.failure = RealmLawActiveCollectionFailure::duplicate_key;
        return false;
      }
    }
  }
  output.count = static_cast<std::uint32_t>(count);
  output.failure = RealmLawActiveCollectionFailure::none;
  return true;
}

} // namespace xar::ck3_12002::private_law
