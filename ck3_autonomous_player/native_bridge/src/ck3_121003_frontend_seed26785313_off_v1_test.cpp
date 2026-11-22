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
int main(){using namespace xar::ck3_121003::build26785313;FrontendMenuSession267V1 session;xar::ck3_11906::MainThreadExecutionStampV1 stamp;
 for(auto action:{FrontendMenuAction267V1::open_bookmarks,FrontendMenuAction267V1::select_1066_bookmark,FrontendMenuAction267V1::select_robert_1066,FrontendMenuAction267V1::start_robert_1066}){FrontendMenuContext267V1 q;q.session=&session;q.request.action=action;q.request.provider_generation=q.request.query_sequence=1;q.request.deadline_unix_ms=frontend_seed_test::WallFuture();const std::string id="off-seed";std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=8;ArmFrontendMenuDeadline267V1(q);
  if(!ExecuteFrontendMenuInner267V1(q,stamp)||q.result.reason!="current_frontend_robert_model_abi_unbound"||q.result.effect_attempted||q.result.native_returned||q.result.claim_sequence||q.result.status!=FrontendMenuStatus267V1::unavailable)throw std::runtime_error("featureOFF entered native model/action or lost explicit unbound reason");}
 std::cout<<"PASS actual owner 4fixed actions defaultOFF/unbound, no model observation/effect/claim\n";return 0;}
