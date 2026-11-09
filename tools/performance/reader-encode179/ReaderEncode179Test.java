package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Full public encode(...).bytes() on existing public DATA; no receive,adopter,private issuer or live operation. */
public final class ReaderEncode179Test {
    private static final String READER="org.xar.ck3.control.application.driver.DriverObservationEvidenceReader";
    private static final String PACKET_SHA="57bf15b3d8ab9de15f5559037b789494d7f5fd7bd71ef521140276633686f19d";
    private static final List<String> FIELDS=List.of("schema","driver_ref","driver_version","episode_epoch","transport","snapshot_id","native_revision","native_state_sha256","native_packet_sha256","native_packet_bytes","observed_at","public_revision","observation_version","source","original_semantic_fields");
    private static final Map<String,String> OLD_READER=Map.ofEntries(
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader","037c6e2a8b0983682a31c1c099a3901af2d4e6be66a7aa97c56c3d6978e3b3ca"),
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader$NativeBodyStage","d5789bd5de6592eaa7592c552408e224a7d3eeaa53f248c49d38a62387a0341c"),
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader$NativeFrameInput","4fc9497017f5f1ebd7103e233ba784e91f6c56add6d9cf0e4b84563e2a324de5"),
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader$NativePacketInput","544dd23457178f8065215864f10f4954d63238d4d94c3e48ac1e26067c08f383"));
    private static final Map<String,String> NEW_READER=Map.ofEntries(
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader","a3866b0e9fa863a770b1ea02f09a7d847ae44277925f62f7ad356db917575a30"),
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader$NativeBodyStage","d5789bd5de6592eaa7592c552408e224a7d3eeaa53f248c49d38a62387a0341c"),
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader$NativeFrameInput","4fc9497017f5f1ebd7103e233ba784e91f6c56add6d9cf0e4b84563e2a324de5"),
        Map.entry("org.xar.ck3.control.application.driver.DriverObservationEvidenceReader$NativePacketInput","544dd23457178f8065215864f10f4954d63238d4d94c3e48ac1e26067c08f383"));
    @TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) Path temporary;
    @Test void completePublicEncodeBytesFirst32AndTwoFailures()throws Throwable {
        long whole=System.nanoTime();Path root=property("ck3.p179.reportRoot");assertTrue(Files.isDirectory(root));Path output=root.resolve("p179-public-encode-bytes-fixed32.json");assertFalse(Files.exists(output));var report=new LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();var functional=new ArrayList<Map<String,Object>>();Throwable primary=null;
        report.put("schema","ck3.p179.public-encode-bytes-first32/v1");report.put("completed",false);report.put("rows",rows);report.put("functional",functional);report.put("fixed_plan","One existingP167compactDATA input,first8ABBA32/16each,0setup targetencode/0extra warmup. Full publicencode(...).bytes() timedincludingRawJsoncast/getter. After32only2publicDATAfailurepairs/4attempts. Allcold/laterwarm/outliers retained,noresample/newN.");
        report.put("adoption_rule","Alloutput/input/functional/originsPASS;allocationall8groupsdecrease;targetwallmeanANDmedian<=A;pairedpercallB-Adeltamedian<=0ANDatleast4groupsbetter. ElseDEFAULT_PARK withoutwarmup/resampling. Outer/CPU/heap/GC/allcostreverse preserved;no worker/Runtime/SAVE claim.");
        report.put("oracle_correction","HistoricalP167manifest985/42e8129bb5cb8c6eda2c5b57fe0c43e8d1e00241d045010406d84e06a2d0ce91 andDriver708/b24b3188acd600f0c77a6151c823287e29173810be082a4d67c7487d63235ebc arehistoricalDATA only,notcrossJVMabsoluteorder/SHA. Map.of innerorder unspecified. FirstactualA fullbytes becomes sameJVMbaseline;all32byteidentical plusfullschema/fields/order/reference/actualvalueoracles. No salt/provider/encoder edits/private reflection.");
        try {
            long setup=System.nanoTime();Fixture f=fixture();report.put("input",Map.of("packet_bytes",f.packet().length,"packet_sha256",sha(f.packet()),"state_bytes",f.state().length,"state_sha256",sha(f.state()),"current_driver_bytes",f.driver().length,"current_driver_sha256",sha(f.driver()),"driver_ref",f.driverRef().toString(),"fixture","P167Test02 exactWIRE/STATE andoriginal3400000x compactconstruction only;publicimported=>Known;no actualreceive/adoption"));report.put("setup_target_encode_calls",0);
            var mx=assertInstanceOf(com.sun.management.ThreadMXBean.class,ManagementFactory.getThreadMXBean());assertTrue(mx.isThreadAllocatedMemorySupported());if(!mx.isThreadAllocatedMemoryEnabled())mx.setThreadAllocatedMemoryEnabled(true);assertTrue(mx.isCurrentThreadCpuTimeSupported());if(!mx.isThreadCpuTimeEnabled())mx.setThreadCpuTimeEnabled(true);long tid=Thread.currentThread().threadId();
            try(Side a=new Side("A",property("ck3.p179.oldReaderRoot"),OLD_READER);Side b=new Side("B",property("ck3.p179.currentReaderRoot"),NEW_READER)) {
                report.put("A",a.metadata);report.put("B",b.metadata);report.put("setup_ns_before_first_target",System.nanoTime()-setup);report.put("heap_before32",heap());byte[] baseline=null;
                for(int cycle=0;cycle<8;cycle++)for(int slot=0;slot<4;slot++) {
                    Side side=slot==0||slot==3?a:b;var row=new LinkedHashMap<String,Object>();row.put("index",rows.size());row.put("cycle",cycle);row.put("slot",slot);row.put("side",side.label);row.put("target_completed",false);row.put("post_passed",false);rows.add(row);long enclosing=System.nanoTime();byte[] encoded;
                    long a0=mx.getThreadAllocatedBytes(tid),c0=mx.getCurrentThreadCpuTime(),w0=System.nanoTime();
                    try{encoded=side.encodeBytes(f,f.driverRef(),f.actual());}catch(Throwable failure){row.put("failure",error(failure));throw failure;}
                    finally{long w1=System.nanoTime(),c1=mx.getCurrentThreadCpuTime(),a1=mx.getThreadAllocatedBytes(tid);row.put("wall_start_ns",w0);row.put("wall_end_ns",w1);row.put("cpu_start_ns",c0);row.put("cpu_end_ns",c1);row.put("allocated_start_bytes",a0);row.put("allocated_end_bytes",a1);row.put("wall_ns",w1-w0);row.put("cpu_ns",c1-c0);row.put("allocated_bytes",a1-a0);}
                    row.put("target_completed",true);post(encoded,f,row);if(baseline==null){assertEquals("A",side.label);baseline=encoded.clone();report.put("same_JVM_baseline",Map.of("first_index",0,"source","firstactualA targetafterfullindependentpost,noextraencode","bytes",baseline.length,"sha256",sha(baseline)));}assertArrayEquals(baseline,encoded);row.put("same_JVM_bytes_passed",true);row.put("post_passed",true);row.put("heap_after_post",heap());row.put("enclosing_ns",System.nanoTime()-enclosing);
                }
                assertEquals(32,rows.size());assertEquals(16,a.calls);assertEquals(16,b.calls);report.put("heap_after32",heap());long fn=System.nanoTime();failures(a,b,f,functional);report.put("functional_ns",System.nanoTime()-fn);assertEquals(2,functional.size());assertEquals(18,a.calls);assertEquals(18,b.calls);unchanged(f);report.put("counts",Map.of("measured_encode_bytes",32,"post_negative_encode_bytes",4,"total_encode_bytes_attempts",36,"setup_target_encode",0,"extra_warmup",0));report.put("original_inputs_unchanged",true);
            }
            report.put("completed",true);
        }catch(Throwable failure){primary=failure;report.put("failure",error(failure));throw failure;}
        finally{report.put("before_report_ns",System.nanoTime()-whole);report.put("limitations","Targetfullpublicencode.bytes includingreflection/firstclassinitialization/RawJsoncast+defensivebytes;model/refhash/driverencode factorysetupandpostfulltyped/hash/arraychecks outside targetyetinenclosing/whole. No targetwarmup. SharedparentJIT/A-first andallcold/warm preserved;historicalP167PARKnotperformancecredit. NestedMaporderonlysameJVMbyteoracle;no fixedsalt. Newlocalarraymayremaininterpreterlive throughrestofencode;heap/GCpostsharednotpeak/OOME/causalCPU. CPUquantumzeros ratioUNKNOWN. before_reportexcludesmaterialize/write/JUnittail;managedactor/waitcostseparate. NoSession/Prepared/readerprivatehelperreflection/Nativeprotocol/Game/P100/HTTP/JFR/Runtime/SAVE.");try{byte[] raw=new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(report);assertTrue(raw.length<=262_144,"bounded external report");Files.write(output,raw,StandardOpenOption.CREATE_NEW);}catch(Throwable write){if(primary!=null)primary.addSuppressed(write);else throw write;}}
    }
    private record Fixture(Known known,NativeObservationPort.ObservedFrame actual,G2Source source,OpportunityJson.Obj semantic,ExactRef driverRef,byte[] driver,byte[] packet,byte[] state) { }
    private static Fixture fixture() {
        String pretty=STATE.replace("\"original_metric\":1.00","\"original_metric\":1.00,\"opaque_unconsumed_extension\":\""+"x".repeat(3_400_000)+"\"");
        String compact=new String(DriverJson.encode(DriverJson.object(bytes(pretty),DriverJson.MAX_NATIVE_BYTES)),StandardCharsets.UTF_8);var empty=new OpportunityJson.Obj(Map.of());byte[] originalDriver=bytes(WIRE);var known=DriverFactsRepository.imported(ref(originalDriver),originalDriver,3,7,game(),empty);var actual=actual(compact);byte[] driver=known.driver().encode();var currentDriver=ref(driver);byte[] packet=actual.originalPacket(),state=actual.state().bytes();assertEquals(3_400_432,packet.length);assertEquals(PACKET_SHA,sha(packet));return new Fixture(known,actual,source(),empty,currentDriver,driver,packet,state);
    }
    private static void post(byte[] bytes,Fixture f,Map<String,Object> row) {
        OpportunityJson.Obj output=DriverJson.object(bytes,DriverJson.MAX_NATIVE_BYTES);assertEquals(FIELDS,new ArrayList<>(output.members().keySet()));assertEquals("xar.java-driver-observation-evidence/v1",text(output.get("schema")));assertEquals(f.driverRef(),DriverObservationEvidenceReader.reference(output.get("driver_ref")));assertEquals(BigInteger.valueOf(f.known().stamp().driverVersion()),integer(output.get("driver_version")));assertEquals(BigInteger.valueOf(f.known().stamp().episodeEpoch()),integer(output.get("episode_epoch")));
        var actual=f.actual();OpportunityJson.Obj transport=obj(output.get("transport"));assertEquals(Set.of("machine_id","pid","creation_filetime","connection_generation","session_id"),transport.members().keySet());assertEquals(actual.session().machineId(),text(transport.get("machine_id")));assertEquals(BigInteger.valueOf(actual.session().game().pid()),integer(transport.get("pid")));assertEquals(actual.session().game().creationFiletime().value().toString(),text(transport.get("creation_filetime")));assertEquals(actual.session().connectionGeneration().toString(),text(transport.get("connection_generation")));assertEquals(actual.session().sessionId(),text(transport.get("session_id")));
        assertEquals(actual.snapshotId(),text(output.get("snapshot_id")));assertEquals(actual.nativeRevision(),integer(output.get("native_revision")));assertEquals(sha(f.state()),text(output.get("native_state_sha256")));assertEquals(sha(f.packet()),text(output.get("native_packet_sha256")));assertEquals(BigInteger.valueOf(f.packet().length),integer(output.get("native_packet_bytes")));assertEquals(actual.observedAt().toString(),text(output.get("observed_at")));assertEquals(BigInteger.TWO,integer(output.get("public_revision")));assertEquals(BigInteger.valueOf(3),integer(output.get("observation_version")));
        OpportunityJson.Obj source=obj(output.get("source"));assertEquals(Set.of("machine_id","observed_at_utc","exact_build","source_ref"),source.members().keySet());assertEquals(f.source().machineId(),text(source.get("machine_id")));assertEquals(f.source().observedAtUtc(),text(source.get("observed_at_utc")));assertEquals(f.source().exactBuild(),text(source.get("exact_build")));assertEquals(f.source().sourceRef(),DriverObservationEvidenceReader.reference(source.get("source_ref")));assertEquals(f.semantic(),obj(output.get("original_semantic_fields")));unchanged(f);
        row.put("manifest_bytes",bytes.length);row.put("manifest_sha256",sha(bytes));row.put("manifest_field_order",new ArrayList<>(output.members().keySet()));row.put("all_typed_fields_refs_passed",true);row.put("packet_sha256",PACKET_SHA);row.put("driver_sha256",sha(f.driver()));row.put("state_sha256",sha(f.state()));
    }
    private static void unchanged(Fixture f){assertEquals(PACKET_SHA,sha(f.packet()));assertArrayEquals(f.packet(),f.actual().originalPacket());assertArrayEquals(f.state(),f.actual().state().bytes());assertArrayEquals(f.driver(),f.known().driver().encode());assertEquals(ref(f.driver()),f.driverRef());}
    private static void failures(Side a,Side b,Fixture f,List<Map<String,Object>> rows)throws Throwable {
        ExactRef badRef=new ExactRef(f.driverRef().path(),f.driverRef().bytes()+1,f.driverRef().sha256());var held=f.actual();var old=held.session();var changedGame=new GameGeneration(old.game().pid(),new PythonOnlyUInt64(old.game().creationFiletime().value().add(BigInteger.ONE)));var badFrame=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(old.machineId(),changedGame,old.connectionGeneration(),old.sessionId()),held.snapshotId(),held.nativeRevision(),held.state(),held.originalPacket(),held.observedAt());
        for(int i=0;i<2;i++){final ExactRef argRef=i==0?badRef:f.driverRef();final NativeObservationPort.ObservedFrame frame=i==0?held:badFrame;String message=i==0?"complete Driver version exact bytes/SHA differ":"semantic producer crossed actual Game/source";var row=new LinkedHashMap<String,Object>();row.put("case",i==0?"bad_currentDriver_length_plus1":"actualFrame_onlyGamebirth_plus1");row.put("target_attempts",0);row.put("passed",false);rows.add(row);Map<String,Object> first=null;
            for(Side side:List.of(a,b)){row.put("target_attempts",((Number)row.get("target_attempts")).intValue()+1);Throwable failure=assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,()->side.encodeBytes(f,argRef,frame));assertEquals(message,failure.getMessage());Map<String,Object> value=error(failure);if(first==null)first=value;else assertEquals(first,value);row.put(side.label,value);}unchanged(f);row.put("scope","PublicDATAonly,no actualreceive/source/permission. Eachcase changesone declaredinput;beforeGameguard order is frozenSource/Code,not anextra combined-fault sample.");row.put("passed",true);
        }
    }
    private static OpportunityJson.Obj obj(OpportunityJson.Value value){return assertInstanceOf(OpportunityJson.Obj.class,value);}
    private static String text(OpportunityJson.Value value){return assertInstanceOf(OpportunityJson.Text.class,value).value();}
    private static BigInteger integer(OpportunityJson.Value value){return assertInstanceOf(OpportunityJson.IntegerValue.class,value).value();}
    private static final class Side implements AutoCloseable {
        final String label;final SideLoader loader;final Method encode;final Map<String,Object> metadata=new LinkedHashMap<>();int calls;
        Side(String label,Path root,Map<String,String> expected)throws Throwable{this.label=label;loader=new SideLoader(root);try{var pins=new ArrayList<Map<String,Object>>();for(var entry:expected.entrySet()){Class<?> type=Class.forName(entry.getKey(),false,loader);assertSame(loader,type.getClassLoader());Path actual=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();assertEquals(root,actual);byte[] raw=Files.readAllBytes(actual.resolve(type.getName().replace('.','/')+".class"));assertEquals(entry.getValue(),sha(raw));pins.add(Map.of("class",type.getName(),"root",actual.toString(),"bytes",raw.length,"sha256",sha(raw)));}assertEquals(4,pins.size());Class<?> top=Class.forName(READER,false,loader);Class<?>[] params={Known.class,NativeObservationPort.ObservedFrame.class,BigInteger.class,long.class,G2Source.class,OpportunityJson.Obj.class,ExactRef.class};encode=top.getMethod("encode",params);assertArrayEquals(params,encode.getParameterTypes());assertSame(RawJson.class,encode.getReturnType());metadata.put("complete4",pins);metadata.put("root",root.toString());metadata.put("loader","OnlyReader4 own,allDTOs/DriverJson/dependencies parent. OtherReaderentry packageaccessnotgranted. Class.forNameinitializefalse:Readerclinit remainsfirsttargetcost;noextraencodewarmup.");}catch(Throwable failure){try{loader.close();}catch(Throwable cleanup){failure.addSuppressed(cleanup);}throw failure;}}
        byte[] encodeBytes(Fixture f,ExactRef currentDriver,NativeObservationPort.ObservedFrame frame)throws Throwable{calls++;try{return assertInstanceOf(RawJson.class,encode.invoke(null,f.known(),frame,BigInteger.TWO,3L,f.source(),f.semantic(),currentDriver)).bytes();}catch(InvocationTargetException failure){throw failure.getCause();}}
        @Override public void close()throws IOException{long start=System.nanoTime();try{loader.close();}finally{metadata.put("loader_close_ns",System.nanoTime()-start);metadata.put("actual_encode_attempts",calls);}}
    }
    private static final class SideLoader extends URLClassLoader {
        SideLoader(Path root)throws Exception{super(new URL[]{root.toUri().toURL()},ReaderEncode179Test.class.getClassLoader());}
        @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException{synchronized(getClassLoadingLock(name)){if(!OLD_READER.containsKey(name)){if(name.startsWith(READER+"$"))throw new ClassNotFoundException("outside fixedReader4 "+name);return getParent().loadClass(name);}Class<?> found=findLoadedClass(name);if(found==null)found=findClass(name);if(resolve)resolveClass(found);return found;}}
    }
    private static Map<String,Object> heap(){long count=0,time=0;for(var gc:ManagementFactory.getGarbageCollectorMXBeans()){count+=gc.getCollectionCount();time+=gc.getCollectionTime();}var heap=ManagementFactory.getMemoryMXBean().getHeapMemoryUsage();return Map.of("used_bytes",heap.getUsed(),"committed_bytes",heap.getCommitted(),"gc_count",count,"gc_time_ms",time,"scope","post-only shared observation,no forcedGC or peak");}
    private static Map<String,Object> error(Throwable failure){var out=new LinkedHashMap<String,Object>();out.put("class",failure.getClass().getName());out.put("message",failure.getMessage());if(failure.getCause()!=null)out.put("cause",error(failure.getCause()));if(failure.getSuppressed().length>0){var list=new ArrayList<Map<String,Object>>();for(var s:failure.getSuppressed())list.add(error(s));out.put("suppressed",list);}return out;}
    private static Path property(String key)throws Exception{return Path.of(java.util.Objects.requireNonNull(System.getProperty(key),"explicitqualifiedofflinepathrequired: "+key)).toRealPath();}
    private static String sha(byte[] value){return DriverJson.sha256(value);}
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
