package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;

/** New component DATA over the already-qualified P107 software READ fixture, without running its old test methods. */
final class CashSnapshotPerformance108Test {
    private static final int LIMIT=FullJsonTree.MAXIMUM_BYTES;
    private record Fixture(PlanningRequest small,PlanningRequest large,Obj cash,OrdinaryFinanceCollector collector,Object reads,Arr history) { }
    private static Fixture fixture;
    @BeforeAll static void load()throws Exception {fixture=fixture();}

    @Test void retainedLoanAndRawContextInputsKeepEveryNormalizedByteAndTypedValue()throws Exception {
        String[] rows=new String((byte[])callFixture("gzip",new Class<?>[]{String.class},"/holyloan/original-v1.jsonl.gz"),StandardCharsets.UTF_8).split("\\R");
        int loan=0,rawContext=0,negative=0;
        for(int i=1;i+1<rows.length;i++) {
            JsonNode request=FullJsonTree.parse(rows[i].getBytes(StandardCharsets.UTF_8),LIMIT);
            if(!request.isObject()||!"normalize".equals(request.path("operation").textValue()))continue;
            JsonNode meta=FullJsonTree.parse(rows[i-1].getBytes(StandardCharsets.UTF_8),LIMIT),args=request.path("arguments"),cash=args.path("value");
            boolean valid="result".equals(meta.path("expected_kind").textValue());
            boolean loanCase=valid&&cash.has(RawCashCodec.LOAN_KEY),rawCase=valid&&cash.has("current_raw_context_v1");
            boolean rejected=meta.path("ordinal").asInt()==261||meta.path("ordinal").asInt()==263;
            if(!loanCase&&!rawCase&&!rejected)continue;
            Obj original=json(FullJsonTree.encode(args.get("snapshot"),LIMIT));
            Obj large=original.with("native_command_history",fixture.history());
            byte[] input=FullJsonTree.encode(cash,LIMIT),before=DriverJson.encode(large),originalCash=input.clone();
            byte[] projected=DriverJson.encode(project(large));
            if(rejected) {
                var a=assertThrows(IllegalArgumentException.class,()->RawCashCodec.normalize(input,before));
                var b=assertThrows(IllegalArgumentException.class,()->RawCashCodec.normalize(input,projected));
                assertEquals(a.getClass(),b.getClass());assertEquals(a.getMessage(),b.getMessage());negative++;
            } else {
                var expected=RawCashCodec.normalize(input,DriverJson.encode(original));
                var withHistory=RawCashCodec.normalize(input,before);
                var actual=RawCashCodec.normalize(input,projected);
                equal(expected,withHistory);equal(expected,actual);
                if(loanCase)loan++;if(rawCase)rawContext++;
            }
            assertArrayEquals(originalCash,input);assertArrayEquals(before,DriverJson.encode(large));
        }
        assertEquals(32,loan);assertEquals(7,rawContext);assertEquals(2,negative);
    }

    @Test void publicCashRetainsOriginalPacketAndFullStateAcrossTheRoleProjection()throws Exception {
        byte[] before=DriverJson.encode(fixture.large().observations().snapshot()),cashBefore=DriverJson.encode(fixture.cash());
        var small=cash(fixture.collector(),fixture.small());
        var actual=cash(fixture.collector(),fixture.large());
        var expected=RawCashCodec.normalize(cashBefore,DriverJson.encode(fixture.small().observations().snapshot()));
        equal(expected,small.normalized());equal(expected,actual.normalized());
        assertArrayEquals(small.original().originalFrame(),actual.original().originalFrame());
        assertArrayEquals(small.original().receipt().original().originalPacket(),actual.original().receipt().original().originalPacket());
        assertEquals(fixture.large().before(),actual.original().receipt().request().before());
        assertEquals(fixture.large().source(),actual.original().receipt().request().source());
        assertEquals(fixture.large().deadline(),actual.original().receipt().request().deadline());
        assertArrayEquals(before,DriverJson.encode(fixture.large().observations().snapshot()));assertArrayEquals(cashBefore,DriverJson.encode(fixture.cash()));
        assertEquals(2,cashCalls(fixture.reads()));
    }

