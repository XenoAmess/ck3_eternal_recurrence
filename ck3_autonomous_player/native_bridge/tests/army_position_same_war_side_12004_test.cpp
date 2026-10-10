#include "xar_bridge/army_position_same_war_side_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <initializer_list>
#include <map>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x100000000;
constexpr std::uintptr_t kActor = 0x200000000;
constexpr std::uintptr_t kHolder = 0x200001000;
constexpr std::uintptr_t kDomain = 0x200002000;
constexpr std::uintptr_t kWarIds = 0x200003000;
constexpr std::uintptr_t kManager = 0x200004000;
constexpr std::uintptr_t kSlots = 0x200005000;
constexpr std::uintptr_t kWar = 0x200006000;
constexpr std::uintptr_t kFallback = 0x200007000;
constexpr std::uintptr_t kManagerSlot = kBase + 0x5D1DE58;
constexpr std::uintptr_t kFallbackSlot = kBase + 0x5D1DE40;
constexpr std::uint32_t kActorId = 0xC0000042;
constexpr std::uint32_t kHolderId = 0xD0000043;
constexpr std::uint32_t kRequestedWarId = 0xE0000001;

void Check(bool condition) {
  if (!condition)
    std::abort();
}
void Known(const ArmyRegularCoreReadonlyPredicate12004 &result, bool value) {
  Check(result.value.has_value() && *result.value == value &&
        result.unavailable_reason.empty());
}
void Unknown(const ArmyRegularCoreReadonlyPredicate12004 &result) {
  Check(!result.value && !result.unavailable_reason.empty());
}

struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  std::size_t manager_reads = 0;
  bool replace_manager_on_second_read = false;
  bool fail_manager_after_initial = false;

  template <class T> void Put(std::uintptr_t address, T value) {
    std::array<std::uint8_t, sizeof(T)> raw{};
    std::memcpy(raw.data(), &value, sizeof(value));
    for (std::size_t index = 0; index < raw.size(); ++index)
      bytes[address + index] = raw[index];
  }

  static bool Read(void *context, std::uintptr_t address, void *out,
                   std::size_t count) noexcept {
    auto &self = *static_cast<Memory *>(context);
    self.reads.emplace_back(address, count);
    if (address == kManagerSlot) {
      ++self.manager_reads;
      if (self.fail_manager_after_initial && self.manager_reads > 1)
        return false;
      if (self.replace_manager_on_second_read && self.manager_reads == 2)
        self.Put<std::uintptr_t>(kManagerSlot, 0);
    }
    auto *result = static_cast<std::uint8_t *>(out);
    for (std::size_t index = 0; index < count; ++index) {
      const auto found = self.bytes.find(address + index);
      if (found == self.bytes.end())
        return false;
      result[index] = found->second;
    }
    return true;
  }

  ArmyRegularCoreReadonlyAccess12004 Access(std::size_t limit = 16) {
    return {kBase, this, &Read, limit};
  }

  bool ReadAddress(std::uintptr_t address) const {
    for (const auto &read : reads)
      if (read.first == address)
        return true;
    return false;
  }

  std::size_t ReadCount(std::uintptr_t address) const {
    std::size_t count = 0;
    for (const auto &read : reads)
      if (read.first == address)
        ++count;
    return count;
  }

  void Characters() {
    Put(kActor + 0x18, kActorId);
    Put(kHolder + 0x18, kHolderId);
  }

  void OneWar() {
    Characters();
    Put(kActor + 0x1C0, kDomain);
    Put(kDomain + 0x318, kWarIds);
    Put<std::int32_t>(kDomain + 0x324, 1);
    Put(kWarIds, kRequestedWarId);
    Put(kManagerSlot, kManager);
    Put(kFallbackSlot, kFallback);
    Put<std::uint32_t>(kManager + 0x2C, 4);
    Put(kManager + 0x20, kSlots);
    Put(kSlots + 16 + 8, kWar);
    Put(kWar + 8, kRequestedWarId);
  }

  void Side(std::uintptr_t descriptor,
            std::initializer_list<std::uint32_t> ids) {
    const auto data = descriptor + 0x10000;
    Put(descriptor + 8, data);
    Put(descriptor + 0x14, static_cast<std::int32_t>(ids.size()));
    std::size_t index = 0;
    for (const auto id : ids) {
      const auto participant = descriptor + 0x20000 + index * 0x40;
      Put(data + index * 8, participant);
      Put(participant + 8, id);
      ++index;
    }
  }
};
} // namespace

