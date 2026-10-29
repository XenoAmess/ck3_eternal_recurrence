package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.HeirPreflightFailure;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.HeirPreconditionFailure;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.LocalRootRevisionFailure;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.RootRevisionPreconditionFailure;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.ReadonlyPlanningRetry;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Software original bytes and explicit authorities exercise the production guard/coordinator/retry chain.
 * These fixture authorities never claim a real Game, native source qualification, Ready or business success. */
final class HeirPreflightPublicPlanningTest {
    private static final Instant NOW=Instant.parse("2026-10-23T16:00:00Z");
    private static final String MESSAGE="current heir relationship needs a paused living-player map frame";
    private static final OperationKey OPERATION=new OperationKey("query-current-first-heir-relationship-v1-private");
    private static final RawJson FRESH=new RawJson("{\"snapshot_id\":\"fresh-whole-plan\",\"revision\":3}".getBytes(java.nio.charset.StandardCharsets.UTF_8));

    @Test void sourceGuardToCoordinatorToPublicPlanConsumesOneWholeReplanBeforeAnyPrepareOrSend() throws Exception {
        Fixture f=new Fixture();AtomicInteger plans=new AtomicInteger();
        RawJson result=ReadonlyPlanningRetry.plan(()->{
            if(plans.incrementAndGet()==1)f.read(f.stale);
            return FRESH;
        });
        assertEquals(2,plans.get());assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
        Obj body=DriverJson.object(result.bytes(),RawJson.MAXIMUM_BYTES);
        Obj marker=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(body.get("readonly_planning_replan_v1"),"actual retry marker");
        assertEquals(new IntegerValue(BigInteger.ONE),marker.get("fresh_replans"));
        assertEquals(new IntegerValue(BigInteger.ZERO),marker.get("business_actions_replayed"));
        Arr rejected=(Arr)marker.get("original_rejections");
        assertEquals(new Obj(Map.of("class",new Text("heir_readonly_frame_precondition"),"business_submission",new Bool(false))),rejected.items().getFirst());
    }
    @Test void secondRealPreflightFailurePreservesTheOriginalPublicFaultAndCannotPlanAThirdTime() {
        Fixture f=new Fixture();AtomicInteger plans=new AtomicInteger();
        RuntimeException failure=assertThrows(RuntimeException.class,()->ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();f.read(f.stale);return FRESH;
        }));
        assertInstanceOf(HeirPreconditionFailure.class,failure);assertEquals(MESSAGE,failure.getMessage());assertEquals(2,plans.get());
        assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }
    @Test void proofClosesWithItsSourceCallbackAndCannotBeFedIntoAnotherPublicPlanningBudget() throws Exception {
        Fixture f=new Fixture();HeirPreflightFailure proof=captureProof(f);
        assertSame(f.session,proof.session());assertSame(f.contract,proof.contract());assertSame(f.stale,proof.request());
        assertSame(proof.originalFailure(),proof.getCause());assertInstanceOf(HeirPreconditionFailure.class,proof.originalFailure());assertEquals(MESSAGE,proof.originalFailure().getMessage());
        assertThrows(IllegalArgumentException.class,proof::requireOriginal);
        PlanningReadRequest copied=new PlanningReadRequest(f.stale.origin(),f.stale.source(),f.stale.sessionId(),f.stale.operation(),f.stale.arguments(),f.stale.deadline());
        assertThrows(IllegalArgumentException.class,()->proof.requireOriginal(f.session,f.contract,copied,f.archive));
        assertThrows(IllegalArgumentException.class,()->proof.requireOriginal(f.session,f.contract(),f.stale,f.archive));
        Fixture foreign=new Fixture();assertThrows(IllegalArgumentException.class,()->proof.requireOriginal(foreign.session,f.contract,f.stale,f.archive));
        f.head=head(4);assertThrows(IllegalArgumentException.class,proof::requireOriginal);f.head=head(3);
        AtomicInteger attempts=new AtomicInteger();
        assertThrows(IllegalArgumentException.class,()->ReadonlyPlanningRetry.plan(()->{
            attempts.incrementAndGet();ReadonlyPlanningRetry.heirPreflightFailed(proof);return FRESH;
        }));
        assertEquals(1,attempts.get());assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }
    @Test void originalSemanticMutationCannotMintAProofOrTriggerAWholePlanRetry() throws Exception {
        Fixture f=new Fixture();f.values.put(f.semantic.semantic(),new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        AtomicInteger plans=new AtomicInteger();ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();assertInstanceOf(PlanningReadResult.Unavailable.class,f.read(f.stale));return FRESH;
        });
        assertEquals(1,plans.get());assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }
    private static HeirPreflightFailure captureProof(Fixture f)throws Exception {
        var captured=new AtomicReference<HeirPreflightFailure>();AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{
            if(plans.incrementAndGet()==1) {
                try {f.read(f.stale);throw new AssertionError("actual source preflight was not rejected");}
                catch(RuntimeException marker) {
                    captured.set(assertInstanceOf(HeirPreflightFailure.class,marker.getCause()));throw marker;
                }
            }
            return FRESH;
        });
        assertEquals(2,plans.get());return java.util.Objects.requireNonNull(captured.get());
    }
    @Test void wrongSourceAndMalformedExpectedRevisionDoNotMintThePrivateProofOrRetry() throws Exception {
        Fixture f=new Fixture();var foreign=new G2Source(f.source.machineId(),f.source.observedAtUtc(),f.source.exactBuild(),f.material("foreign-source"));
        PlanningReadRequest wrongSource=new PlanningReadRequest(f.stale.origin(),foreign,f.stale.sessionId(),OPERATION,f.stale.arguments(),f.stale.deadline());
        for(PlanningReadRequest request:List.of(wrongSource,
                new PlanningReadRequest(f.stale.origin(),f.source,f.stale.sessionId(),OPERATION,new Obj(Map.of("expected_native_revision",new Bool(true))),f.stale.deadline()),
                new PlanningReadRequest(f.stale.origin(),f.source,f.stale.sessionId(),OPERATION,new Obj(Map.of()),f.stale.deadline()))) {
            AtomicInteger plans=new AtomicInteger();ReadonlyPlanningRetry.plan(()->{
                plans.incrementAndGet();assertInstanceOf(PlanningReadResult.Unavailable.class,f.read(request));return FRESH;
            });assertEquals(1,plans.get());
        }
        assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }
    @Test void sameMessageAndUpstreamReadinessIOExceptionDoNotBecomePreflightProof() throws Exception {
        Fixture f=new Fixture();f.upstreamUnavailable=true;AtomicInteger plans=new AtomicInteger();
        var wrapped=assertThrows(UncheckedIOException.class,()->f.guard.verify(f.head,f.stale,f.contract));
        assertSame(f.upstreamFailure,wrapped.getCause());
        assertEquals("actual Root planning-read authority unavailable: IOException:"+MESSAGE,wrapped.getMessage());
        ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();
            var unavailable=assertInstanceOf(PlanningReadResult.Unavailable.class,f.read(f.stale));
            assertEquals("UncheckedIOException:"+wrapped.getMessage(),unavailable.reason());
            assertTrue(unavailable.original().isEmpty());
            assertTrue(unavailable.decodeFailure().isEmpty());
            assertTrue(unavailable.observedFailure().isEmpty());
            return FRESH;
        });
        assertEquals(1,plans.get());assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
        AtomicInteger generic=new AtomicInteger();IOException original=new IOException(MESSAGE);
        assertSame(original,assertThrows(IOException.class,()->ReadonlyPlanningRetry.plan(()->{generic.incrementAndGet();throw original;})));
        assertEquals(1,generic.get());
        AtomicInteger reasonOnly=new AtomicInteger();IllegalArgumentException textOnly=new IllegalArgumentException(MESSAGE);
        assertSame(textOnly,assertThrows(IllegalArgumentException.class,()->ReadonlyPlanningRetry.plan(()->{reasonOnly.incrementAndGet();throw textOnly;})));
        assertEquals(1,reasonOnly.get());
    }
    @Test void actualConsumedUnknownReadHasOneSendAndCannotBeReclassifiedAsUnsentHeirFailure() throws Exception {
        Fixture f=new Fixture();AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();var result=assertInstanceOf(PlanningReadResult.Unavailable.class,f.read(f.current));
            assertInstanceOf(NativeActionPort.Unknown.class,result.original().orElseThrow());return FRESH;
        });
        assertEquals(1,plans.get());assertEquals(1,f.prepared.get());assertEquals(1,f.sent.get());
    }

    @Test void actualAcknowledgedReadFollowedByAChangedPhysicalFrameCannotUseTheUnsentPreflightSeam() throws Exception {
        Fixture f=new Fixture();Fixture changed=new Fixture(DriverObservationAssemblerTest.STATE.replace("\"paused\":true","\"paused\":false"));
        f.values.putAll(changed.values);f.nativeFrames.putAll(changed.nativeFrames);f.afterLease=changed.lease;f.returnAck=true;
        AtomicInteger plans=new AtomicInteger();ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();var unavailable=assertInstanceOf(PlanningReadResult.Unavailable.class,f.read(f.current));
            assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());return FRESH;
        });
        assertEquals(1,plans.get());assertEquals(1,f.prepared.get());assertEquals(1,f.sent.get());
    }

    @Test void directGuardCallWithoutTheCoordinatorsActualPreReadPhaseCannotGrantPublicRetry() {
        Fixture f=new Fixture();AtomicInteger plans=new AtomicInteger();
        HeirPreconditionFailure failure=assertThrows(HeirPreconditionFailure.class,()->ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();f.guard.verify(f.head,f.stale,f.contract);return FRESH;
        }));
        assertEquals(MESSAGE,failure.getMessage());assertEquals(1,plans.get());
        assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }

    private static Head head(long sequence) {
        var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id","test-machine").put("sequence",sequence).put("window_id",1)
                .put("status","running").put("start_date_raw",53144328).put("target_days",1).put("target_date_raw",53144352)
                .put("last_settled_cycles",0).put("last_settled_date_raw",53144328);
        return new Head(ContinuityState.fromJson(row,"test-machine"),List.of(),List.of(),List.of(),false);
    }
    private static final class Fixture {
        final Map<ExactRef,RawJson> values=new HashMap<>();
        final Map<ExactRef,byte[]> nativeFrames=new HashMap<>();
        final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        final AtomicInteger prepared=new AtomicInteger(),sent=new AtomicInteger();
        final IOException upstreamFailure=new IOException(MESSAGE);
        Head head=head(3);boolean upstreamUnavailable,returnAck,afterNative;ReadinessAuthority.LeaseSnapshot afterLease;
        final ContinuityStorePort.Session session=session();
        final ActionPorts.OutcomeArchive archive=archive();
        final G2Source source=new G2Source("test-machine",NOW.toString(),"software-test-source",material("source"));
        final ExactRef definition=material("current-relation-definition");
        final ReadContract<Obj> contract=contract();
        final RootReadContractCatalog catalog=RootReadContractCatalog.staticOnly(List.of(contract));
        final DriverObservationAssembler.Complete frame;
        final SemanticEvidence semantic;
        final ReadinessAuthority.LeaseSnapshot lease;
        final PlanningReadRequest stale,current;
        final PlanningReadCoordinator coordinator;
        final RootPlanningReadGuard guard;
        Fixture(){this(DriverObservationAssemblerTest.STATE);}
        Fixture(String actualNativeState){this(actualNativeState,BigInteger.TWO);}
        Fixture(String actualNativeState,BigInteger actualPublicRevision) {
            var nativeFrame=DriverObservationAssemblerTest.actual(actualNativeState);
            var known=DriverStateAssemblerTest.known();ExactRef nativeRef=putNative(nativeFrame.originalPacket());
            ExactRef driver=put(RawJson.fullMaterial(known.driver().encode()));
            RawJson manifest=DriverObservationEvidenceReader.encode(known,nativeFrame,actualPublicRevision,1,source,
                    new Obj(Map.of("software_fixture",new Bool(true))),driver);
            ExactRef manifestRef=put(manifest);
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,archive.loadFullMaterial(driver),nativeFrame);
            frame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,facts,nativeRef));
            semantic=new SemanticEvidence(frame.identity(),put(RawJson.fullMaterial(DriverJson.encode(frame.semantic()))),nativeRef,material("stamp"),driver,NOW);
            lease=new ReadinessAuthority.LeaseSnapshot(frame,known,new Obj(Map.of("software_query",new Text(OPERATION.value()))),semantic,
                    Set.of(OPERATION),Set.of("software-query-source"),material("hello"),material("heartbeat"),NOW.plusSeconds(30),material("source-qualification"));
            var before=frame.identity();var actual=before.frame();var ids=actual.identity();
            var old=new ObservationIdentity(before.machineId(),before.game(),new JointBudgetSelector.ProposalFrame(
                    new JointBudgetSelector.Frame(ids.player(),ids.nativeRevision().subtract(BigInteger.ONE),ids.dateRaw()),
                    "snapshot-before-current",actual.revision(),actual.episodeRunId()),before.observationVersion());
            stale=request(old);current=request(before);
            ReadinessAuthority authority=new ReadinessAuthority() {
                @Override public <T> T current(ContinuityStorePort.Session same,ObservationIdentity expected,Instant callerDeadline,CheckedWork<T> work)throws IOException {
                    assertSame(session,same);assertEquals(frame.identity().game(),expected.game());assertEquals(NOW.plusSeconds(20),callerDeadline);
                    if(upstreamUnavailable)throw upstreamFailure;
                    return work.apply(returnAck&&afterNative?java.util.Objects.requireNonNull(afterLease):lease);
                }
            };
            guard=new RootPlanningReadGuard(authority,()->session,archive,source,Clock.fixed(NOW,ZoneOffset.UTC),"software-heir-guard",
                    (same,ref,maximum)->{assertSame(session,same);return bytes(ref);},catalog);
            coordinator=new PlanningReadCoordinator(catalog,journal(),guard,(permit,request,deadline)->{
                permit.consumeOnce();sent.incrementAndGet();afterNative=true;
                if(returnAck) {
                    RawJson ack=new RawJson(StrictJson.canonical(StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",permit.requestId()).put("ok",true).putNull("result")));
                    byte[] packet=java.nio.ByteBuffer.allocate(ack.bytes().length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(ack.bytes().length).put(ack.bytes()).array();
                    return new NativeActionPort.AckReceived(permit.requestId(),true,Optional.empty(),ack,packet);
                }
                return new NativeActionPort.Unknown(permit.requestId(),"software actual sent UNKNOWN",new byte[]{1,2,3},Optional.empty());
            },archive,Clock.fixed(NOW,ZoneOffset.UTC));
        }
        PlanningReadResult<Obj> read(PlanningReadRequest request){return coordinator.read(session,contract,request);}
        PlanningReadRequest request(ObservationIdentity before){return new PlanningReadRequest(before,source,frame.sessionId(),OPERATION,
                new Obj(Map.of("expected_native_revision",new IntegerValue(before.frame().identity().nativeRevision()))),NOW.plusSeconds(20));}
        ReadContract<Obj> contract(){return new ReadContract<>("family/current-first-heir-relationship12004/v2",OPERATION,Optional.empty(),
                "source_qualified_current_first_heir_relationship_v2",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definition,
                (request,id)->{prepared.incrementAndGet();return new NativeRequest(OPERATION.value(),Optional.empty(),new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));},
                receipt->new Obj(Map.of()),receipt->new Obj(Map.of()));}
        ExactRef material(String role){return put(new RawJson(StrictJson.canonical(StrictJson.object().put("software_original_role",role))));}
        ExactRef put(RawJson raw){var ref=new ExactRef(Path.of(System.getProperty("java.io.tmpdir"),"xar-heir-software-originals",ActionCodec.sha256(raw.bytes())+".json").toAbsolutePath().toString(),raw.bytes().length,ActionCodec.sha256(raw.bytes()));values.putIfAbsent(ref,raw);return ref;}
        ExactRef putNative(byte[] packet){var ref=new ExactRef(Path.of(System.getProperty("java.io.tmpdir"),"xar-heir-software-originals",ActionCodec.sha256(packet)+".native").toAbsolutePath().toString(),packet.length,ActionCodec.sha256(packet));nativeFrames.put(ref,packet.clone());return ref;}
        byte[] bytes(ExactRef ref){RawJson raw=java.util.Objects.requireNonNull(values.get(ref));StrictJson.require(ref.sha256().equals(ActionCodec.sha256(raw.bytes())),"software retained original bytes SHA changed");assertEquals(ref.bytes(),raw.bytes().length);return raw.bytes();}
        ContinuityStorePort.Session session(){return (ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->switch(method.getName()) {
            case "head"->head;
            case "capturePin"->{ExactRef ref=(ExactRef)args[0];bytes(ref);yield new Pin(ref,new FileIdentity("1","1","1",NOW.toString(),ref.bytes()));}
            case "verifyPin"->{Pin pin=(Pin)args[0];bytes(pin.reference());yield null;}
            default->throw new AssertionError("fixture permits no writer mutation: "+method.getName());
        });}
        ActionPorts.OutcomeArchive archive(){return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->switch(method.getName()) {
            case "withSession"->{assertSame(session,args[0]);yield proxy;}
            case "preserveMaterial"->put((RawJson)args[0]);
            case "loadMaterial"->new RawJson(bytes((ExactRef)args[0]));
            case "loadFullMaterial"->RawJson.fullMaterial(bytes((ExactRef)args[0]));
            case "loadNativeFrame"->{ExactRef ref=(ExactRef)args[0];byte[] packet=java.util.Objects.requireNonNull(nativeFrames.get(ref));assertEquals(ref.sha256(),ActionCodec.sha256(packet));yield packet.clone();}
            case "preserve"->{var ref=material("actual-unknown-outcome");outcomes.put(ref,(NativeActionPort.DispatchOutcome)args[0]);yield ref;}
            case "load"->java.util.Objects.requireNonNull(outcomes.get((ExactRef)args[0]));
            case "referenceOf"->outcomes.entrySet().stream().filter(row->row.getValue()==args[0]).map(Map.Entry::getKey).findFirst().orElseThrow();
            case "preserveRequest"->{var ref=material("actual-prepared-request");requests.put(ref,(NativeRequest)args[0]);yield ref;}
            case "loadRequest"->java.util.Objects.requireNonNull(requests.get((ExactRef)args[0]));
            case "requestReferenceOf"->requests.entrySet().stream().filter(row->row.getValue()==args[0]).map(Map.Entry::getKey).findFirst().orElseThrow();
            default->throw new AssertionError("fixture permits no business/archive invention: "+method.getName());
        });}
        ActionJournal journal(){return new ActionJournal(){
            private final LockedJournal locked=new LockedJournal(){
                @Override public ContinuityStorePort.Session writerSession(){return session;}
                @Override public Optional<ActionReceipt> find(String action){return Optional.empty();}
                @Override public List<ActionReceipt> unresolved(){return List.of();}
                @Override public ActionReceipt append(ActionCommand command,String hash,ActionState state){throw new AssertionError("no action commit");}
            };
            @Override public <T> T locked(Function<LockedJournal,T> work){return work.apply(locked);}
            @Override public <T> T locked(ContinuityStorePort.Session same,Function<LockedJournal,T> work){assertSame(session,same);return work.apply(locked);}
        };}
    }
    @Test void actualTypedPublicRootProducerBeforeSendReplansOnceWithTheOriginalFiveFieldProjection() throws Exception {
        RootFixture f=new RootFixture();AtomicInteger plans=new AtomicInteger();
        RawJson result=ReadonlyPlanningRetry.plan(()->{if(plans.incrementAndGet()==1)f.read(f.request(BigInteger.ONE));return FRESH;});
        assertEquals(2,plans.get());assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
        Obj marker=(Obj)DriverJson.object(result.bytes(),RawJson.MAXIMUM_BYTES).get("readonly_planning_replan_v1");
        Obj rejection=(Obj)((Arr)marker.get("original_rejections")).items().getFirst();
        assertEquals(new Obj(Map.of("class",new Text("campaign_root_local_revision_changed_before_send"),"business_submission",new Bool(false),
                "expected_public_revision",new IntegerValue(BigInteger.ONE),"current_public_revision",new IntegerValue(BigInteger.TWO),
                "failed_root_query_native_request_sent",new Bool(false))),rejection);
    }
    @Test void rootAndHeirConsumeTheSameSinglePublicPlanningBudget() {
        Fixture heir=new Fixture();RootFixture root=new RootFixture();AtomicInteger plans=new AtomicInteger();
        RootRevisionPreconditionFailure failure=assertThrows(RootRevisionPreconditionFailure.class,()->ReadonlyPlanningRetry.plan(()->{
            if(plans.incrementAndGet()==1)heir.read(heir.stale);else root.read(root.request(BigInteger.ONE));return FRESH;
        }));
        assertEquals("campaign-root revision mismatch: expected 1, current 2",failure.getMessage());
        assertEquals(2,plans.get());assertEquals(0,heir.sent.get());assertEquals(0,root.sent.get());
    }
    @Test void rootProofClosesWithItsActualCallbackAndCannotBeReusedInANewBudget() throws Exception {
        RootFixture f=new RootFixture();var retained=new AtomicReference<LocalRootRevisionFailure>();AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{
            if(plans.incrementAndGet()==1)try {f.read(f.request(BigInteger.ONE));}
            catch(RuntimeException marker){retained.set(assertInstanceOf(LocalRootRevisionFailure.class,marker.getCause()));throw marker;}
            return FRESH;
        });
        LocalRootRevisionFailure proof=java.util.Objects.requireNonNull(retained.get());
        assertInstanceOf(RootRevisionPreconditionFailure.class,proof.originalFailure());
        assertThrows(IllegalArgumentException.class,proof::requireOriginal);
        AtomicInteger attempts=new AtomicInteger();assertThrows(IllegalArgumentException.class,()->ReadonlyPlanningRetry.plan(()->{
            attempts.incrementAndGet();ReadonlyPlanningRetry.rootRevisionFailed(proof);return FRESH;
        }));
        assertEquals(1,attempts.get());assertEquals(0,f.sent.get());
    }
    @Test void internalRootCannotMintThePublicSourceFaultOrRetry() throws Exception {
        RootFixture f=new RootFixture();AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{plans.incrementAndGet();assertInstanceOf(PlanningReadResult.Unavailable.class,
                f.read(f.request(BigInteger.ONE,FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS)));return FRESH;});
        assertEquals(1,plans.get());assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }
    @Test void futureAndSigned64BoundaryKeepTheOriginalFaultWithoutAReplanPrepareOrSend() {
        RootFixture current=new RootFixture();RootFixture boundary=new RootFixture(BigInteger.ONE.shiftLeft(63));
        RootFixture wide=new RootFixture(BigInteger.ONE.shiftLeft(100));
        for(var pair:List.of(new RootCase(current,current.request(BigInteger.valueOf(3))),
                new RootCase(boundary,boundary.request(BigInteger.ONE)),new RootCase(wide,wide.request(BigInteger.ONE)))) {
            AtomicInteger plans=new AtomicInteger();
            var failure=assertThrows(RootRevisionPreconditionFailure.class,()->ReadonlyPlanningRetry.plan(()->{
                plans.incrementAndGet();pair.fixture().read(pair.request());return FRESH;
            }));
            assertEquals(pair.request().before().frame().revision(),failure.expectedPublicRevision());
            assertEquals(pair.fixture().lease.frame().identity().frame().revision(),failure.currentPublicRevision());
            assertEquals("campaign-root revision mismatch: expected "+failure.expectedPublicRevision()+", current "+failure.currentPublicRevision(),failure.getMessage());
            assertEquals(1,plans.get());assertEquals(0,pair.fixture().prepared.get());assertEquals(0,pair.fixture().sent.get());
        }
    }
    @Test void zeroExpectedRevisionUsesTheOriginalForwardRetryAndZeroCurrentHasTheOriginalFutureFault() throws Exception {
        RootFixture forward=new RootFixture();AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{if(plans.incrementAndGet()==1)forward.read(forward.request(BigInteger.ZERO));return FRESH;});
        assertEquals(2,plans.get());assertEquals(0,forward.prepared.get());assertEquals(0,forward.sent.get());
        RootFixture zero=new RootFixture(BigInteger.ZERO);
        var failure=assertThrows(RootRevisionPreconditionFailure.class,()->zero.read(zero.request(BigInteger.ONE)));
        assertEquals(BigInteger.ZERO,failure.currentPublicRevision());assertEquals(0,zero.prepared.get());assertEquals(0,zero.sent.get());
    }
    @Test void noPlanningBudgetPreservesTheActualForwardSourceFault() {
        RootFixture f=new RootFixture();
        assertThrows(RootRevisionPreconditionFailure.class,()->f.read(f.request(BigInteger.ONE)));
        assertEquals(0,f.prepared.get());assertEquals(0,f.sent.get());
    }
    @Test void nonretryRootMismatchAfterAcknowledgementKeepsTheActualConsumedAck() throws Exception {
        RootFixture ack=new RootFixture();RootFixture changed=new RootFixture(BigInteger.ONE);
        ack.originals.values.putAll(changed.originals.values);ack.originals.nativeFrames.putAll(changed.originals.nativeFrames);
        ack.afterLease=changed.lease;ack.returnAck=true;AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{
            plans.incrementAndGet();var result=assertInstanceOf(PlanningReadResult.Unavailable.class,ack.read(ack.request(BigInteger.TWO)));
            assertInstanceOf(NativeActionPort.AckReceived.class,result.original().orElseThrow());return FRESH;
        });
        assertEquals(1,plans.get());assertEquals(1,ack.prepared.get());assertEquals(1,ack.sent.get());
    }
    @Test void rootSourceMismatchAndSameMessageGenericErrorsCannotGrantRetry() throws Exception {
        RootFixture f=new RootFixture();var request=f.request(BigInteger.ONE);
        G2Source foreign=new G2Source(f.originals.source.machineId(),f.originals.source.observedAtUtc(),f.originals.source.exactBuild(),f.originals.material("foreign-root-source"));
        var wrong=new PlanningReadRequest(request.origin(),foreign,request.sessionId(),request.operation(),request.arguments(),request.deadline());
        AtomicInteger plans=new AtomicInteger();ReadonlyPlanningRetry.plan(()->{plans.incrementAndGet();assertInstanceOf(PlanningReadResult.Unavailable.class,f.read(wrong));return FRESH;});
        assertEquals(1,plans.get());assertEquals(0,f.sent.get());
        RuntimeException textOnly=new IllegalArgumentException("campaign-root revision mismatch: expected 1, current 2");
        assertSame(textOnly,assertThrows(IllegalArgumentException.class,()->ReadonlyPlanningRetry.plan(()->{throw textOnly;})));
    }
    @Test void rootConsumedUnknownAndAcknowledgedReadCannotBecomeAnUnsentRootRetry() throws Exception {
        RootFixture unknown=new RootFixture();AtomicInteger plans=new AtomicInteger();
        ReadonlyPlanningRetry.plan(()->{plans.incrementAndGet();var result=assertInstanceOf(PlanningReadResult.Unavailable.class,unknown.read(unknown.request(BigInteger.TWO)));assertInstanceOf(NativeActionPort.Unknown.class,result.original().orElseThrow());return FRESH;});
        assertEquals(1,plans.get());assertEquals(1,unknown.sent.get());
        RootFixture ack=new RootFixture();RootFixture changed=new RootFixture(BigInteger.valueOf(3));
        ack.originals.values.putAll(changed.originals.values);ack.originals.nativeFrames.putAll(changed.originals.nativeFrames);
        ack.afterLease=changed.lease;ack.returnAck=true;plans.set(0);
        ReadonlyPlanningRetry.plan(()->{plans.incrementAndGet();var result=assertInstanceOf(PlanningReadResult.Unavailable.class,ack.read(ack.request(BigInteger.TWO)));assertInstanceOf(NativeActionPort.AckReceived.class,result.original().orElseThrow());return FRESH;});
        assertEquals(1,plans.get());assertEquals(1,ack.sent.get());assertEquals(1,ack.prepared.get());
    }
    private record RootCase(RootFixture fixture,PlanningReadRequest request) { }
    private static final class RootFixture {
        final Fixture originals;
        final AtomicInteger prepared=new AtomicInteger(),sent=new AtomicInteger();
        final ReadContract<FinanceReadContracts.Packet> contract;
        final ReadinessAuthority.LeaseSnapshot lease;
        final PlanningReadCoordinator coordinator;
        ReadinessAuthority.LeaseSnapshot afterLease;boolean returnAck,afterNative;
        RootFixture(){this(BigInteger.TWO);}
        RootFixture(BigInteger actualPublicRevision) {
            originals=new Fixture(DriverObservationAssemblerTest.STATE,actualPublicRevision);
            var permission=new FinanceReadContracts.Permission(Optional.of("software-root-native-capability"),"software-installed-root-permission",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP);
            contract=new FinanceReadContracts(query->new FinanceReadContracts.Registration(originals.definition,permission)).contract(FinanceReadContracts.Query.ROOT);
            var base=originals.lease;
            lease=new ReadinessAuthority.LeaseSnapshot(base.frame(),base.driver(),new Obj(Map.of("software_root_capability",new Text("software-root-native-capability"))),base.semantic(),
                    Set.of(FinanceReadContracts.Query.ROOT.operation()),Set.of("software-root-native-capability"),base.originalHello(),base.originalHeartbeat(),base.validUntil(),base.originalSourceQualification());
            ReadinessAuthority authority=new ReadinessAuthority(){
                @Override public <T> T current(ContinuityStorePort.Session same,ObservationIdentity expected,Instant callerDeadline,CheckedWork<T> work)throws IOException {
                    assertSame(originals.session,same);assertEquals(NOW.plusSeconds(20),callerDeadline);return work.apply(returnAck&&afterNative?java.util.Objects.requireNonNull(afterLease):lease);
                }
            };
            var catalog=RootReadContractCatalog.staticOnly(List.of(contract));
            var guard=new RootPlanningReadGuard(authority,()->originals.session,originals.archive,originals.source,Clock.fixed(NOW,ZoneOffset.UTC),"software-root-source-guard",
                    (same,ref,maximum)->{assertSame(originals.session,same);return originals.bytes(ref);},catalog);
            coordinator=new PlanningReadCoordinator(catalog,originals.journal(),guard,(permit,request,deadline)->{
                permit.consumeOnce();sent.incrementAndGet();afterNative=true;
                if(returnAck){RawJson raw=new RawJson(StrictJson.canonical(StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",permit.requestId()).put("ok",true).putNull("result")));
                    byte[] packet=java.nio.ByteBuffer.allocate(raw.bytes().length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(raw.bytes().length).put(raw.bytes()).array();
                    return new NativeActionPort.AckReceived(permit.requestId(),true,Optional.empty(),raw,packet);}
                return new NativeActionPort.Unknown(permit.requestId(),"software actual sent ROOT UNKNOWN",new byte[]{1,2,3},Optional.empty());
            },originals.archive,Clock.fixed(NOW,ZoneOffset.UTC));
        }
        PlanningReadRequest request(BigInteger expected){return request(expected,FinanceReadContracts.RootCapture.PUBLIC_QUERY);}
        PlanningReadRequest request(BigInteger expected,FinanceReadContracts.RootCapture capture){
            var before=originals.frame.identity();var actual=before.frame();
            var expectedIdentity=new ObservationIdentity(before.machineId(),before.game(),new JointBudgetSelector.ProposalFrame(actual.identity(),expected.equals(actual.revision())?actual.snapshotId():"root-public-expected-"+expected,expected,actual.episodeRunId()),before.observationVersion());
            return new PlanningReadRequest(expectedIdentity,originals.source,originals.frame.sessionId(),FinanceReadContracts.Query.ROOT.operation(),FinanceReadContracts.rootArguments(capture),NOW.plusSeconds(20));
        }
        PlanningReadResult<FinanceReadContracts.Packet> read(PlanningReadRequest request){
            return coordinator.read(originals.session,contract,request,new PlanningReadCoordinator.ReadLifecycleObserver(){
                @Override public void prepared(ContinuityStorePort.Session same,ReadContract<?> actual,PlanningReadRequest exact,String id,NativeRequest nativeRequest){prepared.incrementAndGet();}
                @Override public void received(ContinuityStorePort.Session same,ReadContract<?> actual,PlanningReadRequest exact,String id,NativeActionPort.DispatchOutcome original){ }
                @Override public void known(ContinuityStorePort.Session same,ReadContract<?> actual,PlanningReadResult.Known<?> known){ }
                @Override public void failed(ContinuityStorePort.Session same,ReadContract<?> actual,PlanningReadRequest exact,Optional<NativeActionPort.DispatchOutcome> original,String reason){ }
            });
        }
    }
}
