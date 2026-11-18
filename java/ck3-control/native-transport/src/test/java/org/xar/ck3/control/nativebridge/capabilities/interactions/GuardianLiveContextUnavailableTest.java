package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Software callback fixtures exercise the real preparer/effect gates; no native or writer authority is granted. */
final class GuardianLiveContextUnavailableTest {
    private static final ExactRef SOURCE=new ExactRef("guardian-live-context-fixture",1,"a".repeat(64));
    private static final RawJson EMPTY=new RawJson("{}".getBytes(StandardCharsets.UTF_8));

    @Test void actualFlorinReadFailureCarriesItsExactDataWithoutConstructingALegacyContext() {
        Complete actual=florin();
        var ack=new NativeActionPort.AckReceived("context-read",true,Optional.of(EMPTY),EMPTY,new byte[]{1});
        OriginalReadDecodeFailure failure=(contract,request,receipt)->{throw new AssertionError("negative DATA is never replayed as Known");};
        var original=new PlanningReadResult.Unavailable<OrdinaryContext>("actual-context-decode-failure",
                Optional.of(ack),Optional.of(failure),Optional.empty());
        var read=assertInstanceOf(OrdinaryInitiationPreparation.UnavailableFrame.class,
                OrdinaryInitiationPreparation.fromContextRead(actual,original));
        assertSame(actual,read.actual());assertSame(original,read.result());
        var rejected=assertThrows(OrdinaryInitiationPreparation.ContextUnavailableException.class,
                ()->OrdinaryInitiationPreparation.requireAvailable(read));
        assertSame(original,rejected.result());
        assertSame(ack,rejected.result().original().orElseThrow());
        assertSame(failure,rejected.result().decodeFailure().orElseThrow());
        assertEquals("actual-context-decode-failure",rejected.getMessage());
        assertThrows(IllegalArgumentException.class,
                ()->new RootInteractionContextProjection(Build.CROZIER4).project(actual,actual.observedAt().plusSeconds(30)),
                "the same Florin full frame cannot masquerade as archived current4");
    }

    @Test void unavailableLivePreparationNeverTouchesTransportClaimsNativeQueryOrOriginalProjection() {
        Complete actual=florin();var missing=missing();var reads=new AtomicInteger();
        var archive=new NoWritesArchive();
        var frames=unavailableFrames(actual,missing,reads);
        var preparation=preparation(frames,archive);
        var rejected=assertThrows(OrdinaryInitiationPreparation.ContextUnavailableException.class,
                ()->preparation.prepare(null,command(actual),"guardian-request"));
        assertSame(missing,rejected.result());assertEquals(1,reads.get());
        assertEquals(0,archive.references);
    }

    @Test void unavailableLiveEffectRetainsUnknownAndAckWithoutLoadingHistoricalProof() {
        Complete actual=florin();var missing=missing();var command=command(actual);
        for(NativeActionPort.DispatchOutcome outcome:List.of(
                new NativeActionPort.Unknown("guardian-request","original-unknown",new byte[0],Optional.empty()),
                new NativeActionPort.AckReceived("guardian-request",true,Optional.of(EMPTY),EMPTY,new byte[]{1}))) {
            var reads=new AtomicInteger();var archive=new NoWritesArchive();
            var observation=preparation(unavailableFrames(actual,missing,reads),archive)
                    .observeContextResult(null,command,attempt(command),outcome);
            assertSame(missing,observation.unavailable().orElseThrow());
            var pending=assertInstanceOf(ActionPorts.Pending.class,observation.projected().result());
            assertEquals(missing.reason(),pending.reason());
            assertTrue(pending.evidence().contains(actual.originalEvidence()));
            assertTrue(observation.projected().compatibleResult().isEmpty());
            assertEquals(1,reads.get());assertEquals(1,archive.references);
            assertEquals("guardian-request",outcome.requestId());
            assertEquals(command.deadline(),actual.observedAt().plusSeconds(30));
        }
    }

    @Test void unavailableEffectStillRejectsAForeignConnectionBeforeRetainingEvidence() {
        Complete before=florin();
        Complete foreign=new Complete(before.identity(),before.source(),before.sessionId(),BigInteger.TWO,
                before.semantic(),before.originalEvidence(),before.observedAt(),before.fullBindingSha256());
        var archive=new NoWritesArchive();var command=command(before);
        var preparation=preparation(unavailableFrames(foreign,missing(),new AtomicInteger()),archive);
        var unknown=new NativeActionPort.Unknown("guardian-request","original-unknown",new byte[0],Optional.empty());
        assertThrows(IllegalArgumentException.class,
                ()->preparation.observeContextResult(null,command,attempt(command),unknown));
        assertEquals(0,archive.references);
    }

