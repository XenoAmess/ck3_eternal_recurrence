#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_courtier_choices26785313_raw_v1.hpp"
#include <cassert>
#include <iostream>
#include <cstring>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;xar::ck3_1210::CoreSnapshotPrefix core;CourtierChoicesScene267V1 scene;CourtierChoicesRaw267V1 raw;std::string reason;assert(!ReadCourtierChoicesRaw267V1(b,core,scene,1,CourtierProduct267V1::main,CourtierCatalog267V1::education,raw,reason));assert(reason=="current_courtier_choices_default_off");const auto call=ExecuteCourtierChoiceRaw267V1(b,core,scene,1,raw,0);assert(!call.effect_entered&&call.cleanup_known&&call.status==LetterRawCallStatus267V1::unavailable);
 CourtierChoicesRaw267V1 a;a.actor=11;a.cost_definition=12;a.source.confirmation_layer_found=a.source.creator_window_found=a.source.modal_found=a.source.panel_found=a.source.model_available=a.source.complete_model=true;a.source.catalog_count=1;a.source.rows.push_back({"opaque-original","logistician",true,true,false,true});a.identities.resize(1);a.identities[0].definition=100;const std::uint32_t tag=0x36,id=42;std::memcpy(a.identities[0].reference.data(),&tag,4);std::memcpy(a.identities[0].reference.data()+8,&id,4);auto z=a;assert(SameCourtierChoicesRaw267V1(a,z));z.source.rows[0].choice_token="new-query-token";z.identities[0].reference[4]=std::byte{0xA5};assert(SameCourtierChoicesRaw267V1(a,z));z.source.rows[0].selected=true;assert(!SameCourtierChoicesRaw267V1(a,z));z=a;z.source.rows[0].key="military_engineer";assert(!SameCourtierChoicesRaw267V1(a,z));z=a;z.identities[0].definition=101;assert(!SameCourtierChoicesRaw267V1(a,z));z=a;z.identities.clear();assert(!SameCourtierChoicesRaw267V1(a,z));z=a;z.cleanup_known=false;assert(!SameCourtierChoicesRaw267V1(a,z));z=a;z.ancestors.resize(1);assert(!SameCourtierChoicesRaw267V1(a,z));
std::cout<<"Courtier choices defaultOFF and whole-model semantic custody regression\n";}
