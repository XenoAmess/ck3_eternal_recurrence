package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.MessageDigestSpi;
import java.security.Provider;
import java.security.Security;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.Isolated;
import org.junit.jupiter.api.parallel.ResourceLock;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** NONBLIND public-entry prefix witnesses. No CK3, successful adoption or SAVE is claimed. */
@EnabledOnOs(OS.WINDOWS)
@Isolated("Temporarily installs a delegating public SHA-256 provider")
@ResourceLock("java.security.Security.providers")
public final class RestoreCapabilityAdoptionPublicPrefixWitnessTest {
    @TempDir Path root;
    private static final Instant TIME=Instant.parse("2026-10-23T16:00:00Z");

    @Test void lengthFailureRunsNoShaAndStopsBeforeAnyLaterMaterial() throws Exception {
        try (Harness h=harness()) {
            Data d=data(h.writer());
            ExactRef bad=new ExactRef(d.evidence().semantic().path(),d.evidence().semantic().bytes()+1,d.evidence().semantic().sha256());
            d.archive().replaceSemantic(bad);
            h.writer().locked(same->{
                same.head();
                try (DigestProbe ignored=new DigestProbe()) {
                    var failure=assertThrows(IllegalArgumentException.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.withSemantic(bad),d.saved()));
                    assertEquals("original restore capability material differs",failure.getMessage());
                    assertEquals(0,DigestProbe.digests.get());
                }
                assertEquals(List.of("bind","semantic"),d.archive().calls);
                assertEquals(2,d.archive().identityChecks);
                return null;
            });
        }
    }

    @Test void matchingLengthStillHashesAndRejectsWrongDigest() throws Exception {
        try (Harness h=harness()) {
            Data d=data(h.writer());
            ExactRef bad=new ExactRef(d.evidence().semantic().path(),d.evidence().semantic().bytes(),"0".repeat(64));
            d.archive().replaceSemantic(bad);
            h.writer().locked(same->{
                same.head();
                try (DigestProbe ignored=new DigestProbe()) {
                    var failure=assertThrows(IllegalArgumentException.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.withSemantic(bad),d.saved()));
                    assertEquals("original restore capability material differs",failure.getMessage());
                    assertEquals(1,DigestProbe.digests.get());
                }
                assertEquals(List.of("bind","semantic"),d.archive().calls);
                return null;
            });
        }
    }

    @Test void everyPublicReplayReopensMaterialsAndRechecksActualSessionBeforeNativeCallback() throws Exception {
        try (Harness h=harness()) {
            Data d=data(h.writer());
            h.writer().locked(same->{
                same.head();
                for(int attempt=0;attempt<2;attempt++)
                    assertSame(d.archive().atNative,assertThrows(Marker.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.evidence(),d.saved())));
                assertEquals(List.of("bind","semantic","state","manifest","driver","native",
                        "bind","semantic","state","manifest","driver","native"),d.archive().calls);
                assertEquals(12,d.archive().identityChecks);
                return null;
            });
        }
    }

    @Test void differentSavedDriverFailsBeforeNativeCallback() throws Exception {
        try (Harness h=harness()) {
            Data d=data(h.writer());
            var different=driver(BigInteger.valueOf(74));
            h.writer().locked(same->{
                same.head();
                var failure=assertThrows(IllegalArgumentException.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.evidence(),different));
                assertEquals("capability replay cannot borrow another saved Driver",failure.getMessage());
                assertEquals(List.of("bind","semantic","state","manifest","driver"),d.archive().calls);
                assertEquals(5,d.archive().identityChecks);
                return null;
            });
        }
    }

    @Test void secondReplayCannotReuseTheFirstMaterialQualification() throws Exception {
        try (Harness h=harness()) {
            Data d=data(h.writer());
            h.writer().locked(same->{
                same.head();
                assertSame(d.archive().atNative,assertThrows(Marker.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.evidence(),d.saved())));
                d.archive().rejectSemantic=true;
                assertSame(d.archive().changedCurrent,assertThrows(Marker.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.evidence(),d.saved())));
                assertEquals(List.of("bind","semantic","state","manifest","driver","native","bind","semantic"),d.archive().calls);
                assertEquals(8,d.archive().identityChecks);
                return null;
            });
        }
    }

    @Test void foreignSavedEncodeStillExecutesOnEveryPublicReplayBeforeNativeCallback() throws Exception {
        try (Harness h=harness()) {
            Data d=data(h.writer());
            ProbeInteger actor=new ProbeInteger(d.archive().calls);
            var foreign=driver(actor);
            actor.armed=true;
            h.writer().locked(same->{
                same.head();
                for(int attempt=0;attempt<2;attempt++) {
                    actor.reported=false;
                    RuntimeException failure=assertThrows(RuntimeException.class,()->new RestoreCapabilityAdoption(d.archive()).replay(same,d.evidence(),foreign));
                    assertTrue(hasCause(failure,actor.failure),"actual foreign encoding failure must remain visible");
                }
                assertEquals(2,actor.observations);
                assertEquals(List.of("bind","semantic","state","manifest","driver","saved-encode",
                        "bind","semantic","state","manifest","driver","saved-encode"),d.archive().calls);
                assertEquals(10,d.archive().identityChecks);
                return null;
            });
        }
    }

    private record Harness(ContinuityWriter writer,StorageWriteGuard guard) implements AutoCloseable {
        @Override public void close() throws IOException {guard.close();}
    }

    private Harness harness() throws Exception {
        Path directory=Files.createTempDirectory(root,"readonly-writer-");
        // Closed DATA copied from WriterFixture.state(), validated by the actual public reader.
        var state=ContinuityJson.parseObject(bytes("""
            {"schema":"root.ck3.continuity-window/v1","machine_id":"test-machine","sequence":0,"window_id":1,
             "status":"running","target_days":10958,"target_years":30,"calendar_year_days":365.25,
             "start_date_raw":1000,"target_date_raw":263992,"last_settled_date_raw":1000,"last_settled_cycles":1,
             "manual_repair_count":1,"automatic_recovery_count":0,"binding_lineage_count":0,
             "game_binding":{"pid":123,"creation_date":"2026-10-23T01:00:00Z"},"latest_binding":null,
             "pending_cycle":{"stage":"auto_unsettled","auto_sequence":11558},"NEXT":11559}
            """),ContinuityJson.LEDGER_MAX_BYTES);
        byte[] ledger=ContinuityState.fromJson(state,"test-machine").canonicalBytes();
        Path snapshot=directory.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=directory.resolve("anchor.json");
        Files.write(snapshot,ledger);Files.write(anchor,ledger);
        Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Files.write(directory.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);
        Path source=directory.resolve("source.txt");Files.writeString(source,"public restore prefix witness");
        var layout=new WriterContracts.Layout(snapshot,ref(anchor,ledger),"test-machine");
        StorageWriteGuard guard=StorageWriteGuard.noWrites();
        var authority=new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState before,WriterContracts.Request request) {throw new AssertionError("no write preview");}
            @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request) {throw new AssertionError("no reduction");}
        };
        return new Harness(ContinuityWriter.readOnlyExisting(layout,List.of(ref(source,Files.readAllBytes(source))),authority,
                Clock.systemUTC(),ContinuityWriter.Extensions.none(),guard),guard);
    }

    private record Data(Archive archive,SemanticEvidence evidence,DriverStateSnapshot.Complete saved) {
        SemanticEvidence withSemantic(ExactRef semantic) {return new SemanticEvidence(evidence.frame(),semantic,evidence.originalNativePacket(),evidence.driverStamp(),evidence.originalDriver(),evidence.observedAt());}
    }

    private Data data(ContinuityWriter writer) {
        Archive archive=new Archive(writer);
        var saved=driver(BigInteger.valueOf(73));
        RawJson fullDriver=RawJson.fullMaterial(saved.encode());ExactRef driverRef=archive.put("driver",fullDriver);
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var stamp=new DriverSnapshotFacts.Stamp(3,7,game,"episode-real-1",driverRef.sha256());
        var known=new DriverSnapshotFacts.Known(saved,stamp,driverRef,List.of(),new Obj(Map.of()),Optional.empty(),Optional.empty());
        var transport=new NativeObservationPort.TransportSession("test-machine",game,BigInteger.valueOf(5),"held-session");
        var top=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","snapshot-9").put("revision",9);
        top.set("state",StrictJson.object());byte[] body=StrictJson.canonical(top);
        byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var actual=new NativeObservationPort.ObservedFrame(transport,"snapshot-9",BigInteger.valueOf(9),new RawJson(bytes("{}")),packet,TIME);
        var source=new G2Source("test-machine",TIME.toString(),"test-source",ref(root.resolve("source-data.json"),bytes("{}")));
        ExactRef manifest=archive.put("manifest",DriverObservationEvidenceReader.encode(known,actual,BigInteger.TWO,1,source,new Obj(Map.of()),driverRef));
        ExactRef state=archive.put("state",new RawJson(bytes("{}")));
        var exported=new Obj(Map.of(DriverCapabilityStateProducer.STATE_SOURCE,DriverObservationEvidenceReader.reference(state),
                "java_driver_facts_evidence",DriverObservationEvidenceReader.reference(manifest)));
        ExactRef semantic=archive.put("semantic",RawJson.fullMaterial(DriverJson.encode(exported)));
        ExactRef nativeRef=ref(root.resolve("native.packet"),packet),driverStamp=archive.put("stamp",new RawJson(bytes("{}")));
        archive.expectedNative=nativeRef;
        var identity=new ObservationIdentity("test-machine",game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(9),BigInteger.valueOf(53144328)),"snapshot-9",BigInteger.TWO,"episode-real-1"),1);
        return new Data(archive,new SemanticEvidence(identity,semantic,nativeRef,driverStamp,driverRef,TIME),saved);
    }

    private static DriverStateSnapshot.Complete driver(BigInteger actor) {
        var nil=new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("test-pipe",42,actor,"episode-real-1"),List.of(),nil,nil,nil,nil,nil,nil,nil);
    }
    private static byte[] bytes(String text) {return text.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(Path path,byte[] raw) {return new ExactRef(path.toAbsolutePath().toString(),raw.length,DriverJson.sha256(raw));}
    private static final class Marker extends RuntimeException {private static final long serialVersionUID=1L;Marker(String name){super(name);}}
    private static boolean hasCause(Throwable actual,Throwable expected) {
        for(int depth=0;actual!=null&&depth<12;depth++,actual=actual.getCause())if(actual==expected)return true;
        return false;
    }
    private static final class ProbeInteger extends BigInteger {
        private static final long serialVersionUID=1L;
        final transient List<String> calls;final Marker failure=new Marker("actual Saved encode");boolean armed,reported;int observations;
        ProbeInteger(List<String> calls){super("73");this.calls=calls;}
        private void failIfArmed(){if(armed){if(!reported){calls.add("saved-encode");observations++;reported=true;}throw failure;}}
        @Override public String toString(){failIfArmed();return super.toString();}
        @Override public String toString(int radix){failIfArmed();return super.toString(radix);}
    }

    /** Public JCA SPI wrapper delegates real SHA-256; it does not mirror a digest algorithm. */
    public static final class ProbeDigest extends MessageDigestSpi {
        private final MessageDigest delegate;
        public ProbeDigest(){try{delegate=MessageDigest.getInstance("SHA-256",DigestProbe.original);}catch(Exception failure){throw new IllegalStateException(failure);}}
        @Override protected void engineUpdate(byte b){delegate.update(b);}
        @Override protected void engineUpdate(byte[] b,int offset,int length){delegate.update(b,offset,length);}
        @Override protected byte[] engineDigest(){DigestProbe.digests.incrementAndGet();return delegate.digest();}
        @Override protected void engineReset(){delegate.reset();}
        @Override protected int engineGetDigestLength(){return delegate.getDigestLength();}
    }
    private static final class DigestProbe implements AutoCloseable {
        static Provider original;static final AtomicInteger digests=new AtomicInteger();
        private final String name="RestoreCloneWitness";
        DigestProbe() {
            assertNull(Security.getProvider(name),"isolated witness provider name must be unused");
            try {
                original=MessageDigest.getInstance("SHA-256").getProvider();
            } catch(java.security.NoSuchAlgorithmException failure) {
                throw new AssertionError("original SHA-256 unavailable",failure);
            }
            digests.set(0);
            Provider provider=new Provider(name,"1.0","delegating public restore SHA witness"){private static final long serialVersionUID=1L;};
            provider.put("MessageDigest.SHA-256",ProbeDigest.class.getName());
            try {
                assertEquals(1,Security.insertProviderAt(provider,1));
                assertEquals(name,MessageDigest.getInstance("SHA-256").getProvider().getName(),"SHA observation must be active");
            } catch(Exception|Error failure) {
                Security.removeProvider(name);original=null;throw new AssertionError("public SHA probe setup failed",failure);
            }
        }
        @Override public void close(){Security.removeProvider(name);original=null;}
    }

    private final class Archive implements ActionPorts.OutcomeArchive {
        final ContinuityWriter writer;final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,String> labels=new HashMap<>();
        final List<String> calls=new ArrayList<>();final Marker atNative=new Marker("actual native callback"),changedCurrent=new Marker("current material rejected");
        ContinuityStorePort.Session bound;boolean rejectSemantic;int identityChecks;ExactRef semantic,expectedNative;
        Archive(ContinuityWriter writer){this.writer=writer;}
        private void check(ContinuityStorePort.Session same){try{writer.requireSession(same);identityChecks++;}catch(IOException failure){throw new UncheckedIOException(failure);}}
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session same){check(same);if(bound!=null)assertSame(bound,same);bound=same;calls.add("bind");return this;}
        ExactRef put(String label,RawJson raw){ExactRef ref=ref(root.resolve("evidence-"+label+".json"),raw.bytes());materials.put(ref,raw);labels.put(ref,label);if(label.equals("semantic"))semantic=ref;return ref;}
        void replaceSemantic(ExactRef changed){materials.put(changed,materials.get(semantic));labels.put(changed,"semantic");semantic=changed;}
        @Override public RawJson loadMaterial(ExactRef ref){check(bound);String label=labels.get(ref);calls.add(label);if(rejectSemantic&&"semantic".equals(label))throw changedCurrent;RawJson raw=materials.get(ref);assertNotNull(raw,"unexpected material");return raw;}
        @Override public byte[] loadNativeFrame(ExactRef ref){check(bound);assertEquals(expectedNative,ref);calls.add("native");throw atNative;}
        private AssertionError unused(){return new AssertionError("prefix witness may only use actual public material/native reads");}
        @Override public ExactRef preserveMaterial(RawJson v){throw unused();}
        @Override public ExactRef materialReferenceOf(RawJson v){throw unused();}
        @Override public ExactRef preserveRead(PlanningReadReceipt v){throw unused();}
        @Override public PlanningReadReceipt loadRead(ExactRef v){throw unused();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt v){throw unused();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame v){throw unused();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome v){throw unused();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef v){throw unused();}
        @Override public ExactRef preserveRequest(NativeRequest v){throw unused();}
        @Override public NativeRequest loadRequest(ExactRef v){throw unused();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome v){throw unused();}
        @Override public ExactRef requestReferenceOf(NativeRequest v){throw unused();}
        @Override public ExactRef preserveRecord(ActionRecord v){throw unused();}
        @Override public ActionRecord loadRecord(ExactRef v){throw unused();}
        @Override public ExactRef recordReferenceOf(ActionRecord v){throw unused();}
        @Override public ExactRef preserveReceipt(ActionReceipt v){throw unused();}
        @Override public ActionReceipt loadReceipt(ExactRef v){throw unused();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt v){throw unused();}
    }
}
