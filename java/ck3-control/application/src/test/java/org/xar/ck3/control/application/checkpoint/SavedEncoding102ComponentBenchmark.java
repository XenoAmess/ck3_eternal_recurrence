package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;

/** Finite immutable DATA measurement only; no writer, physical verification, Root, Native or Game. */
public final class SavedEncoding102ComponentBenchmark {
    private static final String DRIVER_SHA="092b7df37ab70b5d28981b1c681fbf96cc1e58f0029706bab15fd741adc705f4";
    private static final String PAIR_SHA="be81b46ed5bd7c5d6bc4a5d7125a5c3f649bacaf8d3686f63f40b20ddd6764a6";
    private static long mainEntry;
    private SavedEncoding102ComponentBenchmark() { }

    public static void main(String[] args) throws Exception {
        mainEntry=System.nanoTime();
        if(args.length!=0)throw new IOException("fixed no-argument DATA benchmark required");
        var vm=ManagementFactory.getRuntimeMXBean();
        var initial=StrictJson.object();initial.put("event","benchmark_begin");
        initial.put("java_version",System.getProperty("java.version"));initial.put("vm",System.getProperty("java.vm.name"));
        initial.put("vm_version",System.getProperty("java.vm.version"));initial.put("vm_uptime_at_main_ms",vm.getUptime());
        initial.put("available_processors",Runtime.getRuntime().availableProcessors());initial.put("max_heap_bytes",Runtime.getRuntime().maxMemory());
        initial.put("startup_scope","VM uptime at main; complete process window is the independent managed ACTUAL, not a subtracted startup estimate");
        initial.put("measurement_scope","pure SAVE projection and combined comparison only; original fixed encoder; no physical IO or Runtime");
        emit(initial);

        long readStart=System.nanoTime();
        byte[] raw=resource("driver1475.json.gz",8*1024*1024);
        byte[] pairRaw=resource("pair1475.json.gz",1024*1024);
        if(raw.length!=5255697||!sha(raw).equals(DRIVER_SHA)||pairRaw.length!=1825||!sha(pairRaw).equals(PAIR_SHA))
            throw new IOException("exact qualified immutable DATA required");
        long readNanos=System.nanoTime()-readStart;
        long decodeStart=System.nanoTime();
        var pair=CheckpointPairCodec.decode(pairRaw);
        var saved=DriverStateSnapshot.decodeComplete(raw);
        if(saved.commandHistory().size()!=229||pair.historyIndex()!=229)throw new IOException("original229row pair required");
        var before=new DriverStateSnapshot.Complete(saved.session(),saved.commandHistory().subList(0,228),
                saved.lastCheckpoint(),saved.rollbackWarFailure(),saved.managedRestoreTransaction(),saved.successionExpectation(),
                saved.successionLifecycle(),saved.campaignGoal(),saved.rollbackWarFailures());
        long decodeNanos=System.nanoTime()-decodeStart;
        long markerStart=System.nanoTime();String expectedMarker=sha(saved.encode());long markerSetupNanos=System.nanoTime()-markerStart;
        var setup=StrictJson.object();setup.put("event","setup");setup.put("driver_bytes",raw.length);setup.put("driver_sha256",DRIVER_SHA);
        setup.put("pair_bytes",pairRaw.length);setup.put("pair_sha256",PAIR_SHA);setup.put("history_rows",saved.commandHistory().size());
        setup.put("read_and_source_hash_ns",readNanos);setup.put("decode_and_local_prefix_ns",decodeNanos);
        setup.put("expected_encoding_marker_ns",markerSetupNanos);setup.put("expected_marker",expectedMarker);
        setup.put("prefix_role","local projection DATA, not an original canonical writer or permission");
        setup.put("observer","null for both modes; target2to1 validated separately by the qualified DATA test");
        setup.put("harness","both modes retain their first encoding for post-timing checksum; hash/output excluded from component ns but included in main total");
        emit(setup);

        long aNanos=0,bNanos=0,warmupWindow=0,measurementWindow=0;
        int aCount=0,bCount=0;
        for(int round=0;round<2;round++) {
            String[] order=round==0?new String[]{"A","B","A","B"}:new String[]{"B","A","B","A"};
            long warmStart=System.nanoTime();
            for(int i=0;i<order.length;i++)run(order[i],"warmup",round,i,before,saved,pair,expectedMarker);
            long warmElapsed=System.nanoTime()-warmStart;warmupWindow+=warmElapsed;
            long sampleStart=System.nanoTime();
            for(int i=0;i<order.length;i++) {
                long ns=run(order[i],"sample",round,i,before,saved,pair,expectedMarker);
                if("A".equals(order[i])){aNanos+=ns;aCount++;}else{bNanos+=ns;bCount++;}
            }
            long sampleElapsed=System.nanoTime()-sampleStart;measurementWindow+=sampleElapsed;
            var endRound=StrictJson.object();endRound.put("event","round_end");endRound.put("round",round);
            endRound.put("warmup_wall_ns",warmElapsed);endRound.put("samples_and_markers_wall_ns",sampleElapsed);emit(endRound);
        }
        if(aCount!=4||bCount!=4)throw new IOException("all fixed raw samples must remain");
        var end=StrictJson.object();end.put("event","benchmark_end");end.put("a_samples",aCount);end.put("b_samples",bCount);
        end.put("a_component_sum_ns",aNanos);end.put("b_component_sum_ns",bNanos);end.put("warmup_wall_ns",warmupWindow);
        end.put("samples_and_markers_wall_ns",measurementWindow);end.put("main_total_before_final_output_ns",System.nanoTime()-mainEntry);
        end.put("gc_policy","no explicit GC and no sample deletion");end.put("speed_assertion",false);end.put("all_markers_equal",true);
        end.put("claim","one JVM component experiment; no full pipeline, production old-binary or saved-day performance claim");emit(end);
    }

