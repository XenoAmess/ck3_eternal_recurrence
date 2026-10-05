#include "xar_bridge/ck3_12002_pending_context.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t kPending = 1946157063;
constexpr std::int32_t kActor = 34180;
constexpr std::int32_t kPlayer = 29829;
constexpr std::int32_t kPrisoner = 61540;
constexpr std::array<std::int32_t, 9> kFlags{
    34732, 34724, 7457, 34723, 22491, 19544, 31144, 34738, 49};
constexpr std::array<std::string_view, 9> kKeys{
    "extortionate_gold", "extortionate_current_gold", "gold", "current_gold",
    "favor", "influence_send_option", "herd_send_option", "current_herd", "hook"};

template<class Buffer, class T>
void Store(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data()+offset, &value, sizeof(value));
}
struct Fixture {
  std::array<std::byte, 0x40> pending_storage{}, character_storage{};
  std::array<std::byte, 0x80> pending_slots{};
  std::vector<std::byte> character_slots = std::vector<std::byte>(61541*0x10);
  std::array<std::byte, 0x5C8> pending{};
  std::array<std::byte, 0x2720> definition{};
  std::array<std::byte, 0x220> actor{}, player{}, prisoner{};
  std::array<std::byte, 0x300> extension{};
  std::array<std::byte, 0x10> relation{};
  std::vector<std::byte> rows = std::vector<std::byte>(9*0x730);
  std::array<std::uint8_t, 9> selected{0,0,1,0,0,0,0,0,0};
  void *pending_storage_pointer = pending_storage.data();
  void *character_storage_pointer = character_storage.data();
  std::int32_t expiration_days = 60;
  int named_calls = 0;
  int flag_calls = 0;
  Fixture() {
    Store(pending_storage,0x20,static_cast<void *>(pending_slots.data()));
    Store(pending_storage,0x2C,std::int32_t{8});
    Store(pending_slots,7*0x10+8,static_cast<void *>(pending.data()));
    Store(character_storage,0x20,static_cast<void *>(character_slots.data()));
    Store(character_storage,0x2C,std::int32_t{61541});
    Store(character_slots,kActor*0x10+8,static_cast<void *>(actor.data()));
    Store(character_slots,kPlayer*0x10+8,static_cast<void *>(player.data()));
    Store(character_slots,kPrisoner*0x10+8,static_cast<void *>(prisoner.data()));
    Store(actor,0x18,kActor); Store(player,0x18,kPlayer);
    Store(prisoner,0x18,kPrisoner);
    Store(prisoner,0x1B0,static_cast<void *>(extension.data()));
    Store(extension,0x288,static_cast<void *>(relation.data()));
    Store(relation,0,kPlayer);
    Store(pending,0x10,kPending);
    Store(pending,0x18,static_cast<void *>(definition.data()));
    Store(pending,0x2F0,kActor); Store(pending,0x2F4,kPlayer);
    Store(pending,0x2F8,std::int32_t{-1}); Store(pending,0x2FC,kPrisoner);
    Store(pending,0x300,std::int32_t{-1});
    Store(pending,0x318,static_cast<void *>(selected.data()));
    Store(pending,0x320,std::int32_t{9}); Store(pending,0x324,std::int32_t{9});
    Store(pending,0x5B8,std::int32_t{2});
    Store(definition,0x10,std::int32_t{184});
    Store(definition,0x14,std::uint32_t{2840579925});
    Store(definition,0x2258,static_cast<void *>(rows.data()));
    Store(definition,0x2264,std::int32_t{9});
    for (std::size_t i=0;i<9;++i) Store(rows,i*0x730+0x368,kFlags[i]);
  }
};
bool Capture(void *, xar::game::PendingCharacterInteractionFrameV1 &out) noexcept {
  out = {894,53275704,true,true}; return true;
}
bool MainThread(void *) noexcept { return true; }
bool Memory(void *, const void *address, void *out, std::size_t size) noexcept {
  std::memcpy(out,address,size); return true;
}
bool String(void *context,const void *address,std::string &out) noexcept {
  auto &f=*static_cast<Fixture *>(context);
  if (address!=f.definition.data()+0x18) return false;
  out="pay_ransom_interaction"; return true;
}
bool NativeRoute(void *,void *) { return true; }
bool NativeValidator(void *) { return true; }
bool NativeTrigger(void *,const void *) { return true; }
void NativeCost(const void *,const void *,std::int64_t *) {}
void *NativeWar(void *,void *) { return nullptr; }
void *NativeRegistry() { return nullptr; }
const std::string *NativeIdentifier(std::int32_t) { return nullptr; }
bool Route(void *context,NativePendingInteractionLocalRoutingV1,
           void *pending,void *player,bool &out) noexcept {
  auto &f=*static_cast<Fixture *>(context);
  out=pending==f.pending.data()&&player==f.player.data(); return true;
}
bool Validator(void *,NativePendingInteractionReplyValidatorV1,
               void *,bool &out) noexcept { out=true; return true; }
