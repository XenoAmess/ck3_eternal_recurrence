package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.g2.m7.KernelCheckpointContinuity;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Java receive/Driver/semantic/disk replay chain. No physical SAVE, restore or Game qualification. */
final class NativeOrdinaryGoalReprojectionTest {
    @TempDir Path temporary;
    private static final Instant SOURCE_AT=Instant.parse("2026-10-25T00:00:00Z");
    private static final String STATE="{\"date_raw\":53144328,\"paused\":true,\"map_ready\":true,\"speed\":3,"
            +"\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,"
            +"\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,"
            +"\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{}}";
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(byte[] value){return new ExactRef("software/"+DriverJson.sha256(value),value.length,DriverJson.sha256(value));}
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000017")));}
    private static byte[] packet(String json){byte[] body=bytes(json);return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();}
    private static String hello(){return "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":1,"
            +"\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+"0".repeat(64)+"\","
            +"\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,"
            +"\"capabilities\":[\"game.state.snapshot\"]}";}
    private static DriverStateSnapshot.Complete driver(DriverStateSnapshot.Slot goal){
        var nil=new DriverStateSnapshot.NullValue();
        var lifecycle=new DriverStateSnapshot.Value(bytes("{\"lifecycle\":\"ordinary_campaign_succession\"}"));
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("\\\\.\\pipe\\goal-source-pipe",42,BigInteger.valueOf(73),"same-goal-episode"),
                List.of(),nil,nil,nil,nil,lifecycle,goal,new DriverStateSnapshot.Value(bytes("[]")));
    }
    /** Sole fake Native boundary: packet bytes enter the real transport and no request may leave. */
    private static final class Packets implements NativePacketPort {
        private final ArrayDeque<byte[]> packets;int reads;int writes;
        Packets(byte[]... values){packets=new ArrayDeque<>(Arrays.asList(values));}
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline)throws IOException{reads++;if(packets.isEmpty())throw new IOException("software packets exhausted");return packets.removeFirst();}
        @Override public void writePacket(byte[] value,Instant deadline){writes++;throw new AssertionError("goal observation cannot send a Native request");}
        @Override public void close() { }
    }
    private static final class Journal implements ActionJournal,ActionJournal.LockedJournal {
        final Snapshot snapshot;Journal(ExactRef original){snapshot=new Snapshot(8,"a".repeat(64),List.of(),new BoundHistoryBasis(original));}
        @Override public synchronized <T>T locked(Function<LockedJournal,T> work){return work.apply(this);}
        @Override public Optional<ActionReceipt> find(String id){return Optional.empty();}
        @Override public List<ActionReceipt> unresolved(){return List.of();}
        @Override public ActionReceipt append(ActionCommand command,String sha,ActionState next){throw new AssertionError("goal initialization cannot append an action");}
        @Override public Snapshot snapshot(){return snapshot;}
    }
    private static final class DiskEvidence implements NativeDriverObservationProducer.SemanticEvidencePort {
        private final Path directory;
        DiskEvidence(Path path)throws IOException{directory=Files.createDirectory(path);}
        @Override public ExactRef preserve(byte[] value){
            ExactRef exact=ref(value);Path path=directory.resolve(exact.sha256()+".json");
            try{if(!Files.exists(path))Files.write(path,value,StandardOpenOption.CREATE_NEW);assertArrayEquals(value,Files.readAllBytes(path));return exact;}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        RawJson read(ExactRef exact)throws IOException{byte[] original=Files.readAllBytes(directory.resolve(exact.sha256()+".json"));assertEquals(exact,ref(original));return new RawJson(original);}
    }
    @Test void actualNativeProducerReprojectsSameOccurrenceAfterNullGoalCasAndColdArchiveFeedsOrdinaryPlan()throws Exception{
        exercise(new DriverStateSnapshot.NullValue(),0,true);
    }
    @Test void actualNativeProducerRetainsAlreadyPersistedSameActorProgressWithoutAnotherGoalCas()throws Exception{
        var prior=new OrdinaryCampaignGoal.Goal("stable-campaign",55,73,new OrdinaryCampaignGoal.Progress(1,
                Optional.of(new OrdinaryCampaignGoal.Succession(55,73,List.of(100L),List.of(101L),List.of()))));
        exercise(new DriverStateSnapshot.Value(GoalCodec.encodeGoal(prior)),1,false);
    }
    private void exercise(DriverStateSnapshot.Slot originalGoal,long progress,boolean initialize)throws Exception{
        var original=driver(originalGoal);byte[] originalWire=original.encode();
        var evidence=new DiskEvidence(temporary.resolve("originals"));ExactRef originalRef=evidence.preserve(originalWire);
        var repository=new DriverFactsRepository(DriverFactsRepository.imported(originalRef,originalWire,3,7,game(),new OpportunityJson.Obj(Map.of())));
        var packets=new Packets(packet(hello()),packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"goal-frame\",\"revision\":9,\"state\":"+STATE+"}"));
        var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\goal-source-pipe","goal-machine",game(),"goal-session","fixture","0".repeat(64),"fixture-adapter");
        var source=new G2Source("goal-machine",SOURCE_AT.toString(),"software-goal-source",originalRef);
        try(var transport=NativeGoalObservationFixture.receive(packets,config)){
            var actual=transport.observe(Instant.now().plusSeconds(10));
            var nativeProducer=new NativeDriverObservationProducer(repository,transport,source,evidence);
            var before=assertInstanceOf(DriverObservationFacts.Known.class,nativeProducer.read(actual)).facts();
            assertEquals(originalGoal,before.driver().campaignGoal());
            assertNotEquals(before.nativeRevision(),before.publicRevision(),"public and Native sequences must be distinct in this real receive fixture");
            var assembler=new DriverStateAssembler(new ActionSnapshotReader(new Journal(originalRef)),repository,nativeProducer);
            int reads=packets.reads;
            var after=assertInstanceOf(DriverObservationFacts.Known.class,assembler.read(actual)).facts();
            assertEquals(initialize?4:3,after.driverVersion());
            assertEquals(before.publicRevision(),after.publicRevision());assertEquals(before.nativeRevision(),after.nativeRevision());
            assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
            assertSame(actual,transport.latestObservedSnapshot().orElseThrow());
            assertArrayEquals(originalWire,evidence.read(originalRef).bytes(),"the original null/value Driver remains exact");
            RawJson manifest=evidence.read(after.semanticFactsEvidence());
            var currentRef=DriverObservationEvidenceReader.currentDriverReference(after.semanticFactsEvidence(),manifest);
            var rawAgain=DriverObservationEvidenceReader.nativeFrame(after.semanticFactsEvidence(),manifest,actual.originalPacket());
            var replay=DriverObservationEvidenceReader.decode(after.semanticFactsEvidence(),manifest,evidence.read(currentRef),rawAgain);
            assertArrayEquals(after.driver().encode(),replay.driver().encode());
            var persisted=DriverStateSnapshot.decodeComplete(evidence.read(currentRef).bytes());
            var goal=GoalCodec.decodeGoal(assertInstanceOf(DriverStateSnapshot.Value.class,persisted.campaignGoal()).json());
            assertEquals(73,goal.currentCharacterId());assertEquals(progress,goal.progress().reconciledSuccessions());
            if(initialize){assertEquals("same-goal-episode",goal.campaignId());assertEquals(73,goal.originCharacterId());assertTrue(goal.progress().lastSuccession().isEmpty());}
            else assertEquals(originalGoal,persisted.campaignGoal());
            var full=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(rawAgain,replay,ref(actual.originalPacket())));
            var semanticGoal=GoalCodec.decodeGoal(DriverJson.encode(OpportunityJson.object(full.semantic().get("campaign_goal"),"actual goal")));
            assertEquals(goal,semanticGoal);
            var exported=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(full,true));
            assertEquals(OpportunityJson.toNode(full.semantic()),OpportunityJson.toNode(PublicSnapshotCodec.decode(exported)));
            var request=new PlanningRequest(full.identity(),source,full.sessionId(),Instant.now().plusSeconds(10),
                    new PlanningObservation(full.semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.of(semanticGoal),Optional.empty(),false));
            assertEquals(Optional.of("marriage"),OrdinaryCorePolicy.focus(request));
            independentFixedClockConsumesTheActualGoal(request,goal);
            var again=assertInstanceOf(DriverObservationFacts.Known.class,assembler.read(actual)).facts();
            assertEquals(after.driverVersion(),again.driverVersion());assertArrayEquals(after.driver().encode(),again.driver().encode());
            assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
        }
    }

    /** Same received/archived Driver goal plus the independently pinned scoring-clock producer. */
    private void independentFixedClockConsumesTheActualGoal(PlanningRequest request,
            OrdinaryCampaignGoal.Goal actualGoal)throws IOException {
        var configuration=org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline.configure(
                new org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline.Founding(
                        "fixed-score-clock", "1066.9.15",request.before().frame().identity().dateRaw(),2),
                org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule::calendar,Optional.empty());
        assertNotEquals(actualGoal.campaignId(),configuration.founding().campaignId());
        byte[] clockBytes=org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec.encodeConfiguration(configuration);
        Path clockFile=temporary.resolve("fixed-scoring-clock.json");
        Files.write(clockFile,clockBytes,StandardOpenOption.CREATE_NEW);
        var clockRef=new ExactRef(clockFile.toString(),clockBytes.length,DriverJson.sha256(clockBytes));
        var bound=new org.xar.ck3.control.service.root.RootCampaignPoliciesFactory.BoundDeadline(clockRef,clockBytes);
        assertEquals(configuration,bound.configuration());
        assertArrayEquals(clockBytes,Files.readAllBytes(clockFile));
        assertThrows(IllegalArgumentException.class,()->new org.xar.ck3.control.service.root.RootCampaignPoliciesFactory.BoundDeadline(
                new ExactRef(clockFile.toString(),clockBytes.length,"f".repeat(64)),clockBytes));
        var target=request.before().frame().identity().dateRaw().add(BigInteger.valueOf(45*24));
        var command=clockCommand(request,"battle-decision-epoch-advance-to-"+target,target);
        var draft=new OrdinaryPolicy.Draft("software-policy","ordinary","original software command",
                OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),
                new OpportunityJson.Obj(Map.of()).with("original_evidence",new OpportunityJson.Text("retained")));
        var implementation=ref(bytes("software-clock-policy"));
        var projected=org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.projectGoal(
                request,"a".repeat(64),ref(bytes("software-executable")),Optional.empty()).orElseThrow();
        var rewrites=new java.util.concurrent.atomic.AtomicInteger();
        var policy=new org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.CampaignAdvancePolicy(
                implementation,ignored->Optional.of(bound.configuration()),(same,original,step,cap)->{
                    assertSame(request,same);assertSame(command,original);rewrites.incrementAndGet();
                    assertEquals(configuration.boundaryRaws().get(1),cap.targetDateRaw());
                    return clockCommand(same,step,cap.targetDateRaw());
                },same->{assertSame(request,same);return Optional.of(projected);});
        var updated=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(request,draft)).draft();
        assertEquals(1,rewrites.get());
        var selected=updated.command().orElseThrow();
        assertEquals("battle-decision-epoch-advance-to-"+configuration.boundaryRaws().get(1),selected.operation().value());
        assertEquals(command.before(),selected.before());assertEquals(command.source(),selected.source());
        assertNotEquals(command.expected(),selected.expected());
        var cap=OpportunityJson.object(updated.detail().get("campaign_deadline_v1"),"actual cap");
        assertEquals(new OpportunityJson.Text("fixed-score-clock"),cap.get("campaign_id"));
        var consumed=org.xar.ck3.control.g2.m7.M7KernelPlanConsumer.decode(
                OpportunityJson.encode(updated.detail().get("m7_kernel_plan_consumption")));
        assertEquals(actualGoal,consumed.observation().goal());
        assertEquals(actualGoal.campaignId(),consumed.campaignGoalPlanUsed().campaignId());
        assertEquals(selected.operation().value(),consumed.selectedStep());
        assertEquals(draft.detail().get("original_evidence"),updated.detail().get("original_evidence"));
        assertInstanceOf(OrdinaryPolicy.Keep.class,policy.evaluate(request,updated));
        assertEquals(1,rewrites.get());
        originalGoalBindingsRemainRequired(request,updated,configuration,projected,implementation);
    }
    /** Different clock/Goal IDs do not permit a foreign physical Game, episode, or full Goal. */
    private static void originalGoalBindingsRemainRequired(PlanningRequest request,
            OrdinaryPolicy.Draft capped,
            org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline.Configuration configuration,
            M7CampaignPolicies.GoalInput original,ExactRef implementation) {
        var observed=original.observation();
        var foreignBirth=new GameIdentity(observed.game().pid(),
                new BigInteger(observed.game().creationFiletime()).add(BigInteger.ONE).toString());
        var foreignGoal=new OrdinaryCampaignGoal.Goal("other-goal-lineage",
                observed.goal().originCharacterId(),observed.goal().currentCharacterId(),observed.goal().progress());
        var wrongBirth=assertDoesNotThrow(()->reboundGoalInput(original,foreignBirth,
                observed.episodeRunId(),observed.goal()));
        var wrongEpisode=assertDoesNotThrow(()->reboundGoalInput(original,observed.game(),
                "other-observed-episode",observed.goal()));
        var wrongGoal=assertDoesNotThrow(()->reboundGoalInput(original,observed.game(),
                observed.episodeRunId(),foreignGoal));
        for(var foreign:List.of(wrongBirth,wrongEpisode,wrongGoal)) {
            var policy=new M7CampaignPolicies.CampaignAdvancePolicy(implementation,
                    ignored->Optional.of(configuration),(same,command,step,cap)->{
                        throw new AssertionError("already capped same-frame command cannot be rewritten");
                    },same->{assertSame(request,same);return Optional.of(foreign);});
            var failure=assertThrows(IllegalArgumentException.class,()->policy.evaluate(request,capped));
            assertTrue(failure.getMessage().contains("actual M7 observation crossed"),
                    "the actual policy full-binding guard must reject this otherwise valid input");
        }
    }
    private static M7CampaignPolicies.GoalInput reboundGoalInput(M7CampaignPolicies.GoalInput original,
            GameIdentity game,String episode,OrdinaryCampaignGoal.Goal goal) {
        var observed=original.observation();
        return new M7CampaignPolicies.GoalInput(new KernelCheckpointContinuity.Observation(
                observed.machineId(),"a".repeat(64),game,ref(bytes("software-executable")),
                observed.snapshotId(),observed.revision(),observed.nativeRevision(),episode,
                observed.actorCharacterId(),observed.dateRaw(),goal,null,null),original.government());
    }
    private static ActionCommand clockCommand(PlanningRequest request,String operation,BigInteger target) {
        var arguments=new OpportunityJson.Obj(Map.of()).with("target_date_raw",new OpportunityJson.IntegerValue(target));
        var expected=new ExpectedPostcondition(1,request.before(),request.source(),"software-clock/v1",
                List.of(new ExpectedInteger(new FieldKey("target_date_raw"),target)));
        return new ActionCommand("software-clock-action",request.before(),request.source(),request.sessionId(),
                new OperationKey(operation),arguments,expected,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
}
