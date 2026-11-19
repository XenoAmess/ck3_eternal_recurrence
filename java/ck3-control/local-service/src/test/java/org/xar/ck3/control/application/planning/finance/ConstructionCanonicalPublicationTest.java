package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;

/** Actual temporary writer/CAS publication; software DATA only, with no Root or native authority. */
final class ConstructionCanonicalPublicationTest {
    @TempDir Path directory;
    @Test void canonicalFreshPublicationPassesActualWriterPreviewAndReadback() throws Exception {
        if(Boolean.getBoolean("xar.construction.canonical.genuine")) {
            Path owner=Path.of(ConstructionDomainLifecycle.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            assertTrue(Files.isRegularFile(owner));assertTrue(Files.size(owner)>1_048_576);
        }
        try(var f=new Fixture(directory)) {
            assertFalse(Arrays.equals(encode(f.body),ConstructionDomainLifecycle.Prepared.canonicalBody(f.body)));
            f.writer.locked(same->{
                long before=same.head().state().sequence();
                var published=f.domain.publishOriginal(same,ConstructionDomainLifecycle.Kind.FRESH,obj(),List.of(f.source));
                assertEquals(before+1,same.head().state().sequence());
                var actual=(DomainBodies.Available)same.readDomain(DomainBodies.Slot.CONSTRUCTION);
                assertArrayEquals(ConstructionDomainLifecycle.Prepared.canonicalBody(f.body),actual.canonicalBody());
                assertEquals(f.body,DriverJson.object(actual.canonicalBody(),ConstructionDomainLifecycle.MAX_BYTES));
                assertNotNull(published.receipt());return null;
            });
        }
    }
    @Test void verifierRejectsChangedAuditTypeMissingFieldAndArrayOrder() throws Exception {
        try(var f=new Fixture(directory)) {
            f.writer.locked(same->{
                Obj audit=object(f.body.get("software_audit"),"software audit");
                var missing=new LinkedHashMap<>(audit.members());missing.remove("actor_character_id");
                for(Obj bad:List.of(f.body.with("software_audit",audit.with("actor_character_id",new Bool(true))),
                        f.body.with("software_audit",new Obj(missing)),
                        f.body.with("software_audit",audit.with("order",new Arr(List.of(new Text("second"),new Text("first"))))))) {
                    long before=same.head().state().sequence();
                    var request=f.request(same,ConstructionDomainLifecycle.Prepared.canonicalBody(bad));
                    var failure=assertThrows(IllegalArgumentException.class,()->same.previewImport(request));
                    assertTrue(failure.getMessage().contains("construction body differs"),failure.toString());
                    assertEquals(before,same.head().state().sequence());
                }
                return null;
            });
        }
    }
    @Test void noncanonicalIncomingBytesRemainRejected() throws Exception {
        try(var f=new Fixture(directory)) {
            f.writer.locked(same->{
                long before=same.head().state().sequence();
                var request=f.request(same,encode(f.body));
                assertThrows(IllegalArgumentException.class,()->same.previewImport(request));
                assertEquals(before,same.head().state().sequence());return null;
            });
        }
    }
    @org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.construction.actualBody.path",matches=".+")
    @Test void actualScene19BodyEqualsCanonicalReplayOrderWithoutChangingValues() throws Exception {
        Path path=Path.of(System.getProperty("xar.construction.actualBody.path"));byte[] raw=Files.readAllBytes(path);
        assertEquals(524,raw.length);assertEquals("077da9116ff98ea2c508871d5ae441668755141f2241bbf63fcf46abfb0f0e6a",ActionCodec.sha256(raw));
        Obj actual=DriverJson.object(raw,ConstructionDomainLifecycle.MAX_BYTES);
        Obj oldAudit=object(actual.get("java_fresh_initialization_v2"),"retained actual audit");
        Obj originalRef=object(oldAudit.get("original_basis"),"retained actual basis");
        Obj audit=obj("original_basis",obj("path",originalRef.get("path"),"bytes",originalRef.get("bytes"),"sha256",originalRef.get("sha256")),
                "episode_run_id",oldAudit.get("episode_run_id"),"actor_character_id",oldAudit.get("actor_character_id"));
        Obj producerOrder=obj("schema",actual.get("schema"),"pending",actual.get("pending"),"applied",actual.get("applied"),
                "applied_prior",actual.get("applied_prior"),"java_fresh_initialization_v2",audit);
        assertEquals(actual,producerOrder);assertFalse(Arrays.equals(raw,encode(producerOrder)));
        assertArrayEquals(raw,ConstructionDomainLifecycle.Prepared.canonicalBody(producerOrder));
        ConstructionLedgerCodec.decodeLedger(raw);
    }
    private static ExactRef exact(Path path)throws IOException {
        byte[] raw=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().toString(),raw.length,ActionCodec.sha256(raw));
    }
    private static final class SoftwareOriginal implements ConstructionDomainLifecycle.OriginalBodyProducer {
        final Obj body;final ExactRef source;
        SoftwareOriginal(Obj body,ExactRef source){this.body=body;this.source=source;}
        public ConstructionDomainLifecycle.OriginalBody replay(ContinuityStorePort.Session same,Head head,
                ConstructionDomainLifecycle.Kind kind,Obj input,Optional<ConstructionLedgerCodec.Ledger> previous) {
            assertEquals(ConstructionDomainLifecycle.Kind.FRESH,kind);assertTrue(previous.isEmpty());
            return new ConstructionDomainLifecycle.OriginalBody(body,List.of(source));
        }
    }
    private static final class Fixture implements AutoCloseable {
        final ExactRef source;final StorageWriteGuardTestSupport guard;final ImmutableArtifactStore store;
        final ContinuityWriter writer;final NativeOutcomeArchive archive;final ConstructionDomainLifecycle.Prepared domain;final Obj body;
        Fixture(Path directory)throws IOException {
            String machine="construction-canonical-software-data";var state=StrictJson.object();
            state.put("schema","root.ck3.continuity-window/v1").put("machine_id",machine).put("sequence",0).put("window_id",1).put("status","running")
                    .put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992)
                    .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");state.putNull("latest_binding");
            state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=directory.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=directory.resolve("anchor.json");
            Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));
            Files.write(directory.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer=directory.resolve("software-producer.java");Files.writeString(producer,"temporary construction DATA fixture; no Root or Game authority");source=exact(producer);
            var layout=new Layout(snapshot,exact(anchor),machine);Path objects=directory.resolve("objects");Files.createDirectory(objects);
            guard=StorageWriteGuardTestSupport.create(directory,layout.lock(),4*1024*1024);
            store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects,layout.lock(),4*1024*1024),guard);
            domain=ConstructionDomainLifecycle.prepare(List.of(source),source);
            writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority(){
                public String revalidate(ContinuityState head,Request request){throw new AssertionError("domain imports only");}
                public ContinuityState reduce(ContinuityState head,Request request){throw new AssertionError("no action transition");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(domain.registration()),Optional.of(store),Optional.empty()),guard);
            archive=new NativeOutcomeArchive(store,writer);
            var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(source,new FinanceReadContracts.Permission(Optional.empty(),
                    "construction-canonical-software:"+query.name(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
            domain.bindCore(writer,archive,(basis,originals)->{throw new AssertionError("no native frame");},definitions);
            body=obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,"applied",Nil.INSTANCE,"applied_prior",new Arr(List.of()),
                    "software_audit",obj("actor_character_id",new IntegerValue(java.math.BigInteger.valueOf(31254)),"order",new Arr(List.of(new Text("first"),new Text("second")))));
            domain.bindOriginals(source,new SoftwareOriginal(body,source));
        }
        DomainBodies.ImportRequest request(ContinuityStorePort.Session same,byte[] body)throws IOException {
            Obj details=obj("schema",new Text(ConstructionDomainLifecycle.SCHEMA),"kind",new Text("FRESH"),"original_input",obj());
            byte[] input=encode(details);ExactRef inputRef=archive.preserveArtifact(same,input,ConstructionDomainLifecycle.MAX_INPUT_BYTES);
            ExactRef bodyRef=archive.preserveArtifact(same,body,ConstructionDomainLifecycle.MAX_BYTES);
            return new DomainBodies.ImportRequest(DomainBodies.Slot.CONSTRUCTION,ConstructionLedgerCodec.SCHEMA,bodyRef,input,List.of(source,inputRef),"software-tamper");
        }
        public void close()throws IOException {guard.close();}
    }
}
