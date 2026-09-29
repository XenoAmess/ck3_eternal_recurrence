#include "xar_bridge/activity_feast_resource_balance_v1.hpp"

#include <limits>

namespace xar::bridge {
namespace {

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &address) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  address = base + offset;
  return true;
}

template <typename T>
bool Read(const ActivityHostedIdentityEnvironmentV1 &environment,
          std::uintptr_t base, std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && environment.read_memory != nullptr &&
         environment.read_memory(environment.context, address, &value,
                                 sizeof(value));
}

bool Sample(const ActivityHostedIdentityEnvironmentV1 &environment,
            std::uint32_t actor_id,
            std::array<std::int64_t, 2> &values) noexcept {
  std::uint32_t played_id = 0, slot_count = 0, roundtrip_id = 0;
  std::uintptr_t storage = 0, fallback = 0, slots = 0, actor = 0;
  std::uintptr_t extension = 0;
  const auto base = environment.module_base;
  if (!Read(environment, base, 0x4FE7EE0, played_id) ||
      played_id != actor_id ||
      !Read(environment, base, 0x570C130, storage) || storage == 0 ||
      !Read(environment, base, 0x570C138, fallback) ||
      !Read(environment, storage, 0x20, slots) || slots == 0 ||
      !Read(environment, storage, 0x2C, slot_count) ||
      (actor_id & 0x00FFFFFFU) >= slot_count ||
      !Read(environment, slots,
            static_cast<std::size_t>(actor_id & 0x00FFFFFFU) * 16 + 8,
            actor) || actor == 0 || actor == fallback ||
      !Read(environment, actor, 0x18, roundtrip_id) ||
      roundtrip_id != actor_id ||
      !Read(environment, actor, 0x1A8, extension) || extension == 0 ||
      !Read(environment, extension, 0x100, values[0]) ||
      !Read(environment, extension, 0x110, values[1]))
    return false;
  std::uintptr_t actor_after = 0, extension_after = 0;
  std::uint32_t id_after = 0;
  return Read(environment, slots,
              static_cast<std::size_t>(actor_id & 0x00FFFFFFU) * 16 + 8,
              actor_after) && actor_after == actor &&
         Read(environment, actor, 0x18, id_after) && id_after == actor_id &&
         Read(environment, actor, 0x1A8, extension_after) &&
         extension_after == extension;
}

} // namespace

ActivityFeastBalanceResultV1 ReadActivityFeastResourceBalancesV1(
    const ActivityHostedIdentityEnvironmentV1 &environment,
    const ActivityHostedIdentityFrameV1 &expected) noexcept {
  ActivityFeastBalanceResultV1 result{};
  result.value.frame = expected;
  if (!environment.enabled || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kActivityHostedIdentityExeSha256V1 ||
      environment.read_memory == nullptr || environment.read_frame == nullptr)
    return result;
  ActivityHostedIdentityFrameV1 before{};
  if (!environment.read_frame(environment.context, before) ||
      before != expected || expected.revision == 0 ||
      expected.actor_character_id <= 0 ||
      !expected.application_main_thread || !expected.paused ||
      !expected.map_ready || !expected.actor_alive) {
    result.status = ActivityFeastBalanceStatusV1::frame_rejected;
    return result;
  }
  std::array<std::int64_t, 2> first{}, second{};
  if (!Sample(environment,
              static_cast<std::uint32_t>(expected.actor_character_id), first)) {
    result.status = ActivityFeastBalanceStatusV1::actor_unavailable;
    return result;
  }
  ActivityHostedIdentityFrameV1 after{};
  if (!Sample(environment,
              static_cast<std::uint32_t>(expected.actor_character_id), second) ||
      first != second || !environment.read_frame(environment.context, after) ||
      after != expected) {
    result.status = ActivityFeastBalanceStatusV1::frame_changed;
    return result;
  }
  result.value.available = {true, false, true, false};
  result.value.raw[0] = first[0];
  result.value.raw[2] = first[1];
  result.status = ActivityFeastBalanceStatusV1::observed_partial;
  return result;
}

} // namespace xar::bridge
