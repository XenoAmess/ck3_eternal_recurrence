package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public archived semantic replay only: map-backed originals and a read-only Head grant no live permission. */
final class SemanticDriverReuse366Test {
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    private static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained","bridge_pid":42,"connection_generation":5}}
        """;
    private record Originals(DriverObservationAssembler.Complete frame, SessionPorts.SemanticEvidence evidence,
            Map<ExactRef,byte[]> bytes, DriverStateSnapshot.Complete driver,
            RawJson manifest, ExactRef manifestRef, NativeObservationPort.ObservedFrame nativeFrame) { }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) {
        return new ExactRef(Path.of("target","semantic-driver366",DriverJson.sha256(raw)+".bin").toAbsolutePath().toString(),
                raw.length,DriverJson.sha256(raw));
    }
    private static Originals originals(long version,boolean wide) { return originals(version,wide,STATE); }
    private static Originals originals(long version,boolean wide,String retainedState) {
        String driverText=wide?DRIVER.replace("\"last_checkpoint\":null","\"last_checkpoint\":{\"opaque\":"+"7".repeat(4301)+"}"):DRIVER;
        var driver=DriverStateSnapshot.decodeComplete(bytes(driverText));
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        String state=retainedState.strip();
        byte[] payload=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",game,BigInteger.valueOf(5),"held-session"),
                "snapshot-9",BigInteger.valueOf(9),new RawJson(bytes(state)),packet,Instant.parse("2026-10-23T16:00:00Z"));
        var stamp=new DriverSnapshotFacts.Stamp(3,7,game,driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
        var auxiliary=new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign")));
        var driverRef=ref(driver.encode());
        var known=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),auxiliary,Optional.empty(),Optional.empty());
        var source=new G2Source("test-machine","2026-10-23T16:00:00Z","test-source",ref(bytes("original-source")));
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(2),version,source,auxiliary,driverRef);
        var manifestRef=ref(manifest.bytes());
        // The old public raw path constructs the independent original observation DATA, including wide material.
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(driver.encode()),actual);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,ref(packet)));
        var observed=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),auxiliary,Optional.empty(),Optional.of(facts));
        byte[] semantic=DriverJson.encode(complete.semantic()),stampBytes=NativeDriverStamp.encode(complete,observed);
        var semanticRef=ref(semantic);var stampRef=ref(stampBytes);var nativeRef=ref(packet);
        var originals=new HashMap<ExactRef,byte[]>();originals.put(driverRef,driver.encode());originals.put(manifestRef,manifest.bytes());
        originals.put(semanticRef,semantic);originals.put(stampRef,stampBytes);originals.put(nativeRef,packet);
        return new Originals(complete,new SessionPorts.SemanticEvidence(complete.identity(),semanticRef,nativeRef,stampRef,driverRef,actual.observedAt()),
                originals,driver,manifest,manifestRef,actual);
    }
    private static SessionPorts.SessionIdentity owner(Originals actual) {
        return new SessionPorts.SessionIdentity(actual.frame().identity().machineId(),actual.frame().identity().game(),actual.frame().sessionId());
    }

    @Test void sameCallCanonicalReplayKeepsWideMaterialAndDistinctOriginalReads() throws Exception {
        stageData139();
        for(long version:List.of(DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION,DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION)) {
            for(boolean wide:List.of(false,true)) {
                var actual=originals(version,wide);
                if(wide)assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.decodeTypedDriver(
                        actual.manifestRef(),actual.manifest(),actual.driver(),actual.nativeFrame()),"existing typed helper has a narrower numeric profile");
                for(boolean distinct:List.of(false,true)) {
                    var original=actual.evidence();
                    var originalDriver=distinct?new ExactRef(Path.of("target","semantic-driver366","distinct-driver.json").toAbsolutePath().toString(),
                            original.originalDriver().bytes(),original.originalDriver().sha256()):original.originalDriver();
                    var evidence=new SessionPorts.SemanticEvidence(original.frame(),original.semantic(),original.originalNativePacket(),original.driverStamp(),originalDriver,original.observedAt());
                    var reads=new ArrayList<ExactRef>();var same=new ReadOnlyHead();
                    var verifier=new NativeSemanticEvidenceVerifier((borrowed,reference,maximum)->{
                        assertSame(same,borrowed);reads.add(reference);
                        return actual.bytes().get(reference.equals(originalDriver)?original.originalDriver():reference).clone();
                    });
                    var verified=verifier.verify(same,owner(actual),evidence);
                    assertEquals(actual.frame().identity(),verified.frame());assertEquals(actual.frame().observedAt(),verified.observedAt());
                    assertEquals(1,reads.stream().filter(originalDriver::equals).count());
                    assertEquals(1,reads.stream().filter(actual.manifestRef()::equals).count());
                    assertEquals(1,reads.stream().filter(original.originalDriver()::equals).count(),"different ref still has its real manifest Driver read");
                    assertEquals(distinct?6:5,reads.size(),"all five original reads plus any distinct Driver original remain");
                }
            }
        }
    }

    @Test void archiveMutationAndFailuresCannotReuseStaleDriverOrAuthority() throws Exception {
        fullFailureOracles139();
        var actual=originals(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,false);
        byte[] borrowedDriver=actual.bytes().get(actual.evidence().originalDriver()).clone();
        boolean[] changed={false};
        var mutating=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            if(reference.equals(actual.manifestRef())) { borrowedDriver[0]='!';changed[0]=true; }
            return reference.equals(actual.evidence().originalDriver())?borrowedDriver:actual.bytes().get(reference).clone();
        });
        assertThrows(IOException.class,()->mutating.verify(new ReadOnlyHead(),owner(actual),actual.evidence()));
        assertTrue(changed[0],"the later manifest callback actually changed the previously decoded borrowed bytes");

        var marker=new IOException("actual manifest original I/O marker");
        var unavailable=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            if(reference.equals(actual.manifestRef()))throw marker;
            return actual.bytes().get(reference).clone();
        });
        assertSame(marker,assertThrows(IOException.class,()->unavailable.verify(new ReadOnlyHead(),owner(actual),actual.evidence())));

        var changedHead=new ReadOnlyHead();
        var drifting=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            if(reference.equals(actual.manifestRef()))changedHead.changed=true;
            return actual.bytes().get(reference).clone();
        });
        var drift=assertThrows(IOException.class,()->drifting.verify(changedHead,owner(actual),actual.evidence()));
        assertTrue(drift.getMessage().contains("writer changed during same-lock semantic verification"));

        var badManifest=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            byte[] raw=actual.bytes().get(reference).clone();if(reference.equals(actual.manifestRef()))raw[0]^=1;return raw;
        });
        assertThrows(IOException.class,()->badManifest.verify(new ReadOnlyHead(),owner(actual),actual.evidence()));
    }
    private static final String READER139="org.xar.ck3.control.application.driver.DriverObservationEvidenceReader";
    private static final String VERIFIER139="org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier";
    /** Only the exact source-qualified d56 Reader3/Verifier2; shared DTOs and algorithms remain parent-owned. */
    private static final class OldSource139Loader extends java.net.URLClassLoader {
        private static final java.util.Set<String> FAMILY=java.util.Set.of(READER139,READER139+"$NativePacketInput",READER139+"$NativeFrameInput",VERIFIER139,VERIFIER139+"$ArtifactReader");
        OldSource139Loader()throws Exception {super(new java.net.URL[]{Path.of(java.util.Objects.requireNonNull(System.getProperty("ck3.p139.oldSourceRoot"),"explicit d56 source-qualified old root required")).toRealPath().toUri().toURL()},SemanticDriverReuse366Test.class.getClassLoader());}
        @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException {
            synchronized(getClassLoadingLock(name)) {
                if(!FAMILY.contains(name)) {
                    if(name.startsWith(READER139+"$")||name.startsWith(VERIFIER139+"$"))throw new ClassNotFoundException("unlisted source-qualified old family member "+name);
                    return getParent().loadClass(name);
                }
                Class<?> type=findLoadedClass(name);if(type==null)type=findClass(name);if(resolve)resolveClass(type);return type;
            }
        }
    }
    private static Map<String,Object> initialize139(OldSource139Loader old)throws Exception {
        long begin=System.nanoTime();Class<?> oldReader=Class.forName(READER139,true,old);Class.forName(VERIFIER139,true,old);long middle=System.nanoTime();
        Class<?> current=Class.forName(READER139,true,SemanticDriverReuse366Test.class.getClassLoader());Class.forName(VERIFIER139,true,SemanticDriverReuse366Test.class.getClassLoader());long end=System.nanoTime();
        assertSame(old,oldReader.getClassLoader());assertSame(DriverObservationEvidenceReader.class,current);assertNotSame(oldReader,current);
        return Map.of("old_class_initialization_ns",middle-begin,"parent_class_initialization_ns",end-middle,"old_code_source",oldReader.getProtectionDomain().getCodeSource().getLocation().toString(),"target_warmup_calls",0);
    }
    /** Both routes use the corresponding ArtifactReader Proxy and the same parent SemanticVerifier call. */
    private static org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SemanticVerifier verifier139(ClassLoader loader,
            NativeSemanticEvidenceVerifier.ArtifactReader reader)throws Exception {
        Class<?> verifier=Class.forName(VERIFIER139,true,loader),api=Class.forName(VERIFIER139+"$ArtifactReader",true,loader);
        Object proxy=java.lang.reflect.Proxy.newProxyInstance(loader,new Class<?>[]{api},(ignored,method,args)->{
            assertEquals("read",method.getName());assertNotNull(args);assertEquals(3,args.length);
            return reader.read((ContinuityStorePort.Session)args[0],(ExactRef)args[1],(Integer)args[2]);
        });
        return assertInstanceOf(org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SemanticVerifier.class,verifier.getConstructor(api).newInstance(proxy));
    }
    private static void assertFrame139(NativeObservationPort.ObservedFrame expected,NativeObservationPort.ObservedFrame actual) {
        assertEquals(expected.session(),actual.session());assertEquals(expected.snapshotId(),actual.snapshotId());assertEquals(expected.nativeRevision(),actual.nativeRevision());
        assertEquals(expected.observedAt(),actual.observedAt());assertArrayEquals(expected.state().bytes(),actual.state().bytes());assertArrayEquals(expected.originalPacket(),actual.originalPacket());
    }
    private static Object matching139(DriverObservationEvidenceReader.NativeBodyStage stage,byte[] stableBody)throws Exception {
        var method=stage.getClass().getDeclaredMethod("matchingBody",byte[].class);method.setAccessible(true);return method.invoke(stage,(Object)stableBody);
    }
    private static void released139(DriverObservationEvidenceReader.NativeBodyStage stage)throws Exception {
        for(var field:stage.getClass().getDeclaredFields()) {
            assertTrue(java.lang.reflect.Modifier.isPrivate(field.getModifiers()));field.setAccessible(true);assertNull(field.get(stage),"closed DATA stage drops owned references");
        }
    }
    private static void stageData139()throws Exception {
        assertTrue(java.lang.reflect.Modifier.isFinal(DriverObservationEvidenceReader.NativeBodyStage.class.getModifiers()));
        for(var constructor:DriverObservationEvidenceReader.NativeBodyStage.class.getDeclaredConstructors())assertTrue(java.lang.reflect.Modifier.isPrivate(constructor.getModifiers()));
        String precision=STATE.replace("\"speed\":3","\"speed\":3,\"precision139\":1.00,\"negative139\":-0.0,\"exponent139\":1e+0,\"unicode139\":\"😀\"");
        var actual=originals(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,false,precision);
        byte[] framed=actual.nativeFrame().originalPacket(),stableBody=java.util.Arrays.copyOfRange(framed,4,framed.length);
        var stage=DriverObservationEvidenceReader.stageNativeBody(framed);var first=stage.envelope();byte[] retained=DriverJson.encode(first);
        var parsedState=assertInstanceOf(OpportunityJson.Obj.class,first.get("state"));
        assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,parsedState.get("precision139")).token());
        assertEquals("-0.0",assertInstanceOf(OpportunityJson.DecimalValue.class,parsedState.get("negative139")).token());
        assertEquals("1e+0",assertInstanceOf(OpportunityJson.DecimalValue.class,parsedState.get("exponent139")).token());
        assertEquals("😀",assertInstanceOf(OpportunityJson.Text.class,parsedState.get("unicode139")).value());
        assertEquals(List.of("paused","map_ready","speed","precision139","negative139","exponent139","unicode139"),new ArrayList<>(parsedState.members().keySet()).subList(0,7));
        assertSame(first,matching139(stage,stableBody));
        java.util.Arrays.fill(framed,4,framed.length,(byte)'!');assertArrayEquals(retained,DriverJson.encode(stage.envelope()));
        assertThrows(UnsupportedOperationException.class,()->first.members().clear());
        var originalFrame=DriverObservationEvidenceReader.nativeFrame(actual.manifestRef(),actual.manifest(),actual.nativeFrame().originalPacket());
        assertFrame139(originalFrame,DriverObservationEvidenceReader.nativeFrame(actual.manifestRef(),actual.manifest(),actual.nativeFrame().originalPacket(),stage));
        for(String state:List.of(precision.replace("\"speed\":3","\"speed\":4"),precision.replace("\"speed\":3","\"speed\" : 3"))) {
            var other=originals(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,false,state);
            byte[] late=other.nativeFrame().originalPacket(),borrowedAgain=late.clone(),body=java.util.Arrays.copyOfRange(borrowedAgain,4,borrowedAgain.length);
            assertNull(matching139(stage,body),"even structurally equal but different wire cannot reuse a parse");
            if(state.contains("\"speed\" : 3")) { assertEquals(first,DriverJson.object(body,DriverJson.MAX_NATIVE_BYTES));assertFalse(java.util.Arrays.equals(stableBody,body)); }
            // Actual A -> B(body copy) -> A storage restoration; the candidate still compares the retained stable B copy.
            byte[] originalAgain=actual.nativeFrame().originalPacket();
            if(borrowedAgain.length==originalAgain.length) {System.arraycopy(originalAgain,0,borrowedAgain,0,originalAgain.length);assertArrayEquals(originalAgain,borrowedAgain);assertNull(matching139(stage,body));}
            var expected=DriverObservationEvidenceReader.nativeFrame(other.manifestRef(),other.manifest(),late);
            assertFrame139(expected,DriverObservationEvidenceReader.nativeFrame(other.manifestRef(),other.manifest(),late,stage));
            assertFrame139(expected,DriverObservationEvidenceReader.nativeFrame(other.manifestRef(),other.manifest(),late,null));
        }
        stage.close();stage.close();released139(stage);assertNull(matching139(stage,stableBody));
        assertThrows(IllegalStateException.class,stage::envelope);assertArrayEquals(retained,DriverJson.encode(first));
        assertFrame139(originalFrame,DriverObservationEvidenceReader.nativeFrame(actual.manifestRef(),actual.manifest(),actual.nativeFrame().originalPacket(),stage));
        var failed=DriverObservationEvidenceReader.stageNativeBody(actual.nativeFrame().originalPacket());
        try(failed) {
            byte[] changed=actual.nativeFrame().originalPacket();changed[4]='!';
            var error=assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.nativeFrame(actual.manifestRef(),actual.manifest(),changed,failed));
            assertEquals("archived native framing/manifest differs",error.getMessage());
        }
        released139(failed);
        // Early parse domain stays wider than later physical/native schema lanes; this is not source admission.
        byte[] wide=org.xar.ck3.control.nativebridge.NativeWire.packet(bytes("{\"opaque\":"+"7".repeat(4301)+"}"));
        try(var value=DriverObservationEvidenceReader.stageNativeBody(wide)) {
            assertEquals(4301,assertInstanceOf(OpportunityJson.IntegerValue.class,value.envelope().get("opaque")).value().toString().length());
        }
    }
    private static Originals replaced139(Originals original,byte[] semantic,byte[] nativePacket,byte[] stamp,byte[] driver) {
        var e=original.evidence();var all=new HashMap<ExactRef,byte[]>(original.bytes());
        var sr=semantic==null?e.semantic():ref(semantic);var nr=nativePacket==null?e.originalNativePacket():ref(nativePacket);
        var tr=stamp==null?e.driverStamp():ref(stamp);var dr=driver==null?e.originalDriver():ref(driver);
        if(semantic!=null)all.put(sr,semantic);if(nativePacket!=null)all.put(nr,nativePacket);if(stamp!=null)all.put(tr,stamp);if(driver!=null)all.put(dr,driver);
        var evidence=new SessionPorts.SemanticEvidence(e.frame(),sr,nr,tr,dr,e.observedAt());
        return new Originals(original.frame(),evidence,all,original.driver(),original.manifest(),original.manifestRef(),original.nativeFrame());
    }
    private static void sameError139(IOException expected,IOException actual) {
        assertEquals(expected.getClass(),actual.getClass());assertEquals(expected.getMessage(),actual.getMessage());
        assertEquals(expected.getCause()==null,actual.getCause()==null);
        if(expected.getCause()!=null){assertEquals(expected.getCause().getClass(),actual.getCause().getClass());assertEquals(expected.getCause().getMessage(),actual.getCause().getMessage());}
    }
    private static IOException earlyFailure139(ClassLoader loader,Originals actual)throws Exception {
        var reads=new ArrayList<ExactRef>();var head=new ReadOnlyHead();String before=head.head().digest();
        var verifier=verifier139(loader,(same,reference,maximum)->{assertSame(head,same);reads.add(reference);return actual.bytes().get(reference).clone();});
        var error=assertThrows(IOException.class,()->verifier.verify(head,owner(actual),actual.evidence()));
        assertEquals(List.of(actual.evidence().semantic(),actual.evidence().originalNativePacket(),actual.evidence().driverStamp(),actual.evidence().originalDriver()),reads);
        assertEquals(before,head.head().digest());return error;
    }
    private static IOException nativeMutation139(ClassLoader loader,Originals actual,ExactRef trigger)throws Exception {
        byte[] borrowedNative=actual.nativeFrame().originalPacket();boolean[] changed={false};var reads=new ArrayList<ExactRef>();
        var verifier=verifier139(loader,(same,reference,maximum)->{
            reads.add(reference);if(reference.equals(trigger)){borrowedNative[4]='!';changed[0]=true;}
            return reference.equals(actual.evidence().originalNativePacket())?borrowedNative:actual.bytes().get(reference).clone();
        });
        var error=assertThrows(IOException.class,()->verifier.verify(new ReadOnlyHead(),owner(actual),actual.evidence()));
        assertTrue(changed[0]);assertEquals(trigger.equals(actual.manifestRef())?5:4,reads.size());
        assertEquals(trigger.equals(actual.manifestRef()),reads.contains(actual.manifestRef()));
        if(trigger.equals(actual.manifestRef()))assertTrue(error.getMessage().contains("archived native framing/manifest differs"));
        return error;
    }
    private static void fullFailureOracles139()throws Exception {
        try(var old=new OldSource139Loader()) {
            initialize139(old);ClassLoader current=SemanticDriverReuse366Test.class.getClassLoader();
            var actual=originals(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,false);
            for(var trigger:List.of(actual.evidence().driverStamp(),actual.evidence().originalDriver(),actual.manifestRef()))sameError139(nativeMutation139(old,actual,trigger),nativeMutation139(current,actual,trigger));
            byte[] malformed=bytes("{"),badNative=org.xar.ck3.control.nativebridge.NativeWire.packet(malformed);
            byte[] packet=actual.nativeFrame().originalPacket();String body=new String(packet,4,packet.length-4,StandardCharsets.UTF_8);
            byte[] badHeader=org.xar.ck3.control.nativebridge.NativeWire.packet(bytes(body.replace("\"protocol_version\":1","\"protocol_version\":2")));
            byte[] badLength=packet.clone();badLength[0]^=1;
            byte[] stamp=actual.bytes().get(actual.evidence().driverStamp());byte[] badSchema=bytes(new String(stamp,StandardCharsets.UTF_8).replace(NativeDriverStamp.SCHEMA,"wrong-schema139"));
            assertFalse(java.util.Arrays.equals(stamp,badSchema));
            for(var invalid:List.of(replaced139(actual,malformed,badNative,null,malformed),replaced139(actual,null,badNative,malformed,malformed),
                    replaced139(actual,null,badNative,null,malformed),replaced139(actual,null,badHeader,null,malformed),
                    replaced139(actual,null,badNative,badSchema,null),replaced139(actual,null,badHeader,null,null),replaced139(actual,null,badLength,null,malformed))) {
                sameError139(earlyFailure139(old,invalid),earlyFailure139(current,invalid));
            }
            var marker=new IOException("same original manifest callback marker139");
            for(ClassLoader route:List.of(old,current)) {
                var verifier=verifier139(route,(same,reference,maximum)->{if(reference.equals(actual.manifestRef()))throw marker;return actual.bytes().get(reference).clone();});
                assertSame(marker,assertThrows(IOException.class,()->verifier.verify(new ReadOnlyHead(),owner(actual),actual.evidence())));
            }
        }
    }

    @org.junit.jupiter.api.io.TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) Path directory139;
    /** Full production verify, map-backed original callbacks; source-qualified oldA, not current build307 binary equivalence. */
    @Test void sameOriginalsCompareSourceQualifiedOldVerifierAndOwnedBodyStage139()throws Throwable {
        long startWindow=System.nanoTime();var report=new java.util.LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();report.put("rows",rows);Throwable failed=null;
        report.put("schema","ck3.p139.full-semantic-verify-component/v1");report.put("scenario","native_campaign_v4_large_pretty_originals");
        report.put("fixed_order",List.of("A","B","B","A"));report.put("target_warmups",0);report.put("current_C_old_binary_equivalence",false);
        report.put("archive_kind","map-backed DATA original callbacks and read-only Head; not physicalIO/Game/authority");
        report.put("adapters","Both corresponding ArtifactReader Proxy plus common parent SemanticVerifier interface call; construction/init in setup.");
        try(var old=new OldSource139Loader()) {
            report.put("class_initialization",initialize139(old));report.put("old_root",System.getProperty("ck3.p139.oldSourceRoot"));
            String state=STATE.replace("\"diagnostics\":","\"opaque139\":\""+"x".repeat(3_400_000)+"\",\"diagnostics\":");
            var actual=originals(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,false,state);
            var expectedReads=List.of(actual.evidence().semantic(),actual.evidence().originalNativePacket(),actual.evidence().driverStamp(),actual.evidence().originalDriver(),actual.manifestRef());
            var inputHashes=new java.util.LinkedHashMap<String,String>();for(var reference:expectedReads)inputHashes.put(reference.path(),DriverJson.sha256(actual.bytes().get(reference)));
            report.put("input_sha256",inputHashes);report.put("native_packet_bytes",actual.evidence().originalNativePacket().bytes());report.put("semantic_bytes",actual.evidence().semantic().bytes());
            var head=new ReadOnlyHead();String headBefore=head.head().digest();var reads=new ArrayList<ExactRef>();
            NativeSemanticEvidenceVerifier.ArtifactReader archive=(same,reference,maximum)->{assertSame(head,same);reads.add(reference);return actual.bytes().get(reference).clone();};
            var a=verifier139(old,archive);var b=verifier139(SemanticDriverReuse366Test.class.getClassLoader(),archive);
            var cpu=java.lang.management.ManagementFactory.getThreadMXBean();boolean cpuAvailable=cpu.isCurrentThreadCpuTimeSupported();if(cpuAvailable&&!cpu.isThreadCpuTimeEnabled())cpu.setThreadCpuTimeEnabled(true);
            com.sun.management.ThreadMXBean allocation=cpu instanceof com.sun.management.ThreadMXBean bean?bean:null;
            boolean allocAvailable=allocation!=null&&allocation.isThreadAllocatedMemorySupported();if(allocAvailable&&!allocation.isThreadAllocatedMemoryEnabled())allocation.setThreadAllocatedMemoryEnabled(true);
            report.put("CPU_available",cpuAvailable);report.put("allocation_available",allocAvailable);report.put("setup_ns_before_rows",System.nanoTime()-startWindow);
            org.xar.ck3.control.application.session.OrdinaryCycleTransitions.VerifiedSemantic expected=null;
            for(int index=0;index<4;index++) {
                String entry=index==0||index==3?"A":"B";reads.clear();var row=new java.util.LinkedHashMap<String,Object>();rows.add(row);row.put("index",index);row.put("entry",entry);
                long cpuStart=cpuAvailable?cpu.getCurrentThreadCpuTime():-1,allocatedStart=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1;
                long begin=System.nanoTime();org.xar.ck3.control.application.session.OrdinaryCycleTransitions.VerifiedSemantic verified;boolean completed=false;
                try{verified=(entry.equals("A")?a:b).verify(head,owner(actual),actual.evidence());completed=true;}
                finally{long end=System.nanoTime(),allocatedEnd=allocAvailable?allocation.getThreadAllocatedBytes(Thread.currentThread().threadId()):-1,cpuEnd=cpuAvailable?cpu.getCurrentThreadCpuTime():-1;
                    row.put("wall_start_ns",begin);row.put("wall_end_ns",end);row.put("wall_ns",end-begin);row.put("CPU_start_ns",cpuStart);row.put("CPU_end_ns",cpuEnd);row.put("CPU_ns",cpuAvailable?cpuEnd-cpuStart:-1);
                    row.put("allocation_start_bytes",allocatedStart);row.put("allocation_end_bytes",allocatedEnd);row.put("thread_allocated_bytes",allocAvailable?allocatedEnd-allocatedStart:-1);row.put("completed",completed);}
                assertEquals(expectedReads,reads);assertEquals(headBefore,head.head().digest());if(expected==null)expected=verified;assertEquals(expected,verified);
                assertEquals(actual.frame().identity(),verified.frame());assertEquals(actual.frame().observedAt(),verified.observedAt());
                for(var reference:expectedReads)assertEquals(inputHashes.get(reference.path()),DriverJson.sha256(actual.bytes().get(reference)));
                row.put("read_ref_SHA_order",reads.stream().map(ExactRef::sha256).toList());row.put("verified_record",verified.toString());row.put("head_digest",headBefore);row.put("all_post_checks_passed",true);
            }
        }catch(Throwable failure){failed=failure;report.put("failure_class",failure.getClass().getName());report.put("failure_message",String.valueOf(failure.getMessage()));throw failure;}
        finally{
            report.put("completed",failed==null);report.put("window_ns_before_report_materialization",System.nanoTime()-startWindow);
            report.put("limits","Two samples per entry/one v4 large scenario; full verify plus actual callback clones/hash/parse/guards/result. Stage body/Obj liveness, O(n) compare and synchronization included. Cumulative allocation is not live/peak heap; OS peak for this mixed JVM cannot be attributed per variant. No extra target warmup, no worker/physicalIO/Runtime speed or old C provenance claim.");
            try{byte[] raw=org.xar.ck3.control.contracts.FullJsonTree.encode(new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(report),1_048_576);
                var output=directory139.resolve("p139-semantic-verify-component.json");java.nio.file.Files.write(output,raw,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE);System.out.println("P139 full verify report "+output);
            }catch(Throwable outputFailure){if(failed==null)throw outputFailure;if(failed!=outputFailure)failed.addSuppressed(outputFailure);}
        }
    }

    private static final class ReadOnlyHead implements ContinuityStorePort.Session {
        private final WriterContracts.Head head=head(0),next=head(1);boolean changed;
        private static WriterContracts.Head head(int sequence) {
            byte[] raw=bytes("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"test-machine\",\"sequence\":"+sequence+",\"window_id\":1,\"start_date_raw\":0,\"target_date_raw\":24,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":0}");
            return new WriterContracts.Head(ContinuityState.fromJson(ContinuityJson.parseObject(raw,65536),"test-machine"),List.of(),List.of(),List.of(),false);
        }
        @Override public WriterContracts.Head head(){return changed?next:head;}
        @Override public void requireWriter(Path lock){throw new AssertionError("DATA test grants no writer");}
        @Override public WriterContracts.Pin capturePin(ExactRef reference,int maximum){throw new AssertionError("DATA test grants no pin");}
        @Override public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("DATA test grants no pin");}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("verifier cannot preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("verifier cannot commit");}
        @Override public ExactRef persistedHead(){throw new AssertionError("DATA test has no physical head");}
    }
}
