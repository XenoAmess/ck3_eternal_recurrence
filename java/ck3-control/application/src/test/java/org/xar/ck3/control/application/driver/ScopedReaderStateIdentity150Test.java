package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
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
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Finite public scoped-reader DATA tests; no private carrier mint, Session, writer or live operation. */
public final class ScopedReaderStateIdentity150Test {
    private static final String READER="org.xar.ck3.control.application.driver.DriverObservationEvidenceReader";
    private static final String ASM="org.xar.ck3.control.application.driver.DriverObservationAssembler";
    private static final String DRIVER="org.xar.ck3.control.application.driver.DriverJson";
    @org.junit.jupiter.api.io.TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) Path directory;
    private static Path property(String name)throws Exception {return Path.of(java.util.Objects.requireNonNull(System.getProperty(name),"explicit qualified root required: "+name)).toRealPath();}
    private static final class OldLoader extends java.net.URLClassLoader {
        private static final java.util.Set<String> FAMILY=java.util.Set.of(READER,READER+"$NativeBodyStage",READER+"$NativePacketInput",READER+"$NativeFrameInput",
                ASM,ASM+"$CanonicalNativeState",ASM+"$Complete",ASM+"$FullSnapshot",ASM+"$Incomplete",ASM+"$Result",DRIVER,DRIVER+"$ContentComparison",DRIVER+"$EncodedByteCount");
        private OldLoader()throws Exception {super(new java.net.URL[]{property("ck3.p150.oldProductionRoot").toUri().toURL(),property("ck3.p150.oldDriverRoot").toUri().toURL()},ScopedReaderStateIdentity150Test.class.getClassLoader());}
        @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException {
            synchronized(getClassLoadingLock(name)) {
                if(!FAMILY.contains(name)) {if(name.startsWith(READER+"$")||name.startsWith(ASM+"$")||name.startsWith(DRIVER+"$"))throw new ClassNotFoundException("unlisted old13 family "+name);return getParent().loadClass(name);}
                Class<?> type=findLoadedClass(name);if(type==null)type=findClass(name);if(resolve)resolveClass(type);return type;
            }
        }
    }
    private static void source(Class<?> type,Path root)throws Exception {assertEquals(root,Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath());}
    private static final class Calls implements AutoCloseable {
        private final OldLoader old=new OldLoader();
        private final Method[] methods=new Method[2];private final Object[] assemblers=new Object[2];
        private final Map<String,Object> initialization;
        private final DriverFrameEvidenceLoader nominal=new DriverFrameEvidenceLoader(new DriverObservationAssembler(),true);
        private Calls()throws Exception {
            long start=System.nanoTime();var oldDriver=Class.forName(DRIVER,true,old);var oldReader=Class.forName(READER,true,old);var oldAsm=Class.forName(ASM,true,old);long oldEnd=System.nanoTime();
            var driver=Class.forName(DRIVER,true,ScopedReaderStateIdentity150Test.class.getClassLoader());var reader=Class.forName(READER,true,ScopedReaderStateIdentity150Test.class.getClassLoader());var assembler=Class.forName(ASM,true,ScopedReaderStateIdentity150Test.class.getClassLoader());long currentEnd=System.nanoTime();
            source(oldReader,property("ck3.p150.oldProductionRoot"));source(oldAsm,property("ck3.p150.oldProductionRoot"));source(oldDriver,property("ck3.p150.oldDriverRoot"));
            source(reader,property("ck3.p150.currentReaderRoot"));source(assembler,property("ck3.p150.currentAssemblerRoot"));source(driver,property("ck3.p150.currentDriverRoot"));
            assertSame(old,oldReader.getClassLoader());assertSame(old,oldAsm.getClassLoader());assertSame(old,oldDriver.getClassLoader());
            Class<?>[] readers={oldReader,reader},asms={oldAsm,assembler};
            for(int side=0;side<2;side++) {methods[side]=readers[side].getMethod("assembleOriginalsWithScopedDriverDecode",ExactRef.class,RawJson.class,RawJson.class,byte[].class,ExactRef.class,asms[side],DriverFrameEvidenceLoader.class);assemblers[side]=asms[side].getConstructor().newInstance();}
            initialization=Map.of("old13_init_ns",oldEnd-start,"parent_init_ns",currentEnd-oldEnd,"source_reflection_setup_ns",System.nanoTime()-currentEnd,
                    "old_production_root",property("ck3.p150.oldProductionRoot").toString(),"old_driver_root",property("ck3.p150.oldDriverRoot").toString(),"current_reader_root",property("ck3.p150.currentReaderRoot").toString(),"current_assembler_root",property("ck3.p150.currentAssemblerRoot").toString(),"target_warmups",0);
        }
        private Object call(int side,Fixture f,DriverFrameEvidenceLoader decoder)throws Throwable {return call(side,f,f.driver(),decoder);}
        private Object call(int side,Fixture f,RawJson fullDriver,DriverFrameEvidenceLoader decoder)throws Throwable {
            try{return methods[side].invoke(null,f.manifestRef(),f.manifest(),fullDriver,f.packet(),f.nativeRef(),assemblers[side],decoder);}
            catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
        }
        private OpportunityJson.Obj publicState(int side,NativeObservationPort.ObservedFrame frame)throws Throwable {
            ClassLoader loader=side==0?old:ScopedReaderStateIdentity150Test.class.getClassLoader();
            try{return (OpportunityJson.Obj)Class.forName(ASM,true,loader).getMethod("originalNativeState",NativeObservationPort.ObservedFrame.class).invoke(null,frame);}
            catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
        }
        @Override public void close()throws java.io.IOException {old.close();}
    }
    private record Fixture(NativeObservationPort.ObservedFrame actual,Known known,RawJson manifest,ExactRef manifestRef,RawJson driver,ExactRef driverRef,byte[] packet,ExactRef nativeRef) { }
    private static Fixture fixture(String state,long version,OpportunityJson.Obj extra) {
        byte[] driverBytes=bytes(WIRE);var fields=extra;
        if(version==4) {
            driverBytes=DriverJson.encode(DriverJson.object(driverBytes,DriverJson.MAX_NATIVE_BYTES).with("succession_lifecycle",OpportunityJson.Nil.INSTANCE));
            var entries=new LinkedHashMap<>(extra.members());entries.put("episode_projection",new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE));fields=new OpportunityJson.Obj(entries);
        }
        var k=DriverFactsRepository.imported(ref(driverBytes),driverBytes,3,7,game(),fields);var actual=actual(state);var driver=RawJson.fullMaterial(k.driver().encode());var driverRef=ref(driver.bytes());
        var manifest=DriverObservationEvidenceReader.encode(k,actual,BigInteger.valueOf(2),version,source(),fields,driverRef);var packet=actual.originalPacket();
        return new Fixture(actual,k,manifest,ref(manifest.bytes()),driver,driverRef,packet,ref(packet));
    }
    private static Map<String,Object> observe(Object result) throws Exception {
        Class<?> type=result.getClass();var out=new LinkedHashMap<String,Object>();
        if(type.getName().equals(ASM+"$Incomplete")){out.put("kind","Incomplete");out.put("reasons",type.getMethod("reasons").invoke(result));return out;}
        assertEquals(ASM+"$Complete",type.getName());out.put("kind","Complete");
        for(String field:List.of("identity","source","sessionId","connectionGeneration","originalEvidence","observedAt","fullBindingSha256"))out.put(field,type.getMethod(field).invoke(result).toString());
        var semantic=assertInstanceOf(OpportunityJson.Obj.class,type.getMethod("semantic").invoke(result));out.put("semantic_sha256",DriverJson.sha256(DriverJson.encode(semantic)));out.put("member_order",new ArrayList<>(semantic.members().keySet()));
        out.put("original_metric",assertInstanceOf(OpportunityJson.DecimalValue.class,semantic.get("original_metric")).token());
        out.put("originalProjection_present",assertInstanceOf(java.util.Optional.class,type.getMethod("originalProjection").invoke(result)).isPresent());
        return out;
    }
    private static String inputSha(Fixture f) {return DriverJson.sha256(f.manifest().bytes())+":"+DriverJson.sha256(f.driver().bytes())+":"+DriverJson.sha256(f.packet());}
    private static Map<String,Object> same(Calls calls,Fixture f,DriverFrameEvidenceLoader decoder)throws Throwable {
        String before=inputSha(f);var a=observe(calls.call(0,f,decoder));var b=observe(calls.call(1,f,decoder));assertEquals(a,b);assertEquals(before,inputSha(f));return a;
    }
    private static final class ArchiveProbe implements InvocationHandler {
        private final Fixture fixture;private final byte[] borrowed;private final boolean mutate;private final List<String> events=new ArrayList<>();
        private ArchiveProbe(Fixture fixture,boolean mutate){this.fixture=fixture;this.borrowed=fixture.packet().clone();this.mutate=mutate;}
        private OutcomeArchive archive(){return (OutcomeArchive)Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(),new Class<?>[]{OutcomeArchive.class},this);}
        @Override public Object invoke(Object proxy,Method method,Object[] args) {
            if(method.getDeclaringClass()==Object.class)return switch(method.getName()){case "toString"->"readonly packet150 archive";case "hashCode"->System.identityHashCode(proxy);case "equals"->proxy==args[0];default->throw new AssertionError(method.getName());};
            if(method.getName().equals("loadFullMaterial")) {
                if(fixture.manifestRef().equals(args[0])){events.add("manifest");return fixture.manifest();}
                assertEquals(fixture.driverRef(),args[0]);assertEquals(List.of("manifest","native"),events);events.add("driver");if(mutate)borrowed[0]^=1;return fixture.driver();
            }
            if(method.getName().equals("loadNativeFrame")){assertEquals(fixture.nativeRef(),args[0]);events.add("native");return borrowed;}
            throw new AssertionError("readonly DATA archive has no write/Store/Game permission: "+method.getName());
        }
    }
    @Test public void scopedReaderPreservesStateIdentityAndPublicOriginals150()throws Throwable {
        try(var calls=new Calls()) {
            for(String metric:List.of("1.00","-0.0","1e+0")) {
                var f=fixture(STATE.replace("1.00",metric),3,new OpportunityJson.Obj(Map.of()));
                assertEquals("Complete",same(calls,f,null).get("kind"));assertEquals(metric,same(calls,f,calls.nominal).get("original_metric"));
            }
            // These are real public scoped inputs; no carrier constructor or private method is invoked.
            String compactState=new String(DriverJson.encode(DriverJson.object(bytes(STATE),DriverJson.MAX_NATIVE_BYTES)),StandardCharsets.UTF_8);
            String unicodeLexical=compactState.substring(0,compactState.length()-1)+",\"opaque_note\":\"quote\\\" slash\\\\ emoji😀 \\u0020\""+"}";
            String unicodeCompact=new String(DriverJson.encode(DriverJson.object(bytes(unicodeLexical),DriverJson.MAX_NATIVE_BYTES)),StandardCharsets.UTF_8);
            String integerZero=compactState.substring(0,compactState.length()-1)+",\"opaque_integer\":-0}";
            assertFalse(java.util.Arrays.equals(bytes(unicodeLexical),bytes(unicodeCompact)));
            assertEquals(DriverJson.object(bytes(unicodeLexical),DriverJson.MAX_NATIVE_BYTES),DriverJson.object(bytes(unicodeCompact),DriverJson.MAX_NATIVE_BYTES));
            assertFalse(java.util.Arrays.equals(bytes(integerZero),DriverJson.encode(DriverJson.object(bytes(integerZero),DriverJson.MAX_NATIVE_BYTES))));
            for(String stateWire:List.of(compactState,STATE,unicodeCompact,unicodeLexical,integerZero)) {
                var input=fixture(stateWire,3,new OpportunityJson.Obj(Map.of()));
                for(DriverFrameEvidenceLoader decoder:new DriverFrameEvidenceLoader[]{null,calls.nominal})assertEquals("Complete",same(calls,input,decoder).get("kind"));
                var oldState=calls.publicState(0,input.actual());var currentState=calls.publicState(1,input.actual());
                assertEquals(oldState,currentState);assertEquals(DriverJson.object(bytes(stateWire),DriverJson.MAX_NATIVE_BYTES),currentState);
            }
            // The public tail must still reject at its original envelope/state/object stages.
            var seed=actual(STATE);var arrayState=new RawJson(bytes("[]"));
            var parseError=assertThrows(IllegalArgumentException.class,()->DriverJson.object(arrayState.bytes(),DriverJson.MAX_NATIVE_BYTES));
            for(int protocol:List.of(2,1)) {
                byte[] body=bytes("{\"protocol_version\":"+protocol+",\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":null}");
                byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
                var invalid=new NativeObservationPort.ObservedFrame(seed.session(),seed.snapshotId(),seed.nativeRevision(),arrayState,packet,seed.observedAt());
                var oldError=assertThrows(IllegalArgumentException.class,()->calls.publicState(0,invalid));var newError=assertThrows(IllegalArgumentException.class,()->calls.publicState(1,invalid));
                assertEquals(oldError.getClass(),newError.getClass());assertEquals(oldError.getMessage(),newError.getMessage());
                assertEquals(protocol==2?"original native envelope differs":parseError.getMessage(),oldError.getMessage());
                if(protocol==1) {
                    var invalidPacketState=new NativeObservationPort.ObservedFrame(seed.session(),seed.snapshotId(),seed.nativeRevision(),new RawJson(bytes("{}")),packet,seed.observedAt());
                    var a=assertThrows(IllegalArgumentException.class,()->calls.publicState(0,invalidPacketState));var c=assertThrows(IllegalArgumentException.class,()->calls.publicState(1,invalidPacketState));
                    var expected=assertThrows(IllegalArgumentException.class,()->OpportunityJson.object(OpportunityJson.Nil.INSTANCE,"state"));
                    assertEquals(expected.getMessage(),a.getMessage());assertEquals(a.getClass(),c.getClass());assertEquals(a.getMessage(),c.getMessage());
                }
            }
            var conflict=fixture(STATE,3,new OpportunityJson.Obj(Map.of("paused",new OpportunityJson.Bool(false))));
            for(DriverFrameEvidenceLoader decoder:new DriverFrameEvidenceLoader[]{null,calls.nominal}) {
                var a=assertThrows(IllegalArgumentException.class,()->calls.call(0,conflict,decoder));var b=assertThrows(IllegalArgumentException.class,()->calls.call(1,conflict,decoder));
                assertEquals(a.getClass(),b.getClass());assertEquals(a.getMessage(),b.getMessage());assertEquals("semantic producer overwrote actual native field: paused",a.getMessage());
            }
            var late=fixture(STATE.replace("\"character_id\":73","\"character_id\":74"),3,new OpportunityJson.Obj(Map.of()));
            var gap=same(calls,late,calls.nominal);assertEquals("Incomplete",gap.get("kind"));assertEquals(List.of("native_driver_fact_join: unreconciled played-character/episode transition"),gap.get("reasons"));
            var good=fixture(STATE,3,new OpportunityJson.Obj(Map.of()));String before=inputSha(good);
            var badDriver=new RawJson(bytes("{}"));
            var badA=assertThrows(RuntimeException.class,()->calls.call(0,good,badDriver,calls.nominal));var badB=assertThrows(RuntimeException.class,()->calls.call(1,good,badDriver,calls.nominal));
            assertEquals(badA.getClass(),badB.getClass());assertEquals(badA.getMessage(),badB.getMessage());
            assertEquals(before,inputSha(good));assertEquals("Complete",same(calls,good,calls.nominal).get("kind"));
            // Actual public Loader's three DATA reads; mutation after native read proves the original pre-driver private copy order.
            for(boolean scoped:List.of(false,true)) {
                var archive=new ArchiveProbe(good,true);var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler(),scoped);
                var loaded=loader.load(new NativeEffectEvidence.FrameBasis(good.nativeRef(),good.manifestRef()),archive.archive());
                assertEquals(List.of("manifest","native","driver"),archive.events);assertEquals(observe(calls.call(1,good,scoped?calls.nominal:null)),observe(loaded));assertEquals(before,inputSha(good));
            }
            // Real public profile4 producer data and parent-only Complete constructor's unchanged independent self-replay.
            String campaign=STATE.replace("\"original\":\"retained\"","\"original\":\"retained\",\"bridge_pid\":42,\"connection_generation\":5");
            var p4=fixture(campaign,4,new OpportunityJson.Obj(Map.of()));var result=calls.call(1,p4,calls.nominal);
            assertEquals("Complete",observe(result).get("kind"));assertEquals(true,observe(result).get("originalProjection_present"));
            var archive=new ArchiveProbe(p4,false);var full=new DriverFrameEvidenceLoader(new DriverObservationAssembler(),true).load(new NativeEffectEvidence.FrameBasis(p4.nativeRef(),p4.manifestRef()),archive.archive());
            assertEquals(observe(result),observe(full));assertTrue(full.originalProjection().isPresent());assertEquals(List.of("manifest","native","driver"),archive.events);
        }
    }
    private static Map<String,Object> stats(List<Map<String,Object>> rows,String dataset,String side,String key) {
        var values=new ArrayList<Long>();long total=0;
        for(var row:rows)if(dataset.equals(row.get("dataset"))&&side.equals(row.get("entry"))) {if(!(row.get(key) instanceof Number number)||number.longValue()<0)return Map.of("known",false);long n=number.longValue();values.add(n);total+=n;}
        var out=new LinkedHashMap<String,Object>();out.put("count",values.size());out.put("total",total);
        if(!values.isEmpty()){values.sort(Long::compare);out.put("min",values.get(0));out.put("max",values.get(values.size()-1));out.put("median",java.math.BigDecimal.valueOf(values.get((values.size()-1)/2)).add(java.math.BigDecimal.valueOf(values.get(values.size()/2))).divide(java.math.BigDecimal.valueOf(2)).toPlainString());}return out;
    }
    @Test public void fixedCompactThenPrettyScopedReaderStateIdentity150()throws Throwable {
        long window=System.nanoTime();var report=new LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();report.put("rows",rows);Throwable failure=null;
        report.put("schema","ck3.p150.fixed64-scoped-reader-state-identity-component/v1");report.put("dataset_order",List.of("compact","pretty"));report.put("cycles_each",8);report.put("order",List.of("A","B","B","A"));report.put("calls_each_input",32);report.put("total_calls",64);report.put("extra_target_warmups",0);
        report.put("scope","Actual public scoped Reader with strict parent nominal decoder only decodeCompleteDriverBytes, not parentLoader.load/replay substituting oldReader. OldA13 P147shared10+P143Driver3 in two roots samechild; BnewReader4+Asm6 P150root+sameDriver3 parent with separate source assertions. Common DTO/Jackson/normalizers and parentB fixture/postwriter bias; no identicalJIT/randomization/naturalhitrate claim. Only exact wholeframe match plus same captured immutable RawJson state and Obj admit direct same-call parsed state reuse. Public state path unchanged; no new private encoder/comparator/compact branch. Existing packet clones/token validation/tree lifetime and new reference costs retained; inputs independent.");
        try(var calls=new Calls()) {
            report.put("initialization",calls.initialization);String pretty=STATE.replace("\"original_metric\":1.00","\"original_metric\":1.00,\"opaque_unconsumed_extension\":\""+"x".repeat(3_400_000)+"\"");
            String compact=new String(DriverJson.encode(DriverJson.object(bytes(pretty),DriverJson.MAX_NATIVE_BYTES)),StandardCharsets.UTF_8);
            var compactInput=fixture(compact,3,new OpportunityJson.Obj(Map.of()));var prettyInput=fixture(pretty,3,new OpportunityJson.Obj(Map.of()));
            var cpu=java.lang.management.ManagementFactory.getThreadMXBean();boolean cpuAvailable=cpu.isCurrentThreadCpuTimeSupported();if(cpuAvailable&&!cpu.isThreadCpuTimeEnabled())cpu.setThreadCpuTimeEnabled(true);
            com.sun.management.ThreadMXBean allocation=cpu instanceof com.sun.management.ThreadMXBean bean?bean:null;boolean allocAvailable=allocation!=null&&allocation.isThreadAllocatedMemorySupported();if(allocAvailable&&!allocation.isThreadAllocatedMemoryEnabled())allocation.setThreadAllocatedMemoryEnabled(true);
            report.put("CPU_available",cpuAvailable);report.put("allocation_available",allocAvailable);report.put("setup_ns_before_calls",System.nanoTime()-window);
            for(String dataset:List.of("compact","pretty")) {
                var f=dataset.equals("compact")?compactInput:prettyInput;String input=inputSha(f);Map<String,Object> expected=null;
                for(int cycle=0;cycle<8;cycle++)for(int position=0;position<4;position++) {
                    String side=position==0||position==3?"A":"B";var row=new LinkedHashMap<String,Object>();rows.add(row);row.put("index",rows.size()-1);row.put("dataset",dataset);row.put("cycle",cycle);row.put("position",position);row.put("entry",side);row.put("all_post_checks_passed",false);
                    long outer=System.nanoTime(),cs=cpuAvailable?cpu.getCurrentThreadCpuTime():-1,as=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1;
                    long start=System.nanoTime();Object result;boolean completed=false;
                    try{result=calls.call(side.equals("A")?0:1,f,calls.nominal);completed=true;}
                    finally{long end=System.nanoTime(),ae=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1,ce=cpuAvailable?cpu.getCurrentThreadCpuTime():-1;
                        row.put("wall_start_ns",start);row.put("wall_end_ns",end);row.put("wall_ns",end-start);row.put("CPU_start_ns",cs);row.put("CPU_end_ns",ce);row.put("CPU_ns",cs>=0&&ce>=cs?ce-cs:-1);row.put("allocation_start_bytes",as);row.put("allocation_end_bytes",ae);row.put("thread_allocated_bytes",as>=0&&ae>=as?ae-as:-1);row.put("target_completed",completed);}
                    var output=observe(result);assertEquals("Complete",output.get("kind"));assertEquals("1.00",output.get("original_metric"));if(expected==null)expected=output;assertEquals(expected,output);assertEquals(input,inputSha(f));
                    row.put("output",output);row.put("input_SHA_manifest_driver_packet",input);row.put("all_post_checks_passed",true);row.put("row_including_observer_wall_ns",System.nanoTime()-outer);result=null;
                }
            }
            assertEquals(64,rows.size());
        }catch(Throwable caught){failure=caught;report.put("failure_class",caught.getClass().getName());report.put("failure_message",String.valueOf(caught.getMessage()));throw caught;}
        finally {
            try {
                report.put("completed",failure==null&&rows.size()==64&&rows.stream().allMatch(r->Boolean.TRUE.equals(r.get("all_post_checks_passed"))));report.put("window_ns_before_summary_report",System.nanoTime()-window);
                var datasets=new LinkedHashMap<String,Object>();
                for(String dataset:List.of("compact","pretty")){var perSide=new LinkedHashMap<String,Object>();for(String side:List.of("A","B")){var metrics=new LinkedHashMap<String,Object>();for(String key:List.of("wall_ns","CPU_ns","thread_allocated_bytes"))metrics.put(key,stats(rows,dataset,side,key));perSide.put(side,metrics);}datasets.put(dataset,perSide);}
                report.put("independent_dataset_distributions",datasets);var pairs=new ArrayList<Map<String,Object>>();
                for(String dataset:List.of("compact","pretty"))for(int cycle=0;cycle<8;cycle++){var pair=new LinkedHashMap<String,Object>();pair.put("dataset",dataset);pair.put("cycle",cycle);
                    for(String key:List.of("wall_ns","CPU_ns","thread_allocated_bytes")){long a=0,b=0;int n=0;boolean known=true;for(var row:rows)if(dataset.equals(row.get("dataset"))&&((Number)row.get("cycle")).intValue()==cycle){n++;if(!(row.get(key) instanceof Number value)||value.longValue()<0)known=false;else if(row.get("entry").equals("A"))a+=value.longValue();else b+=value.longValue();}var value=new LinkedHashMap<String,Object>();value.put("A_two_call_sum",n==4&&known?a:null);value.put("B_two_call_sum",n==4&&known?b:null);value.put("B_minus_A",n==4&&known?b-a:null);pair.put(key,value);}pairs.add(pair);}
                report.put("all8_cycle_pairs_per_input",pairs);report.put("limits","Allcold/init/observer/report/actor cost retained. No full64large result objects retained: output fingerprints only. Cumulativeallocation notpeak; CPUquantization/unknown counters notzerocost. Datasetorder fixed, pretty inherits preceding32calls. No extra samples/warmups/retry/hitrate mix/wholeverify/physicalIO/worker/Game/Runtime/P100/SAVE claim. Readerfinallyclear sourceproof; no privatecarrier mint/inspection hooks.");
                byte[] encoded=org.xar.ck3.control.contracts.FullJsonTree.encode(new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(report),1_048_576);Path out=directory.resolve("p150-scoped-reader-state-identity-fixed64.json");java.nio.file.Files.write(out,encoded,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE);System.out.println("P150 scoped reader state-identity fixed64 "+out);
            }catch(Throwable outputFailure){if(failure==null)throw outputFailure;if(failure!=outputFailure)failure.addSuppressed(outputFailure);}
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
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(byte[] raw){return new ExactRef("memory/test-original.json",raw.length,DriverJson.sha256(raw));}
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));}
    private static G2Source source(){return new G2Source("test-machine","2026-10-23T16:00:00Z","test-source",ref(bytes("original-source")));}
    private static NativeObservationPort.ObservedFrame actual(String state){byte[] body=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":"+state+"}");byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",game(),BigInteger.valueOf(5),"held-session"),"snapshot-9",BigInteger.valueOf(9),new RawJson(bytes(state.strip())),packet,Instant.parse("2026-10-23T16:00:00Z"));}
}
