// Reuse the actual qualified Raw fake-image fixture. Do not link Raw again.
#define main OriginalQualifiedRmtmRawMain
#include "rmtm_title_query_capture_nogame_fixture.hpp"
#undef main
namespace capture_test {
bool native_throw=false;
const void* __fastcall Primary(const void*self){if(native_throw)RaiseException(0xE04D0002,0,0,nullptr);return test::Primary(self);}
std::uintptr_t Address(std::uintptr_t,std::uintptr_t rva){if(rva!=0x2D83960)std::abort();return reinterpret_cast<std::uintptr_t>(&Primary);}
}
#define XAR_RMTM_TITLE_QUERY_CALL_ADDRESS(image,rva) capture_test::Address(image,rva)
#include "ck3_121003_rmtm_title_query26785313_capture_v1.cpp"
int main(){try{test::Fixture f;c::RmtmTitleQueryRequest267V1 request;request.expected=f.frame.core;request.deadline_unix_ms=f.request.deadline_unix_ms;std::uint32_t out=0xFFFFFFFFU;bool entered=false,cleanup=true;std::string why;
 const auto run=[&]{request.expected=f.frame.core;return c::CaptureRmtmTitleQueryPrimary267V1(f.bindings,f.frame,request,GetTickCount64()+60000,out,entered,cleanup,why);};
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 test::Need(run()&&out==f.title_id&&entered&&cleanup,"actual primary capture high full generation");
 f.Reset();f.title_id=0;test::Put(f.T(),0x10,std::uint32_t{0});test::Put(reinterpret_cast<std::uintptr_t>(f.title_rows.data()),8,f.T());entered=false;test::Need(run()&&out==0,"private captured Title zero");f.title_id=0xA5000001U;
 f.Reset();test::Put(f.T(),0x14,std::uint32_t{0});test::Need(!run()&&out==0xFFFFFFFFU&&cleanup,"wrong title magic cannot be returned");
 f.Reset();test::Put(f.T(),0,std::uintptr_t{0});test::Need(!run(),"wrong actual title vptr");
 f.Reset();test::Put(reinterpret_cast<std::uintptr_t>(f.title_rows.data()),24,std::uintptr_t{0});test::Need(!run(),"missing current storage membership");
 f.Reset();test::Put(f.T(),0x10,std::uint32_t{0xFFFFFFFFU});test::Need(!run(),"invalid sentinel not actual title");
 f.Reset();entered=false;request.deadline_unix_ms=1;const auto calls=f.calls;test::Need(!run()&&!entered&&f.calls==calls,"expired capture before native entry");request.deadline_unix_ms=f.request.deadline_unix_ms;
 f.Reset();capture_test::native_throw=true;entered=false;cleanup=true;test::Need(!run()&&entered&&!cleanup&&out==0xFFFFFFFFU,"capture native exception preserves unknown");capture_test::native_throw=false;
#else
 test::Need(!run()&&!entered&&cleanup&&f.calls==0&&out==0xFFFFFFFFU,"query capture OFF zero native calls");
#endif
 return 0;}catch(...){return 1;}}
