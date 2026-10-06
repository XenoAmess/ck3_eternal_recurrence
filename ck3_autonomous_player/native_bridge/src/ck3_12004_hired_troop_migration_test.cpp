#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_holy_order_bindings.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_mailbox.hpp"
#include "xar_bridge/ck3_12003_holy_order_hire_action.hpp"
#include "xar_bridge/ck3_12003_holy_order_hire_wire.hpp"
#include "xar_bridge/ck3_12003_player_mercenary_context.hpp"
#include "xar_bridge/ck3_12003_mercenary_hire_action.hpp"
#include "xar_bridge/ck3_12003_mercenary_hire_wire.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace holy = xar::ck3_12003::religion::holy_order;
namespace merc = xar::ck3_12003::mercenary;
namespace {
constexpr std::int32_t kActor = 29829, kDate = 53286648;
constexpr std::uint64_t kRevision = 171, kEpoch = 12004;
constexpr std::uint32_t kOrder = 0x81000000U, kCompany = 0x91000000U;
using Command = std::array<std::byte, 0x30>;
template<class T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p)+offset, &value, sizeof(value));
}
template<class T> T Get(const void *p, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p)+offset, sizeof(value));
  return value;
}
int checks = 0, queues = 0, clones = 0, deletes = 0, selector_calls = 0;
void Check(bool pass, const char *why) {
  ++checks;
  if (!pass) throw std::runtime_error(why);
}
alignas(8) std::array<std::byte, 0x200> actor{};
alignas(8) std::array<std::byte, 0x400> realm{};
alignas(8) std::array<std::byte, 0x100> order{}, company{}, fallback{};
alignas(8) std::array<std::byte, 0x30> holy_manager{}, merc_manager{};
alignas(8) std::array<std::byte, 0x10> holy_entries{}, merc_entries{};
alignas(8) std::array<std::byte, 0x30> regi_storage{};
alignas(8) std::array<std::byte, 0x900> home{}, selected{};
alignas(8) std::array<std::byte, 0x20> title{};
std::array<void *, 9> primary{};
std::array<void *, 2> secondary{};
void *holy_manager_pointer = holy_manager.data();
void *merc_manager_pointer = merc_manager.data();
void *fallback_pointer = fallback.data();
void *regi_storage_pointer = regi_storage.data();
void Reason(void *sink, std::string_view text) {
  if (!sink) return;
  Check(text.size() <= 15, "fixture reason remains inline native SSO");
  std::memcpy(sink, text.data(), text.size());
  Put(sink, 0x10, text.size());
}
void DestroyReason(void *sink) {
  Check(Get<std::size_t>(sink, 0x18) == std::size_t{15}, "native SSO capacity preserved");
}
void *Patron(void *) { return actor.data(); }
bool Military(void *) { return true; }
bool HolyCanHire(void *o, void *a, void *reason) {
  Check(o == order.data() && a == actor.data(), "holy getter receives actual selected pointers");
  Reason(reason, ""); return true;
}
std::int64_t *HolyCost(void *, std::int64_t *out, void *) {
  const std::array<std::int64_t,10> costs{0,-50000,12500000,0,0,0,0,0,0,0};
  std::memcpy(out,costs.data(),sizeof(costs)); return out;
}
bool Afford(const std::int64_t *cost, void *a, void *reason) {
  Check(a == actor.data(), "independent affordability receives current actor");
  const bool result = cost[0] == std::int64_t{0};
  Reason(reason,result ? "" : "native gold low"); return result;
}
std::int32_t Soldiers(void *) { return 1647; }
std::int64_t *MonthlyFraction(void *,std::int64_t *out) { *out=25000; return out; }
std::int32_t MonthsToFull(void *) { return 4; }
bool CanReplenish(void *,void *) { return true; }
bool ChunkCanReplenish(void *) { return true; }
bool MercCanHire(void *c,void *a,std::uint32_t mode,void *reason) {
  Check(c == company.data() && a == actor.data() && mode == std::uint32_t{1},
        "merc native final gate receives ordinary mode1");
  Reason(reason, ""); return true;
}
std::int64_t *MercCost(void *, std::int64_t *out, void *, std::int32_t landstate) {
  Check(landstate == std::int32_t{7}, "current landstate reaches cost getter");
  const std::array<std::int64_t,10> costs{42000000,-50000,0,1,2,3,4,5,6,7};
  std::memcpy(out,costs.data(),sizeof(costs)); return out;
}
std::int32_t Payment(void *,void *,std::uint32_t mode) {
  Check(mode == std::uint32_t{1}, "payment status uses ordinary mode"); return 1;
}
std::int64_t Duration(void *,void *) { return 36; }
bool ReadMemory(void *,const void *source,void *dest,std::size_t bytes) {
  if (!source) return false; std::memcpy(dest,source,bytes); return true;
}
const void *ResolveTitle(void *,std::int32_t id) {
  return id == std::int32_t{2142} ? title.data() : nullptr;
}
const void *ResolveProvince(void *,std::int32_t id) {
  if (id == std::int32_t{2640}) return home.data();
  return id == std::int32_t{2604} ? selected.data() : nullptr;
}
const void *TitleProvince(const void *t) {
  Check(t == title.data(), "position uses the actual company title"); return home.data();
}
std::int32_t SelectProvince(const void *a) {
  Check(a == actor.data(), "position selector receives current actor");
  ++selector_calls; return 2604;
}
void *DeleteCommand(void *owned,std::uint32_t flags) {
  Check(flags == std::uint32_t{1}, "command uses native deleting-destructor convention");
  ++deletes; delete static_cast<Command *>(owned); return nullptr;
}
void **Clone(const void *source,void **returned) {
  ++clones; auto *copy = new Command{};
  std::memcpy(copy->data(),source,copy->size()); *returned = copy; return returned;
}
bool Queue(void *manager,void **owned,std::uint32_t flags) {
  Check(manager == &queues && flags == std::uint32_t{0x0E}, "actual ordinary queue channel");
  Check(*owned != nullptr, "queue receives one owning native pointer");
  ++queues; DeleteCommand(*owned,std::uint32_t{1}); *owned=nullptr; return true;
}
bool Validate(const void *command,void *reason) {
  Check(reason == nullptr && Get<std::uint32_t>(command,0x20) == std::uint32_t{29829},
        "command validator receives actual player ID and null text sink");
  const auto mode=Get<std::uint32_t>(command,0x28);
  Check((mode == std::uint32_t{3} && Get<std::uint32_t>(command,0x24)==kOrder) ||
        (mode == std::uint32_t{1} && Get<std::uint32_t>(command,0x24)==kCompany),
        "typed source retains complete selected ID and native ordinary mode");
  return true;
}
void *Factory() {
  auto *c=new Command{};
  Put(c->data(),0,primary.data()); Put(c->data(),0x18,secondary.data());
  Put(c->data(),0x20,UINT32_MAX); Put(c->data(),0x24,UINT32_MAX);
  Put(c->data(),0x28,std::uint32_t{1}); return c;
}
} // namespace

