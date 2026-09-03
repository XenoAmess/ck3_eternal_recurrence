#include "xar_bridge/cold_map_vfs_observer_v1.hpp"

#include <array>
#include <cassert>
#include <cstring>

namespace {

void Seed(void *target, const std::uint8_t *bytes, std::size_t size) {
  std::memcpy(target, bytes, size);
}

} // namespace

int main() {
  using namespace xar::bridge;

  static_assert(!kColdMapVfsObserverInstalledByDefaultV1);
  static_assert(kColdMapVfsCtorPatchRvaV1 == 0x3B55A40);
  static_assert(kColdMapVfsVariantPatchRvaV1 == 0x3B55ADE);
  static_assert(kColdMapVfsPollPatchRvaV1 == 0x3B55D50);

  ColdMapVfsObserverV1State denied{};
  ColdMapVfsObserverEnvironmentV1 denied_environment{};
  assert(!InstallColdMapVfsObserverV1(denied, denied_environment));
  assert((denied.failure_flags.load() &
          cold_map_vfs_observer_failure_exact_build) != 0);

  std::array<char, 24> path{};
  struct Descriptor {
    const char *data;
    std::uint32_t length;
    std::uint8_t flag;
    std::uint8_t padding[3];
  } descriptor{path.data(), 12, 1, {0, 0, 0}};
  std::memcpy(path.data(), "/default.map", 12);

  ColdMapVfsObserverV1State record{};
  RecordColdMapVfsCtorV1(record,
                         reinterpret_cast<std::uintptr_t>(&descriptor));
  auto d = ReadColdMapVfsObserverV1Diagnostics(record);
  assert(d.ctor_count == 1 && d.ctor_length == 12 && d.ctor_flag == 1);
  assert(d.ctor_word0 != 0);

  struct Variant {
    const char *payload;
    std::uint8_t pad0[8];
    std::uint32_t length;
    std::uint8_t pad1[4];
    std::uint32_t capacity;
    std::uint8_t pad2[4];
    std::uint8_t tag;
    std::uint8_t tail[7];
  } variant{path.data(), {}, 12, {}, 23, {}, 1, {}};
  static_assert(offsetof(Variant, tag) == 0x20);
  RecordColdMapVfsVariantV1(record,
                            reinterpret_cast<std::uintptr_t>(&variant));
  d = ReadColdMapVfsObserverV1Diagnostics(record);
  assert(d.variant_count == 1 && d.variant_tag == 1);
  assert(d.variant_length == 12 && d.variant_capacity == 23);

  struct PollObject {
    std::uint8_t prefix[0x0C];
    std::uint8_t state;
    std::uint8_t aux;
    std::uint8_t gap[0x2A];
    Variant variant;
  } object{{}, 0, 7, {}, variant};
  static_assert(offsetof(PollObject, variant) == 0x38);
  RecordColdMapVfsPollV1(record,
                         reinterpret_cast<std::uintptr_t>(&object));
  d = ReadColdMapVfsObserverV1Diagnostics(record);
  assert(d.poll_count == 1 && d.poll_state == 0 && d.poll_aux_state == 7);
  assert(d.poll_variant_tag == 1 && d.poll_length == 12);

  constexpr std::array<std::uint8_t, 15> ctor{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74,
      0x24, 0x18, 0x48, 0x89, 0x7C, 0x24, 0x20};
  constexpr std::array<std::uint8_t, 14> moved{
      0x49, 0x8D, 0x4E, 0x38, 0xE8, 0x49, 0x0D,
      0x00, 0x00, 0x80, 0x7C, 0x24, 0x40, 0x01};
  constexpr std::array<std::uint8_t, 15> poll{
      0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x0F, 0xB6,
      0x41, 0x0C, 0x48, 0x8B, 0xD9, 0x3C, 0x0A};
  std::array<void *, 3> targets{};
  for (auto &target : targets) {
    target = VirtualAlloc(nullptr, 64, MEM_RESERVE | MEM_COMMIT,
                          PAGE_EXECUTE_READWRITE);
    assert(target != nullptr);
  }
  Seed(targets[0], ctor.data(), ctor.size());
  Seed(targets[1], moved.data(), moved.size());
  Seed(targets[2], poll.data(), poll.size());

  ColdMapVfsObserverV1State installed{};
  ColdMapVfsObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  for (std::size_t i = 0; i < 3; ++i) {
    environment.patch_target_overrides[i] =
        reinterpret_cast<std::uintptr_t>(targets[i]);
    environment.continue_target_overrides[i] =
        reinterpret_cast<std::uintptr_t>(targets[i]) +
        (i == 1 ? 14 : 15);
  }
  environment.variant_move_target_override =
      reinterpret_cast<std::uintptr_t>(targets[1]) + 32;
  assert(InstallColdMapVfsObserverV1(installed, environment));
  assert(installed.installed.load() == 1 && installed.installed_mask.load() == 7);
  for (const auto target : targets) {
    const auto *bytes = static_cast<const std::uint8_t *>(target);
    assert(bytes[0] == 0xFF && bytes[1] == 0x25);
  }
  assert(UninstallColdMapVfsObserverV1(installed));
  assert(installed.installed.load() == 0 && installed.installed_mask.load() == 0);
  assert(std::memcmp(targets[0], ctor.data(), ctor.size()) == 0);
  assert(std::memcmp(targets[1], moved.data(), moved.size()) == 0);
  assert(std::memcmp(targets[2], poll.data(), poll.size()) == 0);
  for (auto target : targets) assert(VirtualFree(target, 0, MEM_RELEASE) != FALSE);
  return 0;
}
