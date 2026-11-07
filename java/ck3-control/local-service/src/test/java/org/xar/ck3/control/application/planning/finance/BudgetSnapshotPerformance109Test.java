package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetCodec;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Budget role DATA only: original producer documents and an unrelated unconsumed history extension. */
final class BudgetSnapshotPerformance109Test {
    private static final int LIMIT=FullJsonTree.MAXIMUM_BYTES;
    private static final Map<String,FinanceStatePort.Domain> DOMAINS=Map.of("construction",FinanceStatePort.Domain.CONSTRUCTION,
            "faction_gift",FinanceStatePort.Domain.FACTION_GIFT,"first_heir_marriage",FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,
            "child_marriage",FinanceStatePort.Domain.CHILD_MARRIAGE);
    private record Fixture(JsonNode corpus,Obj original,PlanningRequest small,PlanningRequest large,Obj root,
            FinanceStatePort.Snapshot state,List<FinanceStatePort.Document> documents,Arr history) { }
    private static Fixture fixture;
    @BeforeAll static void load()throws Exception {fixture=fixture();}

    @Test void allOriginalBudgetRequestsAndResultsRetainTypedPresenceWithLargeHistory()throws Exception {
        int count=0;
        for(JsonNode vector:fixture.corpus().path("cases")) {
            Obj original=json(FullJsonTree.encode(vector.get("request"),LIMIT));Obj snapshot=object(original.get("snapshot"),"snapshot");
            Obj large=snapshot.with("native_command_history",fixture.history());byte[] before=DriverJson.encode(large);
            var expected=FeastBudgetCodec.decode(DriverJson.encode(original));
            var full=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",large)));
            var actual=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",project(large))));
            assertEquals(expected,full,vector.path("name").textValue());assertEquals(expected,actual,vector.path("name").textValue());
            var result=FeastBudgetPolicy.observe(expected);assertEquals(result,FeastBudgetPolicy.observe(actual));
            assertArrayEquals(FeastBudgetCodec.encode(result),FeastBudgetCodec.encode(FeastBudgetPolicy.observe(actual)));
            assertArrayEquals(before,DriverJson.encode(large));count++;
        }
        assertEquals(30,count);
    }

