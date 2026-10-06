#include "xar_bridge/activity_hosted_identity_v1.hpp"
#include "xar_bridge/activity_feast_resource_balance_v1.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string_view>
#include <unordered_map>

// One source-only current-build fixture. All reads are against caller-owned
// sparse memory, and the phase function pointers are compared without calls.
namespace {
using namespace xar::bridge;
namespace phase4 = xar::ck3_12004::phase_character;

constexpr std::string_view kActual4Sha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::string_view kHistorical3Sha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uintptr_t kRoot = 0x200000000ULL;
constexpr std::uintptr_t kWorld = 0x300000000ULL;
constexpr std::uintptr_t kManager = kWorld + 0x22CB8;
constexpr std::uintptr_t kChunks = 0x400000000ULL;
constexpr std::uintptr_t kChunk = 0x410000000ULL;
constexpr std::uintptr_t kIndex = 0x420000000ULL;
constexpr std::uintptr_t kStorage = 0x430000000ULL;
constexpr std::uintptr_t kCharacters = 0x440000000ULL;
constexpr std::uintptr_t kActor = 0x450000000ULL;
constexpr std::uintptr_t kActorExtension = 0x450001000ULL;
constexpr std::uintptr_t kGuest = 0x460000000ULL;
constexpr std::uintptr_t kGuestExtension = 0x460001000ULL;
constexpr std::uintptr_t kGuestRecord = 0x460002000ULL;
constexpr std::uintptr_t kType = 0x470000000ULL;
constexpr std::uintptr_t kAttending = 0x480000000ULL;
constexpr std::int32_t kActorId = 29829;
constexpr std::int32_t kGuestId = 37502;
constexpr std::uint32_t kActivityId = 0x02000005U;
constexpr std::uintptr_t kFeast = kChunk + 5 * 0x628;

bool HostedResourcesFail(const char *reason) {
  std::fprintf(stderr, "Activity hosted/resources actual4 fixture: %s\n", reason);
  return false;
}

struct HostedResourcesFixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityHostedIdentityFrameV1 frame{
      14, 53224008, kActorId, true, true, true, true};

