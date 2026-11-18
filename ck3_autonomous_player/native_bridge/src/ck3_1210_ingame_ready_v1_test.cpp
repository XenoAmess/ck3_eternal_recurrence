// Execute the existing actual Full and all child readers, with only the native
// ABI calls replaced by their established NoGame RAM producer.
#define main ExistingFullFixtureMain
#include "ck3_1210_full_snapshot_v1_test.cpp"
#undef main

namespace {
void DeniedBeforeNative(Fixture &f,std::string_view reason) {
  const auto d=Unavailable(f);
  Require(d.stage=="ingame" && d.reason==reason,"exact readiness failure is preserved");
  Require(f.core_calls==0 && f.selectors==0 && f.predicates==0 && f.validators==0 &&
      f.queue_calls==0 && d.army_state_calls_attempted==0,"unready Full makes zero native calls");
}
void Epoch(Fixture &f,std::uint64_t epoch) {Put(f.players,kIngameCompletedFrameEpochOffsetV1,epoch);}
void FreshWitness(Fixture &f,std::uint64_t epoch) {f.ingame_witness={};Epoch(f,epoch);}
void ConfirmInvalidates(Fixture &f) {
  IngameReadyObservationV1 o{};
  Require(ObserveIngameReadyV1(f.bindings.ingame_ready,f.ingame_witness,o),"ready fixture witness");
  Require(f.ingame_witness.ready,"witness became ready");
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  {Fixture f;FreshWitness(f,50);
    DeniedBeforeNative(f,"full_snapshot_ingame_first_completed_frame_required");
    DeniedBeforeNative(f,"full_snapshot_ingame_completed_frame_not_advanced");
    Epoch(f,51);Observed(f);}
  {Fixture f;f.jomini_slot=nullptr;DeniedBeforeNative(f,"full_snapshot_ingame_root_unpublished");}
  {Fixture f;Put(f.jomini,0,std::uintptr_t{1});DeniedBeforeNative(f,"full_snapshot_ingame_root_type_mismatch");}
  {Fixture f;Put(f.jomini,0x18,static_cast<void *>(nullptr));DeniedBeforeNative(f,"full_snapshot_ingame_application_unavailable");}
  {Fixture f;Put(f.players,0,std::uintptr_t{1});DeniedBeforeNative(f,"full_snapshot_ingame_application_type_mismatch");}
  {Fixture f;Put(f.jomini,0x10,static_cast<void *>(nullptr));DeniedBeforeNative(f,"full_snapshot_ingame_gfx_unpublished");}
  {Fixture f;Put(f.ingame_gfx,0,std::uintptr_t{1});DeniedBeforeNative(f,"full_snapshot_ingame_gfx_type_mismatch");}
  {Fixture f;Put(f.ingame_gfx,0x88,static_cast<void *>(nullptr));DeniedBeforeNative(f,"full_snapshot_ingame_handler_unpublished");}
  {Fixture f;Put(f.ingame_handler,0,std::uintptr_t{1});DeniedBeforeNative(f,"full_snapshot_ingame_handler_type_mismatch");}
  {Fixture f;Put(f.players,0x28,f.player.data());DeniedBeforeNative(f,"full_snapshot_ingame_current_root_mismatch");}
  {Fixture f;Put(f.players,0x78,f.player.data());DeniedBeforeNative(f,"full_snapshot_ingame_transition_pending");}
  {Fixture f;Put(f.players,0x30,std::uint8_t{1});DeniedBeforeNative(f,"full_snapshot_ingame_transition_pending");}
  {Fixture f;Put(f.ingame_gfx,0x20,f.player.data());DeniedBeforeNative(f,"full_snapshot_ingame_gfx_backref_mismatch");}
  {Fixture f;Put(f.ingame_gfx,0x90,f.player.data());DeniedBeforeNative(f,"full_snapshot_ingame_gfx_backref_mismatch");}
  {Fixture f;Put(f.ingame_handler,0x40,f.player.data());DeniedBeforeNative(f,"full_snapshot_ingame_handler_backref_mismatch");}
  {Fixture f;ConfirmInvalidates(f);Put(f.players,0x30,std::uint8_t{1});
    DeniedBeforeNative(f,"full_snapshot_ingame_transition_pending");
    Require(!f.ingame_witness.observed && !f.ingame_witness.ready,"transition immediately invalidates witness");
    Put(f.players,0x30,std::uint8_t{0});Epoch(f,2);
    DeniedBeforeNative(f,"full_snapshot_ingame_first_completed_frame_required");
    Epoch(f,3);Observed(f);}
  {Fixture f;ConfirmInvalidates(f);
    std::array<std::byte,0x48> replacement_handler{};
    Put(replacement_handler,0,f.bindings.ingame_ready.handler_vtable);
    Put(replacement_handler,0x40,f.jomini.data());Put(f.ingame_gfx,0x88,replacement_handler.data());
    Epoch(f,2);DeniedBeforeNative(f,"full_snapshot_ingame_first_completed_frame_required");
    Epoch(f,3);Observed(f);}
  {Fixture f;ConfirmInvalidates(f);
    auto replacement_root=f.jomini;
    f.jomini_slot=replacement_root.data();Put(f.players,0x28,replacement_root.data());
    Put(f.ingame_gfx,0x20,replacement_root.data());Put(f.ingame_handler,0x40,replacement_root.data());
    Epoch(f,2);DeniedBeforeNative(f,"full_snapshot_ingame_first_completed_frame_required");
    Epoch(f,3);Observed(f);}
  {Fixture f;ConfirmInvalidates(f);Epoch(f,0);
    DeniedBeforeNative(f,"full_snapshot_ingame_completed_epoch_restarted");Epoch(f,1);Observed(f);}
  {Fixture f;FreshWitness(f,(std::numeric_limits<std::uint64_t>::max)());
    DeniedBeforeNative(f,"full_snapshot_ingame_first_completed_frame_required");Epoch(f,0);
    DeniedBeforeNative(f,"full_snapshot_ingame_completed_epoch_restarted");Epoch(f,1);Observed(f);}
  {Fixture f;ConfirmInvalidates(f);f.ingame_witness={};
    DeniedBeforeNative(f,"full_snapshot_ingame_first_completed_frame_required");}
  {Fixture f;FreshWitness(f,10);auto current=f.bindings;
    game::Snapshot out{};FullSnapshotDiagnosticsV1 d{};
    Require(!ReadFullSnapshotV1(current,out,d,f.ingame_witness) && f.core_calls==0,
      "first copied Full bindings do not contain a readiness witness");
    Epoch(f,11);current=f.bindings;
    Require(ReadFullSnapshotV1(current,out,d,f.ingame_witness) && d.complete && out==f.Expected(),
      "re-copying immutable bindings preserves separately owned frame witness");}
  {Fixture f;f.bindings.ingame_ready.exact_build_admitted=false;
    const auto d=Unavailable(f);Require(d.stage=="binding" && f.core_calls==0 &&
      !f.ingame_witness.observed,"unsupported readiness binding is zero-call and invalidates witness");}
  {Fixture f;f.bindings.ingame_ready.core.jomini_state_slot=&f.pending_slot;
    const auto d=Unavailable(f);Require(d.stage=="binding" && f.core_calls==0,"mixed Core binding is rejected before getter");}
  {Fixture f;f.mutation=Mutation::ingame_epoch;
    const auto d=Unavailable(f);Require(d.stage=="ingame" &&
      d.reason=="full_snapshot_ingame_completed_frame_changed" && f.selectors>0,
      "epoch changes inside actual child pass clear Full instead of crossing completed frames");}
  {Fixture f;f.mutation=Mutation::ingame_transition;
    const auto d=Unavailable(f);Require(d.stage=="ingame" &&
      d.reason=="full_snapshot_ingame_transition_pending","transition during actual child pass clears Full");}
  {Fixture f;Put(f.jomini,0,std::uintptr_t{1});
    CoreSnapshotPrefix partial{};
    Require(ReadCoreSnapshot(f.bindings.core,partial) && partial.map_ready && f.core_calls==1,
      "front-end Core keeps its actual prefix semantics independent of Full lifecycle gate");}
  std::cout<<"PASS ingame lifecycle actual Full reducer: first/completed epoch, graph/types/backrefs, invalidation, wrap, zero native preinit, Core preserved"<<std::endl;
  return 0;
}
