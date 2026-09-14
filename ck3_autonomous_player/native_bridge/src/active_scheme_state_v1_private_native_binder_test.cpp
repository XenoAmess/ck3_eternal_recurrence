#include "xar_bridge/active_scheme_state_v1_private_native_binder.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <vector>

namespace {

using namespace xar::bridge;

constexpr std::uintptr_t kModuleBase = 0x10000000;
constexpr std::size_t kSchemeSize = 0x358;
constexpr std::int32_t kOwner = 42;
constexpr std::uint32_t kSwayIdentity = 0x01000005;
constexpr std::uint32_t kMurderIdentity = 0x02000008;
constexpr std::uint32_t kSwayTarget = 0x01000003;
constexpr std::uint32_t kMurderTarget = 0x01000004;

template <typename T>
void Store(void *base, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

struct Fixture {
  std::vector<std::byte> application{0xA580};
  std::array<std::byte, 0x58> storage{};
  std::array<std::uintptr_t, 1> block_table{};
  std::vector<std::byte> block{kSchemeSize * 16};
  std::array<std::byte, 0x10 * 16> scheme_slots{};
  std::vector<std::byte> sway_type{0xB60};
  std::vector<std::byte> murder_type{0xB60};

  std::array<std::byte, 0x40> character_storage{};
  std::array<std::byte, 0x10 * 16> character_slots{};
  std::array<std::byte, 0x30> sway_target{};
  std::array<std::byte, 0x30> murder_target{};
  std::array<std::byte, 0x30> fallback_character{};

  bool corrupt_signature = false;
  bool corrupt_vtable_slot = false;
  bool mutate_on_third_key_read = false;
  int key_reads = 0;
  int application_slot_reads = 0;

  std::uintptr_t Manager() noexcept {
    return reinterpret_cast<std::uintptr_t>(application.data()) +
           kActiveSchemeStateV1PrivateManagerOffset;
  }
  std::uintptr_t Storage() noexcept {
    return reinterpret_cast<std::uintptr_t>(storage.data());
  }
  std::uintptr_t Sway() noexcept {
    return reinterpret_cast<std::uintptr_t>(block.data()) +
           5 * kSchemeSize;
  }
  std::uintptr_t Murder() noexcept {
    return reinterpret_cast<std::uintptr_t>(block.data()) +
           8 * kSchemeSize;
  }

  Fixture() {
    const auto manager_vtable =
        kModuleBase + kActiveSchemeStateV1PrivateManagerVtableRva;
    Store(application.data(), kActiveSchemeStateV1PrivateManagerOffset,
          manager_vtable);
    const auto storage_address = Storage();
    Store(application.data(),
          kActiveSchemeStateV1PrivateManagerOffset + 0x20,
          storage_address);

    const auto storage_vtable =
        kModuleBase + kActiveSchemeStateV1PrivateStorageVtableRva;
    Store(storage.data(), 0x00, storage_vtable);
    block_table[0] = reinterpret_cast<std::uintptr_t>(block.data());
    const auto blocks = reinterpret_cast<std::uintptr_t>(block_table.data());
    const auto slots = reinterpret_cast<std::uintptr_t>(scheme_slots.data());
    Store(storage.data(), 0x08, blocks);
    Store(storage.data(), 0x20, slots);
    Store(storage.data(), 0x2C, std::int32_t{16});
    Store(storage.data(), 0x3C, std::int32_t{2});
    const auto sway = Sway();
    const auto murder = Murder();
    Store(scheme_slots.data(), 5 * 0x10 + 0x08, sway);
    Store(scheme_slots.data(), 8 * 0x10 + 0x08, murder);

    InitializeType(sway_type.data(), true, 0, 0);
    InitializeType(murder_type.data(), false, 5, 4);
    InitializeScheme(sway, kSwayIdentity,
                     reinterpret_cast<std::uintptr_t>(sway_type.data()),
                     kSwayTarget, 3, 8, false, false, 0, 0, 0);
    InitializeScheme(murder, kMurderIdentity,
                     reinterpret_cast<std::uintptr_t>(murder_type.data()),
                     kMurderTarget, 4, 10, false, true, 2, 1, 1);

    const auto character_slots_address =
        reinterpret_cast<std::uintptr_t>(character_slots.data());
    Store(character_storage.data(), 0x20, character_slots_address);
    Store(character_storage.data(), 0x2C, std::int32_t{16});
    const auto sway_target_address =
        reinterpret_cast<std::uintptr_t>(sway_target.data());
    const auto murder_target_address =
        reinterpret_cast<std::uintptr_t>(murder_target.data());
    Store(character_slots.data(), 3 * 0x10 + 0x08, sway_target_address);
    Store(character_slots.data(), 4 * 0x10 + 0x08, murder_target_address);
    Store(sway_target.data(), 0x18, kSwayTarget);
    Store(murder_target.data(), 0x18, kMurderTarget);
  }

  void InitializeType(void *type, bool basic, std::int32_t maximum_breaches,
                      std::int32_t phases_per_opportunity) {
    const auto vtable =
        kModuleBase + kActiveSchemeStateV1PrivateSchemeTypeVtableRva;
    Store(type, 0x00, vtable);
    Store(type, 0x9B8, phases_per_opportunity);
    Store(type, 0x9BC, maximum_breaches);
    Store(type, 0xB4E, basic);
  }

  void InitializeScheme(std::uintptr_t address, std::uint32_t identity,
                        std::uintptr_t type, std::uint32_t target,
                        std::int32_t progress, std::int32_t progress_goal,
                        bool exposed, bool frozen, std::int32_t opportunities,
                        std::int32_t breaches, std::int32_t phases_elapsed) {
    auto *const scheme = reinterpret_cast<void *>(address);
    const auto vtable =
        kModuleBase + kActiveSchemeStateV1PrivateActiveSchemeVtableRva;
    Store(scheme, 0x00, vtable);
    Store(scheme, 0x10, identity);
    Store(scheme, 0x20, type);
    Store(scheme, 0x2C, kOwner);
    Store(scheme, 0x30, std::int32_t{0});
    Store(scheme, 0x34, target);
    Store(scheme, 0x78, progress);
    Store(scheme, 0x27C, exposed);
    Store(scheme, 0x294, phases_elapsed);
    Store(scheme, 0x298, opportunities);
    Store(scheme, 0x29C, breaches);
    Store(scheme, 0x2A8, static_cast<std::uint8_t>(frozen ? 1 : 0));
    Store(scheme, 0x350, progress_goal);
  }
};

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto current = reinterpret_cast<std::uintptr_t>(address);
  for (std::size_t index = 0;
       index < kActiveSchemeStateV1PrivateNativeSignatures.size(); ++index) {
    const auto &signature =
        kActiveSchemeStateV1PrivateNativeSignatures[index];
    if (current == kModuleBase + signature.rva && size == signature.size) {
      std::memcpy(output, signature.bytes.data(), size);
      if (fixture.corrupt_signature && index == 0) {
        static_cast<std::uint8_t *>(output)[0] ^= 0x01U;
      }
      return true;
    }
  }
  for (std::size_t index = 0;
       index < kActiveSchemeStateV1PrivateNativeSlots.size(); ++index) {
    const auto &slot = kActiveSchemeStateV1PrivateNativeSlots[index];
    if (current == kModuleBase + slot.slot_rva &&
        size == sizeof(std::uintptr_t)) {
      auto value = kModuleBase + slot.function_rva;
      if (fixture.corrupt_vtable_slot && index == 0) ++value;
      std::memcpy(output, &value, sizeof(value));
      return true;
    }
  }
  if (current ==
          kModuleBase + kActiveSchemeStateV1PrivateApplicationSlotRva &&
      size == sizeof(std::uintptr_t)) {
    ++fixture.application_slot_reads;
    const auto value =
        reinterpret_cast<std::uintptr_t>(fixture.application.data());
    std::memcpy(output, &value, sizeof(value));
    return true;
  }
  if (current == kModuleBase + 0x570C130 &&
      size == sizeof(std::uintptr_t)) {
    const auto value =
        reinterpret_cast<std::uintptr_t>(fixture.character_storage.data());
    std::memcpy(output, &value, sizeof(value));
    return true;
  }
  if (current == kModuleBase + 0x570C138 &&
      size == sizeof(std::uintptr_t)) {
    const auto value =
        reinterpret_cast<std::uintptr_t>(fixture.fallback_character.data());
    std::memcpy(output, &value, sizeof(value));
    return true;
  }
  std::memcpy(output, address, size);
  return true;
}

bool ReadStableKey(void *context, const void *native_string, char *output,
                   std::size_t output_capacity) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.key_reads;
  if (fixture.mutate_on_third_key_read && fixture.key_reads == 3) {
    Store(reinterpret_cast<void *>(fixture.Sway()), 0x78, std::int32_t{4});
  }
  const auto address = reinterpret_cast<std::uintptr_t>(native_string);
  std::string_view key{};
  if (address == reinterpret_cast<std::uintptr_t>(fixture.sway_type.data()) +
                     0x18) {
    key = "sway";
  } else if (address ==
             reinterpret_cast<std::uintptr_t>(fixture.murder_type.data()) +
                 0x18) {
    key = "murder";
  } else {
    return false;
  }
  if (key.size() >= output_capacity) return false;
  std::memset(output, 0, output_capacity);
  std::memcpy(output, key.data(), key.size());
  return true;
}

