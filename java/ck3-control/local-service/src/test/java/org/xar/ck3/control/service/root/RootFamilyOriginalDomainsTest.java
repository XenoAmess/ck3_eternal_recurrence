package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Selection;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Actual immutable publisher + byte-zero writer + three registered original-domain producers. No Game or mocked import receipt. */
final class RootFamilyOriginalDomainsTest {
    @TempDir Path temp;
    private StorageWriteGuardTestSupport storage;
    @org.junit.jupiter.api.AfterEach void closeStorage()throws Exception {
        if(storage!=null)storage.close();
    }
    private static final String MACHINE="fixture-family-writer-machine";
    private static ExactRef reference(Path file)throws Exception {byte[] bytes=Files.readAllBytes(file);return new ExactRef(file.toAbsolutePath().toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}
    private static ObjectNode state() {
        var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE).put("sequence",0).put("window_id",1).put("status","running")
                .put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992)
                .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0);
        row.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);row.put("NEXT",11559);return row;
    }
    private record Fixture(ContinuityWriter writer,RootFamilyOriginalDomains domains,Map<DomainBodies.Slot,ExactRef> originals) { }
    private Fixture fixture()throws Exception {
        Path root=Files.createDirectory(temp.resolve("original-writer"));byte[] state=ContinuityJson.canonical(state());
        Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json"),lock=root.resolve("ROOT-CONTINUITY-WINDOW.lock");
        Files.write(snapshot,state);Files.write(anchor,state);Files.write(lock,new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("artifacts"));
        Path source=root.resolve("reviewed-fixture-producer.txt");Files.writeString(source,"reviewed family import fixture source");ExactRef implementation=reference(source);
        var selected=new EnumMap<DomainBodies.Slot,ExactRef>(DomainBodies.Slot.class);
        for(var slot:List.of(DomainBodies.Slot.FAMILY,DomainBodies.Slot.CHILD_MATRILINEAL,DomainBodies.Slot.DEFAULT_MARRIAGE)) {
            var body=StrictJson.object().put("schema",FamilyDomainSource.schema(slot));body.putNull("pending");body.putNull("resolved");
            if(slot==DomainBodies.Slot.CHILD_MATRILINEAL)body.putObject("pending").put("episode_run_id","original-episode").put("heir_character_id",2).put("candidate_character_id",3)
                    .put("source_bridge_pid",123).put("source_bridge_creation_date","2026-10-23T01:00:00Z").put("pre_native_revision",1);
            Path formal=root.resolve(slot.name()+"-original.json");Files.write(formal,StrictJson.canonical(body));selected.put(slot,reference(formal));
        }
        var originals=new RootFamilyOriginalDomains(lock,selected,List.of(implementation));var layout=new Layout(snapshot,reference(anchor),MACHINE);
        storage=StorageWriteGuardTestSupport.create(root,lock,16L << 20);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),lock,8*1024*1024),storage);
        var writer=new ContinuityWriter(layout,List.of(implementation),new TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor,Request request) {return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState predecessor,Request request) {return OriginalWindowReducer.reduce(predecessor,request);}
        },Clock.systemUTC(),new ContinuityWriter.Extensions(originals.registrations(),Optional.of(artifacts),Optional.empty()),storage);
        originals.bindWriter(writer,new NativeOutcomeArchive(artifacts,writer));return new Fixture(writer,originals,Map.copyOf(selected));
    }
    @Test void actualOriginalFilesImportUnderTheSameWriterAndPreserveUnresolvedPending()throws Exception {
        var fixture=fixture();fixture.writer().locked(same->{
            for(var slot:fixture.originals().keySet()) {
                assertInstanceOf(DomainBodies.Unavailable.class,same.readDomain(slot));fixture.domains().importOriginal(same,slot);
                var actual=assertInstanceOf(DomainBodies.Available.class,same.readDomain(slot));
                assertArrayEquals(Files.readAllBytes(Path.of(fixture.originals().get(slot).path())),actual.canonicalBody());
                assertEquals(FamilyDomainSource.schema(slot),actual.reference().contractSchema());
            }
            String before=same.head().digest();for(var slot:fixture.originals().keySet())fixture.domains().importOriginal(same,slot);assertEquals(before,same.head().digest());
            var mat=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.CHILD_MATRILINEAL));assertTrue(StrictJson.parse(mat.canonicalBody()).get("pending").isObject());return null;
        });
    }
    @Test void ordinaryLedgerConsumerBorrowsTheHeldWriterInsteadOfOpeningANestedScope()throws Exception {
        var fixture=fixture();fixture.writer().locked(same->{
            for(var slot:fixture.originals().keySet())fixture.domains().importOriginal(same,slot);
            var source=new org.xar.ck3.control.g2.common.G2Source(MACHINE,"2026-10-23T18:00:00Z","fixture-build",fixture.originals().get(DomainBodies.Slot.FAMILY));
            var before=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(MACHINE,new GameGeneration(123,new PythonOnlyUInt64(java.math.BigInteger.ONE)),
                    new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(java.math.BigInteger.ONE,java.math.BigInteger.ONE,java.math.BigInteger.ONE),"fixture",java.math.BigInteger.ONE,"fixture-episode"),1);
            var request=new org.xar.ck3.control.application.planning.PlanningRequest(before,source,"fixture-family-session",java.time.Instant.parse("2099-01-01T00:00:00Z"),
                    new org.xar.ck3.control.application.planning.PlanningObservation(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),List.of(),java.util.Set.of(),java.util.Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
            var fixtureBridge=new FamilyDomainSource.CurrentBridge() {
                @Override public Optional<FamilyDomainSource.BridgeObservation> observe(org.xar.ck3.control.application.planning.PlanningRequest actual) {
                    assertSame(request,actual);return Optional.of(new FamilyDomainSource.BridgeObservation(new FamilyPorts.BridgeIdentity(123,"2026-10-23T01:00:00.0000000Z"),fixture.originals().get(DomainBodies.Slot.FAMILY)));
                }
                @Override public boolean verifyRetained(org.xar.ck3.control.application.action.PlanningReadReceipt read,FamilyDomainSource.BridgeObservation observation) {throw new AssertionError("fixture does not qualify native receipts");}
            };
            var result=new FamilyDomainSource(fixture.writer()::borrowedSession,fixtureBridge).readCurrent(request);
            var known=assertInstanceOf(FamilyPorts.KnownDocuments.class,result);assertEquals(same.persistedHead(),known.documents().canonicalHead());
            assertTrue(known.documents().matrilineal().get("pending") instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj);return null;
        });
    }
    @Test void changedSelectedFileCannotBootstrapAnEmptyOrSubstituteDomain()throws Exception {
        var fixture=fixture();Path changed=Path.of(fixture.originals().get(DomainBodies.Slot.FAMILY).path());Files.writeString(changed,"{\"schema\":\"changed\"}");
        String before=fixture.writer().locked(same->same.head().digest());
        assertThrows(java.io.IOException.class,()->fixture.writer().locked(same->{fixture.domains().importOriginal(same,DomainBodies.Slot.FAMILY);return null;}));
        fixture.writer().locked(same->{assertEquals(before,same.head().digest());assertInstanceOf(DomainBodies.Unavailable.class,same.readDomain(DomainBodies.Slot.FAMILY));return null;});
    }
    @Test void historicalDomainReplaySurvivesProducerCodeChangeWithoutChangingItsRetainedBody()throws Exception {
        var fixture=fixture();fixture.writer().locked(same->{
            fixture.domains().importOriginal(same,DomainBodies.Slot.CHILD_MATRILINEAL);
            var actual=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.CHILD_MATRILINEAL));
            var binding=new FamilyDomainReadBinding(actual.reference().slot(),actual.reference().payload(),same.head().state().sequence(),same.head().digest());
            var body=FamilyDomainSource.validate(binding.slot(),actual.canonicalBody());
            var pending=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(body.get("pending"),"pending");
            assertEquals(body,RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,pending));
            fixture.domains().importOriginal(same,DomainBodies.Slot.FAMILY);
            var retainedHead=same.head();byte[] snapshot=Files.readAllBytes(fixture.writer().originalLockPath().resolveSibling("ROOT-CONTINUITY-WINDOW.json"));
            assertNotEquals(binding.sequence(),retainedHead.state().sequence());
            var historicalSource=actual.reference().producerSources().getFirst();Path producer=Path.of(historicalSource.path());
            Files.writeString(producer,"updated producer code after the full family body was retained");
            assertNotEquals(historicalSource.sha256(),org.xar.ck3.control.application.action.ActionCodec.sha256(Files.readAllBytes(producer)));
            assertEquals(body,RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,pending));
            Files.delete(producer);
            assertEquals(body,RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,pending));
            assertEquals(actual.reference(),assertInstanceOf(DomainBodies.Available.class,same.readDomain(binding.slot())).reference());
            assertArrayEquals(actual.canonicalBody(),Files.readAllBytes(Path.of(binding.body().path())));
            assertThrows(IllegalArgumentException.class,()->RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,
                    pending.with("candidate_character_id",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(4)))));
            Path material=Path.of(binding.body().path()),retained=material.resolveSibling(material.getFileName()+".retained-original");
            byte[] original=Files.readAllBytes(material);Files.move(material,retained);Files.write(material,original);
            try {
                assertThrows(IllegalArgumentException.class,()->RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,pending));
            } finally {
                Files.delete(material);Files.move(retained,material);
            }
            assertEquals(retainedHead.digest(),same.head().digest());assertEquals(retainedHead.state().sequence(),same.head().state().sequence());
            assertArrayEquals(snapshot,Files.readAllBytes(fixture.writer().originalLockPath().resolveSibling("ROOT-CONTINUITY-WINDOW.json")));
            return null;
        });
    }
    @Test void historicalDomainReplayRequiresTheRealCanonicalAncestorAndTheExactRegisteredBody()throws Exception {
        var fixture=fixture();fixture.writer().locked(same->{
            String anchor=same.head().digest();fixture.domains().importOriginal(same,DomainBodies.Slot.CHILD_MATRILINEAL);
            var actual=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.CHILD_MATRILINEAL));
            var binding=new FamilyDomainReadBinding(DomainBodies.Slot.CHILD_MATRILINEAL,actual.reference().payload(),same.head().state().sequence(),same.head().digest());
            var body=FamilyDomainSource.validate(binding.slot(),actual.canonicalBody());
            var pending=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(body.get("pending"),"pending");
            fixture.domains().importOriginal(same,DomainBodies.Slot.FAMILY);
            assertNotEquals(binding.sequence(),same.head().state().sequence());
            assertEquals(body,RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,pending));
            assertThrows(java.io.IOException.class,()->RootFamilyDomainReadAuthority.originalBody(same,new FamilyDomainReadBinding(binding.slot(),binding.body(),binding.sequence(),"0".repeat(64)),Selection.PENDING,pending));
            assertThrows(IllegalArgumentException.class,()->RootFamilyDomainReadAuthority.originalBody(same,new FamilyDomainReadBinding(binding.slot(),binding.body(),0,anchor),Selection.PENDING,pending));
            var other=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.FAMILY));
            assertThrows(IllegalArgumentException.class,()->RootFamilyDomainReadAuthority.originalBody(same,new FamilyDomainReadBinding(binding.slot(),other.reference().payload(),binding.sequence(),binding.headDigest()),Selection.PENDING,pending));
            assertThrows(IllegalArgumentException.class,()->RootFamilyDomainReadAuthority.originalBody(same,binding,Selection.PENDING,pending.with("candidate_character_id",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(4)))));
            assertEquals(binding,FamilyDomainReadBinding.fromJson(binding.toJson()));
            for(var invalid:List.of(binding.toJson().with("sequence",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true)),
                    binding.toJson().with("body",org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE),binding.toJson().with("alias",binding.toJson())))
                assertThrows(IllegalArgumentException.class,()->FamilyDomainReadBinding.fromJson(invalid));
            return null;
        });
    }
}
