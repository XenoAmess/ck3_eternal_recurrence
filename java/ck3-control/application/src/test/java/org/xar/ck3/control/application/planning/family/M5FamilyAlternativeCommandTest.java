package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.M5FamilyCandidatePool;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssemblyCodec;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssemblyApplication;
import org.xar.ck3.control.application.planning.military.M5FormalCollection;

/** Actual original five-candidate oracle -> pool -> unchanged FamilyCommands -> shared intent and full command serialization.
 * The projection rows here are an explicit test-only structural derivation of the original diagnostic rows, not fresh Native query custody. */
final class M5FamilyAlternativeCommandTest {
    private static Obj originalInput()throws Exception {
        try(var stream=M5FamilyAlternativeCommandTest.class.getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            assertNotNull(stream,"the same original full candidate corpus must be on the application test classpath");byte[] compressed=stream.readNBytes(65537);assertTrue(compressed.length<=65536);
            assertEquals("61374f70cb7398c98bf88a16d7a797106ecdd47e1e8ee86c83b483461b5df6e6",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
            byte[] raw;try(var gzip=new GZIPInputStream(new ByteArrayInputStream(compressed))){raw=gzip.readNBytes(1048577);assertTrue(raw.length<=1048576);assertEquals(-1,gzip.read());}
            var tree=StrictJson.parse(raw,1048576);assertEquals("MATCH",tree.get("source_postcheck").textValue());
            var sample=java.util.stream.StreamSupport.stream(tree.get("cases").spliterator(),false).filter(x->x.get("name").textValue().equals("family-five-choices")).findFirst().orElseThrow();
            assertTrue(sample.get("accepted").booleanValue());assertTrue(sample.get("actual_native_driver_entry_executed").booleanValue());
            return object(OpportunityJson.parse(StrictJson.canonical(sample.get("input"),131072)));
        }
    }
    @Test void everyRealAlternativeKeepsItsPairAndUsesTheSameCanonicalCommandProducer()throws Exception {
        Obj input=originalInput(),snapshot=object(input.get("before")),plan=object(object(input.get("family")).get("plan"));
        var pool=M5FamilyCandidatePool.collect(plan);var operation=new OperationKey(M5FamilyCandidatePool.SUBMIT);
        var source=new G2Source("synthetic-family-pool-no-game","2026-10-24T00:00:00Z","1.20.0.4",new ExactRef("synthetic-original-candidate-source",1,"a".repeat(64)));
        Obj actor=object(snapshot.get("played_character"));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(OpportunityJson.integer(actor.get("character_id"),"actor"),OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),
                OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot"),OpportunityJson.integer(snapshot.get("revision"),"public revision"),OpportunityJson.text(snapshot.get("episode_run_id"),"episode"));
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        var request=new PlanningRequest(before,source,"actual-family-command-fixture",Instant.parse("2026-10-24T00:01:00Z"),
                new PlanningObservation(snapshot,List.of(),Set.of(operation),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        List<ActionCommand> archivedByActualProducer=new ArrayList<>();
        var commands=new FamilyCommands((r,o,a,p)->{throw new AssertionError("a first-heir proposal cannot become shared date advance");},(original,command)->{
            assertSame(request,original);assertEquals(original.before(),command.before());assertEquals(original.source(),command.source());archivedByActualProducer.add(command);
        });
        List<Integer> comparison=OpportunityJson.array(object(plan.get("family_marriage_private_diagnostic")).get("rows"),"actual five rows").stream().map(v->OpportunityJson.integer(object(v).get("candidate_character_id"),"candidate").intValueExact()).toList();
        for(var variant:pool.variants()) {
            Obj diagnostic=object(variant.plan().get("family_marriage_private_diagnostic"));
            // The original Python plan retained diagnostic rows, while Java's shared command input names its captured projection separately.
            Obj derived=variant.plan().with("family_marriage_projection",new Obj(Map.of("rows",diagnostic.get("rows"))));
            var command=commands.prepare(request,operation,new Obj(Map.of()),derived).orElseThrow();
            var intent=FamilyMarriageIntent.fromJson(command.arguments());
            assertEquals(variant.candidateCharacterId().intValueExact(),intent.candidateId());
            assertEquals(comparison,intent.comparisonCandidateIds());assertEquals(Optional.of(derived),intent.planningProof());
            Obj nativeRow=OpportunityJson.array(object(plan.get("family_marriage_legality")).get("native_legal_candidates"),"actual legal rows").stream().map(M5FamilyAlternativeCommandTest::object)
                    .filter(row->new IntegerValue(variant.candidateCharacterId()).equals(row.get("candidate_character_id"))).findFirst().orElseThrow();
            assertEquals(OpportunityJson.integer(nativeRow.get("recipient_matchmaker_character_id"),"actual recipient").intValueExact(),intent.recipientId());
            assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            assertEquals(intent,FamilyMarriageIntent.fromJson(ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)).arguments()));
        }
        assertEquals(5,archivedByActualProducer.size());assertEquals(5,archivedByActualProducer.stream().map(ActionCommand::actionId).distinct().count());
        assertEquals(5,archivedByActualProducer.stream().map(c->FamilyMarriageIntent.fromJson(c.arguments()).candidateId()).distinct().count());
    }
    /** A software orchestration fixture: current relation, headers and guards are explicitly constructed.
     * Only candidate/legality/diagnostic facts come from the retained original producer. No Native custody is inferred. */
    @Test void selectedAlternativeReentersTheSameActualPolicyReadsAndCommandPreparation()throws Exception {
        Obj input=originalInput(),snapshot=object(input.get("before")),originalPlan=object(object(input.get("family")).get("plan"));
        var pool=M5FamilyCandidatePool.collect(originalPlan);var request=request(snapshot);var evidence=request.source().sourceRef();
        Obj diagnostic=object(originalPlan.get("family_marriage_private_diagnostic")),legality=object(originalPlan.get("family_marriage_legality")).with("exact_ck3_build",new Text("software-family-read-fixture"));
        List<Value> diagnosticRows=OpportunityJson.array(diagnostic.get("rows"),"actual five diagnostic rows");
        // The original corpus lacks a current-relation query and full projection header; these are test-only structural inputs.
        Obj first=object(diagnosticRows.getFirst());
        Obj relation=new Obj(Map.of("status",new Text("available"),"native_revision",snapshot.get("native_revision"),
                "heir_character_id",first.get("heir_character_id"),"betrothed_character_id",Nil.INSTANCE,"primary_spouse_character_id",Nil.INSTANCE,"spouse_character_ids",new Arr(List.of())));
        Obj projection=new Obj(Map.of("schema",new Text("software-family-projection-fixture/v1"),"status",new Text("available"),"native_revision",snapshot.get("native_revision"),
                "legality_query_sequence",legality.get("query_sequence"),"rows",new Arr(diagnosticRows.stream().<Value>map(v->object(v).with("heir_spouse_character_ids",new Arr(List.of()))).toList())));
        var supplied=new EnumMap<FamilyPorts.Query,Obj>(FamilyPorts.Query.class);supplied.put(FamilyPorts.Query.CURRENT_RELATION,relation);
        supplied.put(FamilyPorts.Query.HEIR_LEGALITY,legality);supplied.put(FamilyPorts.Query.HEIR_PROJECTION,projection);
        var projections=new EnumMap<FamilyPorts.Query,FamilyPorts.ProjectedSource>(FamilyPorts.Query.class);List<FamilyPorts.Query> readOrder=new ArrayList<>();
        supplied.forEach((query,value)->projections.put(query,new FamilyPorts.ProjectedSource() {
            @Override public FamilyPorts.ProjectedRead read(PlanningRequest actual,Obj arguments) {
                assertSame(request,actual);readOrder.add(query);
                var rawRequest=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),query.operation(),arguments,actual.deadline());
                String id="software-family-read-"+readOrder.size();
                Obj envelope=new Obj(Map.of("type",new Text("command_result"),"protocol_version",new IntegerValue(BigInteger.ONE),"request_id",new Text(id),"ok",new Bool(true),"result",value));
                var raw=new RawJson(OpportunityJson.encode(envelope));byte[] encoded=raw.bytes();
                byte[] packet=ByteBuffer.allocate(encoded.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(encoded.length).put(encoded).array();
                var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(OpportunityJson.encode(value))),raw,packet);
                var guard=new PlanningReadGuard(new GuardEvidence(actual.before(),actual.source(),actual.sessionId(),BigInteger.ONE,query.operation(),evidence,evidence,
                        "software-family-read-authority",Instant.parse("2026-10-24T00:00:00Z"),actual.deadline()),true,true,true,"b".repeat(64));
                var receipt=new PlanningReadReceipt(rawRequest,"software-family-contract:"+query.name(),id,guard,guard,ack);
                return new FamilyPorts.ProjectedRead(arguments,new PlanningReadResult.Known<>(value,receipt,evidence));
            }
            @Override public Obj decode(PlanningReadReceipt receipt){throw new AssertionError("this fixture does not exercise canonical replay");}
        }));
        Obj ledgers=object(input.get("ledgers_before")),family=object(ledgers.get("family")),child=object(ledgers.get("child_default"));
        var documents=new FamilyPorts.Documents(family,family,child,new FamilyPorts.BridgeIdentity(456,"2026-10-24T00:00:00Z"),evidence,List.of(evidence,evidence,evidence));
        List<ActionCommand> commands=new ArrayList<>();var sameCommands=new FamilyCommands((r,o,a,p)->{throw new AssertionError("no date-advance replacement");},(actual,command)->{assertSame(request,actual);commands.add(command);});
        var policy=new FamilyOrdinaryPolicy(evidence,new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest actual){throw new AssertionError("only the exact supplied projected sources are expected");}
        },new FamilyPorts.Reads(Map.of(),projections),actual->{assertSame(request,actual);return new FamilyPorts.KnownDocuments(documents);},sameCommands,
                (r,q,a,o)->{throw new AssertionError("an empty original ledger has no material result to consume");},new FamilyPorts.Settings(true,false,false,false,Optional.empty()));
        var baseline=new OrdinaryPolicy.Draft("one-life-turn-v1","peace_growth","software original-family baseline",OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),object(input.get("baseline_plan")));
        var initial=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(request,baseline));
        var actualPool=M5FamilyCandidatePool.collect(initial.draft().detail());
        byte[] expanded=OpportunityJson.encode(new Obj(Map.of("plan",actualPool.originalPlan(),"plans",new Arr(actualPool.variants().stream().<Value>map(M5FamilyCandidatePool.Variant::plan).toList()))));
        assertTrue(expanded.length>131072,"actual Java owning-policy full projection/intake proof must reproduce the old expanded-wire failure");
        assertTrue(M5FamilyCandidatePool.encode(actualPool).length<131072,"the one-original compact pool must retain all proof within the unchanged bound");
        var old=PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(input));
        var assembled=new PeacetimeAssembly.Inputs(old.scope(),old.initialSnapshot(),old.baselinePlan(),old.before(),old.after(),old.constructionRelease(),old.construction(),old.faction(),actualPool.family());
        var result=PeacetimeAssemblyApplication.project(assembled);byte[] complete=PeacetimeAssemblyApplication.encode(result);
        assertTrue(complete.length<=131072);Obj roundTrip=object(OpportunityJson.parse(complete));assertEquals(result.sources(),roundTrip.get("sources"));assertEquals(result.intake(),roundTrip.get("intake"));
        Obj domain=object(result.sources().get("domains")),commitments=object(result.sources().get("existing_commitments"));
        for(int index=0;index<actualPool.variants().size();index++) {
            var variant=actualPool.variants().get(index);
            Obj source=result.sources().with("domains",new Obj(Map.of("marriage",domain.get("marriage"))))
                    .with("existing_commitments",commitments.with("character_ids",new Arr(actualPool.variants().subList(0,index).stream().<Value>map(v->new IntegerValue(v.candidateCharacterId())).toList())));
            var selection=M5FormalCollection.collect(request.source(),snapshot,source);
            assertEquals(Optional.of(M5FormalCollection.familyIdentity(snapshot,variant.plan())),selection.dispatch().selectedCandidateId(),"the actual selector must choose this available later alternative");
            var selected=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluateForCandidate(request,baseline,variant.candidateCharacterId()));
            var command=selected.draft().command().orElseThrow();var intent=FamilyMarriageIntent.fromJson(command.arguments());
            assertEquals(variant.candidateCharacterId().intValueExact(),intent.candidateId());
            assertEquals(variant.candidateCharacterId(),OpportunityJson.integer(object(selected.draft().detail().get("family_marriage_choice")).get("candidate_character_id"),"fresh selected choice"));
            assertEquals(command,commands.getLast());assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        }
        assertEquals(java.util.Collections.nCopies(6,List.of(FamilyPorts.Query.CURRENT_RELATION,FamilyPorts.Query.HEIR_LEGALITY,FamilyPorts.Query.HEIR_PROJECTION)).stream().flatMap(List::stream).toList(),readOrder);
        assertInstanceOf(OrdinaryPolicy.Wait.class,policy.evaluateForCandidate(request,baseline,BigInteger.valueOf(999)));
        assertEquals(6,commands.size(),"a missing fresh candidate must never prepare or reuse an old command");
    }
    private static PlanningRequest request(Obj snapshot) {
        var source=new G2Source("synthetic-family-policy-no-game","2026-10-24T00:00:00Z","software-family-read-fixture",new ExactRef("synthetic-family-policy-source",1,"a".repeat(64)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(OpportunityJson.integer(object(snapshot.get("played_character")).get("character_id"),"actor"),OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),
                OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot"),OpportunityJson.integer(snapshot.get("revision"),"public revision"),OpportunityJson.text(snapshot.get("episode_run_id"),"episode"));
        return new PlanningRequest(new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"software-family-policy-session",Instant.parse("2026-10-24T00:01:00Z"),
                new PlanningObservation(snapshot,List.of(),Set.of(new OperationKey(M5FamilyCandidatePool.SUBMIT)),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static Obj object(Value value){return OpportunityJson.object(value,"actual original fixture object");}
}
