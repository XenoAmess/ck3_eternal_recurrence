#pragma once
#include "xar_bridge/holy_site_creation12004.hpp"
namespace xar::ck3_12004::religion::holy_site_creation {
// Only the existing paused owner mailbox supplies jomini_state. The caller
// retains EnterQueryMailbox / FinishQueryMailbox and revision admission.
bool ReadFromJomini12004(const Bindings&,const void* admitted_jomini_state,
 const ck3_12002::religion::Context&,Snapshot&) noexcept;
}
