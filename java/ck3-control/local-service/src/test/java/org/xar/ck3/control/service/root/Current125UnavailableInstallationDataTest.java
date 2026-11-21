package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import java.nio.file.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Real retired52 input DATA into the failing Family adapter. No Managed, Root context, READ or install authority. */
class Current125UnavailableInstallationDataTest {
    static final String VERSION="1.21.0.3",SHA="859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28";
    record Data(Complete held,Instant deadline,JsonNode config) { }
    static ExactRef measured(Path p)throws Exception {
        byte[] raw=Files.readAllBytes(p);return new ExactRef(p.toString(),raw.length,org.xar.ck3.control.application.driver.DriverJson.sha256(raw));
    }
    static Data actual52()throws Exception {
        Path input=Path.of(System.getProperty("installed.actual.summary"));
        var summary=StrictJson.parse(Files.readAllBytes(input),StrictJson.EXPLICIT_MAX_BYTES);
        Path cfg=Path.of(System.getProperty("installed.actual.config"));
        var config=StrictJson.parse(Files.readAllBytes(cfg),StrictJson.EXPLICIT_MAX_BYTES);
        var stateRef=ExactRef.fromJson(summary.path("originals").path("frame").path("raw_state").path("reference"));
        assertEquals(stateRef,measured(Path.of(stateRef.path())));
        var nativeState=StrictJson.parse(Files.readAllBytes(Path.of(stateRef.path())),StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals(VERSION,nativeState.path("game_version").textValue());assertEquals(SHA,nativeState.path("executable_sha256").textValue().toLowerCase(Locale.ROOT));
        assertEquals(config.path("configured_build").path("version").textValue(),nativeState.path("game_version").textValue());
        assertEquals(config.path("configured_build").path("exe_sha256").textValue().toLowerCase(Locale.ROOT),SHA);
        var session=summary.path("session");Instant observed=Instant.parse(summary.path("observed_at_utc").textValue());
        var source=new G2Source(session.path("machine_id").textValue(),observed.toString(),VERSION+"@sha256:"+SHA,stateRef);
        BigInteger actor=nativeState.path("played_character").path("character_id").bigIntegerValue();
        BigInteger revision=new BigInteger(summary.path("native_revision").textValue()),date=nativeState.path("date_raw").bigIntegerValue();
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(session.path("game").path("pid").intValue(),new PythonOnlyUInt64(new BigInteger(session.path("game").path("creation_filetime").textValue()))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,revision,date),summary.path("snapshot_id").textValue(),BigInteger.ONE,"historical52-data-only"),1);
        // This projected Complete is test DATA. Its extra application fields are not a Native receipt or readiness proof.
        ObjectNode semantic=(ObjectNode)nativeState.deepCopy();semantic.put("snapshot_id",summary.path("snapshot_id").textValue());semantic.put("revision",1);semantic.put("native_revision",revision);semantic.put("episode_run_id","historical52-data-only");semantic.put("episode_character_id",actor);
        var held=new Complete(identity,source,session.path("session_id").textValue(),new BigInteger(session.path("connection_generation").textValue()),(Obj)OpportunityJson.parse(StrictJson.canonical(semantic)),stateRef,observed,stateRef.sha256());
        return new Data(held,observed.plusSeconds(30),config);
    }
    static RootFamilyInteractionContext context(Data d) {
        var b=d.config().path("configured_build");return RootFamilyInteractionContext.configuredUnavailable(KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(b.path("version").textValue(),b.path("exe_sha256").textValue()));
    }
    static PlanningRequest planning(Data d) {
        var h=d.held();return new PlanningRequest(h.identity(),h.source(),h.sessionId(),d.deadline(),new PlanningObservation(h.semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    static void unavailable(PlanningReadResult<?> value) {
        var missing=assertInstanceOf(PlanningReadResult.Unavailable.class,value);assertEquals("interaction_native_contract_unmigrated",missing.reason());
        assertTrue(missing.original().isEmpty());assertTrue(missing.decodeFailure().isEmpty());assertTrue(missing.observedFailure().isEmpty());
    }
    @Test @EnabledIfSystemProperty(named="installed.actual.summary",matches=".+")
    void actual52FamilyInstallSubcallBuildsUnavailableWithoutNativeQuery()throws Exception {
        var data=actual52();var gate=context(data);
        unavailable(gate.query(data.held(),data.deadline(),actual->{throw new AssertionError("unqualified current source cannot call Native");}));
        assertThrows(IllegalStateException.class,gate::requireProjection);
        assertEquals(gate,context(data));
    }
    @Test @EnabledIfSystemProperty(named="installed.actual.summary",matches=".+")
    void actual52AllDependentProjectedViewsRetainArgumentsAndNoReadOriginal()throws Exception {
        var d=actual52();var gate=context(d);var request=planning(d);
        for(var query:List.of(FamilyPorts.Query.CURRENT_RELATION,FamilyPorts.Query.HEIR_PROJECTION,FamilyPorts.Query.CHILD_SUBJECT,FamilyPorts.Query.CHILD_VALUE,FamilyPorts.Query.FAMILY_RESULT,FamilyPorts.Query.MATRILINEAL_RESULT,FamilyPorts.Query.DEFAULT_RESULT,FamilyPorts.Query.FAMILY_ALLIANCE,FamilyPorts.Query.MATRILINEAL_ALLIANCE,FamilyPorts.Query.DEFAULT_ALLIANCE,FamilyPorts.Query.EDUCATION_CONTEXT,FamilyPorts.Query.HEIR_LEGALITY,FamilyPorts.Query.RULER_CHOICES)) {
            var flat=new Obj(Map.of("requested_view",new OpportunityJson.Text(query.name())));
            var value=gate.projected(request,d.held(),flat,actual->{throw new AssertionError("no qualified projection/read "+query);});
            assertSame(flat,value.canonicalArguments());unavailable(value.result());
        }
    }
    @Test @EnabledIfSystemProperty(named="installed.actual.summary",matches=".+")
    void typedNegativeRetainsActualRawAndVersionedSourceSpelling()throws Exception {
        var d=actual52();var h=d.held();
        for(String spelling:List.of(SHA,SHA.toUpperCase(Locale.ROOT),VERSION+"@sha256:"+SHA)) {
            var source=new G2Source(h.source().machineId(),h.source().observedAtUtc(),spelling,h.source().sourceRef());
            var result=KnownPendingInteractionPolicy.unavailableForSource(VERSION,SHA,source);unavailable(result.result());
            var prior=planning(d);var request=new PlanningRequest(prior.before(),source,prior.sessionId(),prior.deadline(),prior.observations());
            unavailable(assertInstanceOf(KnownPendingInteractionPolicy.Unavailable.class,KnownPendingInteractionPolicy.typedUnavailable(VERSION,SHA).current(request)).result());
            assertEquals(spelling,source.exactBuild());
        }
    }
    @Test @EnabledIfSystemProperty(named="installed.actual.summary",matches=".+")
    void originalFamilySourceSessionAndPublicationTimeGuardsStillReject()throws Exception {
        var d=actual52();var h=d.held();var gate=context(d);var request=planning(d);var flat=new Obj(Map.of());
        var foreignSource=new G2Source(h.source().machineId(),h.source().observedAtUtc(),"0".repeat(64),h.source().sourceRef());
        var foreign=new Complete(h.identity(),foreignSource,h.sessionId(),h.connectionGeneration(),h.semantic(),h.source().sourceRef(),h.observedAt(),h.fullBindingSha256());
        var otherSession=new Complete(h.identity(),h.source(),h.sessionId()+"-other",h.connectionGeneration(),h.semantic(),h.source().sourceRef(),h.observedAt(),h.fullBindingSha256());
        assertThrows(IllegalArgumentException.class,()->gate.query(foreign,d.deadline(),actual->{throw new AssertionError();}));
        assertThrows(IllegalArgumentException.class,()->gate.projected(request,otherSession,flat,actual->{throw new AssertionError();}));
        assertThrows(IllegalArgumentException.class,()->gate.query(h,h.observedAt(),actual->{throw new AssertionError();}));
        assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.unavailableForSource(VERSION,SHA,foreignSource));
    }
    @Test void knownConfiguredDataDoesNotUpgradeAvailableInteractionOrActionBuilds() {
        var current=KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(VERSION,SHA);assertFalse(current.qualified());assertThrows(IllegalStateException.class,current::requireQualified);
        for(var old:InteractionModels.Build.values()) {
            var legacy=KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(old.version(),old.sha256());assertSame(old,legacy.requireQualified());
            assertThrows(IllegalArgumentException.class,()->RootFamilyInteractionContext.configuredUnavailable(legacy));
            assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.typedUnavailable(old.version(),old.sha256()));
        }
        for(var prior:List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580))assertNotNull(KnownPendingInteractionPolicy.typedUnavailable(prior.version(),prior.executableSha256()));
        assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.typedUnavailable("1.21.0",SHA));
        assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.typedUnavailable(VERSION,"0".repeat(64)));
    }
    @Test @EnabledIfSystemProperty(named="installed.actual.nt.jar",matches=".+")
    void actualNewNTAndRetainedPlainLSAreTheOnlyProductionOwners()throws Exception {
        assertEquals(Path.of(System.getProperty("installed.actual.nt.jar")).toRealPath(),Path.of(KnownPendingInteractionPolicy.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath());
        assertEquals(Path.of(System.getProperty("installed.actual.ls.jar")).toRealPath(),Path.of(RootFamilyInteractionContext.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath());
    }
}
