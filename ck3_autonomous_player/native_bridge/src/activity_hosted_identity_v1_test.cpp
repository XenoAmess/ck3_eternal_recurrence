#include "xar_bridge/activity_hosted_identity_v1.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <map>
#include <string_view>

namespace {

using namespace xar::bridge;

constexpr std::uintptr_t kModule = 0x140000000;
constexpr std::uintptr_t kRoot = 0x200000000;
constexpr std::uintptr_t kWorld = 0x300000000;
constexpr std::uintptr_t kManager = kWorld + 0x1DEC0;
constexpr std::uintptr_t kChunks = 0x400000000;
constexpr std::uintptr_t kChunk = 0x410000000;
constexpr std::uintptr_t kIndex = 0x420000000;
constexpr std::uintptr_t kStorage = 0x430000000;
constexpr std::uintptr_t kCharacters = 0x440000000;
constexpr std::uintptr_t kActor = 0x450000000;
constexpr std::uintptr_t kType = 0x460000000;
constexpr std::int32_t kActorId = 29829;
constexpr std::uintptr_t kOtherActivity = kChunk + 1 * 0x5F0;
constexpr std::uintptr_t kFeast = kChunk + 5 * 0x5F0;

struct Fixture {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  ActivityHostedIdentityFrameV1 frame{
      7, 53219928, kActorId, true, true, true, true};
  bool change_frame_on_second_read = false;
  int frame_reads = 0;

  void WriteBytes(std::uintptr_t address, const void *source,
                  std::size_t size) {
    const auto *first = static_cast<const std::uint8_t *>(source);
    for (std::size_t index = 0; index < size; ++index)
      bytes[address + index] = first[index];
  }

  template <typename T>
  void Write(std::uintptr_t address, const T &value) {
    WriteBytes(address, &value, sizeof(value));
  }

  template <std::size_t Size>
  void WriteCode(std::uintptr_t rva,
                 const std::array<std::uint8_t, Size> &value) {
    WriteBytes(kModule + rva, value.data(), value.size());
  }

  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    auto *destination = static_cast<std::uint8_t *>(output);
    for (std::size_t index = 0; index < size; ++index) {
      const auto found = self.bytes.find(address + index);
      if (found == self.bytes.end()) return false;
      destination[index] = found->second;
    }
    return true;
  }

  static bool ReadFrame(void *context,
                        ActivityHostedIdentityFrameV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    output = self.frame;
    if (self.change_frame_on_second_read && ++self.frame_reads == 2)
      ++output.date_raw;
    return true;
  }

  ActivityHostedIdentityEnvironmentV1 Environment() {
    return {true, kActivityHostedIdentityExeSha256V1, kModule,
            this, Read, ReadFrame};
  }