bool ReadSuccess(void *context, std::uintptr_t module_base,
                 const void *scheme, std::int32_t &success,
                 std::int32_t &maximum) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (module_base != kModuleBase ||
      reinterpret_cast<std::uintptr_t>(scheme) != fixture.Murder()) {
    return false;
  }
  success = 78;
  maximum = 90;
  return true;
}

bool ReadSecrecyFixture(void *context, std::uintptr_t module_base,
                        const void *scheme,
                        std::int32_t &secrecy) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (module_base != kModuleBase ||
      reinterpret_cast<std::uintptr_t>(scheme) != fixture.Murder()) {
    return false;
  }
  secrecy = 65;
  return true;
}

bool ReadSecretFlag(void *context, std::uintptr_t module_base,
                    const void *scheme, bool &is_secret) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (module_base != kModuleBase) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(scheme);
  if (address == fixture.Sway()) {
    is_secret = false;
    return true;
  }
  if (address == fixture.Murder()) {
    is_secret = true;
    return true;
  }
  return false;
}

bool CaptureFrame(void *, ActiveSchemeStateV1PrivateSourceFrame &output) noexcept {
  output = {77, 123456, kOwner, true};
  return true;
}

ActiveSchemeStateV1PrivateNativeEnvironment Environment(Fixture &fixture) {
  ActiveSchemeStateV1PrivateNativeEnvironment environment{};
  environment.binding_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      kActiveSchemeStateV1PrivateObserverExecutableSha256;
  environment.admitted_game_version =
      kActiveSchemeStateV1PrivateNativeBinderGameVersion;
  environment.offline_fixture = true;
  environment.module_base = kModuleBase;
  environment.operation_context = &fixture;
  environment.operations = {&ReadMemory, &ReadStableKey, &ReadSuccess,
                            &ReadSecrecyFixture, &ReadSecretFlag};
  return environment;
}