int main(int argc,char **argv) {
  try {
    Check(argc == 2,"new fixture requires one output JSON path");
    Put(actor.data(),0x18,kActor);
    Put(actor.data(),0x1C,std::uint32_t{0x43686172});
    Put(actor.data(),0x1C0,static_cast<const void *>(realm.data()));
    Put(realm.data(),0x1D0,std::int32_t{7});
    Put(realm.data(),0x324,std::int32_t{0});
    Put(order.data(),0x10,kOrder); Put(order.data(),0x14,std::uint32_t{0x486F4F72});
    Put(order.data(),0x24,std::uint32_t{23}); Put(order.data(),0x40,std::uint32_t{35131});
    Put(order.data(),0x80,UINT32_MAX);
    Put(company.data(),0x10,kCompany); Put(company.data(),0x14,std::uint32_t{0x4D657263});
    Put(company.data(),0x24,std::int32_t{2142}); Put(company.data(),0x48,UINT32_MAX);
    Put(holy_manager.data(),0x20,static_cast<const void *>(holy_entries.data()));
    Put(holy_manager.data(),0x2C,std::int32_t{1}); Put(holy_entries.data(),8,static_cast<void *>(order.data()));
    Put(merc_manager.data(),0x20,static_cast<const void *>(merc_entries.data()));
    Put(merc_manager.data(),0x2C,std::int32_t{1}); Put(merc_entries.data(),8,static_cast<void *>(company.data()));
    Put(title.data(),0x10,std::int32_t{2142});
    Put(home.data(),0x10,std::int32_t{2640}); Put(selected.data(),0x10,std::int32_t{2604});
    Put(home.data(),0x85C,std::uint32_t{0x50726F76}); Put(selected.data(),0x85C,std::uint32_t{0x50726F76});
    primary[0]=reinterpret_cast<void *>(&DeleteCommand);
    primary[8]=reinterpret_cast<void *>(&Clone);
    xar::ck3_12002::CommandBindings commands{};
    commands.enabled=true; commands.command_manager=&queues; commands.queue_owned_command=&Queue;
    holy::Bindings hb{};
    hb.enabled=true; hb.manager_slot=&holy_manager_pointer; hb.fallback_slot=&fallback_pointer;
    hb.patron=&Patron; hb.is_military=&Military; hb.can_hire=&HolyCanHire;
    hb.cost=&HolyCost; hb.can_afford=&Afford; hb.reason_destroy=&DestroyReason; hb.current_soldiers=&Soldiers;
    // This whole current query retains an available empty persistent roster.
    // Callback bindings are synthetic; no EXE getter execution is claimed.
    hb.current_reinforcement={true,&regi_storage_pointer,&MonthlyFraction,
        &MonthsToFull,&CanReplenish,&ChunkCanReplenish,
        &regi_storage_pointer,&regi_storage_pointer};
    xar::ck3_12003::PlayerHolyOrderMailboxContext12003 hq{};
    Check(holy::ReadPlayerHolyOrderContext12003(hb,actor.data(),kActor,kDate,kEpoch,hq.observation),
          "whole holy query uses production reader");
    hq.completed=true; hq.envelope.frame_stable=true;
    hq.envelope.expected_snapshot_revision=kRevision; hq.envelope.expected_snapshot.date_raw=kDate;
    merc::ContextBindings mb{};
    mb.candidates={true,&merc_manager_pointer,&fallback_pointer,&Soldiers};
    mb.final_terms={true,&MercCanHire,&MercCost,&Payment,&Afford,&Duration,&DestroyReason};
    mb.composition={true,&regi_storage_pointer,&fallback_pointer,&Patron};
    mb.position={&TitleProvince,&SelectProvince};
    mb.position.skip_selector_when_no_active_wars=true;
    mb.world={nullptr,&ReadMemory,&ResolveTitle,&ResolveProvince};
    merc::Context mq{};
    Check(merc::ReadPlayerMercenaryContext12003(mb,actor.data(),kActor,kDate,kEpoch,mq),
          "whole merc query uses production reader");
    holy::HireActionBindings ha{};
    ha.enabled=true; ha.context=hb; ha.commands=commands;
    ha.primary_vtable=reinterpret_cast<std::uintptr_t>(primary.data());
    ha.secondary_vtable=reinterpret_cast<std::uintptr_t>(secondary.data()); ha.validate_source=&Validate;
    holy::HireActionResult hr{};
    Check(holy::ApplyHolyOrderHire12003(ha,actor.data(),kActor,kOrder,kDate,kEpoch,hr)==holy::HireActionStatus::submitted,
          "ordinary holy provider remains pending native queue ACK");
    merc::HireActionBindings ma{};
    ma.enabled=true; ma.candidates=mb.candidates; ma.final_terms=mb.final_terms;
    ma.commands=commands; ma.create_default=&Factory; ma.validate_source=&Validate;
    merc::HireActionResult mr{};
    Check(merc::ApplyMercenaryHire12003(ma,actor.data(),kActor,kCompany,mr)==merc::HireActionStatus::submitted,
          "ordinary merc provider supports native debt status independently of affordability");
    Check(hr.verification_pending && mr.verification_pending && queues==2 && clones==2 && deletes==3,
          "two ordinary ACKs keep pending poststate and owning lifetime");
    Check(selector_calls==0,"actual4 zero-war auto-raise position is known unattempted");
    const auto descriptor=xar::game::Ck3_12004AdapterDescriptor();
    const auto render=[&](std::string value) { return xar::game::Render12004BuildIdentity(std::move(value),descriptor); };
    const std::array<std::string,4> samples{
      render(xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(hq,"g2-read-holy-12004")),
      render(merc::SerializePlayerMercenaryContextResultV1(mq,"merc-query-12004",2,kRevision)),
      xar::ck3_12004::religion::holy_order::SerializeHolyOrderHireResult12004(
          hr,"holy-hire-12004",3,kRevision,kDate,descriptor),
      render(xar::ck3_12003::SerializeMercenaryHireResultV1(mr,"merc-hire-12004",4,kRevision,kDate))};
    std::ofstream out(argv[1],std::ios::binary);
    out << "{\"fixture_provenance\":\"synthetic native callbacks/game memory; genuine production readers/providers/serializers and actual4 identity renderer; no EXE callable or live execution\",\"samples\":[";
    for(std::size_t i=0;i<samples.size();++i) { if(i) out << ','; out << samples[i]; }
    out << "]}\n"; Check(out.good(),"write one genuine whole producer document");
    std::cout << "GREEN " << checks << " checks;4 whole command_result samples;synthetic world/callbacks\n";
    return 0;
  } catch(const std::exception &e) { std::cerr << "RED " << e.what() << '\n'; return 1; }
}