// Root's new regular-core position compound calls this once. No old Entry or
// previously GREEN producer fixture is included here.
int RunArmyPositionSameWarSide12004FocusedTests() {
  using namespace xar::ck3_12004;
  int cases = 0;
  {
    Memory m;
    m.Characters();
    m.Put(kHolder + 0x18, kActorId);
    auto access = m.Access();
    access.image_base = 0;
    Known(ReadArmyPosition2C090D012004(access, kActor, kHolder), false);
    Check(m.reads.size() == 2);
    ++cases;
  }
  {
    Memory m;
    m.Characters();
    Unknown(ReadArmyPosition2C090D012004(m.Access(), 0, kHolder));
    ++cases;
  }
  {
    Memory m;
    m.Characters();
    m.Put<std::uintptr_t>(kActor + 0x1C0, 0);
    m.Put<std::uintptr_t>(kBase + 0x5459D38, 0);
    m.Put<std::int32_t>(kBase + 0x5459D44, 0);
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder), false);
    Check(!m.ReadAddress(kManagerSlot));
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Side(kWar + 0x20, {kActorId});
    m.Side(kWar + 0x80, {kActorId, kHolderId});
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder), false);
    Check(!m.ReadAddress(kWar + 0x88));
    Check(m.manager_reads == 2);
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Side(kWar + 0x20, {});
    m.Side(kWar + 0x80, {kActorId, kHolderId});
    m.fail_manager_after_initial = true;
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder), true);
    Check(m.manager_reads == 1);
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Put<std::uint32_t>(kWar + 8, 0xF0000001);
    m.Side(kFallback + 0x20, {kActorId, kHolderId});
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder), true);
    Check(!m.ReadAddress(kWar + 0x28));
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Put<std::uintptr_t>(kManagerSlot, 0);
    for (std::size_t index = 0; index < 4; ++index)
      m.bytes.erase(kWarIds + index);
    m.Side(kFallback + 0x20, {kActorId, kHolderId});
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder), true);
    Check(!m.ReadAddress(kWarIds));
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Put<std::int32_t>(kDomain + 0x324, 2);
    m.Put<std::uintptr_t>(kManagerSlot, 0);
    m.Put<std::uintptr_t>(kFallbackSlot, 0);
    m.fail_manager_after_initial = true;
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder, kWar),
          false);
    Check(m.manager_reads == 1 && !m.ReadAddress(kWarIds));
    Check(m.ReadCount(kActor + 0x18) == 1);
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Side(kWar + 0x20, {});
    m.Side(kWar + 0x80, {});
    m.Side(kFallback + 0x20, {kActorId, kHolderId});
    m.Put<std::int32_t>(kDomain + 0x324, 2);
    m.replace_manager_on_second_read = true;
    Known(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder), true);
    Check(m.manager_reads == 2 && !m.ReadAddress(kWarIds + 4));
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Side(kWar + 0x20, {kActorId});
    m.Side(kWar + 0x80, {kActorId, kHolderId});
    m.bytes.erase(kWar + 0x20 + 0x20000 + 8);
    Unknown(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder));
    Check(!m.ReadAddress(kWar + 0x88));
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Side(kFallback + 0x20, {kActorId, kHolderId});
    m.bytes.erase(kManager + 0x2C);
    Unknown(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder));
    Check(!m.ReadAddress(kFallback + 0x28));
    ++cases;
  }
  {
    Memory m;
    m.OneWar();
    m.Put<std::int32_t>(kDomain + 0x324, -1);
    Unknown(ReadArmyPosition2C090D012004(m.Access(), kActor, kHolder));
    Check(!m.ReadAddress(kManagerSlot));
    m.Put<std::int32_t>(kDomain + 0x324, 2);
    Unknown(ReadArmyPosition2C090D012004(m.Access(1), kActor, kHolder));
    ++cases;
  }
  return cases;
}

#ifdef XAR_ARMY_POSITION_SAME_WAR_SIDE_12004_STANDALONE_TEST
int main() { return RunArmyPositionSameWarSide12004FocusedTests() == 12 ? 0 : 1; }
#endif