ActiveSchemeStateV1PrivateSourceAccess Access() {
  ActiveSchemeStateV1PrivateSourceAccess access{};
  access.current_thread_id = 9;
  access.application_main_thread_id = 9;
  access.capture_frame = &CaptureFrame;
  return access;
}

bool KeyEquals(const auto &key, std::string_view expected) {
  return std::string_view{key.data()} == expected;
}

int failures = 0;

void Expect(bool condition, std::string_view label) {
  if (!condition) {
    ++failures;
    std::cerr << "FAIL: " << label << '\n';
  }
}

void TestSwayAndMurder() {
  Fixture fixture{};
  auto environment = Environment(fixture);
  auto access = Access();
  ActiveSchemeStateV1PrivateNativeBindingState state{};
  Expect(BindActiveSchemeStateV1PrivateNative(environment, state, access),
         "exact binder attaches");
  ActiveSchemeStateV1PrivateSourceResult result{};
  Expect(ObserveActiveSchemeStateV1PrivateSource(access, result),
         "source adapter accepts bound rows");
  Expect(result.failure == ActiveSchemeStateV1PrivateSourceFailure::none,
         "source result GREEN");
  Expect(result.observation.row_count == 2, "two player schemes");
  const auto &sway = result.observation.rows[0];
  const auto &murder = result.observation.rows[1];
  Expect(KeyEquals(sway.scheme_type_key, "sway") && sway.is_basic,
         "basic sway identity");
  Expect(KeyEquals(sway.category_key, "personal") &&
             sway.target_id == kSwayTarget && sway.progress.value == 3 &&
             sway.progress_goal.value == 8,
         "basic sway common fields");
  Expect(sway.success_chance.status ==
             ActiveSchemeStateV1PrivateValueStatus::not_applicable,
         "basic sway typed N/A");
  Expect(KeyEquals(murder.scheme_type_key, "murder") && !murder.is_basic &&
             KeyEquals(murder.category_key, "hostile"),
         "complex murder identity");
  Expect(murder.target_id == kMurderTarget && murder.is_secret &&
             murder.is_frozen && murder.progress.value == 4 &&
             murder.progress_goal.value == 10,
         "complex murder common fields");
  Expect(murder.success_chance.value == 78 &&
             murder.maximum_success_chance.value == 90 &&
             murder.secrecy.value == 65 &&
             murder.opportunity_charges.value == 2 &&
             murder.breaches.value == 1 &&
             murder.maximum_breaches.value == 5 &&
             murder.phases_remaining_until_opportunity.value == 3,
         "complex murder metrics");
  Expect(fixture.application_slot_reads >= 8,
         "root is re-resolved instead of cached");
}