    @Test void unavailableEffectPreservesActualContextReadAckReferenceAndDecodeFailure() {
        var ack=new NativeActionPort.AckReceived("context-read",true,Optional.of(EMPTY),EMPTY,new byte[]{1});
        OriginalReadDecodeFailure failure=(contract,request,receipt)->{throw new AssertionError("not a replay");};
        var original=new PlanningReadResult.Unavailable<OrdinaryContext>("actual-decode-unavailable",
                Optional.of(ack),Optional.of(failure),Optional.empty());
        var archive=new NoWritesArchive();
        var observation=OrdinaryInitiationPreparation.unavailableObservation(original,List.of(SOURCE),archive);
        assertSame(original,observation.unavailable().orElseThrow());
        assertSame(failure,observation.unavailable().orElseThrow().decodeFailure().orElseThrow());
        assertEquals(1,archive.references);
        assertInstanceOf(ActionPorts.Pending.class,observation.projected().result());
        assertTrue(observation.projected().compatibleResult().isEmpty());
    }

    @Test void legacyFrameDefaultsKeepExactAvailableIdentityAndOriginalAfterOrder() {
        Complete actual=NativePendingInteractionConsumerTest.fixture(InteractionJson.F.nullNode(),707,null,List.of());
        Context context=new RootInteractionContextProjection(Build.CROZIER4).project(actual,actual.observedAt().plusSeconds(30));
        var original=new OrdinaryInitiationPreparation.ActualFrame(actual,context);
        var observations=new AtomicInteger();
        var frames=new OrdinaryInitiationPreparation.Frames() {
            @Override public OrdinaryInitiationPreparation.ActualFrame observe(ContinuityStorePort.Session same,ActionCommand command) {
                observations.incrementAndGet();return original;
            }
            @Override public OrdinaryInitiationPreparation.ActualFrame original(ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt) {
                throw new AssertionError("not requested by the default live-read probe");
            }
        };
        assertSame(original,OrdinaryInitiationPreparation.requireAvailable(frames.current(null,command(actual))));
        assertTrue(frames.currentAfter(null,command(actual),attempt(command(actual))).isEmpty());
        assertEquals(1,observations.get(),"legacy effect probe must not observe after before original validation");
    }

    private static OrdinaryInitiationPreparation.Frames unavailableFrames(Complete actual,
            PlanningReadResult.Unavailable<OrdinaryContext> missing,AtomicInteger reads) {
        return new OrdinaryInitiationPreparation.Frames() {
            @Override public OrdinaryInitiationPreparation.FrameRead current(ContinuityStorePort.Session same,ActionCommand command) {
                reads.incrementAndGet();return OrdinaryInitiationPreparation.fromContextRead(actual,missing);
            }
            @Override public Optional<OrdinaryInitiationPreparation.FrameRead> currentAfter(
                    ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt) {
                return Optional.of(current(same,command));
            }
            @Override public OrdinaryInitiationPreparation.ActualFrame observe(ContinuityStorePort.Session same,ActionCommand command) {
                throw new AssertionError("a missing live read cannot project an old Context");
            }
            @Override public OrdinaryInitiationPreparation.ActualFrame original(ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt) {
                throw new AssertionError("unavailable live DATA cannot enter the historical proof reader");
            }
        };
    }

