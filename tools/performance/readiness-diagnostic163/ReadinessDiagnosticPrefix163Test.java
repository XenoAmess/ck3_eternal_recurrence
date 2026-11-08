package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.*;

/** Offline DATA prefix only; no current qualification, private issuer or physical transport is produced. */
final class ReadinessDiagnosticPrefix163Test {
    private static final String COLLECTOR="org.xar.ck3.control.application.readiness.NativeReadinessCollector";
    private static final List<String> NAMES=List.of("org.xar.ck3.control.application.readiness.NativeReadinessCollector$1",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$ActiveObservationSession",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$AdmittedActorAuthority",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$CapabilitiesPort",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$Captured",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$CaptureMode",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$CaptureWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$ExecutableCapabilities",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$FirstCheckpointAdmission",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$HeldReadScope",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$HeldReadWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$LifecycleParentAuthority",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$ObservationSessionAuthority",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PhysicalCapture",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PhysicalSemanticCapture",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PhysicalWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningEvidenceVerifier",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningInputs",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningInputsPort",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningReadScope",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningRoundScope",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningRoundWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PlanningWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicAttempt",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicFrameWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicObserved",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicPlanningFrame",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicPlanningInputsPort",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicPlanningObservation",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicPlanningWork",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicReady",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicScope",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$PublicSourceAuthority",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$ReadyPublication",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$SourceAuthority",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$SourceGuard",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector$SourceQualification",
            "org.xar.ck3.control.application.readiness.NativeReadinessCollector");
    private static final String MACHINE="retained-driver-memory", SESSION="retained-driver-session";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
        "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,
        "succession_expectation":null,"succession_lifecycle":null,"campaign_goal":{"campaign_id":"original","anchor":{"character_id":73}},
        "rollback_war_failures":[]}
        """;
    private static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
        "episode_identity_pending":false,"active_wars":[],"player_armies":[],"diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """;
    private static final int REPORT_LIMIT=262_144;
    @TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) Path temporary;

    @Test void actualQualifierPrefix64ThenIncompleteDiagnostic() throws Throwable {
        String oldRoot=System.getProperty("ck3.p163.oldCollectorRoot"),newRoot=System.getProperty("ck3.p163.currentCollectorRoot");
        org.junit.jupiter.api.Assumptions.assumeTrue(oldRoot!=null&&newRoot!=null,"offline actual-artifact comparison requires two exact Collector roots");
        long beginning=System.nanoTime();Path output=temporary.resolve("p163-eager-diagnostic-prefix-fixed64.json");assertFalse(Files.exists(output));
        var report=new LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();var scenes=new ArrayList<Map<String,Object>>();
        report.put("schema","ck3.p163.actual-qualify-prefix-fixed64/v1");report.put("global_completed",false);report.put("rows",rows);report.put("inputs",scenes);
        report.put("scope","Actual private9arg qualifyPhysical prefix through firstClock Marker, including same reflection/sentinel unwind. No normal return or postclock qualification/capture/worker/IO/Runtime result. PublicCtor only; no production private fields/constructors/issuer.");
        report.put("fixed_order","small originalSTATE -> 3.397M opaque; each8ABBA32/16A16B,total64;0 setupCollector-target/extra warmup; retain all first/cold and later warmed rows.");
        report.put("timer_boundary","Perrow timer is actual qualifier invocation inside real memoryStore.locked+Driver.withFrozenObservation callback. Scene frozen preparation/closure and allpost/setup/functional costs retained separately in enclosing scene/case/Native actor.");
        Throwable primary=null;
        try {
            var mx=assertInstanceOf(com.sun.management.ThreadMXBean.class,ManagementFactory.getThreadMXBean());
            assertTrue(mx.isThreadAllocatedMemorySupported());if(!mx.isThreadAllocatedMemoryEnabled())mx.setThreadAllocatedMemoryEnabled(true);
            assertTrue(mx.isCurrentThreadCpuTimeSupported());if(!mx.isThreadCpuTimeEnabled())mx.setThreadCpuTimeEnabled(true);
            long thread=Thread.currentThread().threadId(),setup=System.nanoTime();
            String tail=" spaces 中😀 quote\" slash\\ newline\n";
            String payload="x".repeat(3_397_000-tail.getBytes(StandardCharsets.UTF_8).length)+tail;
            String large=STATE.substring(0,STATE.lastIndexOf('}'))+",\"opaque_blob\":"+new String(DriverJson.encode(new Text(payload)),StandardCharsets.UTF_8)+"}";
            try(Side a=Side.open("A",Path.of(oldRoot).toRealPath());Side b=Side.open("B",Path.of(newRoot).toRealPath())) {
                report.put("A_setup",a.metadata);report.put("B_setup",b.metadata);report.put("initial_setup_ns",System.nanoTime()-setup);report.put("setup_target_calls",0);
                for(String name:List.of("small","large_3397k")) {
                    long sceneStart=System.nanoTime();
                    try(Fixture f=new Fixture(name,name.equals("small")?STATE:large)) {
                        var scene=new LinkedHashMap<String,Object>();scene.putAll(f.description());scene.put("fixture_construct_ns",System.nanoTime()-sceneStart);scenes.add(scene);
                        long bind=System.nanoTime();a.bind(f);b.bind(f);scene.put("both_publicCtor_bind_ns",System.nanoTime()-bind);assertEquals(0,f.clock.calls);assertEquals(0,f.denials.businessCalls);
                        f.store.locked(same->f.driver.withFrozenObservation(f.actual,same,frozen->{
                            String head=same.head().digest();var stamp=frozen.state().stamp();
                            for(int cycle=0;cycle<8;cycle++)for(int slot=0;slot<4;slot++) {
                                Side side=slot==0||slot==3?a:b;var row=new LinkedHashMap<String,Object>();
                                row.put("index",rows.size());row.put("input",name);row.put("cycle",cycle);row.put("slot",slot);row.put("side",side.label);row.put("prefix_completed",false);row.put("postchecks_passed",false);row.put("normal_target_return",false);rows.add(row);
                                int clocks=f.clock.calls,reads=f.packets.reads,writes=f.packets.writes;long enclosing=System.nanoTime();
                                long w0=System.nanoTime(),c0=mx.getCurrentThreadCpuTime(),a0=mx.getThreadAllocatedBytes(thread);
                                Throwable caught=null;
                                try {side.invoke(same,f.deadline,head,f.actual,frozen.state(),frozen.facts(),f.original);row.put("normal_target_return",true);}
                                catch(Throwable error){caught=error;}
                                long a1=mx.getThreadAllocatedBytes(thread),c1=mx.getCurrentThreadCpuTime(),w1=System.nanoTime();endpoints(row,w0,w1,c0,c1,a0,a1);
                                if(caught!=f.marker) {
                                    Throwable error=caught==null?new AssertionError("actual prefix returned normally instead of firstClock boundary"):caught;
                                    row.put("exception_class",error.getClass().getName());row.put("exception_message",bounded(error.getMessage()));throw rethrow(error);
                                }
                                row.put("prefix_completed",true);assertEquals(clocks+1,f.clock.calls);assertEquals(0,f.denials.businessCalls);assertEquals(reads,f.packets.reads);assertEquals(writes,f.packets.writes);
                                assertEquals(head,same.head().digest());assertEquals(stamp,f.repository.locked(state->((DriverSnapshotFacts.Known)state).stamp()));f.assertOriginals();
                                row.put("marker_identity_passed",true);row.put("clock_call_delta",1);row.put("afterclock_business_calls",0);row.put("packet_read_delta",0);row.put("packet_write_delta",0);row.put("head_SHA256",head);row.put("Driver_stamp",stamp.toString());row.put("packet_SHA256",f.packetSha);row.put("state_SHA256",f.stateSha);row.put("postchecks_passed",true);row.put("enclosing_with_post_ns",System.nanoTime()-enclosing);
                            }
                            return null;
                        }));
                        f.assertOriginals();assertEquals(32,f.clock.calls);assertEquals(0,f.denials.businessCalls);assertEquals(0,f.packets.reads);assertEquals(0,f.packets.writes);
                        scene.put("measured_target_calls",32);scene.put("afterclock_business_calls",0);scene.put("frozen_scope_including_preparation_rows_post_ns",System.nanoTime()-sceneStart);
                    }
                }
                assertEquals(64,rows.size());for(String input:List.of("small","large_3397k"))for(String side:List.of("A","B"))
                    assertEquals(16,rows.stream().filter(x->input.equals(x.get("input"))&&side.equals(x.get("side"))).count());
                long negativeStart=System.nanoTime();report.put("negative_guard",negative(a,b));report.put("negative_function_ns",System.nanoTime()-negativeStart);
                report.put("global_completed",true);
            }
        } catch(Throwable error){primary=error;report.put("global_completed",false);report.put("failure_class",error.getClass().getName());report.put("failure_message",bounded(error.getMessage()));throw error;}
        finally {
            report.put("rows_recorded",rows.size());report.put("before_report_materialization_ns",System.nanoTime()-beginning);
            report.put("limits","Original memoryfixture producer composition adapted only for full-input DATA budget, not production cap change. No source/lifecycle/authority afterMarker. Parent codecs/Driver shared, own38 Collector classes/JIT; nonrandom order/all cold and warmed rows kept. Marker exceptional boundary is not normal output, complete capture or worker latency. CPU zeros/granularity/allocation-not-peak remain. Before-report excludes JSON/write/JUnit/VM tail; Native total includes all.");
            try {byte[] bytes=FullJsonTree.encode(new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(report),REPORT_LIMIT);Files.write(output,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);}
            catch(Throwable outputError){if(primary!=null)primary.addSuppressed(outputError);else throw outputError;}
        }
    }

    private static Map<String,Object> negative(Side a,Side b)throws Throwable {
        var record=new LinkedHashMap<String,Object>();record.put("passed",false);record.put("target_calls",0);
        try(Fixture f=new Fixture("negative_guard",STATE)) {
            a.bind(f);b.bind(f);
            f.store.locked(same->f.driver.withFrozenObservation(f.actual,same,frozen->{
                String changed=STATE.replace("\"character_id\":73","\"character_id\":74");assertNotEquals(STATE,changed);
                var actual=frame(changed,f.actual.observedAt());var facts=f.produce(frozen.state(),actual);var original=f.material(actual.originalPacket());
                assertInstanceOf(DriverObservationAssembler.Incomplete.class,new DriverObservationAssembler().assemble(actual,facts,original));record.put("actual_assembler_Incomplete",true);
                Throwable first=null;
                for(Side side:List.of(a,b)) {
                    record.put("target_calls",(Integer)record.get("target_calls")+1);Throwable caught=null;
                    try{side.invoke(same,f.deadline,same.head().digest(),actual,frozen.state(),facts,original);}catch(Throwable error){caught=error;}
                    assertNotNull(caught);assertInstanceOf(ContractViolationException.class,caught);assertTrue(caught.getMessage().startsWith("actual native/Driver observation join is incomplete: "));
                    if(first==null)first=caught;else{assertEquals(first.getClass(),caught.getClass());assertEquals(first.getMessage(),caught.getMessage());}
                    record.put(side.label+"_exception_class",caught.getClass().getName());record.put(side.label+"_message",bounded(caught.getMessage()));record.put(side.label+"_message_bytes",caught.getMessage().getBytes(StandardCharsets.UTF_8).length);record.put(side.label+"_message_SHA256",DriverJson.sha256(caught.getMessage().getBytes(StandardCharsets.UTF_8)));
                }
                assertEquals(0,f.clock.calls);assertEquals(0,f.denials.businessCalls);assertEquals(0,f.packets.reads);assertEquals(0,f.packets.writes);f.assertOriginals();record.put("clock_calls",0);record.put("afterclock_business_calls",0);record.put("passed",true);return null;
            }));
        }
        return record;
    }
    private static void endpoints(Map<String,Object> r,long w0,long w1,long c0,long c1,long a0,long a1) {
        r.put("wall_start_ns",w0);r.put("wall_end_ns",w1);r.put("wall_ns",w1-w0);r.put("cpu_start_ns",c0);r.put("cpu_end_ns",c1);r.put("cpu_ns",c1-c0);r.put("allocation_start_bytes",a0);r.put("allocation_end_bytes",a1);r.put("allocated_bytes",a1-a0);assertTrue(w1>=w0&&c1>=c0&&c0>=0&&a1>=a0&&a0>=0);
    }
    @SuppressWarnings("unchecked") private static <T extends Throwable> RuntimeException rethrow(Throwable error)throws T{throw (T)error;}
    private static String bounded(String s){return s==null?"<null>":s.substring(0,Math.min(s.length(),4096));}
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static NativeObservationPort.ObservedFrame frame(String state,Instant observed) {
        String body="{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"memory-snapshot\",\"revision\":9,\"state\":"+state+"}";byte[] raw=bytes(body);
        var session=new NativeObservationPort.TransportSession(MACHINE,GAME,BigInteger.valueOf(5),SESSION);
        return new NativeObservationPort.ObservedFrame(session,"memory-snapshot",BigInteger.valueOf(9),new RawJson(bytes(state)),ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array(),observed);
    }
    private static final class Boundary extends RuntimeException {private static final long serialVersionUID=1L;Boundary(){super("actual-firstClock-boundary");}}
    private static final class MarkerClock extends Clock {
        final Boundary marker;int calls;MarkerClock(Boundary marker){this.marker=marker;}
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){assertEquals(ZoneOffset.UTC,zone);return this;}
        @Override public Instant instant(){calls++;throw marker;}
    }
    private static final class Denials implements InvocationHandler {
        int businessCalls;
        AssertionError fail(String label){businessCalls++;return new AssertionError("prefix must not reach afterclock dependency: "+label);}
        @Override public Object invoke(Object proxy,Method method,Object[] args) {
            if(method.getDeclaringClass()==Object.class){if(method.getName().equals("toString"))return "deny-only-prefix-port";if(method.getName().equals("hashCode"))return System.identityHashCode(proxy);if(method.getName().equals("equals"))return proxy==args[0];}
            throw fail(method.getDeclaringClass().getName()+"."+method.getName());
        }
        Object proxy(Class<?> type){assertTrue(type.isInterface());return Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},this);}
    }
    private static final class Side implements AutoCloseable {
        final String label;final CollectorLoader loader;final Constructor<?> constructor;final Method target;final Map<String,Object> metadata;Object collector;
        Side(String label,CollectorLoader loader,Constructor<?> constructor,Method target,Map<String,Object> metadata){this.label=label;this.loader=loader;this.constructor=constructor;this.target=target;this.metadata=metadata;}
        static Side open(String label,Path root)throws Throwable {
            long start=System.nanoTime();var loader=new CollectorLoader(root);
            try {
                var origins=new LinkedHashMap<String,Object>();
                for(String name:NAMES){Class<?> type=Class.forName(name,true,loader);assertSame(loader,type.getClassLoader());assertEquals(root,Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath());Path file=root.resolve(name.replace('.','/')+".class");origins.put(name,Map.of("bytes",Files.size(file),"SHA256",DriverJson.sha256(Files.readAllBytes(file))));}
                Class<?> type=loader.loadClass(COLLECTOR),work=loader.loadClass(COLLECTOR+"$PhysicalWork");
                Constructor<?> ctor=Arrays.stream(type.getConstructors()).filter(c->c.getParameterCount()==14).findFirst().orElseThrow();
                Method target=type.getDeclaredMethod("qualifyPhysical",ContinuityStorePort.Session.class,Instant.class,Instant.class,String.class,NativeObservationPort.ObservedFrame.class,DriverSnapshotFacts.Known.class,DriverObservationFacts.class,ExactRef.class,work);target.setAccessible(true);
                var m=new LinkedHashMap<String,Object>();m.put("root",root.toString());m.put("complete38",origins);m.put("load_link_init_origin_reflection_ns",System.nanoTime()-start);m.put("publicCtor_parameters",Arrays.stream(ctor.getParameterTypes()).map(Class::getName).toList());return new Side(label,loader,ctor,target,m);
            }catch(Throwable failure){try{loader.close();}catch(Throwable close){failure.addSuppressed(close);}throw failure;}
        }
        void bind(Fixture f)throws Throwable {
            Class<?>[] p=constructor.getParameterTypes();assertSame(SessionPorts.SessionIdentity.class,p[0]);assertSame(ContinuityStorePort.class,p[1]);assertSame(NativeGameTransport.class,p[2]);assertSame(DriverStateAssembler.class,p[3]);assertSame(DriverObservationAssembler.class,p[4]);
            var verifier=new NativeSemanticEvidenceVerifier((same,ref,max)->{throw f.denials.fail("verifier");});
            Object[] args={new SessionPorts.SessionIdentity(MACHINE,GAME,SESSION),f.store,f.transport,f.driver,new DriverObservationAssembler(),f.denials.proxy(p[5]),f.denials.proxy(p[6]),verifier,f.denials.proxy(p[8]),f.denials.proxy(p[9]),f.denials.proxy(p[10]),new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(73)),Duration.ZERO,false),Duration.ofSeconds(30),f.clock};
            try{collector=constructor.newInstance(args);}catch(InvocationTargetException wrapped){throw wrapped.getCause();}assertEquals(0,f.denials.businessCalls);
        }
        void invoke(ContinuityStorePort.Session same,Instant deadline,String head,NativeObservationPort.ObservedFrame actual,DriverSnapshotFacts.Known known,DriverObservationFacts facts,ExactRef original)throws Throwable {
            try{target.invoke(collector,same,deadline,deadline,head,actual,known,facts,original,null);}catch(InvocationTargetException wrapped){throw wrapped.getCause();}
        }
        @Override public void close()throws IOException{collector=null;loader.close();}
    }
    private static final class CollectorLoader extends URLClassLoader {
        CollectorLoader(Path root)throws Exception{super(new URL[]{root.toUri().toURL()},ReadinessDiagnosticPrefix163Test.class.getClassLoader());}
        @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException {
            if(!NAMES.contains(name))return super.loadClass(name,resolve);
            synchronized(getClassLoadingLock(name)){Class<?> type=findLoadedClass(name);if(type==null)type=findClass(name);if(resolve)resolveClass(type);return type;}
        }
    }
    /** Full-input-budget DATA adapter composed from the existing memory test's real public Driver/Reader producers. */
    private static final class Fixture implements AutoCloseable {
        final String name;final Instant deadline=Instant.now().plusSeconds(30);final MemoryStore store=new MemoryStore();final QuietPackets packets=new QuietPackets();
        final Boundary marker=new Boundary();final MarkerClock clock=new MarkerClock(marker);final Denials denials=new Denials();
        final Map<ExactRef,byte[]> originals=new HashMap<>();final DriverFactsRepository repository;final DriverStateAssembler driver;final NativeGameTransport transport;final G2Source source;
        final NativeObservationPort.ObservedFrame actual;final ExactRef original;final String packetSha,stateSha;
        Fixture(String name,String state)throws IOException {
            this.name=name;actual=frame(state,Instant.now());packetSha=DriverJson.sha256(actual.originalPacket());stateSha=DriverJson.sha256(actual.state().bytes());original=material(actual.originalPacket());
            var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\pure-prefix-diagnostic-DATA",MACHINE,GAME,SESSION,"memory","0".repeat(64),"memory");transport=NativeTransportReplayTestFactory.create(packets,config,32,16);
            var auxiliary=new Obj(Map.of("capability_session_paths",new Obj(Map.of("queue_dir",Nil.INSTANCE,"driver_state_path",Nil.INSTANCE)),"driver_state_restored",new Bool(false),"driver_state_error",Nil.INSTANCE,"restore_kind",new Text("new_episode"),"episode_binding_state",new Text("active_new"),"cold_candidate_rejection",Nil.INSTANCE,"episode_transition_error",Nil.INSTANCE));
            var known=DriverFactsRepository.imported(material(bytes(WIRE)),bytes(WIRE),3,7,GAME,auxiliary);repository=new DriverFactsRepository(known);var journal=new Journal(store,known.originalHistoryBasis());
            source=new G2Source(MACHINE,"2026-10-29T18:00:00Z","retained-memory",material(bytes("memory source")));
            driver=new DriverStateAssembler(new ActionSnapshotReader(journal),repository,observed->repository.locked(stateKnown->new DriverObservationFacts.Known(produce((DriverSnapshotFacts.Known)stateKnown,observed))));
        }
        DriverObservationFacts produce(DriverSnapshotFacts.Known known,NativeObservationPort.ObservedFrame observed) {
            var extra=new Obj(Map.of("backend_id",new Text("native-headless"),"source",new Text("injected-dll-named-pipe"),"diagnostics",DriverJson.object(observed.state().bytes(),DriverJson.MAX_NATIVE_BYTES).get("diagnostics")));
            var full=material(known.driver().encode());var manifest=DriverObservationEvidenceReader.encode(known,observed,BigInteger.TWO,1,source,extra,full);var ref=material(manifest.bytes());
            return DriverObservationEvidenceReader.decode(ref,manifest,new RawJson(known.driver().encode()),observed);
        }
        ExactRef material(byte[] raw){var ref=new ExactRef("D:/test-memory/prefix163/"+DriverJson.sha256(raw)+".json",raw.length,DriverJson.sha256(raw));originals.putIfAbsent(ref,raw.clone());return ref;}
        void assertOriginals(){assertEquals(packetSha,DriverJson.sha256(actual.originalPacket()));assertEquals(stateSha,DriverJson.sha256(actual.state().bytes()));}
        Map<String,Object> description(){return Map.of("input",name,"state_bytes",actual.state().bytes().length,"packet_bytes",actual.originalPacket().length,"packet_SHA256",packetSha,"state_SHA256",stateSha,"observed_at",actual.observedAt().toString());}
        @Override public void close()throws IOException{transport.close();assertTrue(packets.closed);}
    }
    private static final class MemoryStore implements ContinuityStorePort {
        final WriterContracts.Head head=head();Thread owner;boolean active;
        final Session session=new Session(){
            @Override public WriterContracts.Head head(){requireSession(this);return head;}
            @Override public void requireWriter(Path lock){throw new AssertionError("no physical writer in prefix DATA");}
            @Override public WriterContracts.Pin capturePin(ExactRef ref,int max){throw new AssertionError("no physical pin in prefix DATA");}
            @Override public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("no physical pin in prefix DATA");}
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("prefix cannot preview");}
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("prefix cannot commit");}
            @Override public ExactRef persistedHead(){throw new AssertionError("no persisted memory head");}
        };
        static WriterContracts.Head head(){String raw="{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\""+MACHINE+"\",\"sequence\":0,\"window_id\":1,\"start_date_raw\":53144328,\"target_date_raw\":53144352,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":53144328}";return new WriterContracts.Head(ContinuityState.fromJson(ContinuityJson.parseObject(bytes(raw),65536),MACHINE),List.of(),List.of(),List.of(),false);}
        @Override public void requireSession(Session same){StrictJson.require(active&&owner==Thread.currentThread()&&same==session,"actual original memory writer Session required");}
        @Override public <T>T locked(SessionWork<T> work)throws IOException{assertFalse(active);active=true;owner=Thread.currentThread();try{return work.run(session);}finally{active=false;owner=null;}}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("no preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("no commit");}
        @Override public ExactRef persistedHead(){throw new AssertionError("no persisted memory head");}
    }
    private static final class Journal implements ActionJournal {
        final MemoryStore store;final ExactRef basis;Journal(MemoryStore store,ExactRef basis){this.store=store;this.basis=basis;}
        @Override public <T>T locked(Function<LockedJournal,T> work){return locked(store.session,work);}
        @Override public <T>T locked(ContinuityStorePort.Session same,Function<LockedJournal,T> work){store.requireSession(same);return work.apply(new LockedJournal(){
            @Override public ContinuityStorePort.Session writerSession(){return same;}
            @Override public Optional<ActionReceipt> find(String id){return Optional.empty();}
            @Override public List<ActionReceipt> unresolved(){return List.of();}
            @Override public ActionReceipt append(ActionCommand command,String sha,ActionState state){throw new AssertionError("no action write");}
            @Override public Snapshot snapshot(){return new Snapshot(store.head.state().sequence(),store.head.digest(),List.of(),new BoundHistoryBasis(basis));}
        });}
    }
    private static final class QuietPackets implements NativePacketPort {
        int reads,writes;boolean closed;
        @Override public void verify()throws IOException{if(closed)throw new IOException("memory packet source closed");}
        @Override public void awaitConnection(Instant until){throw new AssertionError("prefix cannot open connection");}
        @Override public byte[] readPacket(Instant until){reads++;throw new AssertionError("prefix cannot receive");}
        @Override public void writePacket(byte[] packet,Instant until){writes++;throw new AssertionError("prefix cannot dispatch");}
        @Override public void close(){closed=true;}
    }
}
