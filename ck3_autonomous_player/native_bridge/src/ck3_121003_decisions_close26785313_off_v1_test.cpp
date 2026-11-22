#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_decisions_close26785313_raw_v1.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;xar::ck3_1210::CoreSnapshotPrefix core;CuratedDecisionScene267V1 scene;CuratedDecisionRaw267V1 raw;const auto call=CloseDecisionsListRaw267V1(b,core,scene,1,1,raw);assert(!call.effect_entered&&call.cleanup_known&&call.status==CuratedDecisionRawCallStatus267V1::refused);raw.source.list_found=raw.source.list_visible=raw.source.list_enabled=raw.source.detail_found=raw.source.complete_model_census=true;raw.source.groups_count=9;raw.source.total_model_rows=37;raw.nav_widget=1;raw.shortcut_manager=2;raw.nav_callbacks.resize(1);assert(DecisionsCloseRawAdmissible267V1(raw));auto same=raw;raw.rows[0]=123;same.rows[0]=456;assert(SameDecisionsCloseRawSource267V1(raw,same));same.source.list_visible=false;assert(!SameDecisionsCloseRawSource267V1(raw,same));assert(!DecisionsCloseRawAdmissible267V1(same));same=raw;same.source.detail_visible=true;assert(!DecisionsCloseRawAdmissible267V1(same));same=raw;same.source.blocked_by_visible_modal=true;assert(!DecisionsCloseRawAdmissible267V1(same));same=raw;same.source.complete_model_census=false;assert(!DecisionsCloseRawAdmissible267V1(same));same=raw;same.nav_callbacks.clear();assert(!DecisionsCloseRawAdmissible267V1(same));std::cout<<"fixed decisions close defaultOFF + current-visible/detail/modal/complete/nav negative guards passed\n";}
