package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer;

/** Closed-scene Current receipt replay plus software domain ports; no Root, writer or Native client. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.lifestyle.progress.inputs", matches=".+")
final class ReadOnlyLifestyleProgressTest {
    private static com.fasterxml.jackson.databind.JsonNode inputs() throws Exception {
        return StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.lifestyle.progress.inputs"))));
    }
    private static byte[] original(String name) throws Exception {
        var ref=ExactRef.fromJson(inputs().get(name)); byte[] bytes=Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(),bytes.length); assertEquals(ref.sha256(),ActionCodec.sha256(bytes)); return bytes;
    }
    private record Fixture(PlanningRequest request, OrdinaryPolicy.Draft previous, Obj query, ExactRef reference) { }
    private static Fixture fixture() throws Exception {
        var read=NativeArchiveDataCodec.retainedFiles().readData(ExactRef.fromJson(inputs().get("current_read"))).receipt();
        var dll=ExactRef.fromJson(inputs().get("actual_dll"));
        var profile=OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,dll).orElseThrow();
        var definitions=new OpeningReadProfile.Bindings(profile,dll); var data=definitions.current().replay(read);
        data.requireApplicationMainOrigin(); assertEquals(BigInteger.ZERO,data.progress().orElseThrow().unspentPerkPoints().orElseThrow());
        var batch=StrictJson.parse(original("actual_batch")); var plan=batch.get("last_plan").get("final_plan");
        var command=ActionCodec.decodeCommand(StrictJson.canonical(plan.get("command")));
        assertEquals(command.before(),read.request().before());
        var frame=command.before().frame();
        byte[] nativePacket=Files.readAllBytes(Path.of(read.before().binding().nativeEvidence().path()));
        assertEquals(nativePacket.length-4,java.nio.ByteBuffer.wrap(nativePacket).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt());
        var nativeFull=StrictJson.parse(java.util.Arrays.copyOfRange(nativePacket,4,nativePacket.length));
        var semantic=((com.fasterxml.jackson.databind.node.ObjectNode)nativeFull.get("state")).deepCopy();
        semantic.put("snapshot_id",frame.snapshotId()).put("episode_run_id",frame.episodeRunId())
                .put("revision",frame.revision()).put("native_revision",frame.identity().nativeRevision());
        var observations=new PlanningObservation((Obj)parse(StrictJson.canonical(semantic)),List.of(),Set.of(new OperationKey("life-advance")),
                Set.of(OpeningReadProfile.Kind.SCOPE.capability(),OpeningReadProfile.Kind.CURRENT.capability()),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var request=new PlanningRequest(command.before(),command.source(),command.sessionId(),command.deadline(),observations);
        var previous=new OrdinaryPolicy.Draft(plan.get("policy").textValue(),plan.get("phase").textValue(),plan.get("reason").textValue(),
                OrdinaryPolicy.Kind.valueOf(plan.get("kind").textValue()),Optional.of(command),OrdinaryPolicy.Purpose.valueOf(plan.get("purpose").textValue()),
                Optional.empty(),(Obj)parse(StrictJson.canonical(plan.get("detail"))));
        // Reuse the production pure projection on already replayed actual Current DATA, with no I/O or authority construction.
        var project=OpeningReadProfile.class.getDeclaredMethod("projectCurrent",PlanningRequest.class,OpeningReadProfile.Data.class);
        project.setAccessible(true); var query=(Obj)parse(StrictJson.canonical((com.fasterxml.jackson.databind.JsonNode)project.invoke(null,request,data)));
        return new Fixture(request,previous,query,ExactRef.fromJson(inputs().get("current_read")));
    }
    @SuppressWarnings("unchecked") private static <T> T unused(Class<T> type) {
        return (T)Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},(proxy,method,args)->{throw new AssertionError("unexpected I/O: "+method);});
    }
    private static GovernanceCollector collector(Fixture f, Read<GovernanceCollector.ReadOnlyOpening> returned, AtomicInteger calls) {
        var port=new GovernanceCollector.LifestyleReadPort() {
            public Read<Obj> formal(PlanningRequest request) {throw new AssertionError("legacy formal must remain uncalled");}
            public Read<Obj> stockFocus(PlanningRequest request,String target) {throw new AssertionError("final action query must remain uncalled");}
            public Optional<Read<GovernanceCollector.ReadOnlyOpening>> openingReadOnly(PlanningRequest request) {calls.incrementAndGet();return Optional.of(returned);}
        };
        var scope=new GovernanceBorrowedSession(()->{throw new AssertionError("no writer may be opened");},Path.of("software-only-unused.lock"),same->{throw new AssertionError("no writer");});
        GovernanceCollector.StateSupplier states=request->new Known<>(new Durable(request.before(),request.sessionId(),Optional.of(CadenceModels.State.empty(request.before().frame().episodeRunId())),
                Optional.empty(),Optional.empty(),Optional.empty()),List.of(f.reference()));
        return new GovernanceCollector(unused(PlanningReadPort.class),unused(OutcomeArchive.class),states,
                new GovernanceCollector.Reads(Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty()),scope,port);
    }
    private static Known<GovernanceCollector.ReadOnlyOpening> softwarePortResult(Fixture f,Obj query) {
        // This is an explicit domain-port fixture, not a fabricated native scope packet or live qualification.
        Obj scope=new Obj(Map.of("status",new Text("admitted"),"at_peace",new Bool(true),"government_key",new Text("feudal_government"),
                "snapshot_revision",new IntegerValue(f.request().before().frame().identity().nativeRevision()),
                "player_character_id",new IntegerValue(f.request().before().frame().identity().player())));
        return new Known<>(new GovernanceCollector.ReadOnlyOpening(scope,query),List.of(f.reference()));
    }
    @Test void ordinaryFalseUsesExplicitCurrentProfileAndOnlyAnnotatesTheOriginalPlan() throws Exception {
        var f=fixture(); var calls=new AtomicInteger(); var collector=collector(f,softwarePortResult(f,f.query()),calls);
        var life=(Known<Life>)collector.lifestyle(f.request(),"wealth_focus",false);
        var available=(LifestyleConsumer.AvailableQuery)life.value().input().query();
        assertFalse(available.policyRequest().minimum().allowWartimeInitialFocus());
        assertEquals(LifestyleConsumer.Route.OBSERVATION_UNAVAILABLE,LifestyleConsumer.consumeWithHistory(life.value().input(),life.value().history()).route(),
                "partial progress must never pass the legacy owned/final-legal minimum guards");
        var decision=(OrdinaryPolicy.Replace)new GovernancePolicies.Lifestyle(collector,f.reference()).evaluate(f.request(),f.previous());
        var retained=decision.draft();assertEquals(f.previous().policy(),retained.policy());assertEquals(f.previous().phase(),retained.phase());
        assertEquals(f.previous().reason(),retained.reason());assertEquals(f.previous().kind(),retained.kind());assertEquals(f.previous().command(),retained.command());
        assertEquals(f.previous().purpose(),retained.purpose());assertEquals(f.previous().domain(),retained.domain());
        assertEquals(f.query(),retained.detail().get("lifestyle_readonly_progress"));
        assertEquals(f.previous().detail().members().size()+1,retained.detail().members().size());assertEquals(2,calls.get());
    }
    @Test void PositivePointsStillNeedOwnedPerksAndFinalLegalityAndLegacyQueriesStayOnTheirPath() throws Exception {
        var f=fixture(); Obj snapshot=object(f.query().get("snapshot"),"snapshot");
        Obj progress=object(snapshot.get("current_lifestyle_progress"),"progress").with("unspent_perk_points",new IntegerValue(BigInteger.ONE));
        Obj positive=f.query().with("snapshot",snapshot.with("current_lifestyle_progress",progress));
        var collector=collector(f,softwarePortResult(f,positive),new AtomicInteger());
        var decision=new GovernancePolicies.Lifestyle(collector,f.reference()).evaluate(f.request(),f.previous());
        assertInstanceOf(OrdinaryPolicy.Stop.class,decision);
        var life=(Known<Life>)collector.lifestyle(f.request(),"wealth_focus",false);
        Obj legacy=new Obj(life.value().originalQuery().members().entrySet().stream().filter(e->!e.getKey().equals("opening_read_profile"))
                .collect(java.util.stream.Collectors.toMap(Map.Entry::getKey,Map.Entry::getValue)));
        assertTrue(GovernancePolicies.readOnlyCurrentProgress(f.request(),f.previous(),new Life(life.value().input(),life.value().history(),legacy)).isEmpty());
    }
    @Test void UnavailableAbsentAndCrossedFrameCannotBecomeAZeroPointObservation() throws Exception {
        var f=fixture(); var unknown=collector(f,new Unavailable<>("actual readonly unavailable"),new AtomicInteger());
        assertInstanceOf(OrdinaryPolicy.Stop.class,new GovernancePolicies.Lifestyle(unknown,f.reference()).evaluate(f.request(),f.previous()));
        Obj snapshot=object(f.query().get("snapshot"),"snapshot");
        Obj absent=f.query().with("snapshot",snapshot.with("current_focus",new Obj(Map.of("presence",new Text("absent")))));
        assertThrows(IllegalArgumentException.class,()->collector(f,softwarePortResult(f,absent),new AtomicInteger()).lifestyle(f.request(),"wealth_focus",false));
        Obj crossed=f.query().with("snapshot",snapshot.with("native_revision",new IntegerValue(f.request().before().frame().identity().nativeRevision().add(BigInteger.ONE))));
        assertThrows(IllegalArgumentException.class,()->collector(f,softwarePortResult(f,crossed),new AtomicInteger()).lifestyle(f.request(),"wealth_focus",false));
    }
}