bool Trigger(void *context,NativePendingInteractionTriggerEvaluatorV1,
             void *trigger,const void *scope,bool &out) noexcept {
  auto &f=*static_cast<Fixture *>(context);
  if (scope!=f.pending.data()+0x20) return false;
  for(std::size_t i=0;i<9;++i) {
    if(trigger==f.rows.data()+i*0x730+0xD0) {
      out=i==2||i==4||i==5||i==8; return true;
    }
    if(trigger==f.rows.data()+i*0x730) {out=i==2||i==4; return true;}
  }
  return false;
}
bool Cost(void *,NativePendingInteractionCostEvaluatorV1,const void *,const void *,
          std::array<std::int64_t,10> &out) noexcept {out.fill(0);return true;}
bool War(void *,NativePendingInteractionCommonWarRelationV1,
         void *,void *,void *&out) noexcept {out=nullptr;return true;}
bool ActiveWar(void *,std::int32_t,void *&out) noexcept {out=nullptr;return false;}
bool Registry(void *,NativePendingInteractionTargetTypeRegistryGetterV1,
              void *&out) noexcept {out=nullptr;return false;}
bool Identifier(void *,NativePendingInteractionScriptIdentifierNameV1,
                std::int32_t,const std::string *&out) noexcept {out=nullptr;return false;}
bool Flag(void *context,std::uintptr_t,std::string_view key,std::int32_t &out) noexcept {
  auto &f=*static_cast<Fixture *>(context);++f.flag_calls;
  for(std::size_t i=0;i<9;++i) if(key==kKeys[i]) {out=kFlags[i];return true;}
  return false;
}
bool NamedGold(void *context,std::uintptr_t,const void *scope,std::int32_t actor,
               std::int32_t jailer,std::int32_t prisoner,std::int64_t &out) noexcept {
  auto &f=*static_cast<Fixture *>(context);++f.named_calls;
  if(scope!=f.pending.data()+0x20||actor!=kActor||jailer!=kPlayer||prisoner!=kPrisoner)
    return false;
  // Synthetic native evaluator result, never a claim about the live R0047 amount.
  out=1250000;return true;
}
}

int main(int argc,char **argv) {
  Fixture fixture;
  PendingCharacterInteractionNativeEnvironmentV1 env{};
  env.exact_build_admitted=true;env.offline_fixture_function_overrides=true;
  env.pending_storage_slot=&fixture.pending_storage_pointer;
  env.character_storage_slot=&fixture.character_storage_pointer;
  env.expiration_days=&fixture.expiration_days;
  env.local_routing=NativeRoute;env.reply_validator=NativeValidator;
  env.trigger_evaluator=NativeTrigger;env.cost_evaluator=NativeCost;
  env.common_war_relation=NativeWar;env.target_type_registry=NativeRegistry;
  env.script_identifier_name=NativeIdentifier;
  env.reply_primary_vtable=0x11111111;env.reply_secondary_vtable=0x22222222;
  env.war_victory_special_vtable=0x33333331;
  env.war_white_peace_special_vtable=0x33333332;
  env.war_defeat_special_vtable=0x33333333;
  PendingCharacterInteractionAccessV1 access{};
  access.context=&fixture;access.capture_frame=Capture;access.is_main_thread=MainThread;
  access.read_memory=Memory;access.read_string=String;
  access.invoke_local_routing=Route;access.invoke_reply_validator=Validator;
  access.invoke_trigger_evaluator=Trigger;access.invoke_cost_evaluator=Cost;
  access.invoke_common_war_relation=War;access.resolve_active_war=ActiveWar;
  access.invoke_target_type_registry=Registry;access.invoke_script_identifier_name=Identifier;
  access.read_ransom_flag_identifier=Flag;access.read_ransom_named_gold=NamedGold;
  xar::game::PendingCharacterInteractionContextV1 context{};
  const auto result=ReadPendingCharacterInteractionContextV1(
      env,access,{894,kPending,kPlayer},context);
  if(result!=xar::game::ReadPendingCharacterInteractionContextResultV1::available ||
     !context.terms || !context.terms->ransom_quote ||
     context.terms->ransom_quote->gold_raw!=1250000 ||
     !context.terms->ransom_quote->decision_input_ready ||
     context.readiness.interaction_semantic_decision_ready ||
     fixture.named_calls!=2 || fixture.flag_calls!=18) return 1;
  const auto wire=xar::game::RenderCrozierBuildIdentity(
      SerializePendingCharacterInteractionContextV1(context),
      xar::game::Ck3_12003AdapterDescriptor());
  if(wire.empty()||wire.find("\"ransom_quote\"")==std::string::npos) return 2;
  std::ofstream output(argc>1?argv[1]:"ck3_12003_pending_ransom_quote_wire.json",
                       std::ios::binary);
  output<<wire<<'\n';output.close();
  if(!output) return 3;
  std::cout<<"GREEN one received R0047 ordinary-gold quote fixture; synthetic amount; two stable observations\n";
  return 0;
}