  Fixture() {
    WriteCode(0x26C8050,
              std::array<std::uint8_t, 7>{0x48, 0x8B, 0x05, 0x11,
                                          0x60, 0x04, 0x03});
    WriteCode(0x2700340,
              std::array<std::uint8_t, 7>{0x48, 0x89, 0x54, 0x24,
                                          0x10, 0x48, 0x89});
    WriteCode(0x2703AF0,
              std::array<std::uint8_t, 7>{0x48, 0x89, 0x5C, 0x24,
                                          0x18, 0x55, 0x56});
    WriteCode(0x218EE1F,
              std::array<std::uint8_t, 7>{0x48, 0x8B, 0x07, 0x49,
                                          0x89, 0x84, 0x24});
    Write(kModule + 0x570E068, kRoot);
    Write(kRoot + 0xA0, kWorld);
    Write(kModule + 0x4FE7EE0, static_cast<std::uint32_t>(kActorId));
    Write(kModule + 0x570C130, kStorage);
    Write(kModule + 0x570C138, static_cast<std::uintptr_t>(0));
    Write(kStorage + 0x20, kCharacters);
    Write(kStorage + 0x2C, static_cast<std::uint32_t>(30000));
    Write(kCharacters + static_cast<std::size_t>(kActorId) * 16 + 8, kActor);
    Write(kActor + 0x18, static_cast<std::uint32_t>(kActorId));
    Write(kManager + 0x10, static_cast<std::uint8_t>(1));
    Write(kManager + 0x60, static_cast<std::uint8_t>(0));
    Write(kManager + 0x61, static_cast<std::uint8_t>(0));
    Write(kManager + 0x20, kChunks);
    Write(kManager + 0x2C, static_cast<std::uint32_t>(1));
    Write(kManager + 0x38, kIndex);
    Write(kManager + 0x44, static_cast<std::uint32_t>(16));
    Write(kManager + 0x50, static_cast<std::int32_t>(5));
    Write(kManager + 0x54, static_cast<std::uint32_t>(2));
    Write(kChunks, kChunk);
    for (std::uint32_t index = 0; index <= 5; ++index)
      Write(kIndex + index * 16 + 8, static_cast<std::uintptr_t>(0));
    Write(kIndex + 1 * 16 + 8, kOtherActivity);
    Write(kIndex + 5 * 16 + 8, kFeast);
    Write(kOtherActivity + 0x08, static_cast<std::uint32_t>(0x01000001));
    Write(kOtherActivity + 0x3A8, static_cast<std::int32_t>(999));
    Write(kFeast, kModule + 0x42F2F28);
    Write(kFeast + 0x08, static_cast<std::uint32_t>(0x02000005));
    Write(kFeast + 0x3A0, kType);
    Write(kFeast + 0x3A8, kActorId);
    Write(kType, kModule + 0x440E308);
    constexpr std::string_view key = "activity_feast";
    WriteBytes(kType + 0x18, key.data(), key.size());
    Write(kType + 0x28, static_cast<std::uint64_t>(key.size()));
    Write(kType + 0x30, static_cast<std::uint64_t>(15));
  }
};

void TestCopiesFullGenerationAndActorIdentity() {
  Fixture fixture;
  const auto result =
      ReadActivityHostedIdentityV1(fixture.Environment(), fixture.frame);
  assert(result.status == ActivityHostedIdentityStatusV1::observed);
  assert(result.manager_active_count == 2);
  assert(result.hosted_count == 1);
  assert(result.hosted[0].activity_id == 0x02000005U);
  assert(result.hosted[0].host_character_id == kActorId);
  assert(std::string_view(result.hosted[0].type_key.data(),
                          result.hosted[0].type_key_size) == "activity_feast");
}

void TestStaleTableEntryCannotClaimCreation() {
  Fixture fixture;
  fixture.Write(kFeast + 0x08, static_cast<std::uint32_t>(0x02000006));
  const auto result =
      ReadActivityHostedIdentityV1(fixture.Environment(), fixture.frame);
  assert(result.status ==
         ActivityHostedIdentityStatusV1::activity_identity_unavailable);
}

void TestNoHostedActivityIsAnObservedEmptySet() {
  Fixture fixture;
  fixture.Write(kFeast + 0x3A8, static_cast<std::int32_t>(999));
  const auto result =
      ReadActivityHostedIdentityV1(fixture.Environment(), fixture.frame);
  assert(result.status == ActivityHostedIdentityStatusV1::observed);
  assert(result.manager_active_count == 2);
  assert(result.hosted_count == 0);
}

void TestActorGenerationMustMatchCharacterStorage() {
  Fixture fixture;
  fixture.Write(kActor + 0x18, static_cast<std::uint32_t>(0x01000000U |
                                                         kActorId));
  const auto result =
      ReadActivityHostedIdentityV1(fixture.Environment(), fixture.frame);
  assert(result.status ==
         ActivityHostedIdentityStatusV1::actor_identity_unavailable);
}

void TestFrameChangeCannotClaimCreation() {
  Fixture fixture;
  fixture.change_frame_on_second_read = true;
  const auto result =
      ReadActivityHostedIdentityV1(fixture.Environment(), fixture.frame);
  assert(result.status == ActivityHostedIdentityStatusV1::snapshot_changed);
}

} // namespace

int main() {
  TestCopiesFullGenerationAndActorIdentity();
  TestStaleTableEntryCannotClaimCreation();
  TestNoHostedActivityIsAnObservedEmptySet();
  TestActorGenerationMustMatchCharacterStorage();
  TestFrameChangeCannotClaimCreation();
}
