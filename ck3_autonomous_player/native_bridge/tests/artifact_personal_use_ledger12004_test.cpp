#ifdef NDEBUG
#error "Finite assertion fixture must be compiled with NDEBUG undefined"
#endif
#include "artifact_personal_use_ledger12004.hpp"
#include <cassert>
namespace obs=xar::ck3_12004::current_player_observers;
namespace item=xar::ck3_12004::artifact_personal_use;
struct Fixture {
  obs::ArtifactIntentLedger12004 ledger;
  item::Frame frame{7,10,2,53144328,1234,77,0x8000,true,true,true,true,true};
  item::Request request{5,900,0,item::absent,true};
  item::Observation before{};
  item::Witness witness{};
  Fixture(){before.available=true;before.loaded_source_pins_verified=true;before.frame=frame;
    before.artifact_id=900;before.personally_owned=true;before.owned_ids={900};
    before.native_equipped_observed=true;witness.actor=0x1000;witness.artifact=0x2000;
    witness.character_owner=77;witness.site_owner=item::absent;}
  bool claim(){return ledger.Claim(frame,request,before,witness);}
  item::Observation after(){auto out=before;out.frame.capture_epoch++;out.equipped=true;
    out.equipped_slot_index=0;out.slots={{0,900,"crown",true}};return out;}
};
int main(){
  // Pure ledger tests: admitted frame/reader DTOs below are fixture-owned; this
  // does not qualify the native frame provider or any actual equipment action.
  {Fixture f;assert(f.claim());assert(!f.claim());}
  {Fixture f;assert(f.claim());f.request.request_sequence++;assert(!f.claim());}
  {Fixture f;assert(f.claim());f.frame.connection_generation++;f.before.frame=f.frame;assert(!f.claim());}
  {Fixture f;assert(f.claim());f.request.artifact_id=901;f.before.artifact_id=901;assert(!f.claim());}
  {Fixture f;f.before.available=false;assert(!f.claim());}
  {Fixture f;f.witness.character_owner=78;assert(!f.claim());}
  {Fixture f;assert(f.claim());item::Request request{};item::Result result{};bool desired=false;
    auto after=f.after();assert(f.ledger.ObserveAfter(after,5,request,result,desired));
    assert(desired&&!result.needs_recovery&&request.request_sequence==5);
    f.request.request_sequence++;f.before=after;f.frame=after.frame;assert(f.claim());}
  {Fixture f;assert(f.claim());item::Request request{};item::Result result{};bool desired=true;
    auto after=f.after();after.frame.connection_generation++;
    assert(f.ledger.ObserveAfter(after,5,request,result,desired));assert(!desired&&result.needs_recovery);
    assert(!f.claim());}
  {Fixture f;assert(f.claim());item::Request request{};item::Result result{};bool desired=false;
    auto after=f.after();assert(f.ledger.ObserveAfter(after,5,request,result,desired)&&desired);
    after.equipped=false;after.equipped_slot_index.reset();after.frame.capture_epoch++;
    assert(f.ledger.ObserveAfter(after,5,request,result,desired)&&!desired);}
  {Fixture f;assert(f.claim());item::Request request{};item::Result result{};bool desired=true;
    assert(!f.ledger.ObserveAfter(f.after(),999,request,result,desired));assert(!desired);}
}
