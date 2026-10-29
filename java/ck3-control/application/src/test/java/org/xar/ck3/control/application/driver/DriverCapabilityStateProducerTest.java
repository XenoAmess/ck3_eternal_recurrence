package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;

final class DriverCapabilityStateProducerTest {
  record Fixture(MemoryArchive archive,NativeObservationPort.ObservedFrame actual,Known current,
          DriverObservationAssembler.Complete frame,DriverCapabilityStateProducer.InitialAuxiliary initial) { }
  static Fixture fresh() {
      MemoryArchive archive=new MemoryArchive();var old=DriverStateAssemblerTest.known();
      var driver=new DriverStateSnapshot.Complete(old.driver().session(),List.of(),old.driver().lastCheckpoint(),old.driver().rollbackWarFailure(),
              old.driver().managedRestoreTransaction(),old.driver().successionExpectation(),old.driver().successionLifecycle(),old.driver().campaignGoal(),old.driver().rollbackWarFailures());
      var full=archive.preserveMaterial(new RawJson(driver.encode()));
      var stamp=new DriverSnapshotFacts.Stamp(3,7,old.stamp().game(),driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
      var bare=new Known(driver,stamp,full,List.of(),new Obj(Map.of()),Optional.empty(),Optional.empty());
      var actual=DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);var nativeSource=archive.preserveNativeFrame(actual);
      Obj protocol=new Obj(Map.of("backend_id",new Text("native-headless"),"source",new Text("injected-dll-named-pipe"),"diagnostics",DriverJson.object(actual.state().bytes(),65536).get("diagnostics")));
      RawJson manifest=DriverObservationEvidenceReader.encode(bare,actual,BigInteger.TWO,1,DriverStateAssemblerTest.source(),protocol,full);
      ExactRef manifestSource=archive.preserveMaterial(manifest);
      var facts=DriverObservationEvidenceReader.decode(manifestSource,manifest,new RawJson(driver.encode()),actual);
      var current=new Known(driver,stamp,full,List.of(),new Obj(Map.of()),Optional.empty(),Optional.of(facts));
      var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,nativeSource));
      var config=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
      var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
              CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
      var policy=archive.preserveMaterial(new RawJson(DriverStateAssemblerTest.bytes("{\"schema\":\"test.actual-new-entry-policy\"}")));
      var initial=DriverCapabilityStateProducer.initializeNewEpisode(frame,current,config,session,policy,archive);
      return new Fixture(archive,actual,current,frame,initial);
  }
  static Known published(Fixture f) {
      var old=f.current();return new Known(old.driver(),old.stamp(),old.originalHistoryBasis(),old.actionRows(),f.initial().auxiliary(),old.loop(),old.observation());
  }
  record Current(Known known,DriverObservationAssembler.Complete frame) { }
  static Current observe(Fixture f,Known before,Obj actualAuxiliary,Instant observedAt) {
      var actual=new NativeObservationPort.ObservedFrame(f.actual().session(),f.actual().snapshotId(),f.actual().nativeRevision(),f.actual().state(),f.actual().originalPacket(),observedAt);
      var extras=new java.util.LinkedHashMap<>(actualAuxiliary.members());
      for(String key:List.of("backend_id","source","diagnostics"))extras.put(key,f.current().observation().orElseThrow().originalSemanticFields().get(key));
      var original=f.archive().materialReferenceOf(new RawJson(before.driver().encode()));
      RawJson manifest=DriverObservationEvidenceReader.encode(before,actual,f.frame().identity().frame().revision(),f.frame().identity().observationVersion(),f.frame().source(),new Obj(extras),original);
      var manifestRef=f.archive().preserveMaterial(manifest);
      var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(before.driver().encode()),actual);
      var known=new Known(before.driver(),before.stamp(),before.originalHistoryBasis(),before.actionRows(),actualAuxiliary,before.loop(),Optional.of(facts));
      return new Current(known,assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,f.archive().preserveNativeFrame(actual))));
  }
  @Test void capabilityV3RetainsEveryStampFieldExceptWallTimeAndBindsCompleteNativeContent() {
      Fixture f=fresh();var first=observe(f,published(f),f.initial().auxiliary(),f.actual().observedAt());
      var later=observe(f,first.known(),first.known().auxiliary(),f.actual().observedAt().plusSeconds(1));
      assertFalse(java.util.Arrays.equals(org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(first.frame(),first.known()),
              org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(later.frame(),later.known())));
      assertEquals(DriverRuntimeCapabilities.capabilityStamp(first.frame(),first.known()),DriverRuntimeCapabilities.capabilityStamp(later.frame(),later.known()));
      assertEquals(new Text(later.known().observation().orElseThrow().nativeStateSha256()),DriverRuntimeCapabilities.capabilityStamp(later.frame(),later.known()).get("native_state_sha256"));
      assertTrue(DriverCapabilityStateProducer.refresh(later.frame(),later.known(),f.archive()).isEmpty());
      Obj capsule=DriverJson.object(f.archive().loadMaterial(DriverObservationEvidenceReader.reference(f.initial().auxiliary().get("capability_inputs"))).bytes(),DriverJson.MAX_NATIVE_BYTES);
      assertEquals(new Text("xar.native-driver-capability-inputs/v3"),capsule.get("schema"));
      byte[] legacy=DriverJson.encode(capsule.with("schema",new Text("xar.native-driver-capability-inputs/v2")));
      assertThrows(IllegalArgumentException.class,()->DynamicCapabilities.DriverInputs.decode(later.frame(),later.known(),new ExactRef("memory/legacy-v2",legacy.length,DriverJson.sha256(legacy)),legacy));
      Obj badStamp=object(capsule.get("driver_stamp"),"driver_stamp").with("native_state_sha256",new Text("a".repeat(64)));
      byte[] forged=DriverJson.encode(capsule.with("driver_stamp",badStamp));
      assertThrows(IllegalArgumentException.class,()->DynamicCapabilities.DriverInputs.decode(later.frame(),later.known(),new ExactRef("memory/forged-native",forged.length,DriverJson.sha256(forged)),forged));
  }
  @Test void planningReplayUsesWholeDriverBytesAndPinsTheExternalSourceWithoutDroppingOtherFields() throws Exception {
      Fixture f=fresh();var first=observe(f,published(f),f.initial().auxiliary(),f.actual().observedAt());
      var later=observe(f,first.known(),first.known().auxiliary(),f.actual().observedAt().plusSeconds(1));
      var observation=new org.xar.ck3.control.application.planning.PlanningObservation(first.frame().semantic(),List.of(),java.util.Set.of(),java.util.Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
      var request=new org.xar.ck3.control.application.planning.PlanningRequest(first.frame().identity(),first.frame().source(),first.frame().sessionId(),Instant.parse("2030-01-01T00:00:00Z"),observation);
      var frame=later.frame();ExactRef sem=f.archive().preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
      ExactRef stamp=f.archive().preserveMaterial(new RawJson(org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(frame,later.known())));
      var evidence=new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(frame.identity(),sem,frame.originalEvidence(),stamp,later.known().originalHistoryBasis(),frame.observedAt());
      ExactRef source=f.archive().preserveMaterial(new RawJson(DriverStateAssemblerTest.bytes("{\"role\":\"actual-source-qualification\"}")));
      var lease=new org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot(frame,later.known(),new Obj(Map.of()),evidence,java.util.Set.of(),java.util.Set.of(),source,source,Instant.parse("2030-01-01T00:00:00Z"),source);
      java.util.concurrent.atomic.AtomicInteger pins=new java.util.concurrent.atomic.AtomicInteger();
      var session=(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session)java.lang.reflect.Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session.class},(proxy,method,args)->{
          if(method.getName().equals("capturePin")){pins.incrementAndGet();assertInstanceOf(ExactRef.class,args[0]);ExactRef ref=ExactRef.class.cast(args[0]);return new org.xar.ck3.control.continuity.writer.WriterContracts.Pin(ref,new org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity("1","2","3","2026-10-23T00:00:00Z",ref.bytes()));}
          if(method.getName().equals("verifyPin"))return null;
          throw new UnsupportedOperationException("planning replay may not write or open another writer: "+method.getName());
      });
      org.xar.ck3.control.application.effects.OriginalEvidencePort originals=(same,ref,maximum)->{
          assertSame(session,same);assertNotEquals(request.source().sourceRef(),ref,"external source must use its actual pin, not an archive fallback");
          if(f.archive().nativeFrames.containsKey(ref))return f.archive().loadNativeFrame(ref);return f.archive().loadMaterial(ref).bytes();
      };
      DriverPlanningEvidence.requireEquivalent(session,request,lease,originals);assertEquals(1,pins.get());
      var forged=frame.semantic().with("unrelated_real_game_fact",new Bool(true));
      var changedFrame=new DriverObservationAssembler.Complete(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),forged,frame.originalEvidence(),frame.observedAt(),DriverObservationAssembler.bindingSha256(forged));
      var changedLease=new org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot(changedFrame,later.known(),lease.capabilities(),evidence,lease.executableSteps(),lease.bridgeCapabilities(),source,source,lease.validUntil(),source);
      assertThrows(IllegalArgumentException.class,()->DriverPlanningEvidence.requireEquivalent(session,request,changedLease,originals));
  }
  @Test void readFlushRejectsTheOldFreezeBeforeItCanTouchTheWriter() throws Exception {
      Fixture f=fresh();Known known=published(f);var journal=new DriverStateAssemblerTest.Journal(DriverStateAssemblerTest.snapshot(known,List.of()));
      var assembler=new DriverStateAssembler(new ActionSnapshotReader(journal),new DriverFactsRepository(known),actual->new DriverObservationFacts.Unavailable(List.of("test has no actual transport")));
      var publisher=new DriverReadHistoryPublisher(assembler,f.archive(),RootReadContractCatalog.staticOnly(List.of()),List.of(f.initial().source()));
      var session=nullSession();
      assembler.withFrozenFacts(frozen->{assertThrows(IllegalArgumentException.class,()->publisher.flushActualReads(session));return null;});
      assertTrue(publisher.flushActualReads(session).isEmpty());
      assertEquals(known.stamp(),assembler.withFrozenFacts(frozen->((Known)frozen.state()).stamp()));
  }
  @Test void actualFramedProducerInitializationAndReplayPreserveCompleteNullAndEmptySemantics() {
      Fixture f=fresh();Known current=published(f);
      Obj replay=DriverCapabilityStateProducer.replay(f.frame(),current,f.initial().source(),f.archive());
      assertEquals(new Arr(List.of()),replay.get("arrange_marriage_choices"));assertEquals(Nil.INSTANCE,replay.get("episode_seed"));
      assertEquals(Nil.INSTANCE,replay.get("campaign_root_context_query"));assertEquals(new Text("active_new"),replay.get("episode_binding_state"));
      assertEquals(f.initial().auxiliary(),replay);assertEquals(f.current().stamp(),f.initial().expectedStamp());
      assertThrows(IllegalArgumentException.class,() -> DriverCapabilityStateProducer.refresh(f.frame(),f.current(),f.archive()));
      assertTrue(DriverCapabilityStateProducer.refresh(f.frame(),current,f.archive()).isEmpty());
  }
  @Test void repositoryPublicationRequiresItsOriginalLockAndExactAuxiliaryCas() {
      Fixture f=fresh();DriverFactsRepository repository=new DriverFactsRepository(f.current());
      assertThrows(IllegalArgumentException.class,() -> repository.publishCapabilityInputs(f.current().stamp(),f.initial().expectedAuxiliarySha256(),f.initial()));
      repository.locked(before -> {
          repository.publishCapabilityInputs(f.current().stamp(),f.initial().expectedAuxiliarySha256(),f.initial());
          assertThrows(IllegalArgumentException.class,() -> repository.publishCapabilityInputs(f.current().stamp(),f.initial().expectedAuxiliarySha256(),f.initial()));return null;
      });
      assertEquals(f.current().stamp(),repository.locked(state -> ((Known)state).stamp()));
      assertEquals(f.initial().auxiliary(),repository.locked(state -> ((Known)state).auxiliary()));
  }
  @Test void actualReadReceiptPublishesMarriageProducerAndItsOriginalReplaySource() {
      Fixture f=fresh();Known current=published(f);
      Obj result=DriverJson.object(DriverStateAssemblerTest.bytes("{\"step\":\"query-arrange-marriage-choices\",\"accepted\":true,\"query_sequence\":7,\"arrange_marriage_choices\":[{\"choice_id\":\"73-74\",\"played_character_id\":73,\"candidate_character_id\":74}]}"),65536);
      var receipt=receipt(f,"query-arrange-marriage-choices",result);var original=f.archive().preserveRead(receipt);
      var actual=new PlanningReadResult.Known<>(result,receipt,original);
      var publication=DriverCapabilityStateProducer.observeRead(f.frame(),current,actual,f.archive());
      var after=new Known(current.driver(),current.stamp(),current.originalHistoryBasis(),current.actionRows(),publication.auxiliary(),current.loop(),current.observation());
      assertEquals(new Arr(DriverCapabilityStateProducer.normalizeMarriageChoices(result.get("arrange_marriage_choices")).stream().map(row -> (Value)row).toList()),after.auxiliary().get("arrange_marriage_choices"));
      assertEquals(new IntegerValue(BigInteger.valueOf(7)),after.auxiliary().get("arrange_marriage_query_sequence"));
      assertEquals(publication.auxiliary(),DriverCapabilityStateProducer.replay(f.frame(),after,publication.source(),f.archive()));
      Obj bad=DriverJson.object(DriverStateAssemblerTest.bytes("{\"step\":\"query-arrange-marriage-choices\",\"accepted\":true,\"query_sequence\":true,\"arrange_marriage_choices\":[]}"),65536);
      var malformed=receipt(f,"query-arrange-marriage-choices",bad);var badRef=f.archive().preserveRead(malformed);
      assertThrows(IllegalArgumentException.class,() -> DriverCapabilityStateProducer.observeRead(f.frame(),current,new PlanningReadResult.Known<>(bad,malformed,badRef),f.archive()));
  }
  @Test void wrongActorAndMissingActualReceiptCannotPublishTheCache() {
      Fixture f=fresh();Known current=published(f);
      Obj bad=DriverJson.object(DriverStateAssemblerTest.bytes("{\"step\":\"query-arrange-marriage-choices\",\"accepted\":true,\"query_sequence\":1,\"arrange_marriage_choices\":[{\"choice_id\":\"99-74\",\"played_character_id\":99,\"candidate_character_id\":74}]}"),65536);
      var receipt=receipt(f,"query-arrange-marriage-choices",bad);var source=f.archive().preserveRead(receipt);
      assertThrows(IllegalArgumentException.class,() -> DriverCapabilityStateProducer.observeRead(f.frame(),current,new PlanningReadResult.Known<>(bad,receipt,source),f.archive()));
      var missing=new ExactRef("memory/missing-read.json",1,"a".repeat(64));
      assertThrows(IllegalArgumentException.class,() -> DriverCapabilityStateProducer.observeRead(f.frame(),current,new PlanningReadResult.Known<>(bad,receipt,missing),f.archive()));
  }
  @Test void nativeMarriageRowsNormalizeOnceAndRejectNoncanonicalAndWrongTokenTypes() {
      Obj nativeRow=new Obj(Map.of("choice_id",new Text("73-74"),"played_character_id",new IntegerValue(BigInteger.valueOf(73)),"candidate_character_id",new IntegerValue(BigInteger.valueOf(74)),"extra_native_diagnostic",new Bool(true)));
      Obj normalized=DriverCapabilityStateProducer.normalizeMarriageChoices(new Arr(List.of(nativeRow))).getFirst();
      assertEquals(new Text("native"),normalized.get("source"));assertFalse(normalized.members().containsKey("extra_native_diagnostic"));
      for(Obj invalid:List.of(nativeRow.with("choice_id",new Text("073-74")),nativeRow.with("candidate_character_id",new IntegerValue(BigInteger.valueOf(73))),nativeRow.with("played_character_id",new Bool(true))))
          assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.normalizeMarriageChoices(new Arr(List.of(invalid))));
      assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.normalizeMarriageChoices(new Arr(List.of(nativeRow,nativeRow))));
  }
  @Test void lifecycleClearInvalidatesReceiptSourcesWithoutInventingUnknownState() {
      Fixture f=fresh();Known current=published(f);var aux=new java.util.LinkedHashMap<>(current.auxiliary().members());
      Obj sources=object(aux.get("capability_read_sources"),"sources");var changed=new java.util.LinkedHashMap<>(sources.members());
      changed.put("marriage",DriverRuntimeCapabilities.referenceJson(f.initial().source()));aux.put("capability_read_sources",new Obj(changed));
      Obj cleared=DriverCapabilityStateProducer.afterEpisodeCacheClear(new Obj(aux));
      assertEquals(Nil.INSTANCE,object(cleared.get("capability_read_sources"),"sources").get("marriage"));
      var without=new Obj(Map.of("historical",new Bool(true)));assertSame(without,DriverCapabilityStateProducer.afterEpisodeCacheClear(without));
  }
  @Test void restoreReplaysTheSavedCompleteSemanticStampAndOriginalCacheSources() {
      Fixture f=fresh();Current observed=observe(f,published(f),f.initial().auxiliary(),f.actual().observedAt().plusSeconds(1));Known current=observed.known();var actualFrame=observed.frame();var semantic=new java.util.LinkedHashMap<>(actualFrame.semantic().members());
      var exported=f.archive().preserveMaterial(new RawJson(DriverJson.encode(new Obj(semantic))));
      var stamp=f.archive().preserveMaterial(new RawJson(org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(actualFrame,current)));
      var evidence=new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(actualFrame.identity(),exported,actualFrame.originalEvidence(),stamp,current.originalHistoryBasis(),actualFrame.observedAt());
      var recovered=new RestoreCapabilityAdoption(f.archive()).replay(nullSession(),evidence,current.driver());
      assertEquals(f.initial().auxiliary(),recovered.ownerAuxiliary());assertEquals(f.initial().source(),recovered.stateSource());
      var bad=new java.util.LinkedHashMap<>(semantic);bad.put("arrange_marriage_query_sequence",new IntegerValue(BigInteger.ONE));
      var badExport=f.archive().preserveMaterial(new RawJson(DriverJson.encode(new Obj(bad))));
      var tampered=new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(evidence.frame(),badExport,evidence.originalNativePacket(),stamp,evidence.originalDriver(),evidence.observedAt());
      assertThrows(IllegalArgumentException.class,()->new RestoreCapabilityAdoption(f.archive()).replay(nullSession(),tampered,current.driver()));
  }
  @Test void onlyTheActiveExactOldLifecycleSubjectMayObserveItsKnownAttemptAndUnknownNeverQualifies() {
      Fixture f=fresh();Known current=published(f);var action=terminalCommand(f,current.stamp().driverVersion());
      var intent=new ActionReceipt(1,8,action,ActionCodec.bodySha256(action),new ActionState.IntentDurable());
      var snapshot=DriverStateAssemblerTest.snapshot(current,List.of(intent));
      assertInstanceOf(DriverStateSnapshot.Complete.class,DriverStateAssembler.projectObservation(current,snapshot,Optional.of(action.actionId())));
      assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.projectObservation(current,snapshot,Optional.empty()));
      var unknown=new ActionReceipt(1,8,action,ActionCodec.bodySha256(action),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual unknown terminal attempt",List.of(f.frame().originalEvidence())));
      assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.projectObservation(current,DriverStateAssemblerTest.snapshot(current,List.of(unknown)),Optional.of(action.actionId())));
      var drift=terminalCommand(f,current.stamp().driverVersion()+1);var stale=new ActionReceipt(1,8,drift,ActionCodec.bodySha256(drift),new ActionState.IntentDurable());
      assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.projectObservation(current,DriverStateAssemblerTest.snapshot(current,List.of(stale)),Optional.of(drift.actionId())));
  }
  @Test void savedThirteenSlotDriverAndCompletePrivateAuxiliaryRoundTripRemovesDeletedNoncacheFields() {
      Fixture f=fresh();Known base=published(f);Obj added=base.auxiliary().with("obsolete_policy_aux",new Text("actual prior private state"));
      Known before=new Known(base.driver(),base.stamp(),base.originalHistoryBasis(),base.actionRows(),added,base.loop(),base.observation());
      var first=DriverCapabilityStateProducer.refresh(f.frame(),before,f.archive()).orElseThrow();
      Map<String,Value> oldExtras=new java.util.LinkedHashMap<>(before.observation().orElseThrow().originalSemanticFields().members());oldExtras.putAll(first.auxiliary().members());
      RawJson manifest=DriverObservationEvidenceReader.encode(before,f.actual(),f.frame().identity().frame().revision(),1,f.frame().source(),new Obj(oldExtras),base.originalHistoryBasis());
      var manifestRef=f.archive().preserveMaterial(manifest);var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(base.driver().encode()),f.actual());
      Map<String,Value> cleared=new java.util.LinkedHashMap<>(first.auxiliary().members());cleared.remove("obsolete_policy_aux");
      Known current=new Known(base.driver(),base.stamp(),base.originalHistoryBasis(),base.actionRows(),new Obj(cleared),base.loop(),Optional.of(facts));
      var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(f.actual(),facts,f.frame().originalEvidence()));
      var second=DriverCapabilityStateProducer.refresh(frame,current,f.archive()).orElseThrow();
      Current finalObservation=observe(f,current,second.auxiliary(),f.actual().observedAt().plusSeconds(1));frame=finalObservation.frame();current=finalObservation.known();
      Map<String,Value> exported=new java.util.LinkedHashMap<>(frame.semantic().members());
      var sem=f.archive().preserveMaterial(new RawJson(DriverJson.encode(new Obj(exported))));
      var stamp=f.archive().preserveMaterial(new RawJson(org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(frame,current)));
      var evidence=new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(frame.identity(),sem,frame.originalEvidence(),stamp,base.originalHistoryBasis(),frame.observedAt());
      var recovered=new RestoreCapabilityAdoption(f.archive()).replay(nullSession(),evidence,base.driver());
      assertFalse(recovered.ownerAuxiliary().members().containsKey("obsolete_policy_aux"));assertEquals(second.auxiliary(),recovered.ownerAuxiliary());
      assertArrayEquals(base.driver().encode(),current.driver().encode());
  }
  static ActionCommand terminalCommand(Fixture f,long subjectVersion) {
      Known known=published(f);var frame=f.frame();
      var evidence=new LifecycleIdentity.Evidence(frame.originalEvidence(),f.archive().preserveMaterial(new RawJson(DriverStateAssemblerTest.bytes("{\"role\":\"hello\"}"))),
              known.observation().orElseThrow().semanticFactsEvidence(),known.originalHistoryBasis(),f.archive().preserveMaterial(new RawJson(DriverStateAssemblerTest.bytes("{\"role\":\"source\"}"))));
      var terminal=new LifecycleIdentity(frame.identity().machineId(),frame.identity().game(),frame.sessionId(),frame.connectionGeneration(),
              new LifecycleIdentity.Subject(known.driver().session().actorId(),known.stamp().episodeRunId(),known.stamp().episodeEpoch(),subjectVersion),
              new LifecycleIdentity.Frame(frame.identity().frame().snapshotId(),frame.identity().frame().revision(),frame.identity().frame().identity().nativeRevision(),frame.identity().frame().identity().dateRaw(),true,true),
              new LifecycleIdentity.Character(known.driver().session().actorId(),false),LifecycleIdentity.TerminalReason.DEAD,evidence,frame.observedAt());
      var expected=new LifecycleExpectedPostcondition(terminal,frame.source(),"test.actual-terminal.v1",LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,
              List.of("native.gameplay_verified","timeline.advance_verified","timeline.checkpoint_eligible").stream().map(key -> (org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue)new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey(key),false)).toList());
      return new ActionCommand("actual-terminal",new CommandOrigin.LifecycleTerminal(terminal),frame.source(),frame.sessionId(),new OperationKey("death-terminal"),new Obj(Map.of()),
              new CommandExpectation.LifecycleTerminal(expected),new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),Instant.parse("2030-01-01T00:00:00Z"));
  }
  static org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session nullSession() {
      return (org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session)java.lang.reflect.Proxy.newProxyInstance(
              DriverCapabilityStateProducerTest.class.getClassLoader(),new Class<?>[]{org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session.class},
              (proxy,method,args)->{throw new UnsupportedOperationException("pure replay must perform no writer operation: "+method.getName());});
  }
  static PlanningReadReceipt receipt(Fixture f,String step,Obj result) {
      var request=new PlanningReadRequest(f.frame().identity(),f.frame().source(),f.frame().sessionId(),new OperationKey(step),new Obj(Map.of()),Instant.parse("2030-01-01T00:00:00Z"));
      var binding=new GuardEvidence(f.frame().identity(),f.frame().source(),f.frame().sessionId(),f.frame().connectionGeneration(),request.operation(),
              f.frame().originalEvidence(),f.frame().originalEvidence(),"test-cache-source",f.frame().observedAt(),request.deadline());
      var guard=new PlanningReadGuard(binding,true,true,true,f.frame().fullBindingSha256());
      RawJson token=new RawJson(DriverJson.encode(result));
      var ack=new NativeActionPort.AckReceived("original-cache-read",true,Optional.of(token),token,DriverObservationAssemblerTest.packet(DriverObservationAssemblerTest.STATE));
      return new PlanningReadReceipt(request,"original-cache-contract","original-cache-read",guard,guard,ack);
  }
  static final class MemoryArchive implements ActionPorts.OutcomeArchive {
      @Override public ActionPorts.OutcomeArchive withSession(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session s){java.util.Objects.requireNonNull(s);return this;}
      final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
      final Map<ExactRef,byte[]> nativeFrames=new HashMap<>();
      private ExactRef ref(String kind,byte[] bytes) { String sha=DriverJson.sha256(bytes);return new ExactRef("D:/test-memory/"+kind+"/"+sha+".json",bytes.length,sha); }
      @Override public ExactRef preserveMaterial(RawJson original) { ExactRef ref=ref("material",original.bytes());materials.putIfAbsent(ref,original);return ref; }
      @Override public RawJson loadMaterial(ExactRef original) { RawJson result=materials.get(original);if(result==null)throw new IllegalArgumentException("original material absent");return result; }
      @Override public ExactRef materialReferenceOf(RawJson original) { ExactRef ref=ref("material",original.bytes());if(!original.equals(materials.get(ref)))throw new IllegalArgumentException("material not preserved");return ref; }
      @Override public ExactRef preserveRead(PlanningReadReceipt original) { var ref=ref("read",original.original().originalFrame().bytes());reads.put(ref,original);return ref; }
      @Override public PlanningReadReceipt loadRead(ExactRef original) { var value=reads.get(original);if(value==null)throw new IllegalArgumentException("original read absent");return value; }
      @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { var ref=ref("read",original.original().originalFrame().bytes());if(!original.equals(reads.get(ref)))throw new IllegalArgumentException("read not preserved");return ref; }
      @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { var ref=ref("native",original.originalPacket());nativeFrames.put(ref,original.originalPacket());return ref; }
      @Override public byte[] loadNativeFrame(ExactRef original) { byte[] raw=nativeFrames.get(original);if(raw==null)throw new IllegalArgumentException("original native frame absent");return raw.clone(); }
      private UnsupportedOperationException unused() { return new UnsupportedOperationException("this static producer test cannot execute a native request or writer action"); }
      @Override public ExactRef preserve(NativeActionPort.DispatchOutcome v) { throw unused(); }
      @Override public NativeActionPort.DispatchOutcome load(ExactRef v) { throw unused(); }
      @Override public ExactRef preserveRequest(NativeRequest v) { throw unused(); }
      @Override public NativeRequest loadRequest(ExactRef v) { throw unused(); }
      @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome v) { throw unused(); }
      @Override public ExactRef requestReferenceOf(NativeRequest v) { throw unused(); }
      @Override public ExactRef preserveRecord(ActionRecord v) { throw unused(); }
      @Override public ActionRecord loadRecord(ExactRef v) { throw unused(); }
      @Override public ExactRef recordReferenceOf(ActionRecord v) { throw unused(); }
      @Override public ExactRef preserveReceipt(ActionReceipt v) { throw unused(); }
      @Override public ActionReceipt loadReceipt(ExactRef v) { throw unused(); }
      @Override public ExactRef receiptReferenceOf(ActionReceipt v) { throw unused(); }
  }

  @Test void configuredVanillaRoundtripsThroughActualPublicTerminalWireWithoutSourceQualification() {
      Fixture f=fresh();
      var vanilla=org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla();
      Obj declared=object(DriverJson.fromNode(vanilla.toJson()),"vanilla lifecycle");
      var lifecycle=new DriverCapabilityStateProducer.PublicTerminalLifecycleData(
              DriverCapabilityStateProducer.PublicTerminalLifecycleMode.OBSERVED_BINDING,
              DriverCapabilityStateProducer.DeclaredLifecyclePresence.VALUE,declared,vanilla,
              Optional.empty(),Optional.empty(),Optional.empty(),List.of());
      var semantic=f.archive().preserveMaterial(new RawJson(DriverJson.encode(f.frame().semantic())));
      var wire=new DriverCapabilityStateProducer.PublicTerminalWire(f.frame().fullBindingSha256(),
              f.frame().originalEvidence(),semantic,f.current().originalHistoryBasis(),BigInteger.TWO,
              new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false),
              Optional.empty(),Optional.empty(),Optional.empty(),lifecycle);
      Obj encoded=wire.toJson();
      var restored=DriverCapabilityStateProducer.decodePublicTerminalWire(DriverJson.encode(encoded));
      assertEquals(wire,restored);
      assertEquals(vanilla,restored.lifecycleInputs().capabilityLifecycle());
      Obj inputs=object(encoded.get("lifecycle_inputs"),"lifecycle_inputs");
      for(String ref:List.of("policy_source","environment_source","native_source"))
          assertEquals(Nil.INSTANCE,inputs.get(ref));
      assertEquals(new Arr(List.of()),inputs.get("source_closure"));
      for(String field:List.of("xar_enabled","environment_sha256")) {
          var missingFields=new java.util.LinkedHashMap<>(declared.members());missingFields.remove(field);
          Obj missing=new Obj(missingFields);
          assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.decodePublicTerminalWire(
                  DriverJson.encode(encoded.with("lifecycle_inputs",inputs.with("capability_lifecycle",missing)))));
          for(Value bad:List.<Value>of(new Bool(true),new IntegerValue(BigInteger.ONE),
                  DriverJson.object("{\"v\":1.0}".getBytes(java.nio.charset.StandardCharsets.UTF_8),1024).get("v"),
                  new Arr(List.of()),new Obj(Map.of()),new Text(""))) {
              Obj changed=declared.with(field,bad);
              assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.decodePublicTerminalWire(
                      DriverJson.encode(encoded.with("lifecycle_inputs",inputs.with("capability_lifecycle",changed)))));
          }
      }
      assertEquals("rogue_one_life",DriverCapabilityStateProducer.privateNullConstructorLifecycle().lifecycle());
      assertEquals(Optional.of("xar_on"),DriverCapabilityStateProducer.privateNullConstructorLifecycle().xarEnabled());
  }
}
