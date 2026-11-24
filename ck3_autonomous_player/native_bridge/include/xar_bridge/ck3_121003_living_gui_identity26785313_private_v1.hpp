#pragma once
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Compare all stable fields. Only ticket and pump receipts naturally differ
// between query and action. Each invocation's owner checks still verify its
// actual ticket/pump/executor/context; current owner thread remains identical.
inline bool SameLivingGuiIdentity267V1(const GuiWindowV1&a,const GuiWindowV1&z)noexcept{
 return a.logical_owner==z.logical_owner&&a.application==z.application&&a.first==z.first&&
  a.context==z.context&&a.global_root==z.global_root&&a.connection_generation==z.connection_generation&&
  a.owner_thread_id==z.owner_thread_id&&a.requested_name==z.requested_name&&
  a.root==z.root&&a.top_level==z.top_level&&a.tree==z.tree&&a.ancestors==z.ancestors&&a.window_found==z.window_found;
}
}
