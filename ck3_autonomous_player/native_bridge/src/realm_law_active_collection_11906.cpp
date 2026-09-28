#include "xar_bridge/realm_law_active_collection_11906.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_11906::private_law {
namespace {

constexpr std::uintptr_t kCharacterLawContextOffset = 0x1B8;
constexpr std::uintptr_t kLawCollectionOffset = 0x200;
constexpr std::uintptr_t kLawKeyOffset = 0x18;
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

bool ReadRealmLawNativeKey11906(
    const RealmLawActiveCollectionAccess &access,
    std::uintptr_t key_storage_address,
    RealmLawActiveKey &output) noexcept {
  if (access.admitted_executable_sha256 !=
          kRealmLawActiveCollectionExeSha256 ||
      access.read_memory == nullptr || key_storage_address == 0) {
    return false;
  }
  return CopyKey(access, key_storage_address, output);
}

bool ReadRealmLawActiveCollection11906(
    const RealmLawActiveCollectionAccess &access,
    RealmLawActiveCollection &output) noexcept {
  output = {};
  if (access.admitted_executable_sha256 !=
      kRealmLawActiveCollectionExeSha256) {
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
    if (!ReadRealmLawNativeKey11906(access, law + kLawKeyOffset, key)) {
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

std::string_view RealmLawActiveCollectionFailureName(
    RealmLawActiveCollectionFailure failure) noexcept {
  switch (failure) {
  case RealmLawActiveCollectionFailure::none: return "none";
  case RealmLawActiveCollectionFailure::exact_build_mismatch:
    return "exact_build_mismatch";
  case RealmLawActiveCollectionFailure::reader_unavailable:
    return "reader_unavailable";
  case RealmLawActiveCollectionFailure::actor_unavailable:
    return "actor_unavailable";
  case RealmLawActiveCollectionFailure::law_context_unavailable:
    return "law_context_unavailable";
  case RealmLawActiveCollectionFailure::collection_unavailable:
    return "collection_unavailable";
  case RealmLawActiveCollectionFailure::count_invalid: return "count_invalid";
  case RealmLawActiveCollectionFailure::law_unavailable:
    return "law_unavailable";
  case RealmLawActiveCollectionFailure::key_invalid: return "key_invalid";
  case RealmLawActiveCollectionFailure::duplicate_key:
    return "duplicate_key";
  }
  return "unknown";
}

} // namespace xar::ck3_11906::private_law