void TestExactImageGates() {
  {
    Fixture fixture{};
    fixture.corrupt_signature = true;
    auto environment = Environment(fixture);
    auto access = Access();
    ActiveSchemeStateV1PrivateNativeBindingState state{};
    Expect(!BindActiveSchemeStateV1PrivateNative(environment, state, access),
           "instruction prefix mismatch rejected");
  }
  {
    Fixture fixture{};
    fixture.corrupt_vtable_slot = true;
    auto environment = Environment(fixture);
    auto access = Access();
    ActiveSchemeStateV1PrivateNativeBindingState state{};
    Expect(!BindActiveSchemeStateV1PrivateNative(environment, state, access),
           "vtable slot mismatch rejected");
  }
  {
    Fixture fixture{};
    auto environment = Environment(fixture);
    environment.admitted_game_version = "1.19.0.5";
    auto access = Access();
    ActiveSchemeStateV1PrivateNativeBindingState state{};
    Expect(!BindActiveSchemeStateV1PrivateNative(environment, state, access),
           "game version mismatch rejected");
  }
}

void TestSecondPassDriftFailsClosed() {
  Fixture fixture{};
  fixture.mutate_on_third_key_read = true;
  auto environment = Environment(fixture);
  auto access = Access();
  ActiveSchemeStateV1PrivateNativeBindingState state{};
  Expect(BindActiveSchemeStateV1PrivateNative(environment, state, access),
         "drift fixture binds");
  ActiveSchemeStateV1PrivateSourceResult result{};
  Expect(!ObserveActiveSchemeStateV1PrivateSource(access, result),
         "second-pass row drift rejected");
  Expect(result.failure == ActiveSchemeStateV1PrivateSourceFailure::row_drift,
         "row drift remains RED");
}

} // namespace

int main() {
  TestSwayAndMurder();
  TestExactImageGates();
  TestSecondPassDriftFailsClosed();
  if (failures != 0) return 1;
  std::cout << "GREEN: active_scheme_state_v1 exact native binder; basic sway "
               "and complex murder fixtures\n";
  return 0;
}
