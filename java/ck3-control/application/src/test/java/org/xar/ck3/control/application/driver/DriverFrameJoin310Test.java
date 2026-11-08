package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
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

public class DriverFrameJoin310Test {
    private static final String ASM137="org.xar.ck3.control.application.driver.DriverObservationAssembler";
    /** Only the six previously qualified Assembler definitions use this loader; all arguments/dependencies remain parent-owned. */
    private static final class Assembler137Loader extends java.net.URLClassLoader {
        private static final java.util.Set<String> FAMILY=java.util.Set.of(ASM137,ASM137+"$CanonicalNativeState",ASM137+"$Complete",ASM137+"$FullSnapshot",ASM137+"$Incomplete",ASM137+"$Result");
        Assembler137Loader()throws Exception {super(new java.net.URL[]{java.nio.file.Path.of(java.util.Objects.requireNonNull(System.getProperty("ck3.p137.oldAssemblerRoot"),"explicit qualified oldAssembler root required")).toRealPath().toUri().toURL()},DriverFrameJoin310Test.class.getClassLoader());}
        @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException {
            synchronized(getClassLoadingLock(name)) {
                if(!FAMILY.contains(name)) {
                    if(name.startsWith(ASM137+"$"))throw new ClassNotFoundException("unlisted old Assembler family member "+name);
                    return getParent().loadClass(name);
                }
                Class<?> type=findLoadedClass(name);if(type==null)type=findClass(name);if(resolve)resolveClass(type);return type;
            }
        }
    }
    private static OpportunityJson.Obj state137(Method method,NativeObservationPort.ObservedFrame frame)throws Throwable {
        try{return assertInstanceOf(OpportunityJson.Obj.class,method.invoke(null,frame));}
        catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
    }
    private static NativeObservationPort.ObservedFrame stateBytes137(NativeObservationPort.ObservedFrame frame,byte[] bytes) {
        return new NativeObservationPort.ObservedFrame(frame.session(),frame.snapshotId(),frame.nativeRevision(),new RawJson(bytes),frame.originalPacket(),frame.observedAt());
    }
    private static NativeObservationPort.ObservedFrame packet137(NativeObservationPort.ObservedFrame frame,byte[] packet) {
        return new NativeObservationPort.ObservedFrame(frame.session(),frame.snapshotId(),frame.nativeRevision(),frame.state(),packet,frame.observedAt());
    }
    private static Method oldState137(Assembler137Loader loader)throws Exception {
        Class<?> old=Class.forName(ASM137,true,loader);assertSame(loader,old.getClassLoader());
        Method method=old.getMethod("originalNativeState",NativeObservationPort.ObservedFrame.class);
        assertSame(OpportunityJson.Obj.class,method.getReturnType());
        assertSame(DriverJson.class.getClassLoader(),DriverObservationAssembler.class.getClassLoader());
        assertNotSame(loader,DriverObservationAssembler.class.getClassLoader());return method;
    }
    private static void equalState137(Method old,Method current,NativeObservationPort.ObservedFrame frame)throws Throwable {
        byte[] packetBefore=frame.originalPacket(),stateBefore=frame.state().bytes();
        var a=state137(old,frame);var b=state137(current,frame);
        assertEquals(a,b);assertEquals(new ArrayList<>(a.members().keySet()),new ArrayList<>(b.members().keySet()));
        assertArrayEquals(DriverJson.encode(a),DriverJson.encode(b));assertArrayEquals(packetBefore,frame.originalPacket());assertArrayEquals(stateBefore,frame.state().bytes());
    }
    private static void sameFailure137(Method old,Method current,NativeObservationPort.ObservedFrame frame) {
        var a=assertThrows(IllegalArgumentException.class,()->state137(old,frame));
        var b=assertThrows(IllegalArgumentException.class,()->state137(current,frame));
        assertEquals(a.getClass(),b.getClass());assertEquals(a.getMessage(),b.getMessage());
    }
    @Test public void exactPrivatePacketStateReuseAndEveryLexicalOrFailureMissKeepOldDataSemantics137()throws Throwable {
        try(var loader=new Assembler137Loader()) {
            Method old=oldState137(loader),current=DriverObservationAssembler.class.getMethod("originalNativeState",NativeObservationPort.ObservedFrame.class);
            String expectedText="😀 quote \" backslash \\ control \n";
            String textWire=new String(DriverJson.encode(new OpportunityJson.Text(expectedText)),StandardCharsets.UTF_8);
            String literal=STATE.replace("\"original_metric\":1.00","\"original_metric\":1.00,\"opaque137\":{\"zero\":-0,\"negative_zero\":-0.0,\"exp\":1e+0,\"text\":"+textWire+"}");
            var original=actual(literal);var model=DriverJson.object(original.state().bytes(),DriverJson.MAX_NATIVE_BYTES);
            byte[] canonical=DriverJson.encode(model);var matched=stateBytes137(original,canonical);
            assertTrue(DriverJson.encodedContentEquals(model,canonical));equalState137(old,current,matched);
            assertFalse(DriverJson.encodedContentEquals(model,java.util.Arrays.copyOf(canonical,canonical.length-1)));
            byte[] longer=java.util.Arrays.copyOf(canonical,canonical.length+1);longer[longer.length-1]=' ';
            assertFalse(DriverJson.encodedContentEquals(model,longer));
            var output=state137(current,matched);assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,output.get("original_metric")).token());
            var opaque=assertInstanceOf(OpportunityJson.Obj.class,output.get("opaque137"));
            assertEquals("-0.0",assertInstanceOf(OpportunityJson.DecimalValue.class,opaque.get("negative_zero")).token());
            assertEquals("1e+0",assertInstanceOf(OpportunityJson.DecimalValue.class,opaque.get("exp")).token());
            assertEquals(expectedText,assertInstanceOf(OpportunityJson.Text.class,opaque.get("text")).value());
            assertFalse(DriverJson.encodedContentEquals(model,original.state().bytes()),"original whitespace/integer -0 wire is a real miss");
            equalState137(old,current,original);
            var reversed=new java.util.LinkedHashMap<String,OpportunityJson.Value>();var keys=new ArrayList<>(model.members().keySet());java.util.Collections.reverse(keys);
            for(String key:keys)reversed.put(key,model.get(key));byte[] reordered=DriverJson.encode(new OpportunityJson.Obj(reversed));
            assertFalse(DriverJson.encodedContentEquals(model,reordered));equalState137(old,current,stateBytes137(original,reordered));
            assertEquals(keys,new ArrayList<>(state137(current,stateBytes137(original,reordered)).members().keySet()));
            byte[] characters=DriverJson.encodeCharacters(model);assertFalse(java.util.Arrays.equals(canonical,characters));
            assertFalse(DriverJson.encodedContentEquals(model,characters));equalState137(old,current,stateBytes137(original,characters));
            sameFailure137(old,current,stateBytes137(original,bytes(literal.replace("\"original_metric\":1.00","\"original_metric\":1e+0"))));
            sameFailure137(old,current,stateBytes137(original,bytes(literal.replace("\"speed\":3","\"speed\":4"))));
            var array=actual("[]");sameFailure137(old,current,array);sameFailure137(old,current,stateBytes137(array,canonical));
            String deep="0";for(int i=0;i<65;i++)deep="["+deep+"]";
            sameFailure137(old,current,stateBytes137(original,bytes("{\"deep\":"+deep+"}")));
            byte[] packet=original.originalPacket();String body=new String(packet,4,packet.length-4,StandardCharsets.UTF_8).replace("\"protocol_version\":1","\"protocol_version\":2");
            var headerAndStateBad=packet137(stateBytes137(original,bytes("[]")),org.xar.ck3.control.nativebridge.NativeWire.packet(bytes(body)));
            sameFailure137(old,current,headerAndStateBad);
            assertEquals("original native envelope differs",assertThrows(IllegalArgumentException.class,()->state137(current,headerAndStateBad)).getMessage());
            var encodedFailure=new java.util.concurrent.atomic.AtomicBoolean();
            BigInteger hostile=new BigInteger("1") {private static final long serialVersionUID=1L;
                @Override public String toString(){encodedFailure.set(true);throw new IllegalStateException("explicit DATA-only encoder failure137");}};
            assertFalse(DriverJson.encodedContentEquals(new OpportunityJson.IntegerValue(hostile),bytes("0")));assertTrue(encodedFailure.get());
        }
    }

    /** Old qualified Assembler6 child A and new parent B; shared new Driver's old public algorithms are unchanged. */
    @Test public void canonicalMatchAndLexicalMissCompareQualifiedOldAssemblerWithoutReplacingGuards137()throws Throwable {
        long startWindow=System.nanoTime();var report=new java.util.LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();report.put("rows",rows);Throwable failed=null;
        report.put("schema","ck3.p137.original-native-state-component/v1");report.put("fixed_order_per_dataset",List.of("A","B","B","A"));
        report.put("dataset_order",List.of("canonical_match","lexical_whitespace_miss"));report.put("extra_warmups",0);
        report.put("A","qualified old P134Assembler6 only child-first; shared current parent dependencies");report.put("B","new Assembler and new DriverJson in same parent loader");
        report.put("whole_old_binary_AB",false);report.put("physicalIO_Game_SAVE_HTTP_Runtime",0);
        report.put("selected_leaf_old_new_binary_same_process_common_dependencies",true);report.put("same_binary_entries",false);
        try(var loader=new Assembler137Loader()) {
            Method old=oldState137(loader),current=DriverObservationAssembler.class.getMethod("originalNativeState",NativeObservationPort.ObservedFrame.class);
            report.put("old_root",System.getProperty("ck3.p137.oldAssemblerRoot"));report.put("old_code_source",old.getDeclaringClass().getProtectionDomain().getCodeSource().getLocation().toString());
            String large=STATE.replace("\"original_metric\":1.00","\"original_metric\":1.00,\"opaque_unconsumed_extension\":\""+"x".repeat(3_400_000)+"\"");
            var lexical=actual(large);var model=DriverJson.object(lexical.state().bytes(),DriverJson.MAX_NATIVE_BYTES);byte[] canonical=DriverJson.encode(model);
            var matched=stateBytes137(lexical,canonical);assertTrue(DriverJson.encodedContentEquals(model,canonical));assertFalse(DriverJson.encodedContentEquals(model,lexical.state().bytes()));
            var cpu=java.lang.management.ManagementFactory.getThreadMXBean();boolean cpuAvailable=cpu.isCurrentThreadCpuTimeSupported();
            if(cpuAvailable&&!cpu.isThreadCpuTimeEnabled())cpu.setThreadCpuTimeEnabled(true);
            com.sun.management.ThreadMXBean allocation=cpu instanceof com.sun.management.ThreadMXBean bean?bean:null;
            boolean allocAvailable=allocation!=null&&allocation.isThreadAllocatedMemorySupported();if(allocAvailable&&!allocation.isThreadAllocatedMemoryEnabled())allocation.setThreadAllocatedMemoryEnabled(true);
            report.put("CPU_available",cpuAvailable);report.put("allocation_available",allocAvailable);report.put("setup_ns_before_rows",System.nanoTime()-startWindow);
            for(String dataset:List.of("canonical_match","lexical_whitespace_miss")) {
                var frame=dataset.equals("canonical_match")?matched:lexical;String rawSha=DriverJson.sha256(frame.state().bytes()),packetSha=DriverJson.sha256(frame.originalPacket());String expected=null;
                for(int i=0;i<4;i++) {
                    String route=i==0||i==3?"A":"B";var row=new java.util.LinkedHashMap<String,Object>();rows.add(row);
                    row.put("dataset",dataset);row.put("index",i);row.put("entry",route);row.put("new_predicate_expected_match",dataset.equals("canonical_match"));
                    long cpuStart=cpuAvailable?cpu.getCurrentThreadCpuTime():-1,allocatedStart=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1;
                    long begin=System.nanoTime();OpportunityJson.Obj result;boolean completed=false;
                    try {result=state137(route.equals("A")?old:current,frame);completed=true;}
                    finally {long end=System.nanoTime(),allocatedEnd=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1,cpuEnd=cpuAvailable?cpu.getCurrentThreadCpuTime():-1;
                        row.put("wall_start_ns",begin);row.put("wall_end_ns",end);row.put("wall_ns",end-begin);row.put("CPU_start_ns",cpuStart);row.put("CPU_end_ns",cpuEnd);row.put("CPU_ns",cpuAvailable?cpuEnd-cpuStart:-1);
                        row.put("allocation_start_bytes",allocatedStart);row.put("allocation_end_bytes",allocatedEnd);row.put("thread_allocated_bytes",allocAvailable?allocatedEnd-allocatedStart:-1);row.put("completed",completed);}
                    assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,result.get("original_metric")).token());
                    assertEquals(3_400_000,assertInstanceOf(OpportunityJson.Text.class,result.get("opaque_unconsumed_extension")).value().length());
                    String semantic=DriverJson.sha256(DriverJson.encode(result));if(expected==null)expected=semantic;assertEquals(expected,semantic);
                    assertEquals(rawSha,DriverJson.sha256(frame.state().bytes()));assertEquals(packetSha,DriverJson.sha256(frame.originalPacket()));
                    row.put("semantic_sha256",semantic);row.put("state_sha256",rawSha);row.put("packet_sha256",packetSha);row.put("all_post_checks_passed",true);
                }
            }
        }catch(Throwable failure){failed=failure;report.put("failure_class",failure.getClass().getName());report.put("failure_message",String.valueOf(failure.getMessage()));throw failure;}
        finally {
            report.put("completed",failed==null);report.put("window_ns_before_report_materialization",System.nanoTime()-startWindow);
            report.put("scope","selected-leaf old/new binary, same process/common dependencies, 2samples/entry/dataset; not same-binary entries or whole old/new CP or actual worker. Both Method.invoke overhead included; fixture setup parses/encodes, postchecks/report/close held in whole JUnit. Report scenarios separately; no unknown natural hitrate combination.");
            try{byte[] encoded=org.xar.ck3.control.contracts.FullJsonTree.encode(new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(report),1_048_576);
                var output=directory.resolve("p137-native-state-component.json");java.nio.file.Files.write(output,encoded,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE);
                System.out.println("P137 native state component "+output);
            }catch(Throwable outputFailure){if(failed==null)throw outputFailure;if(failed!=outputFailure)failed.addSuppressed(outputFailure);}
        }
    }


    @org.junit.jupiter.api.io.TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) java.nio.file.Path directory;

    @Test public void firstProjectionFailuresStayDirectAndLateIdentityStillUsesOriginalResultLayer() {
        var malformed=fixture(STATE.replace("\"paused\":true","\"paused\":\"true\""));
        var assembler=new DriverObservationAssembler();var loader=new DriverFrameEvidenceLoader(assembler);
        var oldOriginals=new Originals(malformed);var newOriginals=new Originals(malformed);
        var expected=assertThrows(IllegalArgumentException.class,()->oldLoad(assembler,loader,malformed,oldOriginals.archive()));
        var actual=assertThrows(IllegalArgumentException.class,()->loader.load(malformed.basis(),newOriginals.archive()));
        assertEquals(expected.getClass(),actual.getClass());assertEquals(expected.getMessage(),actual.getMessage());
        assertNotEquals("archived native/complete Driver no longer rebuild an accepted original semantic frame",actual.getMessage());
        oldOriginals.assertReads(1);newOriginals.assertReads(1);
        var rawReplay=assertInstanceOf(DriverObservationAssembler.Incomplete.class,DriverObservationEvidenceReader.replayOriginals(
                malformed.manifestRef(),malformed.manifest(),malformed.driver(),malformed.packet(),malformed.nativeRef()));
        assertEquals(List.of("native_driver_fact_join: "+expected.getMessage()),rawReplay.reasons());

        var late=fixture(STATE.replace("\"character_id\":73","\"character_id\":74"));
        var oldLate=new Originals(late);var newLate=new Originals(late);
        var oldFailure=assertThrows(IllegalArgumentException.class,()->oldLoad(assembler,loader,late,oldLate.archive()));
        var newFailure=assertThrows(IllegalArgumentException.class,()->loader.load(late.basis(),newLate.archive()));
        assertEquals(oldFailure.getClass(),newFailure.getClass());assertEquals(oldFailure.getMessage(),newFailure.getMessage());
        assertEquals("archived native/complete Driver no longer rebuild an accepted original semantic frame",newFailure.getMessage());
        oldLate.assertReads(1);newLate.assertReads(1);
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,DriverObservationEvidenceReader.replayOriginals(
                late.manifestRef(),late.manifest(),late.driver(),late.packet(),late.nativeRef()));
    }

    /** DATA-original archive callbacks, not disk reads or Game. Same binary's old source chain versus new load. */
    @Test public void largeOriginalsCompareOldSourceChainAndSingleProjectionComponent() throws Throwable {
        long windowStart=System.nanoTime();var report=new java.util.LinkedHashMap<String,Object>();
        var rows=new ArrayList<Map<String,Object>>();report.put("rows",rows);Throwable failed=null;
        report.put("schema","ck3.p134.native-originals-component/v1");
        report.put("same_new_binary_two_entries",true);report.put("old_binary_AB",false);
        report.put("archive_kind","existing310 in-memory original byte fixture; no physicalIO/Game");
        report.put("fixed_order",List.of("A","B","B","A"));report.put("extra_warmups",0);
        report.put("profile",1);report.put("scoped_driver_decode",false);
        report.put("CPU_allocation_queries_bracket_wall",true);report.put("Game_Native_live_HTTP_SAVE_Runtime",0);
        try {
            String large=STATE.replace("\"original_metric\":1.00","\"original_metric\":1.00,\"opaque_unconsumed_extension\":\""+"x".repeat(3_400_000)+"\"");
            var f=fixture(large);var assembler=new DriverObservationAssembler();var loader=new DriverFrameEvidenceLoader(assembler);
            String manifestSha=DriverJson.sha256(f.manifest().bytes()),nativeSha=DriverJson.sha256(f.packet()),driverSha=DriverJson.sha256(f.driver().bytes());
            report.put("manifest_sha256",manifestSha);report.put("native_packet_sha256",nativeSha);report.put("driver_sha256",driverSha);
            report.put("manifest_bytes",f.manifestRef().bytes());report.put("native_packet_bytes",f.nativeRef().bytes());report.put("driver_bytes",f.driverRef().bytes());
            report.put("state_bytes",f.actual().state().bytes().length);report.put("opaque_ASCII_characters",3_400_000);
            var cpu=java.lang.management.ManagementFactory.getThreadMXBean();boolean cpuAvailable=cpu.isCurrentThreadCpuTimeSupported();
            if(cpuAvailable&&!cpu.isThreadCpuTimeEnabled())cpu.setThreadCpuTimeEnabled(true);
            com.sun.management.ThreadMXBean allocation=cpu instanceof com.sun.management.ThreadMXBean bean?bean:null;
            boolean allocationAvailable=allocation!=null&&allocation.isThreadAllocatedMemorySupported();
            if(allocationAvailable&&!allocation.isThreadAllocatedMemoryEnabled())allocation.setThreadAllocatedMemoryEnabled(true);
            report.put("CPU_available",cpuAvailable);report.put("allocation_available",allocationAvailable);
            report.put("setup_ns_before_rows",System.nanoTime()-windowStart);
            String expectedSemantic=null,expectedBinding=null,expectedIdentity=null;
            for(int index=0;index<4;index++) {
                String route=index==0||index==3?"A":"B";var originals=new Originals(f);
                var row=new java.util.LinkedHashMap<String,Object>();rows.add(row);row.put("index",index);row.put("entry",route);
                long cpuStart=cpuAvailable?cpu.getCurrentThreadCpuTime():-1;
                long allocationStart=allocationAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1;
                long start=System.nanoTime();DriverObservationAssembler.Complete value;boolean completed=false;
                try {
                    value=route.equals("A")?oldLoad(assembler,loader,f,originals.archive()):loader.load(f.basis(),originals.archive());
                    completed=true;
                } finally {
                    long end=System.nanoTime();long allocationEnd=allocationAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1;
                    long cpuEnd=cpuAvailable?cpu.getCurrentThreadCpuTime():-1;
                    row.put("wall_start_ns",start);row.put("wall_end_ns",end);row.put("wall_ns",end-start);
                    row.put("CPU_start_ns",cpuStart);row.put("CPU_end_ns",cpuEnd);row.put("CPU_ns",cpuAvailable?cpuEnd-cpuStart:-1);
                    row.put("allocation_start_bytes",allocationStart);row.put("allocation_end_bytes",allocationEnd);
                    row.put("thread_allocated_bytes",allocationAvailable?allocationEnd-allocationStart:-1);row.put("completed",completed);
                    row.put("original_callback_reads",originals.reads.size());
                }
                originals.assertReads(1);
                assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,value.semantic().get("original_metric")).token());
                assertEquals(3_400_000,assertInstanceOf(OpportunityJson.Text.class,value.semantic().get("opaque_unconsumed_extension")).value().length());
                String semanticSha=DriverJson.sha256(DriverJson.encode(value.semantic()));
                String identity=value.identity().toString();
                if(index==0){expectedSemantic=semanticSha;expectedBinding=value.fullBindingSha256();expectedIdentity=identity;}
                assertEquals(expectedSemantic,semanticSha);assertEquals(expectedBinding,value.fullBindingSha256());assertEquals(expectedIdentity,identity);
                assertEquals(source(),value.source());assertEquals("held-session",value.sessionId());assertEquals(f.nativeRef(),value.originalEvidence());
                assertEquals(f.actual().observedAt(),value.observedAt());assertEquals(BigInteger.valueOf(5),value.connectionGeneration());
                assertTrue(value.originalProjection().isEmpty(),"profile1 remains profile1; profile4 constructor replay is not elided");
                assertEquals(manifestSha,DriverJson.sha256(f.manifest().bytes()));assertEquals(nativeSha,DriverJson.sha256(f.packet()));assertEquals(driverSha,DriverJson.sha256(f.driver().bytes()));
                row.put("semantic_sha256",semanticSha);row.put("full_binding_sha256",value.fullBindingSha256());row.put("identity",identity);
                row.put("read_ref_SHA_order",originals.reads.stream().map(ExactRef::sha256).toList());row.put("all_post_checks_passed",true);
            }
        } catch(Throwable failure) {
            failed=failure;report.put("failure_class",failure.getClass().getName());report.put("failure_message",String.valueOf(failure.getMessage()));throw failure;
        } finally {
            report.put("completed",failed==null);report.put("window_ns_before_report_output",System.nanoTime()-windowStart);
            report.put("two_samples_each_not_robust_latency",true);
            report.put("setup_and_post_verification_report_cost_retained_in_whole_JUnit_actor",true);
            try {
                byte[] encoded=org.xar.ck3.control.contracts.FullJsonTree.encode(new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(report),1_048_576);
                var output=directory.resolve("p134-native-originals-component.json");
                java.nio.file.Files.write(output,encoded,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE);
                System.out.println("P134 native original component report "+output);
            } catch(Throwable outputFailure) {if(failed==null)throw outputFailure;if(failed!=outputFailure)failed.addSuppressed(outputFailure);}
        }
    }
    private static DriverObservationAssembler.Complete oldLoad(DriverObservationAssembler assembler,DriverFrameEvidenceLoader loader,
            Fixture f,OutcomeArchive archive) {
        var full=loader.loadFull(f.basis(),archive);
        var result=assembler.assemble(full.actual(),full.facts(),full.originalEvidence());
        org.xar.ck3.control.contracts.StrictJson.require(result instanceof DriverObservationAssembler.Complete,
                "archived native/complete Driver no longer rebuild an accepted original semantic frame");
        return (DriverObservationAssembler.Complete)result;
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

    private static byte[] bytes(String text) { return text.getBytes(java.nio.charset.StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw)); }
    private static GameGeneration game() { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static Known known() { return DriverFactsRepository.imported(ref(bytes(WIRE)), bytes(WIRE), 3, 7, game(), new OpportunityJson.Obj(Map.of())); }
    private static G2Source source() { return new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref(bytes("original-source"))); }

    private static byte[] packet(String state) {
        String json = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}";
        byte[] jsonBytes = bytes(json);
        ByteBuffer buffer = ByteBuffer.allocate(jsonBytes.length + 4).order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(jsonBytes.length);
        buffer.put(jsonBytes);
        return buffer.array();
    }

    private static NativeObservationPort.ObservedFrame actual(String state) {
        var session = new NativeObservationPort.TransportSession("test-machine", game(), BigInteger.valueOf(5), "held-session");
        var rawState = new RawJson(bytes(state.strip()));
        var framed = packet(state);
        return new NativeObservationPort.ObservedFrame(session, "snapshot-9", BigInteger.valueOf(9), rawState, framed, Instant.parse("2026-10-23T16:00:00Z"));
    }

    private record Fixture(NativeObservationPort.ObservedFrame actual, RawJson manifest, ExactRef manifestRef,
            RawJson driver, ExactRef driverRef, byte[] packet, ExactRef nativeRef) {
        NativeEffectEvidence.FrameBasis basis() { return new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef); }
    }
    private static Fixture fixture(String state) {
        var k=known();var actual=actual(state);var driver=new RawJson(k.driver().encode());var driverRef=ref(driver.bytes());
        var manifest=DriverObservationEvidenceReader.encode(k,actual,BigInteger.valueOf(2),1,source(),
                new OpportunityJson.Obj(Map.of()),driverRef);
        var packet=actual.originalPacket();return new Fixture(actual,manifest,ref(manifest.bytes()),driver,driverRef,packet,ref(packet));
    }
    private static final class Originals implements InvocationHandler {
        private final Fixture f;
        private final ExactRef manifestRequested,nativeRequested;
        private final RawJson returnedDriver;
        private final UncheckedIOException lateFailure;
        private final List<ExactRef> reads=new ArrayList<>();
        private boolean mutateNativeOnDriver;
        Originals(Fixture f) { this(f,f.manifestRef(),f.nativeRef(),f.driver(),null); }
        Originals(Fixture f,ExactRef manifestRequested,ExactRef nativeRequested,RawJson returnedDriver,UncheckedIOException lateFailure) {
            this.f=f;this.manifestRequested=manifestRequested;this.nativeRequested=nativeRequested;
            this.returnedDriver=returnedDriver;this.lateFailure=lateFailure;
        }
        OutcomeArchive archive() {
            return (OutcomeArchive)Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{OutcomeArchive.class},this);
        }
        @Override public Object invoke(Object proxy,Method method,Object[] args) {
            assertNotNull(args);assertEquals(1,args.length);var requested=assertInstanceOf(ExactRef.class,args[0]);
            int position=reads.size()%3;reads.add(requested);
            if(position==0) { assertEquals("loadFullMaterial",method.getName());assertEquals(manifestRequested,requested);return f.manifest(); }
            if(position==1) { assertEquals("loadNativeFrame",method.getName());assertEquals(nativeRequested,requested);return f.packet(); }
            assertEquals("loadFullMaterial",method.getName());assertEquals(f.driverRef(),requested);
            if(mutateNativeOnDriver)f.packet()[0]^=1;
            if(lateFailure!=null)throw lateFailure;
            return returnedDriver;
        }
        void assertReads(int cycles) {
            var expected=new ArrayList<ExactRef>();
            for(int i=0;i<cycles;i++)expected.addAll(List.of(manifestRequested,nativeRequested,f.driverRef()));
            assertEquals(expected,reads);
        }
    }
    private static DriverObservationAssembler.FullSnapshot oldPublic(Fixture f,DriverObservationAssembler assembler) {
        var frame=DriverObservationEvidenceReader.nativeFrame(f.manifestRef(),f.manifest(),f.packet());
        var facts=DriverObservationEvidenceReader.decode(f.manifestRef(),f.manifest(),f.driver(),frame);
        return assembler.projectFull(frame,facts,f.nativeRef());
    }
    private static void sameFull(DriverObservationAssembler.FullSnapshot expected,DriverObservationAssembler.FullSnapshot actual) {
        assertEquals(expected.actual().session(),actual.actual().session());
        assertEquals(expected.actual().snapshotId(),actual.actual().snapshotId());
        assertEquals(expected.actual().nativeRevision(),actual.actual().nativeRevision());
        assertArrayEquals(expected.actual().state().bytes(),actual.actual().state().bytes());
        assertArrayEquals(expected.actual().originalPacket(),actual.actual().originalPacket());
        assertEquals(expected.actual().observedAt(),actual.actual().observedAt());
        assertEquals(expected.facts(),actual.facts());assertEquals(expected.semantic(),actual.semantic());
        assertArrayEquals(DriverJson.encode(expected.semantic()),DriverJson.encode(actual.semantic()));
        assertEquals(expected.originalEvidence(),actual.originalEvidence());assertEquals(expected.fullBindingSha256(),actual.fullBindingSha256());
    }
    @Test
    public void fullProjectionPreservesOriginalPlayerShapesAndReadsEveryOriginal() {
        String player="\"played_character\":{\"character_id\":73,\"alive\":true},";
        var states=List.of(STATE,STATE.replace(player,""),STATE.replace(player,"\"played_character\":null,"),
                STATE.replace("\"character_id\":73","\"character_id\":74"));
        for(int index=0;index<states.size();index++) {
            var f=fixture(states.get(index));var assembler=new DriverObservationAssembler();var loader=new DriverFrameEvidenceLoader(assembler);
            var originals=new Originals(f);var archive=originals.archive();var expected=oldPublic(f,assembler);
            var actual=loader.loadFull(f.basis(),archive);sameFull(expected,actual);originals.assertReads(1);
            var repeated=loader.loadFull(f.basis(),archive);sameFull(expected,repeated);originals.assertReads(2);
            assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,actual.semantic().get("original_metric")).token());
            assertEquals(2,assertInstanceOf(OpportunityJson.Arr.class,actual.semantic().get("native_command_history")).items().size());
            assertEquals(f.manifestRef(),DriverObservationEvidenceReader.reference(actual.semantic().get("java_driver_facts_evidence")));
            assertEquals(new BigInteger("9007199254740993"),actual.actual().session().game().creationFiletime().value());
            if(index==1)assertFalse(actual.semantic().members().containsKey("played_character"));
            if(index==2)assertSame(OpportunityJson.Nil.INSTANCE,actual.semantic().get("played_character"));
            if(index==3)assertEquals(BigInteger.valueOf(74),OpportunityJson.integer(
                    assertInstanceOf(OpportunityJson.Obj.class,actual.semantic().get("played_character")).get("character_id"),"character_id"));
            var ordinary=new Originals(f);
            if(index==0)assertInstanceOf(DriverObservationAssembler.Complete.class,loader.load(f.basis(),ordinary.archive()));
            else assertThrows(IllegalArgumentException.class,()->loader.load(f.basis(),ordinary.archive()));
            ordinary.assertReads(1);
            var replay=DriverObservationEvidenceReader.replayOriginals(f.manifestRef(),f.manifest(),f.driver(),f.packet(),f.nativeRef());
            if(index==0)assertInstanceOf(DriverObservationAssembler.Complete.class,replay);
            else assertInstanceOf(DriverObservationAssembler.Incomplete.class,replay);
            byte[] capturedPacket=actual.actual().originalPacket(),capturedState=actual.actual().state().bytes(),semantic=DriverJson.encode(actual.semantic());
            f.packet()[0]^=1;
            assertArrayEquals(capturedPacket,actual.actual().originalPacket());assertArrayEquals(capturedState,actual.actual().state().bytes());
            assertArrayEquals(semantic,DriverJson.encode(actual.semantic()));
        }
        // The native original is borrowed by an archive; capture must precede its next callback.
        var alias=fixture(STATE);var assembler=new DriverObservationAssembler();var expected=oldPublic(alias,assembler);
        byte originalFirstByte=alias.packet()[0];
        var aliasOriginals=new Originals(alias);aliasOriginals.mutateNativeOnDriver=true;
        var captured=new DriverFrameEvidenceLoader(assembler).loadFull(alias.basis(),aliasOriginals.archive());
        assertNotEquals(originalFirstByte,alias.packet()[0]);
        sameFull(expected,captured);aliasOriginals.assertReads(1);
    }
    @Test
    public void exactArchiveGuardsAndLateReadFailureRemainObservable() {
        var f=fixture(STATE);var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var wrongManifest=new ExactRef(f.manifestRef().path(),f.manifestRef().bytes(),"0".repeat(64));
        var manifestOriginals=new Originals(f,wrongManifest,f.nativeRef(),f.driver(),null);
        assertThrows(IllegalArgumentException.class,()->loader.loadFull(new NativeEffectEvidence.FrameBasis(f.nativeRef(),wrongManifest),manifestOriginals.archive()));
        assertEquals(List.of(wrongManifest),manifestOriginals.reads);
        var wrongNative=new ExactRef(f.nativeRef().path(),f.nativeRef().bytes(),"0".repeat(64));
        var nativeOriginals=new Originals(f,f.manifestRef(),wrongNative,f.driver(),null);
        assertThrows(IllegalArgumentException.class,()->loader.loadFull(new NativeEffectEvidence.FrameBasis(wrongNative,f.manifestRef()),nativeOriginals.archive()));
        assertEquals(List.of(f.manifestRef(),wrongNative),nativeOriginals.reads);
        var changedDriver=new RawJson(bytes(new String(f.driver().bytes(),StandardCharsets.UTF_8).replace("campaign-original","changed-campaign")));
        var driverOriginals=new Originals(f,f.manifestRef(),f.nativeRef(),changedDriver,null);
        assertThrows(IllegalArgumentException.class,()->loader.loadFull(f.basis(),driverOriginals.archive()));driverOriginals.assertReads(1);
        var marker=new IOException("owned late original read failure");var failure=new UncheckedIOException(marker);
        var lateOriginals=new Originals(f,f.manifestRef(),f.nativeRef(),f.driver(),failure);
        assertSame(failure,assertThrows(UncheckedIOException.class,()->loader.loadFull(f.basis(),lateOriginals.archive())));
        assertSame(marker,failure.getCause());lateOriginals.assertReads(1);
    }
}
