#include "xar_bridge/religion_ui12004_navigation.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <utility>
#ifndef XAR_ENABLE_RELIGION_UI12004_PRESENTATION
#define XAR_ENABLE_RELIGION_UI12004_PRESENTATION 0
#endif

namespace xar::ck3_11906 {
namespace {
bool Exact(const ZhongguoScoreboardNativeEnvironmentV1&e) noexcept {
  return XAR_ENABLE_RELIGION_UI12004_PRESENTATION&&e.exact_build_admitted&&!e.offline_fixture_function_overrides&&e.module_base&&
      e.gui_abi_revision==GuiAbiRevisionV1::crozier12004&&e.executable_sha256==ck3_12004::kExecutableSha256;
}
std::string_view RootName(ck3_12004::religion_ui::Window kind) noexcept {
  if(kind==ck3_12004::religion_ui::Window::character)return "character_window";
  if(kind==ck3_12004::religion_ui::Window::faith)return "faith_window";
  return {};
}
}
bool CanOpenReligionPresentation12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void*handler,
    ck3_12004::religion_ui::Window kind,std::uint32_t id) noexcept {
  return Exact(e)&&ck3_12004::religion_ui::CanOpen12004(
      ck3_12004::religion_ui::BindImage12004(e.module_base,e.executable_sha256),handler,kind,id);
}
bool InvokeReligionPresentation12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void*handler,
    ck3_12004::religion_ui::Window kind,std::uint32_t id,bool&attempted) noexcept {
  attempted=false;return Exact(e)&&ck3_12004::religion_ui::InvokeOpen12004(
      ck3_12004::religion_ui::BindImage12004(e.module_base,e.executable_sha256),handler,kind,id,attempted);
}
bool ReadReligionPresentation12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void*handler,
    ck3_12004::religion_ui::Window kind,IngameUiResultV1&out) noexcept {
  try{
    const auto name=RootName(kind);out.tree.scope_root_name=std::string(name);
    const auto fail=[&](const char*why){out.unavailable_reason=why;return false;};
    if(!Exact(e)||name.empty())return fail("religion_presentation_requires_exact12004");
    const auto b=ck3_12004::religion_ui::BindImage12004(e.module_base,e.executable_sha256);
    ck3_12004::religion_ui::Selection first{},last{};
    if(!ck3_12004::religion_ui::ReadSelection12004(b,handler,kind,first)){
      out.unavailable_reason=first.unavailable_reason;return false;
    }
    if(!first.root)return fail("religion_presentation_root_not_created");
    ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr,*vtable=nullptr;
    std::string runtime_name;bool visible=false,enabled=false;NamedGuiTreeInspectionV1 tree{};
    if(!ResolveNamedGuiWidgetV1(e,access,name,name,root,widget)||!root||widget!=root||root!=first.root||
        !ReadGuiWidgetRuntimeV1(access,root,runtime_name,vtable,visible,enabled)||runtime_name!=name||
        !InspectNamedGuiSubtreeV1(access,e.module_base,root,name,tree)||tree.truncated)
      return fail("religion_presentation_visible_root_census_unverified");
    void*last_vtable=nullptr;std::string last_name;bool last_visible=false,last_enabled=false;
    if(!ck3_12004::religion_ui::ReadSelection12004(b,handler,kind,last)||last.window!=first.window||last.root!=first.root||
        last.gfx!=first.gfx||last.subject_available!=first.subject_available||last.subject_id!=first.subject_id||
        last.selected_rite_id!=first.selected_rite_id||
        !ReadGuiWidgetRuntimeV1(access,root,last_name,last_vtable,last_visible,last_enabled)||last_name!=runtime_name||
        last_vtable!=vtable||last_visible!=visible||last_enabled!=enabled)
      return fail("religion_presentation_window_or_visibility_changed");
    out.window_exists=true;out.effective_visible=visible;out.enabled=enabled;
    out.subject_id_available=first.subject_available;
    if(first.subject_available)out.current_subject_id=first.subject_id;
    out.tree=std::move(tree);out.unavailable_reason.clear();return true;
  }catch(...){out.unavailable_reason="religion_presentation_capture_exception";return false;}
}
}
