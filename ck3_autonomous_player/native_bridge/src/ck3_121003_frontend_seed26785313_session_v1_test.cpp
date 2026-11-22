// Actual owner/reader/wire code over a self-owned memory image and explicitly
// stubbed native entry addresses. No engine ABI or Game qualification is claimed.
#define XAR_FRONTEND_SEED_SELF_OWNED_TEST 1
#include "ck3_121003_frontend_seed26785313_test_fixture.hpp"
#define XAR_FRONTEND_SEED_CALL_ADDRESS(image,rva) xar::ck3_121003::build26785313::frontend_seed_test::CallAddress(image,rva)
#include "ck3_121003_frontend_menu26785313_wire_v1.cpp"
#include "ck3_121003_frontend_menu26785313_v1.cpp"
#include <iostream>
#include <filesystem>
#include <fstream>
namespace x=xar::ck3_121003::build26785313;
namespace t=x::frontend_seed_test;
namespace model {
t::FakeImage*f=nullptr;bool adapter=true;unsigned ids=0;
std::uintptr_t root=0,first=0,children=0;
void Gui(std::uintptr_t widget,std::uintptr_t parent,std::string_view name,unsigned slot,bool visible){
 auto&v=*f;const auto image=v.image;v.Put(widget,0,image+0x1000);v.Put(image+0x1000-8,0,image+0x2000);
 v.Put(image+0x2000,0,std::uint32_t{1});v.Put(image+0x2000,4,std::uint32_t{0});v.Put(image+0x2000,8,std::uint32_t{0});v.Put(image+0x2000,20,std::uint32_t{0x2000});v.Put(image+0x2000,16,std::uint32_t{0x3000});
 v.Put(image+0x3000,0,std::uint32_t{0});v.Put(image+0x3000,8,std::uint32_t{1});v.Put(image+0x3000,12,std::uint32_t{0x3100});v.Put(image+0x3100,0,std::uint32_t{0x3200});v.Put(image+0x3200,0,std::uint32_t{0x6082F78});v.Put(image+0x3200,8,std::int32_t{0});v.Put(image+0x3200,12,std::int32_t{-1});
 v.Put(widget,0xD0,std::uint32_t{visible?0U:8U});v.Put(widget,0xD8,v.context);v.Put(widget,0xE8,parent);v.Put(widget,0xF0,std::uintptr_t{0});v.Put(widget,0xF8,std::int32_t{0});v.Put(widget,0xFC,std::int32_t{0});v.Key(widget,0x1B8,name,slot);
}
void Init(t::FakeImage&v){f=&v;adapter=true;root=v.application+0x12000;first=root+0x400;children=root+0x800;
 v.Put(v.image,0x6A643B8,v.application);v.Put(v.application,0,v.image+x::kGuiRootApplicationVtableRvaV1);v.Put(v.application,0x89,std::uint8_t{0});v.Put(v.application,0x1B8,first);v.Put(first,0x58,v.context);v.Put(v.context,0xD0,root);
 // Existing exact menu application guard, copied solely into our fake image.
 const std::array<unsigned char,3>a{0x48,0x8b,0xf9};std::memcpy(reinterpret_cast<void*>(v.image+0x3F5854B),a.data(),a.size());
 const std::array<unsigned char,7>b{0x48,0x89,0x3d,0x84,0xbc,0xb0,0x2};std::memcpy(reinterpret_cast<void*>(v.image+0x3F5872D),b.data(),b.size());
 const std::array<unsigned char,8>c{0x48,0x8b,0x5,0x81,0x2d,0xbc,0x2,0xc3};std::memcpy(reinterpret_cast<void*>(v.image+0x3EA1630),c.data(),c.size());
 const std::array<unsigned char,12>d{0x48,0x8b,0xd,0x1a,0xc8,0xb0,0x2,0xe8,0xcd,0x35,0x0,0x0};std::memcpy(reinterpret_cast<void*>(v.image+0x3F57B97),d.data(),d.size());
 Gui(root,0,"root",4,true);Gui(v.main_root,root,"mainmenu_panel_bottom",5,true);Gui(v.book_root,root,"frontend_bookmarks",6,false);
 v.Put(root,0xF0,children);v.Put(root,0xF8,std::int32_t{2});v.Put(root,0xFC,std::int32_t{2});v.Put(children,0,v.main_root);v.Put(children,8,v.book_root);
 v.after_open=[](t::FakeImage*p){p->Put(p->main_root,0xD0,std::uint32_t{8});p->Put(p->book_root,0xD0,std::uint32_t{0});};
}
}
namespace xar::ck3_121003::build26785313 {
ReadonlyBindings BindReadonlyImage(std::uintptr_t,std::string_view)noexcept {ReadonlyBindings b;b.exact_image_admitted=true;b.module_base=model::f->image;b.core.game_state_slot=&model::f->world;return b;}
bool VerifyGuiWindowImageV1(std::uintptr_t image)noexcept{return model::f&&image==model::f->image;}
bool VerifyApplicationExitImage267V1(std::uintptr_t image)noexcept{return model::f&&image==model::f->image;}
bool FrontendAdapterAdmitted267V1(const FrontendMenuContext267V1&,std::string_view cap)noexcept{return model::adapter&&std::find(kFrontendAllCaps267V1.begin(),kFrontendAllCaps267V1.end(),cap)!=kFrontendAllCaps267V1.end();}
}
namespace xar::ck3_1210 {ApplicationExitStatusV1 RequestApplicationExitV1(const ApplicationExitBindingsV1&,ApplicationExitSessionV1&,BeforeApplicationExitV1,void*)noexcept{return ApplicationExitStatusV1::unavailable;}}
int main(int argc,char**argv){try{
 using A=x::FrontendMenuAction267V1;using S=x::FrontendMenuStatus267V1;using x::frontend_seed_test::Require;
 std::filesystem::path emit;if(argc==3&&std::string_view(argv[1])=="--emit-owner")emit=argv[2];else Require(argc==1,"unsupported arguments");
 for(unsigned scenario=0;scenario<8;++scenario){t::FakeImage f;model::Init(f);x::FrontendMenuSession267V1 session;auto mailbox=std::make_unique<xar::ck3_11906::MainThreadQueryMailboxV1>();mailbox->permitted_frontend_executor=&x::ExecuteFrontendMenuOnOwner267V1;mailbox->state=xar::ck3_11906::MainThreadQueryMailboxStateV1::executing;mailbox->owner_thread_id=GetCurrentThreadId();mailbox->owner_verified_pump_epochs=2;mailbox->published_sequence=1;
 xar::ck3_11906::MainThreadExecutionStampV1 stamp;stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=7;stamp.tls_initialized_flag_address=1;stamp.tls_initialized=1;stamp.tls_context=8;stamp.tls_main_thread_marker=1;
 const auto make=[&](A a){x::FrontendMenuContext267V1 q;q.session=&session;q.connection_generation=3;q.mailbox=mailbox.get();q.ticket.sequence=1;q.request.action=a;q.request.deadline_unix_ms=t::WallFuture();const auto id="frontend-owner-"+std::to_string(++model::ids);std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());x::ArmFrontendMenuDeadline267V1(q);return q;};
 const auto run=[&](x::FrontendMenuContext267V1&q){mailbox->executor=&x::ExecuteFrontendMenuOnOwner267V1;mailbox->executor_context=&q;Require(x::ExecuteFrontendMenuInner267V1(q,stamp),"actual owner returned");};
 const auto query=[&](){auto q=make(A::query_menu);run(q);Require(q.result.status==S::available&&q.result.facts.no_world,"genuine query over self-owned no-world GUI");return q;};
 const auto effect=[&](A a,const x::FrontendMenuContext267V1&before){auto q=make(a);q.request.deadline_unix_ms=before.request.deadline_unix_ms;q.request.provider_generation=before.result.provider_generation;q.request.query_sequence=before.result.query_sequence;x::ArmFrontendMenuDeadline267V1(q);return q;};
 auto q=query();auto open=effect(A::open_bookmarks,q);
 if(scenario==1){open.connection_generation=4;run(open);Require(open.result.status==S::query_consumed&&f.Effects()==0,"foreign connection no effect");continue;}
 if(scenario==2){open.request.deadline_unix_ms+=1;run(open);Require(open.result.status==S::query_consumed&&f.Effects()==0,"original wall deadline cannot be refreshed");continue;}
 if(scenario==3){open.monotonic_deadline_ms=1;run(open);Require(open.result.status==S::expired&&f.Effects()==0,"expired query no effects");continue;}
 if(scenario==4){f.Put(f.main,0xA0,std::uintptr_t{0});run(open);Require(open.result.status==S::query_consumed&&f.Effects()==0,"changed actual receiver no effect");continue;}
 if(scenario==5){f.throw_rva=0x1BB01C0;run(open);Require(open.result.status==S::indeterminate&&open.result.effect_attempted&&f.calls.open==1,"native uncertainty retains attempted original claim");f.throw_rva=0;auto blocked=make(A::query_menu);run(blocked);Require(blocked.result.status==S::indeterminate,"Unknown never reset by new query");continue;}
 run(open);Require(open.result.effect_attempted&&open.result.native_returned&&open.seed_readback_only&&f.calls.open==1,"open once waits for independently observed route");run(open);Require(open.result.status==S::bookmarks_opened&&!open.seed_readback_only&&f.calls.open==1,"readonly postproof never replays original open");
 q=query();auto book=effect(A::select_1066_bookmark,q);run(book);Require(book.result.effect_attempted&&f.calls.bookmark==1,"current exact model bookmark setter once");run(book);Require(book.result.status==S::bookmark_selected&&f.calls.bookmark==1,"bookmark postproof readonly");
 q=query();auto select=effect(A::select_robert_1066,q);run(select);run(select);Require(select.result.status==S::selection_dispatched&&select.result.post_selection_verified&&f.calls.character==1,"actual model keyed Robert selection with independent same-lease proof");
 q=query();Require(q.result.facts.robert_source_verified,"raw selected character canonical script name readback");
 if(scenario==6){f.can_start=false;q=query();Require(!q.result.facts.start_admissible,"native false predicate remains false");auto no=effect(A::start_robert_1066,q);run(no);Require(no.result.status==S::unavailable&&f.calls.start_game==0&&f.calls.on_start==0,"CanStart false never enters either Start stage");continue;}
 auto start=effect(A::start_robert_1066,q);
 if(scenario==7)f.ignore_start_game=true;
 run(start);
 if(scenario==7){Require(start.result.status==S::indeterminate&&f.calls.start_game==1&&f.calls.on_start==0,"preparation mismatch cannot invoke OnStart or claim a world");continue;}
 Require(start.result.status==S::start_dispatched&&start.result.native_returned&&f.calls.start_game==1&&f.calls.on_start==1,"official preparation then OnStart once; dispatch only");
 const auto first_claim=start.result.claim_sequence;run(start);Require(!start.result.effect_attempted&&start.result.status==S::query_consumed&&f.calls.on_start==1,"original seed action cannot replay after consuming private query");Require(first_claim>0&&f.calls.layout_errors==0,"actual typed stub receivers and source identities coherent");
 if(!emit.empty()){std::filesystem::create_directories(emit);for(const auto&row:{std::pair{"query.json",q.result},std::pair{"open.json",open.result},std::pair{"bookmark.json",book.result},std::pair{"selection.json",select.result}}){std::ofstream out(emit/row.first,std::ios::binary);out<<x::SerializeFrontendMenuResult267V1(row.second.action==A::query_menu?q.request.id():"owner-NoGame",row.second)<<'\n';Require(bool(out),"exclusive own producer file output");}}
 }
 std::cout<<"PASS actual current frontend owner/wire/reader with self-owned GUI+model and explicit native address stubs; 4finite actions/independent postproof/once/connection/deadline/CanStart/UNKNOWN, no Game or actual ABI call\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
