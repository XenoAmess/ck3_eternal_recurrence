package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;

/** Authored peaceful native source DATA plus unrelated retained 139-row history extensions.
 * Tests the real formatter/finalizer/assembly, not a live construction quote, material, intent or permission. */
final class PeacetimeFinalizer112Test {
    @Test void completeLargeSnapshotLeavesTheSdkLaneWhileOriginalQueryAndWholeNativeWorldRemainExact()throws Exception {
        Obj small=input(true),snapshot=object(small.get("starting_snapshot"),"snapshot");
        Obj envelope=object(small.get("native_envelope"),"envelope"),result=object(envelope.get("result"),"result"),probe=object(result.get("private_probe"),"probe");
        Obj world=object(probe.get("player_world_building_sources"),"world").with("opaque_world_extension",obj("y",n(2),"x",n(1),"decimal",new DecimalValue("1.00")));
        small=small.with("native_envelope",envelope.with("result",result.with("private_probe",probe.with("player_world_building_sources",world))));
        byte[] expected=ConstructionQueryCodec.finalizeObservation(DriverJson.encode(small));
        assertArrayEquals(expected,DriverJson.encode(OrdinaryConstructionCollector.finalizePeacetime(small)));
        Arr history=history();assertEquals(139,history.items().size());
        Obj largeSnapshot=snapshot.with("native_command_history",history).with("unconsumed_fact",obj("retained",new Bool(true),"token",new DecimalValue("-0.0")));
        Obj large=small.with("starting_snapshot",largeSnapshot).with("ending_snapshot",largeSnapshot);
        byte[] original=DriverJson.encode(large),nativeBefore=DriverJson.encode(object(large.get("native_envelope"),"native"));
        assertTrue(original.length>6_000_000);assertThrows(IllegalArgumentException.class,()->ConstructionQueryCodec.finalizeObservation(original));
        Obj actual=OrdinaryConstructionCollector.finalizePeacetime(large);assertArrayEquals(expected,DriverJson.encode(actual));
        var assembly=ConstructionPeacetimeSources.assembly(actual);assertEquals(PeacetimeAssembly.ConstructionStatus.NO_LEGAL_BUDGETED_BUILDING,assembly.status());
        assertArrayEquals(expected,DriverJson.encode(assembly.originalQuery()));
        assertArrayEquals(original,DriverJson.encode(large));assertArrayEquals(nativeBefore,DriverJson.encode(object(large.get("native_envelope"),"native")));
        assertEquals(object(DriverJson.object(expected,ConstructionQueryCodec.MAX_BYTES).get("world"),"fixed-codec world"),
                object(actual.get("world"),"full finalized world, including opaque members"));
        System.out.println("P112 original_query="+original.length+" finalized="+expected.length+" original_sha="+ActionCodec.sha256(original));
    }
    @Test void copyPresentBuildParentsAndSourceFrameErrorsRetainTheOriginalSdkMeaning() {
        Obj base=input(true),snapshot=object(base.get("starting_snapshot"),"snapshot"),diagnostics=object(snapshot.get("diagnostics"),"diagnostics"),hello=object(diagnostics.get("hello"),"hello");
        for(Value diagnostic:List.of(Nil.INSTANCE,new Text("opaque-parent"),new Arr(List.of()),obj(),obj("hello",Nil.INSTANCE),obj("hello",new Bool(false)))) {
            Obj variant=snapshot.with("diagnostics",diagnostic);sameReference(base.with("starting_snapshot",variant).with("ending_snapshot",variant));
        }
        sameReference(base.with("starting_snapshot",without(snapshot,"diagnostics")));
        Obj fallback=hello.with("game_version",hello.get("expected_ck3_version")).with("executable_sha256",hello.get("expected_ck3_sha256"));
        for(String key:List.of("expected_ck3_version","expected_ck3_sha256")) {
            sameReference(base.with("starting_snapshot",snapshot.with("diagnostics",diagnostics.with("hello",without(fallback,key)))));
            for(Value bad:List.of(Nil.INSTANCE,new Text(""),new Bool(true)))
                sameReference(base.with("starting_snapshot",snapshot.with("diagnostics",diagnostics.with("hello",fallback.with(key,bad)))));
        }
        for(Value bad:List.of(Nil.INSTANCE,new Text("not-object"),new Arr(List.of())))sameReference(base.with("starting_snapshot",bad));
        sameReference(without(base,"starting_snapshot"));
        for(Value bad:List.of(Nil.INSTANCE,new Bool(false),new Arr(List.of())))sameReference(base.with("starting_snapshot",snapshot.with("played_character",bad)));
        for(String field:List.of("active_event","pending_character_interaction")) {
            sameReference(base.with("starting_snapshot",without(snapshot,field)));
            sameReference(base.with("starting_snapshot",snapshot.with(field,new Bool(false))));
        }
        sameReference(base.with("ending_snapshot",snapshot.with("episode_run_id",new Text("another-episode"))));
        sameReference(base.with("expected_revision",new DecimalValue("3.0")));
    }
    @Test void originalModesSchemaEnvelopeAndConsumedArraysKeepTheirBoundedRefusals() {
        Obj base=input(true),envelope=object(base.get("native_envelope"),"envelope"),snapshot=object(base.get("starting_snapshot"),"snapshot");
        for(String key:List.of("material_receipt","wartime_observation"))assertThrows(IllegalArgumentException.class,()->OrdinaryConstructionCollector.finalizePeacetime(base.with(key,new Bool(true))));
        sameReference(base.with("schema",new Text("unknown")));sameReference(base.with("extra_root_member",new Bool(true)));
        sameReference(base.with("native_envelope",envelope.with("request_id",new Text("other-request"))));
        sameReference(base.with("native_query_request_id",new Bool(false)));
        Obj oversized=base.with("native_envelope",envelope.with("unknown_native_result",new Text("x".repeat(ConstructionQueryCodec.MAX_BYTES))));
        assertThrows(IllegalArgumentException.class,()->OrdinaryConstructionCollector.finalizePeacetime(oversized));
        Obj consumed=base.with("starting_snapshot",snapshot.with("active_wars",new Arr(List.of(new Text("x".repeat(ConstructionQueryCodec.MAX_BYTES))))));
        assertThrows(IllegalArgumentException.class,()->OrdinaryConstructionCollector.finalizePeacetime(consumed));
        assertThrows(IllegalArgumentException.class,()->OrdinaryConstructionCollector.finalizePeacetime(input(false)));
    }
    private static void sameReference(Obj input) {
        byte[] before=DriverJson.encode(input);Obj original;
        try { original=DriverJson.object(ConstructionQueryCodec.finalizeObservation(before),ConstructionQueryCodec.MAX_BYTES); }
        catch(IllegalArgumentException rejected) {assertThrows(IllegalArgumentException.class,()->OrdinaryConstructionCollector.finalizePeacetime(input));assertArrayEquals(before,DriverJson.encode(input));return;}
        if(List.of(new Text("selected"),new Text("no_legal_budgeted_building")).contains(original.get("status")))
            assertArrayEquals(DriverJson.encode(original),DriverJson.encode(OrdinaryConstructionCollector.finalizePeacetime(input)));
        else assertThrows(IllegalArgumentException.class,()->OrdinaryConstructionCollector.finalizePeacetime(input));
        assertArrayEquals(before,DriverJson.encode(input));
    }
    private static Obj without(Obj original,String key){var copy=new java.util.LinkedHashMap<>(original.members());copy.remove(key);return new Obj(copy);}
    private static Arr history()throws Exception {
        try(var raw=PeacetimeFinalizer112Test.class.getResourceAsStream("/org/xar/ck3/control/application/checkpoint/encoding102/driver1475.json.gz")) {
            assertNotNull(raw,"qualified Driver fixture must be packaged");
            try(var gzip=new GZIPInputStream(raw)) {
                byte[] bytes=gzip.readNBytes(8*1024*1024);assertEquals(-1,gzip.read());
                var driver=DriverStateSnapshot.decodeComplete(bytes);var values=new ArrayList<Value>();
                for(int index=0;index<139;index++)values.add(DriverJson.object(driver.commandHistory().get(index).originalRow().json(),DriverJson.MAX_NATIVE_BYTES));
                return new Arr(values);
            }
        }
    }
    /** Fixed finite full static-finalizer call. Only the ordinary production Collector classpath differs in A/B. */
    public static void main(String[] args)throws Exception {
        long mainStarted=System.nanoTime();
        if(args.length!=2)throw new IllegalArgumentException("mode and exact output path required");
        long setup=System.nanoTime();Obj small=input(true),snapshot=object(small.get("starting_snapshot"),"snapshot").with("unconsumed_text",new Text("x".repeat(96*1024)));
        Obj input=small.with("starting_snapshot",snapshot).with("ending_snapshot",snapshot);byte[] original=DriverJson.encode(input);
        if(original.length>=ConstructionQueryCodec.MAX_BYTES)throw new IllegalArgumentException("A/B DATA must remain in the unchanged baseline lane");
        byte[] expected=ConstructionQueryCodec.finalizeObservation(original);String expectedSha=ActionCodec.sha256(expected);long setupNs=System.nanoTime()-setup;
        var bean=java.lang.management.ManagementFactory.getThreadMXBean();com.sun.management.ThreadMXBean allocation=bean instanceof com.sun.management.ThreadMXBean extended&&extended.isThreadAllocatedMemorySupported()?extended:null;
        if(allocation!=null&&!allocation.isThreadAllocatedMemoryEnabled())allocation.setThreadAllocatedMemoryEnabled(true);
        var out=StrictJson.object().put("schema","ck3.p112.full-static-finalizer-component/v1").put("mode",args[0]).put("setup_ns",setupNs)
                .put("input_bytes",original.length).put("input_sha256",ActionCodec.sha256(original)).put("expected_bytes",expected.length).put("expected_sha256",expectedSha)
                .put("allocation_supported",allocation!=null);var events=out.putArray("events");
        for(int index=0;index<6;index++) {
            long allocatedBefore=allocation==null?0:allocation.getThreadAllocatedBytes(Thread.currentThread().threadId());long started=System.nanoTime();
            Obj actual=OrdinaryConstructionCollector.finalizePeacetime(input);long elapsed=System.nanoTime()-started;
            Long allocated=allocation==null?null:allocation.getThreadAllocatedBytes(Thread.currentThread().threadId())-allocatedBefore;
            byte[] wire=DriverJson.encode(actual);if(!ArraysEqual(expected,wire))throw new AssertionError("full finalizer output changed");
            var event=events.addObject().put("kind",index<2?"warm":"measured").put("index",index).put("elapsed_ns",elapsed).put("bytes",wire.length).put("sha256",ActionCodec.sha256(wire));
            if(allocated==null)event.putNull("thread_allocated_bytes");else event.put("thread_allocated_bytes",allocated);
        }
        if(!ArraysEqual(original,DriverJson.encode(input)))throw new AssertionError("original input changed");
        out.put("main_ns_before_output",System.nanoTime()-mainStarted);
        Files.write(Path.of(args[1]),StrictJson.canonical(out));System.out.println(new String(StrictJson.canonical(out),StandardCharsets.UTF_8));
    }
    private static boolean ArraysEqual(byte[] a,byte[] b){return java.util.Arrays.equals(a,b);}
    private static Obj input(boolean coverage) {
        Obj snapshot = obj("snapshot_id", new Text("native:3"), "revision", n(3), "native_revision", n(3), "date_raw", n(100), "episode_run_id", new Text("episode"),
                "paused", new Bool(true), "map_ready", new Bool(true), "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "played_character", obj("character_id", n(1), "alive", new Bool(true)), "active_wars", new Arr(List.of()), "player_armies", new Arr(List.of()),
                "diagnostics", obj("bridge_pid", n(42), "bridge_creation_date", new Text("actual-fixture-process"), "hello",
                        obj("expected_ck3_version", new Text("1.20.0.4"), "expected_ck3_sha256", new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"))));
        Obj world = obj("status", new Text("source_available"), "snapshot_revision", n(3), "date_raw", n(100), "player_character_id", n(1),
                "native_final_legality_evaluated", new Bool(true), "native_cost_evaluated", new Bool(true), "player_gold_raw", n(100),
                "active_constructions", new Arr(List.of()), "completed_buildings_observed", new Bool(true), "completed_buildings", new Arr(List.of()),
                "positive_income_coverage_complete", new Bool(coverage), "legal_samples", new Arr(List.of()));
        Obj probe = obj("advertised", new Bool(false), "snapshot_revision", n(3), "date_raw", n(100), "proof_epoch", n(2), "player_world_building_sources", world);
        Obj envelope = obj("type", new Text("command_result"), "protocol_version", n(1), "request_id", new Text("actual-fixture-query"), "ok", new Bool(true),
                "result", obj("step", new Text("g2_player_construction_view_probe_v1"), "accepted", new Bool(true), "private_probe", probe));
        return obj("schema", new Text("xar.construction-query-observation-input.v1"), "starting_snapshot", snapshot, "ending_snapshot", snapshot,
                "native_envelope", envelope, "expected_revision", n(3), "native_query_request_id", new Text("actual-fixture-query"),
                "material_receipt", new Bool(false), "wartime_observation", new Bool(false));
    }
    private static IntegerValue n(long number){return new IntegerValue(BigInteger.valueOf(number));}
}