    private static long run(String mode,String phase,int round,int ordinal,DriverStateSnapshot.Complete before,
            DriverStateSnapshot.Complete saved,CheckpointPair pair,String expectedMarker) throws Exception {
        long start=System.nanoTime();
        java.util.Map.Entry<DriverStateSnapshot.Complete,byte[]> holder=null;
        byte[] first;
        try {
            first=CheckpointCommitVerifier.saveProjectionEncoding(before,saved,pair,null);
            if("B".equals(mode))holder=CheckpointCommitVerifier.sameCallSavedEncoding(before,saved,first);
            if("B".equals(mode)&&holder==null)throw new IOException("fixed eligible DATA failed reuse guard");
            CheckpointCommitVerifier.requireCombinedSaveDriver(saved,saved,holder,null);
        } catch(Exception|Error failure) {
            var row=StrictJson.object();row.put("event","operation_failed");row.put("phase",phase);row.put("mode",mode);
            row.put("round",round);row.put("ordinal",ordinal);row.put("elapsed_ns",System.nanoTime()-start);
            row.put("failure_class",failure.getClass().getName());row.put("failure_message",String.valueOf(failure.getMessage()));emit(row);throw failure;
        } finally {if(holder!=null)holder.setValue(null);}
        long nanos=System.nanoTime()-start;
        String marker=sha(first);
        if(!marker.equals(expectedMarker))throw new IOException("actual encoded DATA marker changed");
        var row=StrictJson.object();row.put("event",phase);row.put("mode",mode);row.put("round",round);row.put("ordinal",ordinal);
        row.put("component_ns",nanos);row.put("marker",marker);row.put("mode_definition",mode.equals("A")?"projection + original fixed re-encode":"projection + exact local byte reuse");
        emit(row);return nanos;
    }
    private static byte[] resource(String name,int maximum) throws IOException {
        var in=SavedEncoding102ComponentBenchmark.class.getResourceAsStream("encoding102/"+name);
        if(in==null)throw new IOException("exact frozen DATA resource absent");
        try(var zip=new GZIPInputStream(in)) {
            byte[] raw=zip.readNBytes(maximum+1);
            if(raw.length==0||raw.length>maximum||zip.read()!=-1)throw new IOException("bounded frozen DATA resource required");
            return raw;
        }
    }
    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
    private static void emit(com.fasterxml.jackson.databind.node.ObjectNode row) throws IOException {
        byte[] bytes=StrictJson.canonical(row);
        System.out.write(bytes);System.out.write('\n');System.out.flush();
    }
}
