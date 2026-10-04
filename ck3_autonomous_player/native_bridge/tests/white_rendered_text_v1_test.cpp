#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstring>
#include <iostream>
#include "../src/white_rendered_text_v1.cpp"
// This isolated memory/string test never enters a GUI owner resolver. These
// fail-closed link stubs prevent a synthetic object being mistaken for CK3.
namespace xar::ck3_11906 {
bool ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,void *&,void *&) noexcept {return false;}
bool ResolveNamedGuiWidgetV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,std::string_view,std::string_view,void *&,void *&) noexcept {return false;}
bool ResolveFixedGuiChildPathV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,std::string_view,const std::uint32_t *,std::size_t,void *&,void *&) noexcept {return false;}
bool ReadGuiWidgetRuntimeV1(const ZhongguoScoreboardAccessV1 &,void *,std::string &,void *&,bool &,bool &) noexcept {return false;}
bool InspectNamedGuiSubtreeV1(const ZhongguoScoreboardAccessV1 &,std::uintptr_t,void *,std::string_view,NamedGuiTreeInspectionV1 &) noexcept {return false;}
}
int main() {
  using namespace xar::ck3_11906;
  std::array<unsigned char,0x3B0> widget{};std::string value;
  const auto scalar=[&](std::size_t offset,std::uint64_t n){std::memcpy(widget.data()+0x390+offset,&n,sizeof(n));};
  scalar(0x18,15);assert(ActualText(widget.data(),value)&&value.empty());
  std::memcpy(widget.data()+0x390,"30",3);scalar(0x10,2);assert(ActualText(widget.data(),value)&&value=="30");
  const std::string heap="\xE4\xB8\xAD\xE6\x96\x87 \"#gold 20#!\\line";
  const auto ptr=reinterpret_cast<std::uintptr_t>(heap.c_str());scalar(0,ptr);scalar(0x10,heap.size());scalar(0x18,heap.size());
  assert(ActualText(widget.data(),value)&&value==heap);
  assert(Quote("\"\\\n")=="\"\\\"\\\\\\u000a\"");
  scalar(0x10,2049);scalar(0x18,2049);assert(!ActualText(widget.data(),value));
  scalar(0x10,2);scalar(0x18,1);assert(!ActualText(widget.data(),value));
  widget={};scalar(0x18,15);scalar(0x10,1);widget[0x390]=0xFF;assert(!ActualText(widget.data(),value));
  widget[0x390]=0;assert(!ActualText(widget.data(),value));
  std::vector<std::uint32_t> path;assert(Path("0/1/3/11/1",path)&&path.size()==5);
  assert(!Path("0/1x",path)&&!Path("0/2049",path));
  WhiteRenderedTextResultV1 out{};out.unavailable_reason="actual_hidden";
  const auto wire=SerializeWhiteRenderedTextV1(out);
  assert(wire.find("\"selected_down_available\":false")!=std::string::npos);
  assert(wire.find("\"ervc_cc_age_value_text\":null")!=std::string::npos);
  std::cout<<"PASS 11 native fixed-text memory/UTF8/JSON/path/refusal assertions; no game contact\n";
}
