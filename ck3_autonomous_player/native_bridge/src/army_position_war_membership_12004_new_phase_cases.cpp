#include "xar_bridge/army_position_war_membership_12004.hpp"
#include <array>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
struct OwnedMembershipMemory {
  std::array<std::byte, 0x18> descriptor{};
  std::array<std::uintptr_t, 3> records{};
  std::array<std::array<std::byte, 0x10>, 3> objects{};
  std::uintptr_t denied = 0;
  std::size_t data_header_reads = 0;
  bool change_ending_header = false;
};
template <typename T> void Store(void *memory, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(memory) + offset, &value, sizeof(value));
}
bool In(const void *memory, std::size_t length, std::uintptr_t address,
        std::size_t size) noexcept {
  const auto begin = reinterpret_cast<std::uintptr_t>(memory);
  return address >= begin && address - begin <= length &&
      size <= length - static_cast<std::size_t>(address - begin);
}
bool CopyOwned(void *context, std::uintptr_t address, void *out,
               std::size_t size) noexcept {
  auto &m = *static_cast<OwnedMembershipMemory *>(context);
  if (address == m.denied) return false;
  if (address == reinterpret_cast<std::uintptr_t>(m.descriptor.data()) + 8) {
    ++m.data_header_reads;
    if (m.change_ending_header && m.data_header_reads == 2) {
      const std::uintptr_t changed = 0;
      std::memcpy(out, &changed, size);
      return true;
    }
  }
  bool owned = In(m.descriptor.data(), m.descriptor.size(), address, size) ||
      In(m.records.data(), sizeof(m.records), address, size);
  for (const auto &record : m.objects)
    owned = owned || In(record.data(), record.size(), address, size);
  if (!owned) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  return true;
}
void Need(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
void Prepare(OwnedMembershipMemory &m, std::int32_t count) {
  Store(m.descriptor.data(), 8,
        reinterpret_cast<std::uintptr_t>(m.records.data()));
  Store(m.descriptor.data(), 0x14, count);
  constexpr std::array<std::int32_t,3> ids{0x01000001,0x01000001,0x02000001};
  for (std::size_t i=0;i<m.records.size();++i) {
    m.records[i]=reinterpret_cast<std::uintptr_t>(m.objects[i].data());
    Store(m.objects[i].data(),8,ids[i]);
  }
}
ArmyPositionWarMembershipSide12004Read Run(OwnedMembershipMemory &m,
                                          std::int32_t id) {
  const auto descriptor_before=m.descriptor;
  const auto records_before=m.records;
  const auto objects_before=m.objects;
  ArmyRegularCoreReadonlyAccess12004 access;
  access.read=CopyOwned; access.read_context=&m;
  const auto out=ReadArmyWarMembershipSide12004(access,
      reinterpret_cast<std::uintptr_t>(m.descriptor.data()),id);
  Need(m.descriptor==descriptor_before && m.records==records_before &&
       m.objects==objects_before,"membership observer wrote source memory");
  return out;
}
} // namespace

// Exported to Root10's single NEW phase compound. No main, prior focus,
// native EXE callback, game connection or independent execution.
void RunArmyPositionMembership12004NewPhaseCases() {
  {
    OwnedMembershipMemory m; Prepare(m,3);
    const auto out=Run(m,0x02000001);
    Need(out.predicate.value==true && out.matched_index==2 &&
        out.evaluated_full_ids.size()==3 &&
        out.evaluated_full_ids[0]==out.evaluated_full_ids[1],
        "ordered duplicates or complete generation equality were lost");
  }
  {
    OwnedMembershipMemory m; Prepare(m,3);
    m.denied=reinterpret_cast<std::uintptr_t>(&m.records[1]);
    const auto out=Run(m,0x01000001);
    Need(out.predicate.value==true && out.matched_index==0 &&
        out.evaluated_full_ids.size()==1,
        "native first-match short circuit read later records");
  }
  {
    OwnedMembershipMemory m; Prepare(m,0);
    Store(m.descriptor.data(),8,std::uintptr_t{0});
    const auto out=Run(m,0x03000001);
    Need(out.raw_count==0 && out.data_present==false &&
        out.predicate.value==false && out.evaluated_full_ids.empty(),
        "lawful null-data empty descriptor was unavailable");
  }
  {
    OwnedMembershipMemory m; Prepare(m,3);
    const auto out=Run(m,0x03000001);
    Need(out.predicate.value==false && out.evaluated_full_ids.size()==3,
        "same low24 with another generation yielded membership");
  }
  {
    OwnedMembershipMemory m; Prepare(m,1);
    Store(m.descriptor.data(),8,std::uintptr_t{0});
    const auto out=Run(m,0x01000001);
    Need(out.raw_count==1 && out.data_present==false && !out.predicate.value,
        "nonempty absent data became known false");
  }
  {
    OwnedMembershipMemory m; Prepare(m,1);
    m.denied=reinterpret_cast<std::uintptr_t>(m.descriptor.data())+0x14;
    const auto out=Run(m,0x01000001);
    Need(!out.raw_count && !out.predicate.value &&
        out.predicate.unavailable_reason=="army_position_membership_count_unread",
        "unread signed count became zero");
  }
  {
    OwnedMembershipMemory m; Prepare(m,1);
    m.denied=m.records[0]+8;
    const auto out=Run(m,0x01000001);
    Need(!out.predicate.value && out.evaluated_full_ids.size()==1 &&
        !out.evaluated_full_ids[0],"unread record fullID became false membership");
  }
  {
    OwnedMembershipMemory m; Prepare(m,1); m.change_ending_header=true;
    const auto out=Run(m,0x01000001);
    Need(!out.predicate.value && out.matched_index==0 &&
        out.predicate.unavailable_reason=="army_position_membership_header_changed",
        "changed native ending header yielded certified membership");
  }
}
} // namespace xar::ck3_12004
