#define main ExistingRouterIdentityMainNotCalled
#include "ck3_12004_faction_gift_raw_identity_whole_test.cpp"
#undef main

namespace {
int negative_checks=0, validator_calls=0;
void Require(bool value,const char *reason) {
  ++negative_checks;if(!value)throw std::runtime_error(reason);
}
bool DenySecondValidation(void *,void *error) {
  Require(error==nullptr,"validator diagnostic sink");
  ++validator_calls;return validator_calls!=2;
}
std::string SubmitPayload() {
  return FramePayload(1)+",\"source_faction_id\":"+std::to_string(source_id)+
    ",\"recipient_character_id\":"+std::to_string(recipient_id)+
    ",\"membership_role\":\"leader\",\"definition_stable_hash\":"+std::to_string(definition_hash)+
    ",\"gold_cost_raw\":7500000,\"opinion_delta\":35,\"minimum_gold_reserve_raw\":5000000,\"expected_native_revision\":1}";
}
}

int main(int argc,char **argv) {
 try {
  if(argc!=4)return 90;
  actor_id=static_cast<std::uint32_t>(std::stoul(argv[1]));
  recipient_id=static_cast<std::uint32_t>(std::stoul(argv[2]));
  const std::filesystem::path out=argv[3];std::filesystem::create_directories(out);
  Fixture fixture;RouterAdapter adapter;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};mailbox.offline_fixture=true;
  mailbox.permitted_executor_quattuortrigintary=&ExecuteFactionGiftPrivateMailbox12004;
  FactionGiftPrivateFixtureBindings12004 bindings{};
  bindings.factions=fixture.factions;bindings.gift=fixture.b;
  bindings.context=&fixture;bindings.read_campaign=&RootSource;bindings.read_alerts=&AlertSource;
  const auto frame=[&](std::string_view actor) {
    return std::string("{\"expected_revision\":1,\"expected_date_raw\":53175816,\"expected_player_character_id\":")+std::string(actor);
  };
  struct Token {const char *name;const char *value;};
  const Token tokens[]={{"sentinel","4294967295"},{"overflow","4294967296"},{"public-minus-one","-1"},{"public-signed","-2147483648"},{"boolean","true"},{"float","0.0"},{"string","\"0\""}};
  int rejections=0;
  const auto reject=[&](std::string_view name,std::string_view step,const std::string &payload,const char *expected_failure) {
    FactionGiftPrivateState12004 fresh;std::string wire,failure;
    const bool handled=HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,step,payload,"identity-control",fresh,wire,failure,&bindings);
    Require(!handled&&failure==expected_failure,"malformed private token must reject at its real boundary");
    Require(queues==0&&clones==0,"invalid private request must not queue");
    std::ofstream(out/(std::string(name)+".request.json"))<<payload<<'\n';
    std::ofstream(out/(std::string(name)+".failure.txt"))<<failure<<'\n';++rejections;
  };
  for(const auto &t:tokens) {
    reject(std::string("actor-")+t.name,ck3_11906::kFactionGiftPrivateQueryStepV1,frame(t.value)+"}","private_faction_frame_invalid");
    reject(std::string("recipient-")+t.name,ck3_11906::kFactionGiftPrivateColdRecoveryStepV1,FramePayload(1)+",\"source_faction_id\":"+std::to_string(source_id)+",\"recipient_character_id\":"+t.value+"}","private_faction_cold_frame_or_identity_invalid");
  }
  reject("actor-missing",ck3_11906::kFactionGiftPrivateQueryStepV1,"{\"expected_revision\":1,\"expected_date_raw\":53175816}","private_faction_frame_invalid");
  reject("recipient-missing",ck3_11906::kFactionGiftPrivateColdRecoveryStepV1,FramePayload(1)+",\"source_faction_id\":"+std::to_string(source_id)+"}","private_faction_cold_frame_or_identity_invalid");
  reject("source-zero",ck3_11906::kFactionGiftPrivateColdRecoveryStepV1,FramePayload(1)+",\"source_faction_id\":0,\"recipient_character_id\":"+std::to_string(recipient_id)+"}","private_faction_cold_frame_or_identity_invalid");
  reject("actor-generation",ck3_11906::kFactionGiftPrivateQueryStepV1,frame(std::to_string(actor_id^0x01000000U))+"}","private_faction_frame_invalid");
  auto stale=FramePayload(1)+"}";stale.replace(stale.find("53175816"),8,"53175817");
  reject("date-drift",ck3_11906::kFactionGiftPrivateQueryStepV1,stale,"private_faction_frame_invalid");
  std::string wire,failure;FactionGiftPrivateState12004 state;
  Require(HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,ck3_11906::kFactionGiftPrivateQueryStepV1,FramePayload(1)+"}","before-validator",state,wire,failure,&bindings),"legitimate private query");
  validator_calls=0;bindings.gift.interaction.validate=&DenySecondValidation;
  Require(HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,ck3_11906::kFactionGiftPrivateSubmitStepV1,SubmitPayload(),"denied-final-validator",state,wire,failure,&bindings),"native negative is a complete action reply");
  Require(validator_calls==2&&queues==0&&!state.pending_ack&&!state.action_may_have_submitted,"actual final validator denial precedes claim/queue");
  Require(wire.find("native_validation_failed")!=std::string::npos,"final validator reason preserved");
  WriteWire(out,"final-validator-negative.json",wire);
  state={};bindings.gift.interaction.validate=&Validate;
  Require(HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,ck3_11906::kFactionGiftPrivateQueryStepV1,FramePayload(1)+"}","before-claim",state,wire,failure,&bindings),"legitimate query before claim conflict");
  state.claimed_idempotency_keys.insert("already-claimed");
  Require(HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,ck3_11906::kFactionGiftPrivateSubmitStepV1,SubmitPayload(),"already-claimed",state,wire,failure,&bindings),"claim rejection is a complete action reply");
  Require(queues==0&&!state.pending_ack&&!state.action_may_have_submitted&&wire.find("idempotency_key_already_claimed")!=std::string::npos,"once-only claim remains required");
  WriteWire(out,"claim-conflict.json",wire);
  state={};other_payer=true;
  Require(!HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,ck3_11906::kFactionGiftPrivateQueryStepV1,FramePayload(1)+"}","wrong-context-payer",state,wire,failure,&bindings),"redirected payer must not become an eligible preview");
  Require(failure=="private_faction_native_observation_unavailable"&&queues==0,"context payer identity readback retained");other_payer=false;
  Put(fixture.characters[1].data(),0x18,recipient_id^0x01000000U);
  state={};
  Require(!HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,1,ck3_11906::kFactionGiftPrivateQueryStepV1,FramePayload(1)+"}","stale-full-recipient",state,wire,failure,&bindings),"stale full recipient cannot resolve by index");
  Require(queues==0&&clones==0,"all negative controls keep queue empty");
  std::ofstream(out/"SUMMARY.json")<<"{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\",\"software_fixture\":true,\"actor_raw_bits\":"<<actor_id<<",\"recipient_raw_bits\":"<<recipient_id<<",\"malformed_rejections\":"<<rejections<<",\"checks\":"<<negative_checks<<",\"queue_calls\":"<<queues<<"}\n";
  std::cout<<"PASS malformed="<<rejections<<" checks="<<negative_checks<<" queues="<<queues<<'\n';return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
