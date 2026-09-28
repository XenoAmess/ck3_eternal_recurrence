#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906::private_law {

inline constexpr std::string_view kRealmLawActiveCollectionExeSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::size_t kRealmLawActiveCollectionMaximumLaws = 64;
inline constexpr std::size_t kRealmLawActiveCollectionKeyCapacity = 96;

enum class RealmLawActiveCollectionFailure : std::uint8_t {
  none,
  exact_build_mismatch,
  reader_unavailable,
  actor_unavailable,
  law_context_unavailable,
  collection_unavailable,
  count_invalid,
  law_unavailable,
  key_invalid,
  duplicate_key,
};

struct RealmLawActiveKey {
  std::uint16_t size = 0;
  std::array<char, kRealmLawActiveCollectionKeyCapacity> bytes{};

  friend bool operator==(const RealmLawActiveKey &,
                         const RealmLawActiveKey &) = default;
};

struct RealmLawActiveCollection {
  RealmLawActiveCollectionFailure failure =
      RealmLawActiveCollectionFailure::reader_unavailable;
  std::uint32_t count = 0;
  std::array<RealmLawActiveKey, kRealmLawActiveCollectionMaximumLaws> keys{};
};

using ReadRealmLawActiveMemory = bool (*)(void *context, std::uintptr_t address,
                                         void *output,
                                         std::size_t size) noexcept;

struct RealmLawActiveCollectionAccess {
  std::string_view admitted_executable_sha256{};
  std::uintptr_t played_character_address = 0;
  void *context = nullptr;
  ReadRealmLawActiveMemory read_memory = nullptr;
};

// Private read-only first anchor for LAW3. The caller resolves and validates
// the current full-generation played character on the paused application-main
// thread. No native pointer or law-group identity is retained in the result.
bool ReadRealmLawActiveCollection11906(
    const RealmLawActiveCollectionAccess &access,
    RealmLawActiveCollection &output) noexcept;

// Both CLaw and CLawGroup carry their native MSVC key string at +0x18.
bool ReadRealmLawNativeKey11906(
    const RealmLawActiveCollectionAccess &access,
    std::uintptr_t key_storage_address,
    RealmLawActiveKey &output) noexcept;

std::string_view RealmLawActiveCollectionFailureName(
    RealmLawActiveCollectionFailure failure) noexcept;

} // namespace xar::ck3_11906::private_law
