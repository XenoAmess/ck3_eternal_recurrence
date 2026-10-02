#include "xar_bridge/activity_hosted_identity_v1.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <map>
#include <iostream>
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
  std::uintptr_t change_address_on_second_read = 0;
  std::uint32_t changed_value = 0;
  int changed_address_reads = 0;
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
    if (address == self.change_address_on_second_read &&
        ++self.changed_address_reads == 2)
      self.Write(address, self.changed_value);
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

constexpr std::uint32_t kActualTerminalActivityId = 83886111;
constexpr std::int32_t kActualGuestId = 37265;
constexpr std::uintptr_t kTargetFeast = kChunk + 31 * 0x628;
constexpr std::uintptr_t kGuest = 0x470000000;
constexpr std::uintptr_t kGuestExtension = 0x480000000;
constexpr std::uintptr_t kGuestRecord = 0x490000000;
constexpr std::uintptr_t kAttending = 0x4A0000000;

struct TargetFixture : Fixture {
  TargetFixture() {
    frame.date_raw = 53222952;
    WriteCode(0x2ADD8EE, std::array<std::uint8_t, 7>{
        0x49, 0x8D, 0xBF, 0xB8, 0x2C, 0x02, 0x00});
    WriteCode(0x29C2E97, std::array<std::uint8_t, 7>{
        0x48, 0x81, 0xC3, 0x28, 0x06, 0x00, 0x00});
    WriteCode(0x23F0195, std::array<std::uint8_t, 7>{
        0x41, 0x89, 0x87, 0xA8, 0x03, 0x00, 0x00});
    Write(kModule + kActivityHosted12002GameStateRva, kRoot);
    Write(kModule + kActivityHosted12002CharacterStorageRva, kStorage);
    Write(kModule + kActivityHosted12002CharacterFallbackRva,
          static_cast<std::uintptr_t>(0));
    Write(kStorage + 0x2C, static_cast<std::uint32_t>(40000));
    Write(kCharacters + static_cast<std::size_t>(kActualGuestId) * 16 + 8,
          kGuest);
    Write(kGuest + 0x18, static_cast<std::uint32_t>(kActualGuestId));
    const auto manager = kWorld + kActivityHosted12002ManagerOffset;
    Write(manager + 0x10, static_cast<std::uint8_t>(1));
    Write(manager + 0x60, static_cast<std::uint8_t>(0));
    Write(manager + 0x61, static_cast<std::uint8_t>(0));
    Write(manager + 0x20, kChunks);
    Write(manager + 0x2C, static_cast<std::uint32_t>(1));
    Write(manager + 0x38, kIndex);
    Write(manager + 0x44, static_cast<std::uint32_t>(64));
    Write(manager + 0x50, static_cast<std::int32_t>(31));
    Write(manager + 0x54, static_cast<std::uint32_t>(1));
    for (std::uint32_t index = 0; index <= 31; ++index)
      Write(kIndex + index * 16 + 8, static_cast<std::uintptr_t>(0));
    Write(kIndex + 31 * 16 + 8, kTargetFeast);
    Write(kTargetFeast, kModule + kActivityHosted12002ActivityVtableRva);
    Write(kTargetFeast + 0x08, kActualTerminalActivityId);
    Write(kTargetFeast + 0x3A0, kType);
    Write(kTargetFeast + 0x3A8, kActorId);
    Write(kType, kModule + kActivityHosted12002ActivityTypeVtableRva);
    Write(kTargetFeast + 0x421, static_cast<std::uint8_t>(1));
    Write(kTargetFeast + 0x422, static_cast<std::uint8_t>(0));
    Write(kTargetFeast + 0x528, kAttending);
    Write(kTargetFeast + 0x534, static_cast<std::int32_t>(2));
    Write(kAttending, static_cast<std::uint32_t>(35466));
    Write(kAttending + 4, static_cast<std::uint32_t>(kActualGuestId));
    Write(kGuest + 0x1B0, kGuestExtension);
    Write(kGuestExtension + 0x4F8, kGuestRecord);
    Write(kGuestRecord + 0x04, kActualTerminalActivityId);
    Write(kGuestRecord + 0x38, static_cast<std::uint32_t>(2));
  }

  ActivityHostedIdentityEnvironmentV1 Environment() {
    return {true,
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
      kModule, this, Read, ReadFrame};
  }

  ActivityHostedTargetResultV1 Observe() {
    return ReadActivityHostedTargetV1(Environment(), frame,
                                     kActualTerminalActivityId, kActualGuestId);
  }
};

