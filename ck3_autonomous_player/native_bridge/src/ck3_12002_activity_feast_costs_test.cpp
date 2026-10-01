#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"
#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"
#include "ck3_12002_activity_feast_cost_private_transport_v1.hpp"

#define main LegacyActivityGoldFixtureMain
#include "activity_stage5_gold_cost_v1_test.cpp"
#undef main

#include <cstdio>

namespace {

void Populate12002(Fixture &f) {
  Populate(f);
  f.Put(kBase + 0x11B2885,
      std::array<std::uint8_t,8>{0x49,0x89,0xB4,0x24,0xA0,0,0,0});
  f.Put(kBase + 0x21603AA,
      std::array<std::uint8_t,4>{0x48,0x8B,0x59,0x60});
  f.Put(kBase + 0x11B8693,
      std::array<std::uint8_t,7>{0x48,0x63,0x81,0xE8,0x1A,0,0});
  f.Put(kBase + 0x45325C8, kBase + 0x11B2E30);
  f.Put(kBase + 0x45325C8 + 7*8, kBase + 0x21603A0);
  f.Put(kBase + 0x45325C8 + 11*8, kBase + 0xB1F0A0);
  f.Put(kBase + 0x45325C8 + 12*8, kBase + 0x11B5B30);
  f.Put(kBase + 0x45326A0, kBase + 0x11D3404);
  f.Put(kBase + kActivityGetCostByName12002RvaV1,
      std::array<std::uint8_t,13>{0x48,0x89,0x5C,0x24,0x18,0x56,0x57,
                                0x41,0x56,0x48,0x83,0xEC,0x30});
  f.Put(kBase + kActivityGetCostIndexed12002RvaV1,
      std::array<std::uint8_t,4>{0x49,0x8B,0x0C,0xC6});
  f.Put(kBase + kActivityGoldLeaf12002RvaV1,
      std::array<std::uint8_t,7>{0x48,0x8B,0x80,0,1,0,0});
  f.Put(kBase + kActivityCostRefresh12002RvaV1,
      std::array<std::uint8_t,14>{0x48,0x89,0x5C,0x24,0x20,0x55,0x56,0x57,
                                0x41,0x54,0x41,0x55,0x41,0x56});
  f.Put(kBase + kActivityCostSlot12Return12002RvaV1 - 5,
      std::array<std::uint8_t,5>{0xE8,0x71,0x4B,0,0});
  f.Put(kBase + 0x5C6A520, kRoot);
  f.Put(kGfx, kBase + 0x44BC408);
  f.Put(kHandler, kBase + 0x44BA890);
  f.Put(kBase + 0x54DBC00, kActorId);
  f.Put(kBase + 0x5C67568, kStorage);
  f.Put(kBase + 0x5C67570, std::uintptr_t{0});
  f.Put(kActor + 0x1B0, kExtension);
  f.Put(kHandler + 0x3C0, kPlanner);
  f.Put(kHandler + 0x3E0, std::uintptr_t{0});
  f.Put(kHandler + 0x3D8, std::uintptr_t{0});
  f.Fill(kPlanner + 0x1500, 0x1B10 - 0x1500);
  f.Put(kPlanner, kBase + 0x45325C8);
  f.Put(kPlanner + 0x10, kBase + 0x45326A0);
  f.Put(kPlanner + 0xA0, kHandler);
  f.Put(kPlanner + 0x60, kWidget);
  f.Put(kPlanner + 0x1500, kType);
  f.Put(kPlanner + 0x1AE8, std::int32_t{5});
  for (std::size_t i=0;i<10;++i)
    f.Put(kPlanner + 0x1B10 + 0x50 + i*0x90 + 0x78,
          std::int64_t{i==0 ? 99900000 : 0});
  f.Put(kType, kBase + 0x48BFE50);
}

std::uintptr_t Cast12002(void *, std::uintptr_t source,
    std::uintptr_t from, std::uintptr_t to) noexcept {
  return source==kIdler && from==kBase+0x5514438 && to==kBase+0x5514460
      ? kGfx : 0;
}

bool Visible12002(void *, std::uintptr_t planner, std::uintptr_t entry,
    bool &out) noexcept {
  out=planner==kPlanner && entry==kBase+0x21603A0; return out;
}

struct FourCosts {
  Fixture *fixture;
  std::array<std::int64_t,4> values{18500000,0,-100000,3500000};
  std::array<std::uint32_t,4> indices{0,3,5,8};
  std::size_t calls=0;
  bool change_options=false;
  bool unknown_resource=false;
};

bool Named12002(void *opaque,std::uintptr_t base,std::uintptr_t breakdown,
    std::string_view key,std::uint32_t &index,std::int64_t &raw) noexcept {
  auto &f=*static_cast<FourCosts *>(opaque);
  if(base!=kBase || breakdown!=kPlanner+0x1B10 || f.calls>=4 ||
      key!=kActivityFeastCostKeysV1[f.calls]) return false;
  index=f.unknown_resource ? 10 : f.indices[f.calls];
  raw=f.values[f.calls++];
  if(f.change_options && f.calls==4) f.fixture->bytes[kPlanner+0x1600]^=1;
  return true;
}

} // namespace

