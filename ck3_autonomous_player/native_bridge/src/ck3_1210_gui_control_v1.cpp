#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include <limits>

namespace xar::ck3_1210 {
namespace {
bool Reject(GuiControlResultV1 &out, GuiControlStatusV1 status, std::string_view reason) {
  out.status=status;out.unavailable_reason.assign(reason);return false;
}
bool Complete(const GuiControlCaptureV1 &c, std::string_view root) {
  if(!c.complete || c.root_name!=root || !c.root || !c.context || !c.logical_owner ||
      !c.application || !c.gui_owner || !c.shortcut_manager || !c.global_root ||
      (c.played_character_id==0 || c.played_character_id==-1) || !c.native_revision || !c.connection_generation ||
      c.widgets.empty() || c.widgets.size()>kGuiControlMaximumRowsV1 ||
      c.widgets.front().widget!=c.root || c.widgets.front().row.runtime_name!=root ||
      !c.widgets.front().row.child_path.empty())return false;
  for(std::size_t i=0;i<c.widgets.size();++i) if(c.widgets[i].row.widget_id!=i+1 ||
      !c.widgets[i].widget || c.widgets[i].context!=c.context)return false;
  return true;
}
void Rows(const GuiControlCaptureV1 &c, GuiControlResultV1 &out) {
  out.widgets.reserve(c.widgets.size());
  for(const auto &w:c.widgets)out.widgets.push_back(w.row);
}
} // namespace
bool GuiControlRootNameV1(std::string_view value) noexcept {
  if(value.empty() || value.size()>128)return false;
  if(!((value.front()>='a' && value.front()<='z') || (value.front()>='A' && value.front()<='Z') || value.front()=='_'))return false;
  for(const char ch:value)if(!((ch>='a' && ch<='z') || (ch>='A' && ch<='Z') ||
      (ch>='0' && ch<='9') || ch=='_'))return false;
  return true;
}
bool ApplyGuiControlV1(GuiControlProviderV1 &p,const GuiControlRequestV1 &r,
    const GuiControlBackendV1 &b,GuiControlResultV1 &out) noexcept {
  try {
    out={};
    if(!GuiControlRootNameV1(r.root_name) || !b.capture ||
        (r.activate && !b.dispatch))return Reject(out,GuiControlStatusV1::unavailable,"invalid_gui_request");
    if(r.activate && (!p.valid || !r.query_generation || r.query_generation!=p.query_generation ||
        !r.widget_id || r.widget_id>p.capture.widgets.size() || p.capture.root_name!=r.root_name ||
        p.capture.native_revision!=r.native_revision)) {
      p.valid=false;return Reject(out,GuiControlStatusV1::stale_gui,"gui_query_handle_stale");
    }
    GuiControlCaptureV1 first{},second{};std::string reason;
    if(!b.capture(b.context,r.root_name,first,reason) || !Complete(first,r.root_name) ||
        first.native_revision!=r.native_revision) {
      p.valid=false;return Reject(out,GuiControlStatusV1::unavailable,
          reason.empty()?"gui_complete_capture_unavailable":reason);
    }
    if(!b.capture(b.context,r.root_name,second,reason) || first!=second) {
      p.valid=false;return Reject(out,GuiControlStatusV1::stale_gui,"gui_capture_changed");
    }
    if(!r.activate) {
      p.valid=false;
      if(p.query_generation==(std::numeric_limits<std::uint64_t>::max)())
        return Reject(out,GuiControlStatusV1::unavailable,"gui_generation_exhausted");
      ++p.query_generation;p.capture=std::move(first);p.valid=true;
      out.query_generation=p.query_generation;Rows(p.capture,out);
      out.status=GuiControlStatusV1::available;return true;
    }
    // A handle is consumed even on a disabled/stale rejection. An attempted
    // callback is never retried through this provider generation.
    p.valid=false;out.query_generation=p.query_generation;
    if(first!=p.capture)return Reject(out,GuiControlStatusV1::stale_gui,"gui_identity_or_binding_changed");
    const auto &target=p.capture.widgets[static_cast<std::size_t>(r.widget_id-1)];
    if(!target.row.clickable || !target.row.effective_visible || !target.row.enabled)
      return Reject(out,GuiControlStatusV1::disabled,"gui_button_not_currently_clickable");
    bool attempted=false,handled=false;
    const bool invoked=b.dispatch(b.context,p.capture,target,handled,attempted);
    out.effect_attempted=attempted;out.native_handled=handled;
    if(!invoked)return Reject(out,attempted?GuiControlStatusV1::indeterminate:GuiControlStatusV1::unavailable,
        attempted?"gui_dispatch_indeterminate_no_retry":"gui_dispatch_admission_failed");
    if(!attempted)return Reject(out,GuiControlStatusV1::unavailable,"gui_dispatch_missing_attempt");
    out.status=GuiControlStatusV1::submitted;out.verification_pending=true;return true;
  } catch(...) {
    p.valid=false;
    return Reject(out,out.effect_attempted?GuiControlStatusV1::indeterminate:GuiControlStatusV1::unavailable,
        "gui_control_exception_no_retry");
  }
}
} // namespace xar::ck3_1210