void TestTerminalTargetMemberAndExplicitActive() {
  TargetFixture fixture;
  const auto result = fixture.Observe();
  assert(result.status == ActivityHostedTargetStatusV1::observed);
  assert(ActivityHostedTargetStatusKeyV1(result.status) == "observed");
  assert(result.frame == fixture.frame);
  assert(result.activity_id == kActualTerminalActivityId);
  assert(result.guest_character_id == kActualGuestId);
  assert(result.host_character_id == kActorId);
  assert(std::string_view(result.type_key.data(), result.type_key_size) ==
         "activity_feast");
  assert(result.native_completed && !result.native_invalidated);
  assert(result.attending_list_observed && result.attending_count == 2);
  assert(result.target_in_attending_list && result.character_record_observed);
  assert(result.character_activity_id == kActualTerminalActivityId);
  assert(result.character_activity_state_raw == 2);
  assert(result.character_record_matches_activity && result.native_active_attendee);
  // The new API requires actual .3, never the caller's reviewed AE1 hash.
  auto reviewed = fixture.Environment();
  reviewed.admitted_executable_sha256 = kActivityHostedIdentity12002ExeSha256V1;
  assert(ReadActivityHostedTargetV1(reviewed, fixture.frame,
      kActualTerminalActivityId, kActualGuestId).status ==
      ActivityHostedTargetStatusV1::exact_build_rejected);
}

void TestTravelAndPassiveMembersAreNotActive() {
  for (std::uint32_t state : {0U, 1U}) {
    TargetFixture fixture;
    fixture.Write(kGuestRecord + 0x38, state);
    const auto result = fixture.Observe();
    assert(result.status == ActivityHostedTargetStatusV1::observed);
    assert(result.target_in_attending_list);
    assert(result.character_record_matches_activity);
    assert(result.character_activity_state_raw == state);
    assert(!result.native_active_attendee);
  }
}

void TestObservedEmptyListAndEmptyAssociation() {
  TargetFixture fixture;
  fixture.Write(kTargetFeast + 0x528, static_cast<std::uintptr_t>(0));
  fixture.Write(kTargetFeast + 0x534, static_cast<std::int32_t>(0));
  auto result = fixture.Observe();
  assert(result.status == ActivityHostedTargetStatusV1::observed);
  assert(result.attending_list_observed && result.attending_count == 0);
  assert(!result.target_in_attending_list && !result.native_active_attendee);
  for (bool extension_is_empty : {false, true}) {
    TargetFixture empty;
    empty.Write(extension_is_empty ? kGuest + 0x1B0 : kGuestExtension + 0x4F8,
                static_cast<std::uintptr_t>(0));
    result = empty.Observe();
    assert(result.status == ActivityHostedTargetStatusV1::observed);
    assert(result.target_in_attending_list && !result.character_record_observed);
    assert(result.character_activity_state_raw == UINT32_MAX);
    assert(!result.character_record_matches_activity && !result.native_active_attendee);
  }
  TargetFixture unreadable;
  unreadable.bytes.erase(kGuestRecord + 0x38);
  result = unreadable.Observe();
  assert(result.status == ActivityHostedTargetStatusV1::character_record_unavailable);
  assert(!result.character_record_observed && !result.attending_list_observed);
}

void TestForeignAssociationDoesNotClaimActiveAttendance() {
  TargetFixture fixture;
  fixture.Write(kGuestRecord + 0x04, static_cast<std::uint32_t>(83886112));
  const auto result = fixture.Observe();
  assert(result.status == ActivityHostedTargetStatusV1::observed);
  assert(result.target_in_attending_list && result.character_record_observed);
  assert(result.character_activity_state_raw == 2);
  assert(!result.character_record_matches_activity && !result.native_active_attendee);
}

void TestChangedFrameOrTargetRecordCannotPublishObservation() {
  TargetFixture fixture;
  fixture.change_frame_on_second_read = true;
  auto result = fixture.Observe();
  assert(result.status == ActivityHostedTargetStatusV1::snapshot_changed);
  assert(!result.attending_list_observed && !result.character_record_observed);
  TargetFixture changed;
  changed.change_address_on_second_read = kGuestRecord + 0x38;
  changed.changed_value = 0;
  result = changed.Observe();
  assert(result.status == ActivityHostedTargetStatusV1::snapshot_changed);
  assert(!result.attending_list_observed && !result.character_record_observed);
}

} // namespace

int main(int argc, char **argv) {
  const bool target_only = argc == 2 && std::string_view(argv[1]) == "--target-only";
  if (!target_only) {
    TestCopiesFullGenerationAndActorIdentity();
    TestStaleTableEntryCannotClaimCreation();
    TestNoHostedActivityIsAnObservedEmptySet();
    TestActorGenerationMustMatchCharacterStorage();
    TestFrameChangeCannotClaimCreation();
  }
  TestTerminalTargetMemberAndExplicitActive();
  TestTravelAndPassiveMembersAreNotActive();
  TestObservedEmptyListAndEmptyAssociation();
  TestForeignAssociationDoesNotClaimActiveAttendance();
  TestChangedFrameOrTargetRecordCannotPublishObservation();
  std::cout << "ActivityHostedTarget: 5 focused production-reader groups PASS\n";
}