    @Test void budgetKeepsItsOwnWarValidationAndCompletePendingPresence()throws Exception {
        Obj original=json(FullJsonTree.encode(fixture.corpus().path("cases").get(0).get("request"),LIMIT));
        Obj snapshot=object(original.get("snapshot"),"snapshot");
        for(Value row:List.of(Nil.INSTANCE,new Text("not-a-war"),new Bool(false),obj("war_id",new DecimalValue("7.0")),obj("war_id",new Text("7")),obj("war_id",new Bool(true)))) {
            Obj changed=snapshot.with("active_wars",new Arr(List.of(row)));
            var a=assertThrows(IllegalArgumentException.class,()->FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",changed))));
            var b=assertThrows(IllegalArgumentException.class,()->FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",project(changed)))));
            assertEquals(a.getClass(),b.getClass());assertEquals(a.getMessage(),b.getMessage());
        }
        for(Value row:List.of(obj(),obj("war_id",Nil.INSTANCE),obj("war_id",n(0)),obj("war_id",n(-1)))) {
            Obj changed=snapshot.with("active_wars",new Arr(List.of(row)));
            var expected=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",changed)));
            assertEquals(expected,FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",project(changed)))));
            assertInstanceOf(FeastBudgetPolicy.Unavailable.class,FeastBudgetPolicy.observe(expected));
        }
        Obj duplicate=snapshot.with("active_wars",new Arr(List.of(obj("war_id",n(7)),obj("war_id",n(7)))));
        var duplicateInput=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",project(duplicate))));
        assertEquals(2,duplicateInput.snapshot().activeWars().value().size());
        for(Value pending:List.of(Nil.INSTANCE,new Bool(false),n(0),new Arr(List.of()),obj("complete_unknown",new Text("retained")))) {
            Obj changed=snapshot.with("pending_character_interaction",pending);Obj projected=project(changed);
            assertEquals(pending,projected.get("pending_character_interaction"));
            var a=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",changed)));
            var b=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",projected)));
            assertEquals(a,b);assertEquals(FeastBudgetPolicy.observe(a),FeastBudgetPolicy.observe(b));
            if(pending!=Nil.INSTANCE)assertInstanceOf(FeastBudgetPolicy.Unavailable.class,FeastBudgetPolicy.observe(b));
        }
        var members=new java.util.LinkedHashMap<>(snapshot.members());members.remove("pending_character_interaction");
        var missing=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",project(new Obj(members)))));
        var nil=FeastBudgetCodec.decode(DriverJson.encode(original.with("snapshot",project(snapshot.with("pending_character_interaction",Nil.INSTANCE)))));
        assertNotEquals(missing.snapshot().pendingInteraction(),nil.snapshot().pendingInteraction());
        assertEquals(FeastBudgetPolicy.Presence.MISSING,missing.snapshot().pendingInteraction());
    }

    @Test void publicBudgetPreservesFourOriginalDocumentsHeadAndResult()throws Exception {
        byte[] snapshot=DriverJson.encode(fixture.large().observations().snapshot()),root=DriverJson.encode(fixture.root());
        var expected=FeastBudgetPolicy.observe(FeastBudgetCodec.decode(DriverJson.encode(fixture.original())));
        var small=OrdinaryFinanceCollector.budget(fixture.small(),fixture.state(),fixture.root());
        var large=OrdinaryFinanceCollector.budget(fixture.large(),fixture.state(),fixture.root());
        assertEquals(expected,small);assertEquals(expected,large);assertArrayEquals(FeastBudgetCodec.encode(expected),FeastBudgetCodec.encode(large));
        assertEquals(fixture.small().before(),fixture.state().head().current());
        for(var document:fixture.documents()) {
            var actual=fixture.state().ledger(document.domain()).orElseThrow();
            assertSame(document,actual.document());assertArrayEquals(document.bytes(),actual.document().bytes());
            assertArrayEquals(document.bytes(),DriverJson.encode(actual.original()));
        }
        assertArrayEquals(snapshot,DriverJson.encode(fixture.large().observations().snapshot()));assertArrayEquals(root,DriverJson.encode(fixture.root()));
        System.out.println("P109-budget-wrapper full="+DriverJson.encode(fixture.original().with("snapshot",fixture.large().observations().snapshot())).length
                +" role="+DriverJson.encode(fixture.original().with("snapshot",project(fixture.large().observations().snapshot()))).length);
    }

    /** Complete public budget call; input documents/head are unchanged in the two compiled Collector modes. */
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("baseline|candidate OUTPUT required");
        long started=System.nanoTime();Fixture data=fixture();long loaded=System.nanoTime();
        if(!args[0].equals("baseline")&&!args[0].equals("candidate"))throw new IllegalArgumentException("mode required");
        byte[] snapshot=DriverJson.encode(data.large().observations().snapshot()),root=DriverJson.encode(data.root());
        long oracleStarted=System.nanoTime();var typed=FeastBudgetCodec.decode(DriverJson.encode(data.original()));
        var expected=FeastBudgetPolicy.observe(typed);byte[] expectedWire=FeastBudgetCodec.encode(expected);String expectedSha=sha(expectedWire);
        long oracleNanos=System.nanoTime()-oracleStarted;
        var bean=java.lang.management.ManagementFactory.getThreadMXBean();
        com.sun.management.ThreadMXBean allocations=bean instanceof com.sun.management.ThreadMXBean available&&available.isThreadAllocatedMemorySupported()?available:null;
        if(allocations!=null&&!allocations.isThreadAllocatedMemoryEnabled())allocations.setThreadAllocatedMemoryEnabled(true);
        ObjectNode summary=JsonNodeFactory.instance.objectNode();summary.put("schema","xar.p109-public-budget-same-input/v1");summary.put("mode",args[0]);
        summary.put("reconstruction","ORIGINAL_PRODUCER_SOFTWARE_BUDGET_VECTOR_PLUS_UNCONSUMED_DRIVER139_EXTENSION_NOT_RUNTIME_AUTHORITY");
        summary.put("snapshot_bytes",snapshot.length);summary.put("snapshot_sha256",sha(snapshot));summary.put("root_sha256",sha(root));
        summary.put("expected_result_bytes",expectedWire.length);summary.put("expected_result_sha256",expectedSha);
        summary.put("load_ns",loaded-started);summary.put("independent_oracle_setup_ns",oracleNanos);summary.put("main_thread_allocation_supported",allocations!=null);
        ArrayNode samples=summary.putArray("all_warm_and_measured_samples");
        for(int i=0;i<6;i++) {
            long before=allocations==null?0:allocations.getThreadAllocatedBytes(Thread.currentThread().threadId());
            long began=System.nanoTime();var result=OrdinaryFinanceCollector.budget(data.large(),data.state(),data.root());long elapsed=System.nanoTime()-began;
            long allocated=allocations==null?0:allocations.getThreadAllocatedBytes(Thread.currentThread().threadId())-before;
            assertEquals(expected,result);assertArrayEquals(expectedWire,FeastBudgetCodec.encode(result));
            ObjectNode sample=samples.addObject();sample.put("index",i);sample.put("warmup",i<2);sample.put("public_budget_ns",elapsed);
            if(allocations==null)sample.putNull("main_thread_allocated_bytes");else sample.put("main_thread_allocated_bytes",allocated);
        }
        assertArrayEquals(snapshot,DriverJson.encode(data.large().observations().snapshot()));assertArrayEquals(root,DriverJson.encode(data.root()));
        for(var document:data.documents())assertArrayEquals(document.bytes(),data.state().ledger(document.domain()).orElseThrow().document().bytes());
        summary.put("main_ns_before_output",System.nanoTime()-started);summary.put("scope","complete public budget input assembly/encode/decode/observe; pure document/state fixture only, no HTTP/Game or saved-day throughput; all samples retained");
        byte[] result=FullJsonTree.encode(summary,32768);Files.write(Path.of(args[1]),result);System.out.write(result);System.out.println();
    }

    private static Fixture fixture()throws Exception {
        callFixture("retainedInputs",new Class<?>[]{});
        var base=(PlanningRequest)callFixture("request",new Class<?>[]{});
        Field field=FinancingSnapshotRole107Test.class.getDeclaredField("unrelatedHistory");field.setAccessible(true);Arr history=(Arr)field.get(null);
        byte[] bytes=(byte[])callFixture("resource",new Class<?>[]{String.class},"/feastbudget/original-producer-golden.json");
        JsonNode corpus=FullJsonTree.parse(bytes,LIMIT);Obj original=json(FullJsonTree.encode(corpus.path("cases").get(2).get("request"),LIMIT));
        Obj snapshot=object(original.get("snapshot"),"snapshot").with("episode_run_id",new Text("p109-software-episode"))
                .with("player_armies",new Arr(List.of())).with("active_event",Nil.INSTANCE);
        var identity=new JointBudgetSelector.Frame(integer(object(snapshot.get("played_character"),"actor").get("character_id"),"actor"),integer(snapshot.get("native_revision"),"native"),integer(snapshot.get("date_raw"),"date"));
        var frame=new JointBudgetSelector.ProposalFrame(identity,text(snapshot.get("snapshot_id"),"snapshot"),integer(snapshot.get("revision"),"revision"),"p109-software-episode");
        var before=new ObservationIdentity(base.before().machineId(),base.before().game(),frame,base.before().observationVersion());
        var small=new PlanningRequest(before,base.source(),base.sessionId(),base.deadline(),new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var large=(PlanningRequest)callFixture("withSnapshot",new Class<?>[]{PlanningRequest.class,Obj.class},small,snapshot.with("native_command_history",history));
        var documents=new ArrayList<FinanceStatePort.Document>();var readers=new ArrayList<FinanceStatePort.ReaderBinding>();
        for(var entry:DOMAINS.entrySet()) {
            byte[] body=DriverJson.encode(object(object(original.get("ledgers"),"ledgers").get(entry.getKey()),"original domain body"));
            var reference=new ExactRef("p109-original-software-domain-"+entry.getKey(),body.length,ActionCodec.sha256(body));
            documents.add(new FinanceStatePort.Document(entry.getValue(),reference,body));
            readers.add(new FinanceStatePort.ReaderBinding(entry.getValue(),reference,document->
                    json(document.bytes()).get("pending") instanceof Obj?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR));
        }
        var head=new FinanceStatePort.Head(small.before(),new ExactRef("p109-software-head",1,"a".repeat(64)),documents,List.of(),Optional.empty());
        var state=new FinanceStatePort(request->head,readers);var held=assertInstanceOf(FinanceStatePort.Known.class,state.read(small)).snapshot();
        return new Fixture(corpus,original,small,large,object(original.get("campaign_root"),"campaign root"),held,List.copyOf(documents),history);
    }
    private static Obj project(Obj original)throws Exception {Method method=OrdinaryFinanceCollector.class.getDeclaredMethod("budgetSnapshot",Obj.class);method.setAccessible(true);return (Obj)method.invoke(null,original);}
    private static Object callFixture(String name,Class<?>[] signature,Object...args)throws Exception {Method method=FinancingSnapshotRole107Test.class.getDeclaredMethod(name,signature);method.setAccessible(true);try{return method.invoke(null,args);}catch(InvocationTargetException error){if(error.getCause() instanceof Exception cause)throw cause;if(error.getCause() instanceof Error cause)throw cause;throw error;}}
    private static Obj obj(Object...pairs){return OrdinaryFinanceCollector.obj(pairs);}
    private static Obj json(byte[] bytes){return DriverJson.object(bytes,LIMIT);}
    private static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}
