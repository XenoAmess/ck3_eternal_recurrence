package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Fixed offline DATA experiment, not an adaptive benchmark or production entry point. */
public final class ProjectFullThreeVersion146Test {
    private static final String ASM="org.xar.ck3.control.application.driver.DriverObservationAssembler";
    private static final String DRIVER="org.xar.ck3.control.application.driver.DriverJson";
    private static final List<String> VARIANTS=List.of("A","B","C");
    private static final List<String> ORDER=List.of("A","B","C","C","B","A");
    @org.junit.jupiter.api.io.TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) Path directory;

    private static Path property(String key)throws Exception {return Path.of(java.util.Objects.requireNonNull(System.getProperty(key),"explicit qualified source root required: "+key)).toRealPath();}
    /** Only A's exact8 and B's exact9; public DTOs/Jackson/normalizers are shared with the parent. */
    private static final class VersionLoader extends java.net.URLClassLoader {
        private final java.util.Set<String> family;
        private static java.net.URL[] roots(String variant)throws Exception {
            return switch(variant) {
                case "A" -> new java.net.URL[]{property("ck3.p146.oldAssemblerRoot").toUri().toURL(),property("ck3.p146.oldDriverRoot").toUri().toURL()};
                case "B" -> new java.net.URL[]{property("ck3.p146.countRoot").toUri().toURL()};
                default -> throw new IllegalArgumentException("only qualified A or B child loader required");
            };
        }
        private VersionLoader(String variant)throws Exception {
            super(roots(variant),ProjectFullThreeVersion146Test.class.getClassLoader());
            var names=new java.util.HashSet<>(java.util.Set.of(ASM,ASM+"$CanonicalNativeState",ASM+"$Complete",ASM+"$FullSnapshot",ASM+"$Incomplete",ASM+"$Result",DRIVER,DRIVER+"$ContentComparison"));
            if(variant.equals("B"))names.add(DRIVER+"$EncodedByteCount");family=java.util.Set.copyOf(names);
        }
        @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException {
            synchronized(getClassLoadingLock(name)) {
                if(!family.contains(name)) {
                    if(name.startsWith(ASM+"$")||name.startsWith(DRIVER+"$"))throw new ClassNotFoundException("unlisted qualified version family member "+name);
                    return getParent().loadClass(name);
                }
                Class<?> type=findLoadedClass(name);if(type==null)type=findClass(name);if(resolve)resolveClass(type);return type;
            }
        }
    }
    private static void sourceEquals(Class<?> type,Path expected)throws Exception {
        assertEquals(expected,Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath());
    }
    private static Object invoke(Method target,Object instance,NativeObservationPort.ObservedFrame frame,DriverObservationFacts facts,ExactRef evidence)throws Throwable {
        try{return target.invoke(instance,frame,facts,evidence);}catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
    }
    private static Map<String,Object> metricStats(List<Map<String,Object>> rows,String variant,String key) {
        var values=new ArrayList<Long>();int missing=0;long total=0;
        for(var row:rows)if(variant.equals(row.get("variant"))) {
            long value=row.get(key) instanceof Number number?number.longValue():-1;if(value<0)missing++;else{values.add(value);total+=value;}
        }
        var result=new LinkedHashMap<String,Object>();result.put("known_count",values.size());result.put("missing_count",missing);result.put("known_total",total);
        if(missing==0&&!values.isEmpty()) {
            values.sort(Long::compare);int n=values.size();long low=values.get((n-1)/2),high=values.get(n/2);
            result.put("total",total);result.put("min",values.get(0));result.put("max",values.get(n-1));
            result.put("median",java.math.BigDecimal.valueOf(low).add(java.math.BigDecimal.valueOf(high)).divide(java.math.BigDecimal.valueOf(2)).toPlainString());
        } else {result.put("total",null);result.put("min",null);result.put("max",null);result.put("median",null);}
        return result;
    }
    private static Map<String,Object> cycleMetric(List<Map<String,Object>> rows,int cycle,String key) {
        var sums=new LinkedHashMap<String,Long>();boolean complete=true;
        for(String variant:VARIANTS){long total=0;int count=0;boolean known=true;
            for(var row:rows)if(((Number)row.get("cycle")).intValue()==cycle&&variant.equals(row.get("variant"))) {
                count++;long value=row.get(key) instanceof Number number?number.longValue():-1;if(value<0)known=false;else total+=value;
            }
            if(count!=2||!known)complete=false;sums.put(variant,count==2&&known?total:null);
        }
        var out=new LinkedHashMap<String,Object>();out.put("two_call_sums",sums);
        out.put("B_minus_A",complete?sums.get("B")-sums.get("A"):null);
        out.put("C_minus_B",complete?sums.get("C")-sums.get("B"):null);
        out.put("C_minus_A",complete?sums.get("C")-sums.get("A"):null);return out;
    }
    @Test public void fixedSixteenCyclesCompareThreeQualifiedProjectFullVersions()throws Throwable {
        long windowStart=System.nanoTime();var report=new LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();report.put("rows",rows);Throwable primary=null;
        report.put("schema","ck3.p146.three-version-fixed-public-project-experiment/v1");report.put("cycles_declared",16);report.put("order_per_cycle",ORDER);
        report.put("total_target_calls_declared",96);report.put("calls_per_variant_declared",32);report.put("extra_target_warmups",0);
        report.put("variant_semantics",Map.of("A","pre-count P138Assembler6+P137Driver2 two roots same child8","B","P143 count-only complete9 same child","C","P144 count+guardcopy Assembler6 plus original P143Driver3 parent9"));
        report.put("known_design_bias","Fixture and postchecks use parent DriverJson, so C shares writer/factory/hash code and state with observation while A/B use independent child Drivers. All share parent JDK/Jackson/normalizers. ABCCBA balances linear order only, is not randomized and does not create identical JIT/GC states. No isolated causality or worker-speed acceptance is encoded.");
        try(var old=new VersionLoader("A");var count=new VersionLoader("B")) {
            ClassLoader[] loaders={old,count,ProjectFullThreeVersion146Test.class.getClassLoader()};Method[] targets=new Method[3];Object[] instances=new Object[3];Method[][] getters=new Method[3][5];
            var initialization=new ArrayList<Map<String,Object>>();String[] getterNames={"actual","facts","originalEvidence","semantic","fullBindingSha256"};
            for(int side=0;side<3;side++) {
                String variant=VARIANTS.get(side);long start=System.nanoTime();var driver=Class.forName(DRIVER,true,loaders[side]);long driverEnd=System.nanoTime();
                var assembler=Class.forName(ASM,true,loaders[side]);long asmEnd=System.nanoTime();
                targets[side]=assembler.getMethod("projectFull",NativeObservationPort.ObservedFrame.class,DriverObservationFacts.class,ExactRef.class);
                instances[side]=assembler.getConstructor().newInstance();Class<?> result=targets[side].getReturnType();assertEquals(ASM+"$FullSnapshot",result.getName());
                for(int i=0;i<getterNames.length;i++)getters[side][i]=result.getMethod(getterNames[i]);
                Path expectedAsm=property(side==0?"ck3.p146.oldAssemblerRoot":side==1?"ck3.p146.countRoot":"ck3.p146.currentAssemblerRoot");
                Path expectedDriver=property(side==0?"ck3.p146.oldDriverRoot":side==1?"ck3.p146.countRoot":"ck3.p146.currentDriverRoot");
                sourceEquals(assembler,expectedAsm);sourceEquals(driver,expectedDriver);
                assertSame(loaders[side],assembler.getClassLoader());assertSame(loaders[side],driver.getClassLoader());
                if(side>0)assertSame(loaders[side],Class.forName(DRIVER+"$EncodedByteCount",false,loaders[side]).getClassLoader());
                initialization.add(Map.of("variant",variant,"driver_init_ns",driverEnd-start,"assembler_load_init_ns",asmEnd-driverEnd,"reflection_and_sourcechecks_ns",System.nanoTime()-asmEnd,"assembler_root",expectedAsm.toString(),"driver_root",expectedDriver.toString()));
            }
            report.put("initialization",initialization);
            String large=STATE.replace("\"original_metric\":1.00","\"original_metric\":1.00,\"opaque_unconsumed_extension\":\""+"x".repeat(3_400_000)+"\"");
            var frame=actual(large);String stateSha=DriverJson.sha256(frame.state().bytes()),packetSha=DriverJson.sha256(frame.originalPacket());
            var evidence=ref(frame.originalPacket());var facts=new DriverObservationFacts(known().driver(),3,7,frame.session(),frame.snapshotId(),frame.nativeRevision(),stateSha,BigInteger.valueOf(2),3,source(),new OpportunityJson.Obj(Map.of()),ref(bytes("p146-fixed-facts")));
            report.put("input",Map.of("state_bytes",frame.state().bytes().length,"packet_bytes",frame.originalPacket().length,"state_sha256",stateSha,"packet_sha256",packetSha,"facts_evidence_sha256",facts.semanticFactsEvidence().sha256(),"observation_version",facts.observationVersion()));
            var cpu=java.lang.management.ManagementFactory.getThreadMXBean();boolean cpuAvailable=cpu.isCurrentThreadCpuTimeSupported();if(cpuAvailable&&!cpu.isThreadCpuTimeEnabled())cpu.setThreadCpuTimeEnabled(true);
            com.sun.management.ThreadMXBean allocation=cpu instanceof com.sun.management.ThreadMXBean bean?bean:null;boolean allocAvailable=allocation!=null&&allocation.isThreadAllocatedMemorySupported();if(allocAvailable&&!allocation.isThreadAllocatedMemoryEnabled())allocation.setThreadAllocatedMemoryEnabled(true);
            report.put("CPU_available",cpuAvailable);report.put("allocation_available",allocAvailable);report.put("setup_ns_before_calls",System.nanoTime()-windowStart);
            String expectedSemantic=null,expectedBinding=null;List<String> expectedOrder=null;int[] seen=new int[3];
            for(int cycle=0;cycle<16;cycle++)for(int position=0;position<6;position++) {
                String variant=ORDER.get(position);int side=VARIANTS.indexOf(variant);var row=new LinkedHashMap<String,Object>();rows.add(row);
                row.put("index",rows.size()-1);row.put("cycle",cycle);row.put("position",position);row.put("variant",variant);row.put("variant_index",seen[side]++);row.put("all_post_checks_passed",false);
                long outerStart=System.nanoTime(),cs=cpuAvailable?cpu.getCurrentThreadCpuTime():-1,as=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1;
                long start=System.nanoTime();Object result;boolean completed=false;
                try{result=invoke(targets[side],instances[side],frame,facts,evidence);completed=true;}
                finally{long end=System.nanoTime(),ae=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1,ce=cpuAvailable?cpu.getCurrentThreadCpuTime():-1;
                    row.put("wall_start_ns",start);row.put("wall_end_ns",end);row.put("wall_ns",end-start);row.put("CPU_start_ns",cs);row.put("CPU_end_ns",ce);row.put("CPU_ns",cs>=0&&ce>=cs?ce-cs:-1);
                    row.put("allocation_start_bytes",as);row.put("allocation_end_bytes",ae);row.put("thread_allocated_bytes",as>=0&&ae>=as?ae-as:-1);row.put("target_completed",completed);}
                assertSame(frame,getters[side][0].invoke(result));assertSame(facts,getters[side][1].invoke(result));assertEquals(evidence,getters[side][2].invoke(result));
                var semantic=assertInstanceOf(OpportunityJson.Obj.class,getters[side][3].invoke(result));String binding=assertInstanceOf(String.class,getters[side][4].invoke(result));
                String sha=DriverJson.sha256(DriverJson.encode(semantic));var order=new ArrayList<>(semantic.members().keySet());
                if(expectedSemantic==null){expectedSemantic=sha;expectedBinding=binding;expectedOrder=order;}
                assertEquals(expectedSemantic,sha);assertEquals(expectedBinding,binding);assertEquals(expectedOrder,order);
                assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,semantic.get("original_metric")).token());assertEquals(3_400_000,assertInstanceOf(OpportunityJson.Text.class,semantic.get("opaque_unconsumed_extension")).value().length());
                assertEquals(stateSha,DriverJson.sha256(frame.state().bytes()));assertEquals(packetSha,DriverJson.sha256(frame.originalPacket()));
                row.put("semantic_sha256",sha);row.put("full_binding_sha256",binding);row.put("member_order",order);row.put("state_sha256",stateSha);row.put("packet_sha256",packetSha);row.put("all_post_checks_passed",true);
                row.put("row_including_observer_wall_ns",System.nanoTime()-outerStart);result=null;semantic=null;
            }
            assertEquals(96,rows.size());for(int n:seen)assertEquals(32,n);
        }catch(Throwable caught){primary=caught;report.put("failure_class",caught.getClass().getName());report.put("failure_message",String.valueOf(caught.getMessage()));throw caught;}
        finally {
            try {
            report.put("completed",primary==null&&rows.size()==96&&rows.stream().allMatch(r->Boolean.TRUE.equals(r.get("all_post_checks_passed"))));
            report.put("window_ns_before_summary_and_report",System.nanoTime()-windowStart);
            var totals=new LinkedHashMap<String,Object>();var paired=new ArrayList<Map<String,Object>>();
            for(String variant:VARIANTS){var metrics=new LinkedHashMap<String,Object>();for(String key:List.of("wall_ns","CPU_ns","thread_allocated_bytes"))metrics.put(key,metricStats(rows,variant,key));totals.put(variant,metrics);}
            for(int cycle=0;cycle<16;cycle++){var entry=new LinkedHashMap<String,Object>();entry.put("cycle",cycle);for(String key:List.of("wall_ns","CPU_ns","thread_allocated_bytes"))entry.put(key,cycleMetric(rows,cycle,key));paired.add(entry);}
            report.put("all32_per_variant_totals_and_distributions",totals);report.put("all16_cycle_two_calls_per_variant_paired_sums_and_differences",paired);
            report.put("statistics_contract","All samples, no dropped cold calls or later sample-count changes. Medians are exact decimal strings; unknown CPU/allocation make total/median/min/max null, known count/sum remain. Windows CPU may remain coarse: per-call0 does not mean zerocost. Cumulative allocation is not peak/live. No speed acceptance encoded.");
            report.put("clock_scope","Primary brackets cover Method.invoke publicprojectFull only, not ownSnapshot getters/postchecks. Per-row observer wall includes those costs. Method window excludes test-classinit/JUnit/framework/reportencoding/write/VMexit; full managed actor/OS windows separate and actor includes parent qualification.");
            report.put("scope","Fixed single-process selected-family threeversions/publicv3 DATA caller. Not wholeverify/IO/worker/Game/Runtime or 10secSavedDay. No JFR/extra targetwarmup/protocolplatform. Originalcause stops first failure, partialglobalfalse retained.");
                byte[] encoded=org.xar.ck3.control.contracts.FullJsonTree.encode(new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(report),1_048_576);
                Path out=directory.resolve("p146-three-version-project-full.json");java.nio.file.Files.write(out,encoded,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE);System.out.println("P146 fixed three-version project experiment "+out);
            }catch(Throwable outputFailure){if(primary==null)throw outputFailure;if(primary!=outputFailure)primary.addSuppressed(outputFailure);}
        }
    }

    private static final String WIRE = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}""";
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"},"original_metric":1.00}""";
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(byte[] raw){return new ExactRef("memory/test-original.json",raw.length,DriverJson.sha256(raw));}
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));}
    private static Known known(){return DriverFactsRepository.imported(ref(bytes(WIRE)),bytes(WIRE),3,7,game(),new OpportunityJson.Obj(Map.of()));}
    private static G2Source source(){return new G2Source("test-machine","2026-10-23T16:00:00Z","test-source",ref(bytes("original-source")));}
    private static NativeObservationPort.ObservedFrame actual(String state){
        byte[] json=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",game(),BigInteger.valueOf(5),"held-session"),"snapshot-9",BigInteger.valueOf(9),new RawJson(bytes(state.strip())),packet,Instant.parse("2026-10-23T16:00:00Z"));
    }
}