  template <typename T>
  void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index)
      bytes[address + index] = source[index];
  }

  static bool Read(void *opaque, std::uintptr_t address, void *out,
                   std::size_t size) noexcept {
    const auto &self = *static_cast<HostedResourcesFixture *>(opaque);
    auto *destination = static_cast<std::uint8_t *>(out);
    for (std::size_t index = 0; index < size; ++index) {
      const auto found = self.bytes.find(address + index);
      if (found == self.bytes.end()) return false;
      destination[index] = found->second;
    }
    return true;
  }

  static bool ReadFrame(void *opaque,
                        ActivityHostedIdentityFrameV1 &out) noexcept {
    out = static_cast<HostedResourcesFixture *>(opaque)->frame;
    return true;
  }

  ActivityHostedIdentityEnvironmentV1 Environment() {
    return {true, kActual4Sha, kModule, this, &Read, &ReadFrame};
  }

  HostedResourcesFixture() {
    // The old build's guard locations are deliberately not present.
    Put(kModule + 0x2ADD8CE,
        std::array<std::uint8_t, 7>{0x49, 0x8D, 0xBF, 0xB8, 0x2C, 0x02, 0x00});
    Put(kModule + 0x29C2E77,
        std::array<std::uint8_t, 7>{0x48, 0x81, 0xC3, 0x28, 0x06, 0x00, 0x00});
    Put(kModule + 0x23F0175,
        std::array<std::uint8_t, 7>{0x41, 0x89, 0x87, 0xA8, 0x03, 0x00, 0x00});
    Put(kModule + 0x5C68C50, kRoot);
    Put(kRoot + 0xA0, kWorld);
    Put(kModule + 0x5C67568, kStorage);
    Put(kModule + 0x5C67570, std::uintptr_t{0});
    Put(kStorage + 0x20, kCharacters);
    Put(kStorage + 0x2C, std::uint32_t{40000});
    Put(kCharacters + static_cast<std::size_t>(kActorId) * 16 + 8, kActor);
    Put(kCharacters + static_cast<std::size_t>(kGuestId) * 16 + 8, kGuest);
    Put(kActor + 0x18, static_cast<std::uint32_t>(kActorId));
    Put(kGuest + 0x18, static_cast<std::uint32_t>(kGuestId));
    Put(kActor + 0x1B0, kActorExtension);
    Put(kActorExtension + 0x100, std::int64_t{12500000});
    Put(kActorExtension + 0x110, std::int64_t{-100000});
    Put(kGuest + 0x1B0, kGuestExtension);
    Put(kGuestExtension + 0x4F8, kGuestRecord);
    Put(kGuestRecord + 0x04, kActivityId);
    Put(kGuestRecord + 0x38, std::uint32_t{2});
    Put(kManager + 0x10, std::uint8_t{1});
    Put(kManager + 0x60, std::uint8_t{0});
    Put(kManager + 0x61, std::uint8_t{0});
    Put(kManager + 0x20, kChunks);
    Put(kManager + 0x2C, std::uint32_t{1});
    Put(kManager + 0x38, kIndex);
    Put(kManager + 0x44, std::uint32_t{16});
    Put(kManager + 0x50, std::int32_t{5});
    Put(kManager + 0x54, std::uint32_t{1});
    Put(kChunks, kChunk);
    for (std::uint32_t index = 0; index <= 5; ++index)
      Put(kIndex + index * 16 + 8, std::uintptr_t{0});
    Put(kIndex + 5 * 16 + 8, kFeast);
    // Parent closes this actual-4 constructor entry in the shared map.
    Put(kFeast, kModule + Activity12004RvaV1(kActual4Sha, 0x472E130));
    Put(kFeast + 0x08, kActivityId);
    Put(kFeast + 0x3A0, kType);
    Put(kFeast + 0x3A8, kActorId);
    Put(kFeast + 0x421, std::uint8_t{0});
    Put(kFeast + 0x422, std::uint8_t{0});
    Put(kFeast + 0x528, kAttending);
    Put(kFeast + 0x534, std::int32_t{1});
    Put(kAttending, static_cast<std::uint32_t>(kGuestId));
    Put(kType, kModule + 0x48BFE60);
    constexpr std::string_view key = "activity_feast";
    for (std::size_t index = 0; index < key.size(); ++index)
      Put(kType + 0x18 + index, static_cast<std::uint8_t>(key[index]));
    Put(kType + 0x28, static_cast<std::uint64_t>(key.size()));
    Put(kType + 0x30, std::uint64_t{15});
  }
};
}  // namespace

