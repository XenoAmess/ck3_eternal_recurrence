#include "xar_bridge/nonwar_private_snapshot_guard_diagnostics_v1.hpp"
#include <iostream>
#include <stdexcept>

namespace {
void Require(bool value,const char *why) { if (!value) throw std::runtime_error(why); }
void Has(const std::string &text,const char *part) { Require(text.find(part)!=std::string::npos,part); }
}
int main() {
  try {
    // Retained R0090 has last native3, public4 and raw date53290128. These are
    // deterministic caller-admissible DTOs, not a claim about the missing wire
    // or an invented current Game snapshot. Both production and this fixture
    // call the same helper with the actual game::Snapshot type.
    xar::game::Snapshot base{};
    base.date_raw=53290128; base.paused=true; base.map_ready=true;
    base.has_played_character=true; base.played_character_alive=true;
    base.played_character_id=1;
    std::optional<xar::game::Snapshot> previous=base;
    xar::game::Snapshot current{};
    int reads=0;
    auto equal=[&](xar::game::Snapshot &out) { ++reads; out=base; return true; };
    const auto run=[&](bool status,bool parsed,std::uint64_t expected) {
      return xar::bridge::NonwarPrivateSnapshotGuardFailureV1(
          status,parsed,expected,3,previous,current,equal);
    };
    Require(run(false,true,3).empty() && reads==1,"matching native caller passes with exactly one read");
    reads=0; Has(run(false,false,3),"cause=revision_parse_failed");
    Require(reads==0,"parse failure short circuits read");
    Has(run(false,true,0),"cause=expected_revision_zero");
    Require(reads==0,"zero short circuits read");
    const auto mismatch=run(false,true,4);
    Has(mismatch,"cause=revision_mismatch"); Has(mismatch,"expected_revision=4 native_revision=3");
    Require(reads==0,"revision mismatch short circuits read");
    previous.reset(); Has(run(false,true,3),"cause=previous_snapshot_missing");
    Require(reads==0,"missing previous short circuits read");
    Require(run(true,false,0).empty() && reads==0,"status-only bypass unchanged");
    previous=base;
    auto unreadable=[&](xar::game::Snapshot &) { ++reads; return false; };
    Has(xar::bridge::NonwarPrivateSnapshotGuardFailureV1(false,true,3,3,previous,current,unreadable),"cause=current_snapshot_read_failed");
    Require(reads==1,"failed read called once");
    reads=0;
    auto changed=[&](xar::game::Snapshot &out) { ++reads; out=base; out.played_character_gold.raw=100000; return true; };
    const auto difference=xar::bridge::NonwarPrivateSnapshotGuardFailureV1(false,true,3,3,previous,current,changed);
    Has(difference,"cause=full_snapshot_changed"); Has(difference,"expected_revision=3 native_revision=3");
    Has(difference,"changed_snapshot_fields=[\"played_character_gold\"]");
    Require(reads==1,"full difference called once");
    reads=0;
    auto traits=[&](xar::game::Snapshot &out) { ++reads; out=base; out.played_character_event_trait_membership.emplace(); return true; };
    Has(xar::bridge::NonwarPrivateSnapshotGuardFailureV1(false,true,3,3,previous,current,traits),"changed_snapshot_fields=[\"played_character_event_trait_membership\"]");
    Require(reads==1,"optional current Snapshot member called once");
    std::cout << "PASS: production guard original order/status bypass/one read/expected-native and owned diff diagnostics; 9 cases; no Game or old fixtures\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 17;
  }
}
