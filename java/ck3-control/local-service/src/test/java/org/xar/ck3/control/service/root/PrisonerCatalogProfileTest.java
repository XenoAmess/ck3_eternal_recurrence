package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;

/** Actual old stock bytes plus controlled policy DATA. No RootContext, ManagedGame, writer or Native endpoint is constructed. */
final class PrisonerCatalogProfileTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-11-18T21:00:00Z");
    private static final String LEGACY="1.20.0.4@sha256:"+PrisonerVanillaResearch.EXE_SHA256;
    private static final String HOTFIX="1.21.0@sha256:bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79";
    private ExactRef missing(){return new ExactRef(temporary.resolve("must-not-be-read.txt").toString(),PrisonerVanillaResearch.STOCK_BYTES,PrisonerVanillaResearch.STOCK_SHA256);}
    private static ExactRef measured(Path p)throws Exception{var r=ControlBuild.FileRef.measure(p);return new ExactRef(r.path(),r.bytes(),r.sha256());}
    @Test void unsupportedProfilesNeverReadOrRelabelLegacyStock()throws Exception {
        for(String build:List.of(HOTFIX,"1.21.0@sha256:2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc","unknown@sha256:"+"c".repeat(64)))
            assertTrue(PrisonersRuntimeInstaller.stockCatalog(build,missing(),"pure-policy",NOW).isEmpty());
        assertFalse(Files.exists(Path.of(missing().path())));
    }
    @Test void originalLegacyPinStillProducesAllFiveSourceBoundInteractionTrees()throws Exception {
        Path stock=Path.of(System.getProperty("xar.prison.stock.original"));ExactRef ref=measured(stock);
        assertEquals(PrisonerVanillaResearch.STOCK_BYTES,ref.bytes());assertEquals(PrisonerVanillaResearch.STOCK_SHA256,ref.sha256());
        var value=PrisonersRuntimeInstaller.stockCatalog(LEGACY,ref,"pure-policy",NOW).orElseThrow();
        assertEquals(5,value.interactions().size());assertEquals("1.20.0.4",value.source().provenance().exactBuild());
        assertEquals(ref,value.source().provenance().sourceRef());assertEquals(PrisonerVanillaResearch.EXE_SHA256,value.source().executableSha256());
    }
    @Test void originalLegacyScopeStillRejectsWrongPinsAndChangedBytes()throws Exception {
        Path wrong=temporary.resolve("wrong.txt");Files.writeString(wrong,"not the pinned stock");
        assertThrows(IllegalArgumentException.class,()->PrisonersRuntimeInstaller.stockCatalog(LEGACY,measured(wrong),"pure-policy",NOW));
        Path copy=temporary.resolve("original-copy.txt");Files.copy(Path.of(System.getProperty("xar.prison.stock.original")),copy);ExactRef original=measured(copy);
        byte[] bytes=Files.readAllBytes(copy);bytes[0]=(byte)(bytes[0]^1);Files.write(copy,bytes,StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IllegalArgumentException.class,()->PrisonersRuntimeInstaller.stockCatalog(LEGACY,original,"pure-policy",NOW));
    }
    @Test void realPrisonerPolicyRetainsUnavailableInsteadOfEmptyWithZeroReadsAndCommands()throws Exception {
        Path source=temporary.resolve("policy-data.txt");Files.writeString(source,"controlled software policy DATA");ExactRef ref=measured(source);
        AtomicInteger reads=new AtomicInteger(),commands=new AtomicInteger(),records=new AtomicInteger();
        PlanningReadPort port=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){reads.incrementAndGet();throw new AssertionError("unsupported profile reached a query");}};
        var natives=new PrisonerNativeQueries(ref,(ordinal,request,arguments)->{throw new AssertionError("unsupported profile reached Native admission");});
        var queries=new Queries(natives.contracts(),Map.of());
        var binding=new Bindings(port,queries,PrisonersRuntimeInstaller.stockCatalog(HOTFIX,missing(),"pure-policy",NOW),
                ignored->new KnownLedger(ref,Optional.empty(),Optional.empty()),(request,operation,args,claims,original)->{commands.incrementAndGet();return Optional.empty();},
                (request,value)->{records.incrementAndGet();return new RecordUnavailable("no live record port");});
        var result=new PrisonerCollector12004(binding).collectRansom(request(ref));assertInstanceOf(PrisonerCollector12004.Unavailable.class,result);
        var previous=new OrdinaryPolicy.Draft("pure-policy","ordinary","original plan",OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(Map.of()));
        var decision=new PrisonerOrdinaryPolicy12004(PlanningStage.PRISONER_RANSOM,ref,binding).evaluate(request(ref),previous);
        var replaced=assertInstanceOf(OrdinaryPolicy.Replace.class,decision);assertNotNull(replaced.draft().detail().get("prisoner_observation_unavailable"));
        assertTrue(replaced.draft().command().isEmpty());assertEquals(0,reads.get());assertEquals(0,commands.get());assertEquals(0,records.get());
    }
    private static PlanningRequest request(ExactRef ref){
        var snap=StrictJson.object().put("snapshot_id","public:37").put("episode_run_id","episode").put("episode_character_id",29829).put("revision",37).put("native_revision",1014).put("date_raw",53286360).put("paused",true).put("map_ready",true).put("one_life_terminal",false);
        snap.putNull("one_life_terminal_reason");snap.putNull("active_event");snap.putNull("pending_character_interaction");snap.putObject("played_character").put("character_id",29829).put("alive",true);
        snap.putObject("played_character_gold").put("raw",10000000).put("scale",100000);snap.putObject("succession_lifecycle").put("lifecycle","ordinary_campaign_succession");snap.putArray("player_armies");snap.putArray("active_wars");
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(1014),BigInteger.valueOf(53286360)),"public:37",BigInteger.valueOf(37),"episode");
        var before=new ProposalLifecycle.ObservationIdentity("pure-policy",new GameGeneration(4242,new PythonOnlyUInt64(new BigInteger("133000000000000000"))),frame,1);
        var observations=new PlanningObservation(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(snap)),"snapshot"),List.of(),Set.of(PrisonerOrdinaryPolicy12004.RANSOM),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,new G2Source("pure-policy",NOW.toString(),HOTFIX,ref),"pure-session",NOW.plusSeconds(60),observations);
    }
}
