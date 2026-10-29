package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Software registry/persistence regression. No Rite command, once-business verifier or Game qualification. */
final class RiteCreationDomainWriterTest {
    private static final String SCHEMA="fixture.separate-rite-registry/v1";
    private static final int MAXIMUM=65_536;
    @TempDir Path temporary;
    private record Fixture(WriterFixture files,ContinuityWriter writer,AtomicInteger validations) { }

    private Fixture fixture(String name)throws IOException {
        assertTrue(Platform.isWindows(),"actual Windows lock/FileID fixture required");
        WriterFixture files=new WriterFixture(temporary.resolve(name));
        Path archive=files.layout.snapshot().resolveSibling("domain-archive");Files.createDirectory(archive);
        ImmutableArtifactStore artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive,files.layout.lock(),4_194_304), StorageWriteGuardTestSupport.forOriginalLock(files.layout.lock()));
        List<ExactRef> sources=List.of(LedgerFiles.read(files.source,MAXIMUM).pin().reference());
        AtomicReference<ContinuityWriter> original=new AtomicReference<>();AtomicInteger validations=new AtomicInteger();
        List<DomainBodies.Registration> registrations=new ArrayList<>();
        for(var slot:List.of(DomainBodies.Slot.RITE_CREATION,DomainBodies.Slot.ORDINARY_ONCE_CLAIM)) {
            DomainBodies.Verifier verifier=new DomainBodies.Verifier() {
                @Override public String verify(ContinuityState head,Optional<DomainBodies.BodyRef> previous,
                        DomainBodies.ImportRequest request,byte[] raw)throws IOException {
                    throw new IOException("actual complete Head and original owning Session required");
                }
                @Override public String verify(Head head,Optional<DomainBodies.BodyRef> previous,
                        DomainBodies.ImportRequest request,byte[] raw)throws IOException {
                    ContinuityWriter owner=original.get();var same=owner.borrowedSession();owner.requireSession(same);
                    if(!same.head().digest().equals(head.digest()))throw new IOException("fixture source head changed");
                    ObjectNode body=ContinuityJson.parseObject(raw,MAXIMUM);
                    if(request.slot()!=slot||!StrictJson.text(body.get("slot")).equals(slot.name())
                            ||!StrictJson.text(body.get("claim_id")).equals(StrictJson.text(object(request.producerInput()).get("claim_id"))))
                        throw new IOException("registered original producer/claim/slot differs");
                    validations.incrementAndGet();return ContinuityJson.digest(body);
                }
            };
            registrations.add(new DomainBodies.Registration(slot,SCHEMA,MAXIMUM,sources,verifier));
        }
        TransitionAuthority noOrdinaryTransition=new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head,Request request)throws IOException {
                throw new IOException("registry fixture cannot grant ordinary or Game authority");
            }
            @Override public ContinuityState reduce(ContinuityState head,Request request)throws IOException {
                throw new IOException("registry fixture only permits registered original domain imports");
            }
        };
        ContinuityWriter writer=new ContinuityWriter(files.layout, sources, noOrdinaryTransition, Clock.systemUTC(), new ContinuityWriter.Extensions(registrations,Optional.of(artifacts),Optional.empty()), StorageWriteGuardTestSupport.forLayout(files.layout));
        original.set(writer);return new Fixture(files,writer,validations);
    }

    private DomainBodies.ImportRequest original(Fixture f,DomainBodies.Slot requestedSlot,DomainBodies.Slot bodySlot,
            String claimId)throws IOException {
        ObjectNode body=StrictJson.object();body.put("schema",SCHEMA);body.put("slot",bodySlot.name());
        body.put("claim_id",claimId);body.put("outcome","UNKNOWN");body.putNull("late_ack");
        Path path=f.files().layout.snapshot().resolveSibling(claimId+".json");
        Files.write(path,ContinuityJson.canonical(body));ObjectNode input=StrictJson.object();input.put("claim_id",claimId);
        return new DomainBodies.ImportRequest(requestedSlot,SCHEMA,LedgerFiles.read(path,MAXIMUM).pin().reference(),
                ContinuityJson.canonical(input),List.of(),"actual-fixture-"+claimId);
    }

    @Test void actualImportsKeepRiteAndInteractionClaimsSeparateThroughDurableReadAndAncestry()throws Exception {
        Fixture f=fixture("separate");Head before=f.writer().locked(ContinuityStorePort.Session::head);
        var rite=original(f,DomainBodies.Slot.RITE_CREATION,DomainBodies.Slot.RITE_CREATION,"rite-unknown");
        f.writer().locked(same->{same.commitImport(same.previewImport(rite));return null;});
        DomainBodies.Available riteRead=assertInstanceOf(DomainBodies.Available.class,f.writer().read(DomainBodies.Slot.RITE_CREATION));
        var once=original(f,DomainBodies.Slot.ORDINARY_ONCE_CLAIM,DomainBodies.Slot.ORDINARY_ONCE_CLAIM,"interaction-unknown");
        f.writer().locked(same->{same.commitImport(same.previewImport(once));return null;});
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());int validations=f.validations().get();
        assertTrue(validations>=4,"actual original producers are revalidated during preview and commit");
        f.writer().locked(same->{
            same.requireDomainImportContinuation(before.state().sequence(),before.digest());
            var current=same.head().state();var persisted=DomainBodies.reference(current,DomainBodies.Slot.RITE_CREATION).orElseThrow();
            assertEquals(riteRead.reference(),persisted,"another once-domain import must retain exact Rite body and FileID");
            assertEquals(persisted,DomainBodies.BodyRef.fromJson(ContinuityJson.parseObject(ContinuityJson.canonical(persisted.toJson()),MAXIMUM)));
            assertEquals(WriterFixture.state().get("pending_cycle"),current.toJson().get("pending_cycle"));
            assertEquals(WriterFixture.state().get("NEXT"),current.toJson().get("NEXT"));
            assertEquals("UNKNOWN",ContinuityJson.parseObject(same.readPinned(new Pin(persisted.payload(),persisted.identity()),MAXIMUM),MAXIMUM).get("outcome").textValue());
            assertNotEquals(persisted,DomainBodies.reference(current,DomainBodies.Slot.ORDINARY_ONCE_CLAIM).orElseThrow());
            return null;
        });
        assertEquals(validations,f.validations().get(),"readonly ancestry/codec cannot replay live original producers");
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(3)));
    }

    @Test void aRiteRegistrationCannotPublishAnInteractionBodyAndMissingIsNeverAClaimRelease()throws Exception {
        Fixture f=fixture("rejected");byte[] originalSnapshot=Files.readAllBytes(f.files().layout.snapshot());
        var missing=assertInstanceOf(DomainBodies.Unavailable.class,f.writer().read(DomainBodies.Slot.RITE_CREATION));
        assertEquals(DomainBodies.Reason.UNIMPORTED,missing.reason());
        var wrong=original(f,DomainBodies.Slot.RITE_CREATION,DomainBodies.Slot.ORDINARY_ONCE_CLAIM,"wrong-domain");
        assertThrows(IOException.class,()->f.writer().previewImport(wrong));
        assertArrayEquals(originalSnapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(1)));
        var rite=original(f,DomainBodies.Slot.RITE_CREATION,DomainBodies.Slot.RITE_CREATION,"exact-rite");
        f.writer().locked(same->{same.commitImport(same.previewImport(rite));return null;});
        var body=assertInstanceOf(DomainBodies.Available.class,f.writer().read(DomainBodies.Slot.RITE_CREATION)).reference();
        ObjectNode renamed=body.toJson();renamed.put("slot","rite_creation");
        assertThrows(ContractViolationException.class,()->DomainBodies.BodyRef.fromJson(renamed));
        ObjectNode wrongType=body.toJson();wrongType.put("slot",true);
        assertThrows(ContractViolationException.class,()->DomainBodies.BodyRef.fromJson(wrongType));
        var interaction=assertInstanceOf(DomainBodies.Unavailable.class,f.writer().read(DomainBodies.Slot.ORDINARY_ONCE_CLAIM));
        assertEquals(DomainBodies.Reason.UNIMPORTED,interaction.reason());
    }
}
