#include "xar_bridge/ck3_12002_family_obligations_wire.hpp"

#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
}
int main(int argc, char **argv) {
  using namespace xar::ck3_12002;
  try {
    FamilyObligationsObservation12002 o{};
    o.snapshot_revision = 53;
    o.frame.date_raw = 53220000;
    o.frame.played_character_id = 0x01000001;
    o.frame.paused = o.frame.map_ready = o.frame.played_character_alive = true;
    o.request.subject_character_id = 0x01000002;
    o.request.candidate_character_id = 0x01000003;
    o.lineage_available = true;
    o.lineage.available = true;
    o.lineage.native_selected_parent_character_id = o.request.candidate_character_id;
    o.lineage.selected_matrilineal_option = true;
    o.lineage.effective_matrilineal_if_accepted = false;
    o.lineage.complete_can_send = false;
    Require(FamilyObligationsQueryStatus12002(o) == "available", "omitted unrelated lanes do not block lineage");
    auto wire = SerializeFamilyObligationsResult12002("wire\"request\n", o);
    Require(wire.find("\"selected_matrilineal_option\":true") != std::string::npos &&
        wire.find("\"effective_matrilineal_if_accepted\":false") != std::string::npos &&
        wire.find("\"complete_can_send\":false") != std::string::npos,
        "selected option, effective outcome and negative final legality stay distinct");
    Require(wire.find("\"house_id\":null,\"dynasty_id\":null") != std::string::npos &&
        wire.find("\"status\":\"not_requested\"") != std::string::npos &&
        wire.find("wire\\\"request\\u000a") != std::string::npos,
        "legal no-lineage identity and escaped request preserved");
    o.request.ally_character_id = 0x01000004;
    Require(FamilyObligationsQueryStatus12002(o) == "partial",
        "missing requested war source preserves independently available family lane");
    o.alliance_available = true;
    wire = SerializeFamilyObligationsResult12002("deferred", o);
    Require(wire.find("\"first_wars\":[]") != std::string::npos &&
        wire.find("deferred_by_owner") == std::string::npos,
        "available empty native wars are distinct from an unavailable source");
    o.request.break_recipient_character_id = 0x01000005;
    o.break_terms.status = FamilyObligationsBreakStatusV1::available;
    o.break_terms.final_legality_sampled = true;
    o.break_terms.native_send_costs_available = true;
    o.break_terms.native_send_costs_raw[0] = 1000000;
    o.break_terms.outcome_resource_penalty.resource_penalty_available = true;
    o.break_terms.outcome_resource_penalty.effects_complete = false;
    o.break_terms.outcome_resource_penalty.stock_prestige_effect_raw = -8000000;
    o.break_terms.outcome_resource_penalty.stock_prestige_level_effect = -1;
    Require(FamilyObligationsQueryStatus12002(o) == "available", "all requested native observations available");
    wire = SerializeFamilyObligationsResult12002("family-obligations-wire-fixture", o);
    Require(wire.find("\"native_send_costs_raw\":[1000000,0,0,0,0,0,0,0,0,0]") != std::string::npos &&
        wire.find("\"stock_prestige_effect_raw\":-8000000") != std::string::npos &&
        wire.find("\"effects_complete\":false") != std::string::npos,
        "send charges never alias stock outcome losses or complete effects");
    if (argc == 2) {
      std::ofstream output(argv[1], std::ios::binary);
      output << wire << '\n';
      Require(static_cast<bool>(output), "wire fixture output");
    }
    o.lineage_available = false; o.alliance_available = false;
    o.break_terms.status = FamilyObligationsBreakStatusV1::unavailable;
    Require(FamilyObligationsQueryStatus12002(o) == "unavailable", "missing actual sources never become empty complete data");
    std::cout << "PASS family obligations wire: lane availability, native negative gates, full IDs and distinct send/outcome costs\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
