#include "xar_bridge/rite_creation_actions12004.hpp"
#include <cstdio>
#include <stdexcept>

using namespace xar::ck3_12004::religion::rite_creation_actions;
namespace {
void Require(bool value,const char*why){if(!value)throw std::runtime_error(why);}
}
int main(){
 try{
  Request q{};q.expected_source_rite_id=13;
  Require(ValidateRequest(q),"finite read-only preview accepted");
  q.expected_source_rite_id=absent;Require(!ValidateRequest(q),"absent full source rejected");q.expected_source_rite_id=13;
  q.operation=static_cast<Operation>(999);Require(!ValidateRequest(q),"unknown operation rejected");
  q.operation=Operation::set_name_field;q.name_field=NameField::name;q.text="short";
  Require(ValidateRequest(q),"SSO input accepted");
  q.text="a native long UTF-8 name";Require(ValidateRequest(q),"borrowed long input accepted");
  q.text=std::string(31,'x');Require(!ValidateRequest(q),"stock name character limit retained");
  q.text=std::string("a\0b",3);Require(!ValidateRequest(q),"embedded NUL rejected before native scan");
  q.text="\xC0\xAF";Require(!ValidateRequest(q),"overlong UTF-8 rejected");
  q.text="line\nline";Require(!ValidateRequest(q),"single-line name newline rejected");
  q.name_field=NameField::description;Require(ValidateRequest(q),"stock multiline description accepted");
  q.text=std::string(241,'x');Require(!ValidateRequest(q),"stock description character limit retained");
  q={};q.expected_source_rite_id=13;q.operation=Operation::select_core_tenet;
  q.core_slot_index=0;q.tenet_key="tenet_adaptive";Require(ValidateRequest(q),"typed core selector accepted");
  q.core_slot_index=64;Require(!ValidateRequest(q),"unbounded slot rejected before materializer");
  q.core_slot_index=0;q.tenet_key="not/a/key";Require(!ValidateRequest(q),"arbitrary selector rejected");
  q={};q.expected_source_rite_id=13;q.operation=Operation::prepare_confirmation;
  q.expected_outcome_kind=Outcome::create_rite;q.expected_preview_identity=std::string(64,'a');
  Require(ValidateRequest(q),"prepare requires explicit native-outcome expectation and opaque proof");
  q.expected_outcome_kind.reset();Require(!ValidateRequest(q),"missing outcome assertion rejected");
  q.expected_outcome_kind=Outcome::edit_rite;q.operation=Operation::confirm_once;
  Require(!ValidateRequest(q),"confirm without durable action identity rejected");
  q.action_id="episode-source-intent-1";Require(ValidateRequest(q),"finite confirmation contract accepted");
  q.expected_preview_identity[0]='G';Require(!ValidateRequest(q),"malformed proof rejected");
  // No native game/GUI is constructed. This file is a future C++ fixture;
  // current V5 policy forbids compiling or claiming its execution.
  std::puts("rite creation request contract checks passed");return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"FAIL %s\n",e.what());return 1;}
}
