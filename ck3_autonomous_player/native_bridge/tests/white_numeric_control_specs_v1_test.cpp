#include "xar_bridge/white_control_action_v1.hpp"
#include <cassert>
#include <string>
int main() {
  using namespace xar::ck3_11906;
  const std::array<std::string_view,6> names{{"diplomacy","martial","stewardship","intrigue","learning","prowess"}};
  for(std::size_t i=0;i<names.size();++i) {
    const auto key=std::string(names[i])+"_plus_1";
    const auto *spec=FindWhiteControlSpecV1(key);
    assert(spec&&spec->control==key&&!spec->legacy_age);
    assert(spec->button=="ervc_cc_"+key+"_button");
    assert(spec->variable_index==i+2&&spec->text_index==i+1&&spec->maximum==100);
    assert(!FindWhiteControlSpecV1(std::string(names[i])+"_plus_10"));
  }
  const auto *age=FindWhiteControlSpecV1("age_plus_1");
  assert(age&&age->legacy_age&&age->maximum==120&&age->variable_index==1&&age->text_index==0);
  assert(!FindWhiteControlSpecV1("ervc_cc_diplomacy_plus_1_button"));
  assert(!FindWhiteControlSpecV1(""));
  const std::string embedded("diplomacy_plus_1\0suffix",22);
  assert(!FindWhiteControlSpecV1(embedded));
}