    /** Same old/new public cash method, software READ packet and large input; only Collector prefix differs. */
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("baseline|candidate OUTPUT required");
        long began=System.nanoTime();Fixture data=fixture();long loaded=System.nanoTime();
        boolean baseline=args[0].equals("baseline");if(!baseline&&!args[0].equals("candidate"))throw new IllegalArgumentException("mode required");
        byte[] snapshotBefore=DriverJson.encode(data.large().observations().snapshot()),cashBefore=DriverJson.encode(data.cash());
        long oracleStarted=System.nanoTime();
        var expected=RawCashCodec.normalize(cashBefore,DriverJson.encode(data.small().observations().snapshot()));
        byte[] expectedWire=expected.toJson();String expectedSha=sha(expectedWire);long oracleNanos=System.nanoTime()-oracleStarted;
        var bean=java.lang.management.ManagementFactory.getThreadMXBean();
        com.sun.management.ThreadMXBean allocations=bean instanceof com.sun.management.ThreadMXBean available&&available.isThreadAllocatedMemorySupported()?available:null;
        if(allocations!=null&&!allocations.isThreadAllocatedMemoryEnabled())allocations.setThreadAllocatedMemoryEnabled(true);
        ObjectNode summary=JsonNodeFactory.instance.objectNode();summary.put("schema","xar.p108-public-cash-same-input/v1");summary.put("mode",args[0]);
        summary.put("reconstruction","EXISTING_SOFTWARE_PRODUCER_VECTOR_314_PLUS_UNCONSUMED_DRIVER139_EXTENSION_NOT_RUNTIME_AUTHORITY");
        summary.put("snapshot_bytes",snapshotBefore.length);summary.put("snapshot_sha256",sha(snapshotBefore));summary.put("role_snapshot_bytes",DriverJson.encode(project(data.large().observations().snapshot())).length);
        summary.put("raw_cash_bytes",cashBefore.length);summary.put("raw_cash_sha256",sha(cashBefore));summary.put("normalized_wire_bytes",expectedWire.length);summary.put("normalized_wire_sha256",expectedSha);
        summary.put("load_ns",loaded-began);summary.put("independent_oracle_setup_ns",oracleNanos);summary.put("main_thread_allocation_supported",allocations!=null);
        ArrayNode samples=summary.putArray("all_warm_and_measured_samples");
        byte[] originalPacket=null;
        for(int i=0;i<6;i++) {
            long allocatedBefore=allocations==null?0:allocations.getThreadAllocatedBytes(Thread.currentThread().threadId());
            long start=System.nanoTime();var actual=cash(data.collector(),data.large());long elapsed=System.nanoTime()-start;
            long allocated=allocations==null?0:allocations.getThreadAllocatedBytes(Thread.currentThread().threadId())-allocatedBefore;
            equal(expected,actual.normalized());
            assertEquals(expectedSha,sha(actual.normalized().toJson()));
            byte[] packet=actual.original().receipt().original().originalPacket();
            if(originalPacket==null)originalPacket=packet;else assertArrayEquals(originalPacket,packet);
            ObjectNode sample=samples.addObject();sample.put("index",i);sample.put("warmup",i<2);sample.put("public_cash_ns",elapsed);
            if(allocations==null)sample.putNull("main_thread_allocated_bytes");else sample.put("main_thread_allocated_bytes",allocated);
        }
        assertEquals(6,cashCalls(data.reads()));assertArrayEquals(snapshotBefore,DriverJson.encode(data.large().observations().snapshot()));assertArrayEquals(cashBefore,DriverJson.encode(data.cash()));
        summary.put("all_original_software_read_packets_identical_sha256",sha(originalPacket));summary.put("software_read_calls",cashCalls(data.reads()));
        summary.put("main_ns_before_output",System.nanoTime()-began);summary.put("scope","complete public cash software producer includes registered packet decode, original cash encode and normalize; no live query/HTTP or saved-game-day throughput; all samples retained");
        byte[] output=FullJsonTree.encode(summary,32768);Files.write(Path.of(args[1]),output);System.out.write(output);System.out.println();
    }

    private static Fixture fixture()throws Exception {
        callFixture("retainedInputs",new Class<?>[]{});
        PlanningRequest small=(PlanningRequest)callFixture("request",new Class<?>[]{});
        Arr history=(Arr)field("unrelatedHistory");JsonNode loan=(JsonNode)field("loanOriginal");
        Obj raw=json(FullJsonTree.encode(loan.path("cash_resources"),LIMIT));
        Class<?> readsType=Class.forName(FinancingSnapshotRole107Test.class.getName()+"$OriginalReads");
        Constructor<?> constructor=readsType.getDeclaredConstructor(Obj.class);constructor.setAccessible(true);Object reads=constructor.newInstance(raw);
        var collector=(OrdinaryFinanceCollector)callFixture("collector",new Class<?>[]{readsType,PlanningRequest.class},reads,small);
        Obj extended=small.observations().snapshot().with("native_command_history",history);
        var large=(PlanningRequest)callFixture("withSnapshot",new Class<?>[]{PlanningRequest.class,Obj.class},small,extended);
        return new Fixture(small,large,raw,collector,reads,history);
    }
    private static void equal(RawCashCodec.NormalizedCurrentCash expected,RawCashCodec.NormalizedCurrentCash actual) {
        assertArrayEquals(expected.toJson(),actual.toJson());assertEquals(expected.frame(),actual.frame());
        assertEquals(expected.activeWarIds(),actual.activeWarIds());assertEquals(expected.playerArmyIds(),actual.playerArmyIds());
        assertEquals(expected.metrics(),actual.metrics());assertEquals(expected.loanObservation(),actual.loanObservation());
    }
    private static OrdinaryFinanceCollector.Cash cash(OrdinaryFinanceCollector collector,PlanningRequest request){return assertInstanceOf(OrdinaryFinanceCollector.Cash.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,collector.cash(request)).value());}
    private static Obj project(Obj snapshot)throws Exception {Method method=OrdinaryFinanceCollector.class.getDeclaredMethod("financingSnapshot",Obj.class);method.setAccessible(true);return (Obj)method.invoke(null,snapshot);}
    private static int cashCalls(Object reads)throws Exception {Field field=reads.getClass().getDeclaredField("cashCalls");field.setAccessible(true);return field.getInt(reads);}
    private static Object field(String name)throws Exception {Field field=FinancingSnapshotRole107Test.class.getDeclaredField(name);field.setAccessible(true);return field.get(null);}
    private static Object callFixture(String name,Class<?>[] signature,Object...args)throws Exception {Method method=FinancingSnapshotRole107Test.class.getDeclaredMethod(name,signature);method.setAccessible(true);try{return method.invoke(null,args);}catch(InvocationTargetException error){if(error.getCause() instanceof Exception cause)throw cause;if(error.getCause() instanceof Error cause)throw cause;throw error;}}
    private static Obj json(byte[] value){return DriverJson.object(value,LIMIT);}
    private static String sha(byte[] value)throws Exception {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
}
