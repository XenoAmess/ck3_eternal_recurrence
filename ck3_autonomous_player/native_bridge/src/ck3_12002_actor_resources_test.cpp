#include "xar_bridge/ck3_12002_actor_resources.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <utility>

namespace {
struct Fixture {
  std::array<std::byte, 0x200> actor{};
  std::array<std::byte, 0x300> extension{};
};
template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
bool Read(void *context, std::uintptr_t address, void *output,
          std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  for (const auto span : {std::pair{fixture.actor.data(), fixture.actor.size()},
                          std::pair{fixture.extension.data(), fixture.extension.size()}}) {
    const auto base = reinterpret_cast<std::uintptr_t>(span.first);
    if (address >= base && address - base <= span.second &&
        size <= span.second - (address - base)) {
      std::memcpy(output, reinterpret_cast<void *>(address), size);
      return true;
    }
  }
  return false;
}
void Check(bool condition) { if (!condition) std::abort(); }
}

int main() {
  Fixture fixture{};
  Put(fixture.actor, 0x18, std::int32_t{0x01007485});
  Put(fixture.actor, 0x1B0, reinterpret_cast<std::uintptr_t>(fixture.extension.data()));
  Put(fixture.extension, 0x100, std::int64_t{12345000});
  Put(fixture.extension, 0x130, std::int64_t{-500000});
  Put(fixture.extension, 0x110, std::int64_t{7000000});
  Put(fixture.extension, 0x2F8, std::int32_t{48});
  xar::ck3_12002::ActorResourceBalances12002 result{};
  const auto actor = reinterpret_cast<std::uintptr_t>(fixture.actor.data());
  Check(xar::ck3_12002::ReadActorResourceBalances12002(
      &Read, &fixture, actor, 0x01007485, result));
  Check(result.gold_raw == 12345000 && result.prestige_raw == -500000 &&
        result.piety_raw == 7000000 && result.stress_points == 48);
  Check(!xar::ck3_12002::ReadActorResourceBalances12002(
      &Read, &fixture, actor, 0x02007485, result));
  Put(fixture.actor, 0x1B0, std::uintptr_t{0});
  Check(xar::ck3_12002::ReadActorResourceBalances12002(
      &Read, &fixture, actor, 0x01007485, result));
  Check(result == xar::ck3_12002::ActorResourceBalances12002{});
  Put(fixture.actor, 0x1B0, std::uintptr_t{1});
  Check(!xar::ck3_12002::ReadActorResourceBalances12002(
      &Read, &fixture, actor, 0x01007485, result));
  return 0;
}
