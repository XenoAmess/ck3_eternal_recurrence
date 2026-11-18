package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Synthetic frame/receipt DATA exercises the actual adapter, without creating Root Installed or Native qualification. */
final class RootFamilyInteractionContextTest {
    private static final Instant NOW=Instant.parse("2026-11-18T00:00:00Z"),DEADLINE=NOW.plusSeconds(30);
    private static final ExactRef REF=new ExactRef("D:/synthetic-family-context/source",1,"a".repeat(64));
    private static final Obj FLAT=new Obj(Map.of("expected_native_revision",new OpportunityJson.IntegerValue(BigInteger.valueOf(7))));
    private static RootFamilyInteractionContext unavailable() {
        var build=ExactCk3Build.CK3_1210;
        return RootFamilyInteractionContext.configuredUnavailable(KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(build.version(),build.executableSha256()));
    }
    private static Complete frame(boolean florin) {
        String version=florin?ExactCk3Build.CK3_1210.version():InteractionModels.Build.CROZIER4.version();
        String sha=florin?ExactCk3Build.CK3_1210.executableSha256():InteractionModels.Build.CROZIER4.sha256();
        var source=new G2Source("synthetic-family-context",NOW.toString(),version+"@sha256:"+sha,REF);
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(100)),
                        "synthetic-frame",BigInteger.valueOf(9),"synthetic-episode"),1);
        ObjectNode semantic=StrictJson.object().put("snapshot_id","synthetic-frame").put("revision",9).put("native_revision",7)
                .put("date_raw",100).put("episode_run_id","synthetic-episode").put("episode_character_id",101)
                .put("paused",true).put("map_ready",true).put("speed",0).put("local_player_id",101);
        semantic.putNull("active_event");semantic.putNull("current_event");semantic.putNull("pending_character_interaction");
        semantic.putArray("active_wars");semantic.putArray("player_armies");
        var actor=semantic.putObject("played_character").put("character_id",101).put("alive",true);actor.putNull("betrothed_id");actor.putArray("spouse_ids");
        semantic.putObject("diagnostics").putObject("hello").put("expected_ck3_version",version).put("expected_ck3_sha256",sha);
        return new Complete(identity,source,"synthetic-session",BigInteger.ONE,(Obj)OpportunityJson.parse(StrictJson.canonical(semantic)),REF,NOW,"b".repeat(64));
    }
    private static PlanningRequest planning(Complete frame) {
        return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),DEADLINE,new PlanningObservation(frame.semantic(),List.of(),Set.of(),
                Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static PlanningReadResult.Known<Obj> known(Complete frame) {
        var operation=new OperationKey("synthetic-family-read");var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),operation,FLAT,DEADLINE);
        var evidence=new GuardEvidence(frame.identity(),frame.source(),frame.sessionId(),BigInteger.ONE,operation,REF,REF,"synthetic-authority",NOW,DEADLINE);
        var guard=new PlanningReadGuard(evidence,true,true,true,"c".repeat(64));var raw=new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var receipt=new PlanningReadReceipt(request,"synthetic-family-contract","synthetic-read",guard,guard,
                new NativeActionPort.AckReceived("synthetic-read",true,Optional.empty(),raw,raw.bytes()));
        return new PlanningReadResult.Known<>(FLAT,receipt,REF);
    }

    @Test void allThirteenDependentViewsReturnTrueUnavailableWithoutCallingAnyKnownRead()throws Exception {
        var queries=List.of(FamilyPorts.Query.CURRENT_RELATION,FamilyPorts.Query.HEIR_PROJECTION,FamilyPorts.Query.CHILD_SUBJECT,
                FamilyPorts.Query.CHILD_VALUE,FamilyPorts.Query.FAMILY_RESULT,FamilyPorts.Query.MATRILINEAL_RESULT,FamilyPorts.Query.DEFAULT_RESULT,
                FamilyPorts.Query.FAMILY_ALLIANCE,FamilyPorts.Query.MATRILINEAL_ALLIANCE,FamilyPorts.Query.DEFAULT_ALLIANCE,
                FamilyPorts.Query.EDUCATION_CONTEXT,FamilyPorts.Query.HEIR_LEGALITY,FamilyPorts.Query.RULER_CHOICES);
        var held=frame(true);var request=planning(held);var gate=unavailable();
        for(var query:queries) {
            var flat=FLAT.with("synthetic_query",new OpportunityJson.Text(query.name()));
            var result=gate.projected(request,held,flat,actual->{throw new AssertionError("unmigrated source cannot read "+query);});
            assertSame(flat,result.canonicalArguments());var missing=assertInstanceOf(PlanningReadResult.Unavailable.class,result.result());
            assertEquals(KnownInteractionsRuntimeInstaller.ConfiguredBuild.UNMIGRATED_REASON,missing.reason());
            assertTrue(missing.original().isEmpty());assertTrue(missing.decodeFailure().isEmpty());assertTrue(missing.observedFailure().isEmpty());
        }
    }

    @Test void publicQueryHasNoManufacturedPlanningRequestContextOrReadOriginal()throws Exception {
        PlanningReadResult<InteractionModels.MarriageChoices> result=unavailable().query(frame(true),DEADLINE,
                actual->{throw new AssertionError("unmigrated public choices cannot call Native");});
        var missing=assertInstanceOf(PlanningReadResult.Unavailable.class,result);
        assertEquals("interaction_native_contract_unmigrated",missing.reason());
        assertTrue(missing.original().isEmpty());assertTrue(missing.decodeFailure().isEmpty());assertTrue(missing.observedFailure().isEmpty());
        assertThrows(IllegalStateException.class,()->unavailable().requireProjection());
    }

    @Test void negativeGateRetainsExactHeldSourceSessionAndPublicationDeadlineGuards()throws Exception {
        var held=frame(true);var request=planning(held);var gate=unavailable();
        var otherSession=new Complete(held.identity(),held.source(),held.sessionId()+"-other",held.connectionGeneration(),held.semantic(),REF,NOW,held.fullBindingSha256());
        assertThrows(IllegalArgumentException.class,()->gate.projected(request,otherSession,FLAT,actual->{throw new AssertionError();}));
        assertThrows(IllegalArgumentException.class,()->gate.projected(request,frame(false),FLAT,actual->{throw new AssertionError();}));
        assertThrows(IllegalArgumentException.class,()->gate.query(frame(false),DEADLINE,actual->{throw new AssertionError();}));
        for(Instant invalid:List.of(NOW,NOW.minusNanos(1)))
            assertThrows(IllegalArgumentException.class,()->gate.query(held,invalid,actual->{throw new AssertionError();}));
        var equalDeadline=new PlanningRequest(request.before(),request.source(),request.sessionId(),NOW,request.observations());
        assertThrows(IllegalArgumentException.class,()->gate.projected(equalDeadline,held,FLAT,actual->{throw new AssertionError();}));
    }

    @Test void qualifiedContextAndKnownReadObjectsPassThroughExactlyOnceWithOriginalProjection()throws Exception {
        var held=frame(false);var request=planning(held);var projection=new RootInteractionContextProjection(InteractionModels.Build.CROZIER4);
        var expectedContext=projection.project(held,DEADLINE);var gate=RootFamilyInteractionContext.qualified(projection);
        assertSame(projection,gate.requireProjection());assertEquals(projection.hashCode(),gate.hashCode());
        assertEquals(gate,RootFamilyInteractionContext.qualified(projection));
        var known=known(held);var projected=new FamilyPorts.ProjectedRead(FLAT,known);AtomicInteger calls=new AtomicInteger();
        assertSame(projected,gate.projected(request,held,FLAT,actual->{assertEquals(expectedContext,actual);calls.incrementAndGet();return projected;}));
        assertSame(known,gate.query(held,DEADLINE,actual->{assertEquals(expectedContext,actual);calls.incrementAndGet();return known;}));
        assertEquals(2,calls.get());assertSame(known.receipt(),assertInstanceOf(PlanningReadResult.Known.class,projected.result()).receipt());
    }

    @Test void qualifiedProducerFailuresAndUnavailableReasonsArePreservedWithoutRetyping()throws Exception {
        var held=frame(false);var gate=RootFamilyInteractionContext.qualified(new RootInteractionContextProjection(InteractionModels.Build.CROZIER4));
        var missing=new PlanningReadResult.Unavailable<Obj>("actual_original_getter_not_available",Optional.empty());
        var projected=new FamilyPorts.ProjectedRead(FLAT,missing);
        assertSame(missing,gate.query(held,DEADLINE,actual->missing));
        assertSame(projected,gate.projected(planning(held),held,FLAT,actual->projected));
        var failure=new IOException("actual retained ROOT/archive proof unavailable");
        assertSame(failure,assertThrows(IOException.class,()->gate.projected(planning(held),held,FLAT,actual->{throw failure;})));
        assertSame(failure,assertThrows(IOException.class,()->gate.query(held,DEADLINE,actual->{throw failure;})));
    }

    @Test void qualifiedSourceNeverTakesTheUnmigratedOrWrongBuildPath() {
        var old=InteractionModels.Build.CROZIER4;
        assertThrows(IllegalArgumentException.class,()->RootFamilyInteractionContext.configuredUnavailable(
                KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(old.version(),old.sha256())));
        var legacy=RootFamilyInteractionContext.qualified(new RootInteractionContextProjection(old));
        assertThrows(IllegalArgumentException.class,()->legacy.query(frame(true),DEADLINE,actual->{throw new AssertionError();}));
        var florin=ExactCk3Build.CK3_1210;
        assertEquals(unavailable(),RootFamilyInteractionContext.configuredUnavailable(KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(
                florin.version(),florin.executableSha256().toUpperCase(java.util.Locale.ROOT))));
    }

    @Test void rawReviewedExecutionShaKeepsItsActualSourceForProjectedAndPublicNegativeReads()throws Exception {
        var original=frame(true);var build=ExactCk3Build.CK3_1210;
        for(String spelling:List.of(build.executableSha256(),build.executableSha256().toUpperCase(java.util.Locale.ROOT))) {
            var prior=original.source();var source=new G2Source(prior.machineId(),prior.observedAtUtc(),spelling,prior.sourceRef());
            var held=new Complete(original.identity(),source,original.sessionId(),original.connectionGeneration(),original.semantic(),
                    original.originalEvidence(),original.observedAt(),original.fullBindingSha256());
            var projected=unavailable().projected(planning(held),held,FLAT,actual->{throw new AssertionError("no Native read");});
            assertInstanceOf(PlanningReadResult.Unavailable.class,projected.result());
            assertInstanceOf(PlanningReadResult.Unavailable.class,unavailable().query(held,DEADLINE,actual->{throw new AssertionError("no Native read");}));
            assertSame(source,held.source());assertEquals(spelling,held.source().exactBuild());
        }
    }
}