    private static PlanningReadResult.Unavailable<OrdinaryContext> missing() {
        return new PlanningReadResult.Unavailable<>("actual-context-read-unavailable",Optional.empty());
    }
    private static Complete florin() {
        Complete old=NativePendingInteractionConsumerTest.fixture(InteractionJson.F.nullNode(),707,null,List.of());
        ObjectNode semantic=(ObjectNode)DriverJson.toNode(old.semantic());
        var hello=(ObjectNode)semantic.path("diagnostics").get("hello");
        hello.put("expected_ck3_version",ExactCk3Build.CK3_1210.version());
        hello.put("expected_ck3_sha256",ExactCk3Build.CK3_1210.executableSha256());
        G2Source source=new G2Source(old.source().machineId(),old.source().observedAtUtc(),
                ExactCk3Build.CK3_1210.version()+"@sha256:"+ExactCk3Build.CK3_1210.executableSha256(),old.source().sourceRef());
        return new Complete(old.identity(),source,old.sessionId(),old.connectionGeneration(),
                DriverJson.object(DriverJson.encodeNode(semantic),65536),old.originalEvidence(),old.observedAt(),old.fullBindingSha256());
    }
    private static ActionCommand command(Complete actual) {
        var intent=new OrdinaryInitiationIntent("educate_child_interaction",2,
                Optional.of(new OrdinaryInitiationIntent.Education(2,3,List.of())),Optional.empty());
        var expected=new ExpectedPostcondition(1,actual.identity(),actual.source(),GuardianOutgoingEffects.SCHEMA,
                List.of(new ExpectedBoolean(new FieldKey("family.send_observed"),true)));
        return new ActionCommand("guardian-fixture",actual.identity(),actual.source(),actual.sessionId(),
                new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP),intent.toJson(),expected,
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),actual.observedAt().plusSeconds(30));
    }
    private static ActionState.Attempt attempt(ActionCommand command) {
        var guard=new GuardEvidence(command.before(),command.source(),command.sessionId(),BigInteger.ONE,
                command.operation(),SOURCE,SOURCE,"software-fixture",Instant.parse("2026-10-24T00:00:00Z"),command.deadline());
        return new ActionState.Attempt("guardian-request",guard.observedAt(),guard,
                new NativeRequest(OrdinaryInteractionCodec.INITIATE_STEP,OrdinaryInteractionCodec.INITIATE_CAPABILITY,EMPTY));
    }
    private static OrdinaryInitiationPreparation preparation(OrdinaryInitiationPreparation.Frames frames,NoWritesArchive archive) {
        PlanningReadPort reads=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                throw new AssertionError("missing live context must not issue a native preflight");
            }
        };
        var query=new ReadContract<OrdinaryContext>("interactions:ordinary-query",new OperationKey(OrdinaryInteractionCodec.QUERY_STEP),
                Optional.of(OrdinaryInteractionCodec.QUERY_CAPABILITY),OrdinaryInteractionCodec.QUERY_CAPABILITY,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,SOURCE,
                request->{throw new AssertionError("no query encoding");},receipt->{throw new AssertionError("no legacy decoding");});
        var claims=new OrdinaryClaimDomain(Path.of("D:/software-guardian-fixture/writer.lock"),new OrdinaryClaimDomain.Artifacts() {
            @Override public ExactRef publish(ContinuityStorePort.Session same,byte[] original) {throw new AssertionError("no claim write");}
            @Override public byte[] read(ExactRef original) {throw new AssertionError("no claim read");}
        },new OrdinaryClaimDomain.PermitAuthority() {
            @Override public OrdinaryOnceClaims.Permit requireNextIntent(ContinuityStorePort.Session same,OrdinaryOnceClaims.State before,OrdinaryOnceClaims.Request request) {
                throw new AssertionError("no permit consumption");
            }
            @Override public void verifyOriginal(OrdinaryOnceClaims.State before,OrdinaryOnceClaims.Request request,OrdinaryOnceClaims.Permit permit) {
                throw new AssertionError("no permit replay");
            }
        });
        NativeEffectEvidence.FrameLoader loader=(basis,originals)->{throw new AssertionError("no historical frame read");};
        var effects=new GuardianOutgoingEffects(reads,query,claims,loader);
        return new OrdinaryInitiationPreparation(()->{throw new AssertionError("no Native transport");},reads,query,frames,claims,archive,effects);
    }

    /** Callback-only dictionary: no Session, writer, packet or archive authority. Every write fails the test. */
    private static final class NoWritesArchive implements ActionPorts.OutcomeArchive {
        int references;
        @Override public <T>T inSession(ContinuityStorePort.Session same,Function<ActionPorts.OutcomeArchive,T> work) {return work.apply(this);}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) {references++;return SOURCE;}
        private static AssertionError unused() {return new AssertionError("no archive/native/writer operation is permitted");}
        public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unused();}public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unused();}
        public ExactRef preserveRequest(NativeRequest value){throw unused();}public NativeRequest loadRequest(ExactRef ref){throw unused();}
        public ExactRef requestReferenceOf(NativeRequest value){throw unused();}
        public ExactRef preserveRead(PlanningReadReceipt value){throw unused();}public PlanningReadReceipt loadRead(ExactRef ref){throw unused();}
        public ExactRef readReferenceOf(PlanningReadReceipt value){throw unused();}
        public ExactRef preserveRecord(ActionRecord value){throw unused();}public ActionRecord loadRecord(ExactRef ref){throw unused();}
        public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        public ExactRef preserveReceipt(ActionReceipt value){throw unused();}public ActionReceipt loadReceipt(ExactRef ref){throw unused();}
        public ExactRef receiptReferenceOf(ActionReceipt value){throw unused();}
        public ExactRef preserveMaterial(RawJson value){throw unused();}public RawJson loadMaterial(ExactRef ref){throw unused();}
        public ExactRef materialReferenceOf(RawJson value){throw unused();}
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unused();}public byte[] loadNativeFrame(ExactRef ref){throw unused();}
    }
}
