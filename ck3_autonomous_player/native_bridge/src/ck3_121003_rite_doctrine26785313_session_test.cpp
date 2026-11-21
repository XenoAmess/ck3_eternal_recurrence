#include "ck3_1210_core.cpp"
#include "ck3_1210_core_frame_v1.cpp"
#include "ck3_121003_rite_doctrine26785313_v1.cpp"
#include <iostream>
#include <fstream>
#include <stdexcept>
namespace f=xar::ck3_121003::build26785313;
namespace {
void Check(bool value,const char*why){if(!value)throw std::runtime_error(why);}
f::RiteDoctrineRequest267V1 Request(std::string_view id,f::RiteDoctrineAction267V1 action=f::RiteDoctrineAction267V1::select_dynastic) {
 f::RiteDoctrineRequest267V1 r;std::copy(id.begin(),id.end(),r.request_id.begin());r.request_id_size=static_cast<std::uint8_t>(id.size());
 r.action=action;r.expected_source_rite_id=152;r.provider_generation=7;r.query_sequence=11;
 r.window.window_name="rite_creation_window";r.window.deadline_unix_ms=4102444800000;r.window.expected_core.clock={53144376,1,true};
 r.window.expected_core.local_player_id=1;r.window.expected_core.map_ready=true;r.window.expected_core.has_played_character=true;
 r.window.expected_core.played_character_id=-16777215;r.window.expected_core.played_character_alive=true;return r;
}
f::RiteClaimSource Source(const f::RiteDoctrineRequest267V1&r) {return {0x1000,0x2000,r.expected_source_rite_id,r.window.expected_core};}
}
int main(int argc,[[maybe_unused]]char**argv){try {
 using Decision=f::RiteClaimDecision;using Status=f::RiteDoctrineStatus267V1;using Action=f::RiteDoctrineAction267V1;
 {f::RiteClaimBook book;auto r=Request("select-original");auto source=Source(r);
  Check(book.Inspect(r,source)==Decision::ready,"new record has no fabricated dispatch");
  const auto sequence=book.ClaimOnce(r,source);Check(sequence==1,"one retained original sequence");book.Finish(sequence,Status::draft_selected);
  Check(book.Inspect(r,source)==Decision::consumed,"original ID never replays");
  auto changed=Request("select-new-id");changed.provider_generation=999;changed.query_sequence=999;
  source.core.clock.speed=5;changed.window.expected_core.clock.speed=5;
  Check(book.Inspect(changed,source)==Decision::consumed,"new ID/connection lease/speed cannot replay same actor-day effect");
  auto confirm=Request("confirm-new-intent",Action::confirm_edit);
  Check(book.Inspect(confirm,source)==Decision::ready,"fresh separate confirmation action is not a selector replay");
  const auto confirmation=book.ClaimOnce(confirm,source);Check(confirmation==2,"fresh separate action receives its own record");
  book.Finish(confirmation,Status::indeterminate);
  auto later=Request("later-different-day");auto later_source=Source(later);later_source.core.clock.date_raw+=24;
  Check(book.Inspect(later,later_source)==Decision::unknown,"unknown survives new ID, date, intent and query generation");
  book.Finish(1,Status::draft_selected);Check(book.Inspect(later,later_source)==Decision::unknown,"a known old record cannot clear sticky unknown");}
 {f::RiteClaimBook book;
  for(std::size_t i=0;i<f::kRiteDoctrineMaximumClaims267V1;++i) {
   auto r=Request("claim-"+std::to_string(i));auto source=Source(r);source.core.clock.date_raw+=static_cast<std::int32_t>(24*i);
   const auto sequence=book.ClaimOnce(r,source);Check(sequence==i+1,"bounded retained records never evict earlier IDs");book.Finish(sequence,Status::draft_selected);
  }
  auto r=Request("capacity-next");auto source=Source(r);source.core.clock.date_raw+=24*64;
  Check(book.Inspect(r,source)==Decision::capacity_exhausted&&!book.ClaimOnce(r,source),"capacity refuses new action instead of discarding history");
  auto original=Request("claim-0");Check(book.Inspect(original,Source(original))==Decision::consumed,"first original remains protected at capacity");}
 {f::RiteClaimBook book;book.Finish(123,Status::confirmation_dispatched);auto r=Request("unknown-invalid-sequence");Check(book.Inspect(r,Source(r))==Decision::unknown,"invalid completion sequence cannot produce a known post-state");}
 Check(!f::ExecuteRiteDoctrineOnOwner267V1(nullptr,{}),"missing actual owner context rejects");
 f::RiteDoctrineSession267V1 session;f::RiteDoctrineContext267V1 q;q.session=&session;q.request=Request("nogame-no-authority");
 f::ArmRiteDoctrineDeadline267V1(q);Check(f::ExecuteRiteDoctrineOnOwner267V1(&q,{})&&!q.result.effect_attempted&&q.result.status==Status::unavailable,"NoGame cannot turn request/claim data into native owner permission");
 Check(q.result.provider_generation==q.request.provider_generation&&q.result.query_sequence==q.request.query_sequence&&q.result.claim_sequence==0,"known early refusal echoes original lease without granting a claim");
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
 const auto image=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
 Check(!f::BindDoctrineSelectImage267V1(image,f::kExecutableSha256).exact_image_verified,"ordinary registered test EXE is not the current CK3 primary module");
 const auto disabled=f::BindReadonlyImage(image,f::kExecutableSha256);
 const auto call=f::CallRawSelectDoctrine267V1(disabled,{},0,0);Check(!call.effect_attempted&&call.status==f::RawDoctrineSelectDispatch267V1::unavailable,"unverified ABI primitive never calls a guessed target");
 if(argc==3&&std::string_view(argv[1])=="--emit-owner-refusal") {
  f::RiteDoctrineContext267V1 refused;refused.session=&session;refused.request=Request("rite-doctrine-qa-1");
  refused.request.provider_generation=18446744073709551615ULL;refused.request.query_sequence=18446744073709551615ULL;
  f::ArmRiteDoctrineDeadline267V1(refused);Check(f::ExecuteRiteDoctrineOnOwner267V1(&refused,{})&&!refused.result.effect_attempted&&!refused.result.native_returned&&refused.result.claim_sequence==0,"actual fixed ON executor refuses missing live game without entering native effect");
  std::ofstream out(argv[2],std::ios::binary);Check(bool(out),"owner refusal output open");out<<f::SerializeRiteDoctrineResult267V1(refused.request.id(),refused.result)<<'\n';Check(bool(out),"owner refusal output write");
 }else Check(argc==1,"no args or bounded NoGame refusal output mode");
#else
 Check(argc==1,"OFF contract accepts no native invocation mode");
#endif
 std::cout<<"PASS retained actor-day once/UNKNOWN/capacity and NoGame owner refusal; Native predicates/selection/confirmation NOT_RUN\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