int main() {
  Fixture f{}; Populate12002(f);
  ActivityCostSlot12ObserverV1 passive{};
  passive.environment={true,true,kActivityFeastCosts12002ExeSha256V1,
      kBase,&f,&Read,&ReadCostFrame};
  Expect(VerifyActivityCostSlot12ExactAbiV1(passive.environment));
  ActivityStage5FeastFullCostEnvironmentV1 env{};
  env.enabled=true; env.gold.enabled=true;
  env.gold.diagnostic={true,kActivityFeastCosts12002ExeSha256V1,kBase,&f,
      &Read,&ReadDiagFrame,&Cast12002,&Visible12002};
  env.gold.passive_cost=&passive;
  FourCosts named{&f}; env.invoke_named_cost=&Named12002;env.named_context=&named;
  auto result=ReadActivityStage5FeastFullCostV1(env,f.frame);
  Expect(result.gold_gate_status==ActivityStage5GoldCostStatusV1::no_normal_refresh);
  Expect(named.calls==0);
  Expect(!RecordActivityCostSlot12NormalReturnV1(passive,
      kBase+kActivityCostSlot12ReturnRvaV1,kPlanner));
  Expect(RecordActivityCostSlot12NormalReturnV1(passive,
      kBase+kActivityCostSlot12Return12002RvaV1,kPlanner));
  result=ReadActivityStage5FeastFullCostV1(env,f.frame);
  Expect(result.status==ActivityStage5FeastFullCostStatusV1::observed);
  Expect(result.configured_cost_raw==named.values && result.resource_indices==named.indices);
  Expect(result.actor_gold_raw==134000000 && result.scale==100000 && named.calls==4);
  Expect(result.configured_cost_raw[0]!=passive.latest.raw_aggregate[0]);
  xar::ck3_12002::ActivityStage5FeastFullCostPrivateQueryV1 query{};
  query.completed=true;query.cost=result;
  query.can_start.status=ActivityStage5CanStartStatusV1::observed;
  query.can_start.frame=result.frame;query.can_start.final_can_start=false;
  const auto payload=xar::ck3_12002::SerializeActivityStage5FeastFullCostPrivateV1(query);
  Expect(payload.find("\"barter_goods\"")!=std::string::npos);
  Expect(payload.find("\"configured_cost_raw\":-100000")!=std::string::npos);
  Expect(payload.find("\"final_can_start\":false")!=std::string::npos);
  std::puts(payload.c_str());
  named.calls=0;named.change_options=true;
  result=ReadActivityStage5FeastFullCostV1(env,f.frame);
  Expect(result.gold_gate_status==ActivityStage5GoldCostStatusV1::configuration_changed);
  Expect(result.configured_cost_raw==std::array<std::int64_t,4>{});
  named.change_options=false;f.bytes[kPlanner+0x1600]^=1;
  named.calls=0;named.unknown_resource=true;
  result=ReadActivityStage5FeastFullCostV1(env,f.frame);
  Expect(result.status==ActivityStage5FeastFullCostStatusV1::resource_unmapped);
  Expect(result.normal_refresh_sequence==0);
  named.unknown_resource=false;named.calls=0;
  f.Put(kActor+0x1B0,std::uintptr_t{0});
  result=ReadActivityStage5FeastFullCostV1(env,f.frame);
  Expect(result.status==ActivityStage5FeastFullCostStatusV1::observed && result.actor_gold_raw==0);
  f.Put(kActor+0x1B0,kExtension);f.Put(kPlanner+0x1AE8,std::int32_t{2});
  named.calls=0;
  result=ReadActivityStage5FeastFullCostV1(env,f.frame);
  Expect(result.gold_gate_status==ActivityStage5GoldCostStatusV1::not_feast_stage_five && named.calls==0);
  return 0;
}