bool RunActivityHostedResources12004Fixture() {
  if (Activity12004RvaV1(kActual4Sha, 0x23F0195) != 0x23F0175)
    return HostedResourcesFail("closed actual4 host CharacterID write guard");
  if (Activity12004RvaV1(kActual4Sha, 0x48BFE50) != 0x48BFE60)
    return HostedResourcesFail("closed actual4 ActivityType constructor vptr");
  const auto bindings = phase4::BindImage(kModule, kActual4Sha);
  if (!bindings.enabled ||
      reinterpret_cast<std::uintptr_t>(bindings.get_trait_database) != kModule + 0x89E5B0 ||
      reinterpret_cast<std::uintptr_t>(bindings.character_has_trait) != kModule + 0x28BB1D0 ||
      reinterpret_cast<std::uintptr_t>(bindings.character_trait_tracks) != kModule + 0x28BB0D0 ||
      reinterpret_cast<std::uintptr_t>(bindings.trait_track_index) != kModule + 0x30E56F0 ||
      reinterpret_cast<std::uintptr_t>(bindings.is_human_player_character) != kModule + 0x2BAA6F0 ||
      reinterpret_cast<std::uintptr_t>(bindings.knight_context) != kModule + 0x28BFC50 ||
      phase4::BindImage(kModule, kHistorical3Sha).enabled)
    return HostedResourcesFail("explicit actual4 six-entry phase binding");

  HostedResourcesFixture fixture;
  const auto environment = fixture.Environment();
  const auto initial = ReadActivityHostedIdentityV1(environment, fixture.frame);
  if (initial.status != ActivityHostedIdentityStatusV1::observed ||
      initial.manager_active_count != 1 || initial.hosted_count != 1 ||
      initial.hosted[0].activity_id != kActivityId ||
      initial.hosted[0].host_character_id != kActorId ||
      std::string_view(initial.hosted[0].type_key.data(),
                       initial.hosted[0].type_key_size) != "activity_feast" ||
      !initial.hosted[0].terminal_flags_observed ||
      initial.hosted[0].native_completed || initial.hosted[0].native_invalidated)
    return HostedResourcesFail("actual4 full hosted identity and independent ongoing observation");

  const auto target = ReadActivityHostedTargetV1(
      environment, fixture.frame, kActivityId, kGuestId);
  if (target.status != ActivityHostedTargetStatusV1::observed ||
      target.activity_id != kActivityId || target.guest_character_id != kGuestId ||
      target.host_character_id != kActorId || !target.attending_list_observed ||
      target.attending_count != 1 || !target.target_in_attending_list ||
      !target.character_record_observed || !target.character_record_matches_activity ||
      target.character_activity_id != kActivityId || target.character_activity_state_raw != 2 ||
      !target.native_active_attendee || target.native_completed || target.native_invalidated)
    return HostedResourcesFail("current native attendance and matching full ActivityID state2 record");

  const auto balances = ReadActivityFeastResourceBalancesV1(environment, fixture.frame);
  if (balances.status != ActivityFeastBalanceStatusV1::observed_partial ||
      balances.value.available != std::array<bool, 4>{true, false, true, false} ||
      balances.value.raw[0] != 12500000 || balances.value.raw[2] != -100000)
    return HostedResourcesFail("actual4 signed actor Gold and Piety");
  fixture.Put(kActorExtension + 0x100, std::int64_t{0});
  fixture.Put(kActorExtension + 0x110, std::int64_t{0});
  const auto known_zero = ReadActivityFeastResourceBalancesV1(environment, fixture.frame);
  if (known_zero.status != ActivityFeastBalanceStatusV1::observed_partial ||
      known_zero.value.available != std::array<bool, 4>{true, false, true, false} ||
      known_zero.value.raw[0] != 0 || known_zero.value.raw[2] != 0)
    return HostedResourcesFail("known zero balances retain their actual availability");

  // A pending Start is not an input to this query. Only later copied native
  // flags can change this full activity's observed terminal state.
  ++fixture.frame.revision;
  fixture.Put(kFeast + 0x421, std::uint8_t{1});
  const auto completed = ReadActivityHostedIdentityV1(environment, fixture.frame);
  if (completed.status != ActivityHostedIdentityStatusV1::observed ||
      completed.hosted_count != 1 || !completed.hosted[0].native_completed ||
      completed.hosted[0].native_invalidated || initial.hosted[0].native_completed)
    return HostedResourcesFail("independent hosted completed read preserves copied ongoing result");
  ++fixture.frame.revision;
  fixture.Put(kFeast + 0x421, std::uint8_t{0});
  fixture.Put(kFeast + 0x422, std::uint8_t{1});
  const auto invalidated = ReadActivityHostedIdentityV1(environment, fixture.frame);
  if (invalidated.status != ActivityHostedIdentityStatusV1::observed ||
      invalidated.hosted_count != 1 || invalidated.hosted[0].native_completed ||
      !invalidated.hosted[0].native_invalidated)
    return HostedResourcesFail("independent hosted invalidated observation");
  return true;
}
