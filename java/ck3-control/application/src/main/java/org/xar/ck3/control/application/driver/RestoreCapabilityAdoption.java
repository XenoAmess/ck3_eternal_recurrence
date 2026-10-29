package org.xar.ck3.control.application.driver;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.contracts.ExactRef;

/** Archived private-state replay; grants no live authority. */
public final class RestoreCapabilityAdoption {
 public static final class Recovered {
  private final Obj auxiliary;
  private final SemanticEvidence original;
  private final ExactRef stateSource;
  private Recovered(Obj auxiliary,SemanticEvidence original,ExactRef stateSource){this.auxiliary=auxiliary;this.original=original;this.stateSource=stateSource;}
  public Obj ownerAuxiliary(){return auxiliary;}
  public SemanticEvidence original(){return original;}
  public ExactRef stateSource(){return stateSource;}
 }
 private final ActionPorts.OutcomeArchive archive;
 public RestoreCapabilityAdoption(ActionPorts.OutcomeArchive actualOriginalArchive){archive=Objects.requireNonNull(actualOriginalArchive);}
 public Recovered replay(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,SemanticEvidence original,DriverStateSnapshot.Complete actuallySavedDriver) {
  return new RestoreCapabilityAdoption(archive.withSession(Objects.requireNonNull(borrowed))).replayOriginal(original,actuallySavedDriver);
 }
 private Recovered replayOriginal(SemanticEvidence original,DriverStateSnapshot.Complete actuallySavedDriver) {
  Objects.requireNonNull(original);Objects.requireNonNull(actuallySavedDriver);
  Obj exported=DriverJson.object(load(original.semantic()).bytes(),DriverJson.MAX_NATIVE_BYTES);
  ExactRef stateSource=DriverObservationEvidenceReader.reference(exported.get(DriverCapabilityStateProducer.STATE_SOURCE));
  Obj state=DriverJson.object(load(stateSource).bytes(),DriverJson.MAX_NATIVE_BYTES);
  ExactRef manifestSource=DriverObservationEvidenceReader.reference(exported.get("java_driver_facts_evidence"));RawJson manifest=load(manifestSource);
  require(DriverObservationEvidenceReader.currentDriverReference(manifestSource,manifest).equals(original.originalDriver()),"saved capability state differs from actual archived complete Driver");
  RawJson fullDriver=load(original.originalDriver());require(Arrays.equals(fullDriver.bytes(),actuallySavedDriver.encode()),"capability replay cannot borrow another saved Driver");
  var actual=DriverObservationEvidenceReader.nativeFrame(manifestSource,manifest,archive.loadNativeFrame(original.originalNativePacket()));
  var observation=DriverObservationEvidenceReader.decode(manifestSource,manifest,fullDriver,actual);
  var stamp=new DriverSnapshotFacts.Stamp(observation.driverVersion(),observation.episodeEpoch(),actual.session().game(),actuallySavedDriver.session().episodeRunId(),DriverJson.sha256(fullDriver.bytes()));
  var originalOwner=new Known(actuallySavedDriver,stamp,original.originalDriver(),List.of(),observation.originalSemanticFields(),Optional.empty(),Optional.of(observation));
  var joined=new DriverObservationAssembler().assemble(actual,observation,original.originalNativePacket());
  require(joined instanceof DriverObservationAssembler.Complete,"saved capability native/Driver join incomplete");var frame=(DriverObservationAssembler.Complete)joined;
  require(frame.semantic().equals(exported),"saved export differs from its exact current original observation manifest");
  require(frame.identity().equals(original.frame())&&frame.observedAt().equals(original.observedAt())
      &&Arrays.equals(NativeDriverStamp.encode(frame,originalOwner),load(original.driverStamp()).bytes()),"saved capability replay crossed original SEM/stamp frame");
  Obj cache=DriverCapabilityStateProducer.replay(frame,originalOwner,stateSource,archive);
  Map<String,Value> extras=new LinkedHashMap<>(cache.members());
  for(String key:List.of("backend_id","source","diagnostics")) {
   require(observation.originalSemanticFields().members().containsKey(key),"actual original native protocol extra missing: "+key);
   extras.put(key,observation.originalSemanticFields().get(key));
  }
  var replayedFacts=new DriverObservationFacts(actuallySavedDriver,observation.driverVersion(),observation.episodeEpoch(),observation.transport(),
      observation.snapshotId(),observation.nativeRevision(),observation.nativeStateSha256(),observation.publicRevision(),observation.observationVersion(),
      observation.source(),new Obj(extras),observation.semanticFactsEvidence());
  var replayed=new DriverObservationAssembler().assemble(actual,replayedFacts,original.originalNativePacket());
  require(replayed instanceof DriverObservationAssembler.Complete complete&&complete.semantic().equals(exported),"saved complete semantic export differs from actual full private auxiliary/native producer replay");
  require(Objects.equals(exported.get(DriverRuntimeCapabilities.AUXILIARY_KEY),cache.get(DriverRuntimeCapabilities.AUXILIARY_KEY)),"saved capability input reference differs");
  return new Recovered(cache,original,stateSource);
 }
 /** Verify a real cold reducer's result retains the verified configuration/source lineage and explicit private cache semantics. */
 public Obj requireReduced(Recovered recovered,Obj actualColdReducerAuxiliary) {
  Objects.requireNonNull(recovered);Objects.requireNonNull(actualColdReducerAuxiliary);
  for(String key:List.of("capability_configuration","capability_session_paths","capability_initialization_source",DriverCapabilityStateProducer.STATE_SOURCE,"capability_state_version",DriverRuntimeCapabilities.AUXILIARY_KEY))
   require(Objects.equals(recovered.ownerAuxiliary().get(key),actualColdReducerAuxiliary.get(key)),"cold reducer replaced verified original capability lineage: "+key);
  for(String key:List.of("arrange_marriage_choices","arrange_marriage_query_sequence","campaign_root_context_query","active_combat_retreat_token","episode_seed","episode_transition","succession_reconciliation","independent_battle_speed_readiness","capability_read_sources"))
   require(actualColdReducerAuxiliary.members().containsKey(key),"actual cold reducer omitted private cache: "+key);
  var presentation=DriverCapabilityStateProducer.sessionPresentation(actualColdReducerAuxiliary);
  require(presentation.driverStateRestored(),"actual cold adoption must expose its genuine restored session result");
  require(presentation.bindingState()==org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.BindingState.ACTIVE_RESUMED
      &&presentation.restoreKind().filter(kind->kind==org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.RestoreKind.COLD_CHECKPOINT
       ||kind==org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.RestoreKind.MANAGED_RESTORE_CHECKPOINT_REBIND
       ||kind==org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.RestoreKind.MANAGED_HOT_RESTORE).isPresent(),"actual cold reducer restore kind/binding state unavailable");
  require(new Arr(List.of()).equals(actualColdReducerAuxiliary.get("arrange_marriage_choices"))&&actualColdReducerAuxiliary.get("arrange_marriage_query_sequence")==Nil.INSTANCE
      &&actualColdReducerAuxiliary.get("active_combat_retreat_token")==Nil.INSTANCE,"cold reducer must genuinely invalidate episode-local consumable choices/tokens");
  require(actualColdReducerAuxiliary.members().containsKey(DriverSemanticReadState.SOURCES)
      &&DriverSemanticReadState.clearForCold(actualColdReducerAuxiliary).equals(actualColdReducerAuxiliary),"actual cold reducer must invalidate every fixed semantic read-cache slot");
  return actualColdReducerAuxiliary;
 }
 private RawJson load(ExactRef ref){RawJson value=archive.loadMaterial(ref);require(value.bytes().length==ref.bytes()&&DriverJson.sha256(value.bytes()).equals(ref.sha256()),"original restore capability material differs");return value;}
}
