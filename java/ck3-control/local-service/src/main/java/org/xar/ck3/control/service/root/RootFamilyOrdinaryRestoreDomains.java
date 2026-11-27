package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Same-writer Family imports from the already admitted private ORDINARY restoration. No restore or action dispatch. */
final class RootFamilyOrdinaryRestoreDomains {
    static final String SCHEMA = "xar.java.family-ordinary-restoration-domain-import/v1";
    private static final int MAX = ContinuityJson.DOMAIN_MAX_BYTES;
    private static final List<Slot> SLOTS = List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE);
    private final Path lock;
    private ContinuityWriter writer;
    private NativeOutcomeArchive archive;
    private RootRuntimeContext current;
    private static final class Retained {
        final DomainBodies.BodyRef saved, previous;
        final byte[] savedBytes, previousBytes, output;
        final FamilyOrdinaryRestoreMigration.Transition transition;
        DomainBodies.PreparedImport prepared;
        WriterContracts.Receipt receipt;
        boolean attempted;
        Retained(DomainBodies.BodyRef saved, DomainBodies.BodyRef previous, byte[] savedBytes, byte[] previousBytes,
                FamilyOrdinaryRestoreMigration.Transition transition, byte[] output) {
            this.saved=saved; this.previous=previous; this.savedBytes=savedBytes.clone(); this.previousBytes=previousBytes.clone();
            this.transition=transition; this.output=output.clone();
        }
    }
    @FunctionalInterface
    private interface OriginalScope {
        void requireCurrent(ContinuityStorePort.Session same) throws IOException;
    }
    @FunctionalInterface
    private interface ReadSavedBodies {
        Map<Slot, Body> read(ContinuityStorePort.Session same) throws IOException;
    }
    private record Body(DomainBodies.BodyRef reference, byte[] bytes) { }
    private record Original(ExactRef basis, ExactRef material, ContinuityState attachmentHead, Episode episode,
            SessionIdentity savedOwner, SessionIdentity departed, SessionIdentity successor, List<ExactRef> evidence,
            OriginalScope scope, ReadSavedBodies savedBodies, boolean committed) { }
    private record Batch(RootRuntimeContext context, Original original, Map<Slot, Retained> slots) { }
    private record Authorization(Batch batch, Slot slot, String inputSha256, String outputSha256) { }
    private final Map<String,Batch> batches = new java.util.HashMap<>();
    private final Map<String,Authorization> authorizations = new java.util.HashMap<>();

    RootFamilyOrdinaryRestoreDomains(Path lock) { this.lock=Objects.requireNonNull(lock); }
    synchronized void bindWriter(ContinuityWriter actual, NativeOutcomeArchive actualArchive) {
        StrictJson.require(writer==null && actualArchive.writer()==actual && actual.originalLockPath().equals(lock),
                "ordinary Family restore uses the identical once-bound original writer/archive");
        writer=actual; archive=actualArchive;
    }
    synchronized void bindGame(RootRuntimeContext actual) {
        StrictJson.require(writer!=null && actual.writer()==writer && actual.archive()==archive && current!=actual,
                "ordinary Family restore must bind the actual installed physical context");
        current=actual;
    }

    List<DomainBodies.BodyRef> initialize(RootRuntimeContext actual, ContinuityStorePort.Session same,
            RootRestorationOriginalProof proof) throws IOException {
        requireContext(actual,same); proof.requireCurrent(same);
        var source=actual.restorationOriginal(same);
        if(source.material().kind()!=SavedCheckpointMaterial.Kind.ORDINARY)
            throw new IOException("FIRST restoration must retain its existing Family episode initializer");
        var origin=actual.requireRestoredOrigin(same); origin.requireOriginal(same);
        var data=origin.evidence();
        StrictJson.require(data.savedOwner().equals(source.material().session())
                && data.restoredOwner().game().equals(source.game()) && data.restoredOwner().sessionId().equals(source.sessionId())
                && data.materialWitness().equals(source.material().witness()) && data.pair().equals(source.pair()),
                "ordinary Family source changed its genuine SAVE/replacement identity");
        var frame = source.pair().frame().frame();
        var original = new Original(source.basis(), source.material().reference(), source.attachmentHead(),
                new Episode(frame.episodeRunId(), frame.identity().player()), data.savedOwner(), data.previousOwner(),
                data.restoredOwner(), source.evidence(), borrowed -> {
                    proof.requireCurrent(borrowed);
                    source.requireImportPredecessor(borrowed, borrowed.head());
                    origin.requireOriginal(borrowed);
                    StrictJson.require(origin == actual.requireRestoredOrigin(borrowed),
                            "ordinary Family restore changed its private origin issuer");
                }, borrowed -> readBodies(borrowed, source.originalSavedHead()), false);
        return initialize(actual, same, original);
    }

    List<DomainBodies.BodyRef> initializeCommitted(RootRuntimeContext actual, ContinuityStorePort.Session same,
            RootCommittedOrdinaryRestoration committed) throws IOException {
        requireContext(actual, same);
        Objects.requireNonNull(committed).requireCurrent(same, actual);
        var frame = committed.pair().frame().frame();
        // Stable domain originals belong to the closing attachment and the independent confirmed SAVE.
        // This session's live SEM qualifies the origin without becoming part of a canonical receipt identity.
        var evidence = List.of(committed.basis(), committed.attachment().reference(),
                committed.importedOrigin().targetEntry().reference(), committed.importedOrigin().physicalConfirmation().reference());
        var original = new Original(committed.basis(), committed.material().reference(), committed.attachmentHead(),
                new Episode(frame.episodeRunId(), frame.identity().player()), committed.material().session(), committed.departed(),
                committed.successor(), evidence, borrowed -> committed.requireCurrent(borrowed, actual),
                borrowed -> committed.withOriginalSavedWriter(borrowed, RootFamilyOrdinaryRestoreDomains::readBodies), true);
        return initialize(actual, same, original);
    }

    private List<DomainBodies.BodyRef> initialize(RootRuntimeContext actual, ContinuityStorePort.Session same,
            Original original) throws IOException {
        Batch batch;
        synchronized(this) { batch=batches.get(original.basis().sha256()); }
        if(batch==null) {
            var saved=original.savedBodies().read(same);
            var previous=readBodies(same, original.attachmentHead());
            var slots=new EnumMap<Slot,Retained>(Slot.class);
            for(Slot slot:SLOTS) {
                // Preserve the entire departed body, including any UNKNOWN commitment.
                var originalSaved=saved.get(slot); var originalPrevious=previous.get(slot);
                var transition=new FamilyOrdinaryRestoreMigration.Transition(original.savedOwner(),original.departed(),
                        original.successor(),original.episode(),original.material(),original.basis(),
                        originalSaved.reference().payload(),originalPrevious.reference().payload());
                var output=FamilyOrdinaryRestoreMigration.derive(slot,originalSaved.bytes(),originalPrevious.bytes(),transition);
                slots.put(slot,new Retained(originalSaved.reference(),originalPrevious.reference(),originalSaved.bytes(),originalPrevious.bytes(),transition,output));
            }
            batch=new Batch(actual,original,Map.copyOf(slots));
            synchronized(this) {
                StrictJson.require(batches.size()<192 && batches.putIfAbsent(original.basis().sha256(),batch)==null,
                        "bounded ordinary Family restore history exhausted or raced its original writer");
            }
        }
        StrictJson.require(batch.context() == actual && batch.original().basis().equals(original.basis()),
                "ordinary Family restore changed its original context or basis");
        requireBatch(batch,same);
        var result=new java.util.ArrayList<DomainBodies.BodyRef>();
        for(Slot slot:SLOTS) {
            requireBatch(batch,same); var retained=batch.slots().get(slot);
            var read=same.readDomain(slot);
            if(!(read instanceof DomainBodies.Available known))throw new IOException("ordinary Family current full body unavailable: "+slot);
            FamilyOrdinaryRestoreMigration.requireCompatibleCurrent(slot,retained.savedBytes,retained.previousBytes,known.canonicalBody(),retained.transition);
            if(retained.attempted && retained.receipt==null)retained.receipt=readReceipt(actual,same,slot,retained.prepared);
            if(retained.receipt!=null)same.requireCommitted(retained.prepared,retained.receipt);
            if(Arrays.equals(retained.output,known.canonicalBody())) {
                if (batch.original().committed() && retained.receipt == null)
                    requireRecordedImport(same, actual.core().configuration().ledger(), batch.original().attachmentHead().sequence(),
                            request(slot, retained.saved, retained.previous, retained.transition, batch.original().evidence(), known.reference().payload()), retained.previous, known.reference());
                result.add(known.reference());
                continue;
            }
            if(retained.attempted)throw new IOException("ordinary Family original import remains UNKNOWN; never reissue it");
            StrictJson.require(known.reference().equals(retained.previous),"ordinary Family actual CAS predecessor native identity changed");
            var output=archive.preserveArtifact(same,retained.output,MAX);
            var request=request(slot, retained.saved, retained.previous, retained.transition, batch.original().evidence(), output);
            synchronized(this) {
                StrictJson.require(authorizations.size()<576 || authorizations.containsKey(request.evidenceId()),"bounded ordinary Family import custody exhausted");
                var authorization=new Authorization(batch,slot,ActionCodec.sha256(request.producerInput()),ActionCodec.sha256(retained.output));
                var prior=authorizations.putIfAbsent(request.evidenceId(),authorization);
                StrictJson.require(prior==null || prior.equals(authorization),"ordinary Family identity changed its private restore source");
            }
            requireBatch(batch,same); retained.prepared=same.previewImport(request); requireBatch(batch,same);
            retained.attempted=true; retained.receipt=same.commitImport(retained.prepared);
            same.requireCommitted(retained.prepared,retained.receipt); requireBatch(batch,same);
            var committed=same.readDomain(slot);
            if(!(committed instanceof DomainBodies.Available available) || !Arrays.equals(retained.output,available.canonicalBody()))
                throw new IOException("ordinary Family import did not publish its exact retained complete body");
            result.add(available.reference());
        }
        requireBatch(batch,same); return List.copyOf(result);
    }

    String verify(Slot slot, ContinuityState head, Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request, byte[] actual) throws IOException {
        var same=writer.borrowedSession(); Authorization authorization;
        synchronized(this) { authorization=authorizations.get(request.evidenceId()); }
        StrictJson.require(authorization!=null,"decoded Family restoration DATA cannot mint the private ordinary restore source");
        var batch=authorization.batch(); requireBatch(batch,same); var retained=batch.slots().get(slot);
        StrictJson.require(authorization.slot()==slot && previous.filter(retained.previous::equals).isPresent()
                && request.slot()==slot && request.contractSchema().equals(FamilyDomainSource.schema(slot))
                && authorization.inputSha256().equals(ActionCodec.sha256(request.producerInput()))
                && authorization.outputSha256().equals(ActionCodec.sha256(actual))
                && ContinuityJson.digest(head.toJson()).equals(same.head().digest()),
                "ordinary Family restore input/body/current CAS head differs");
        var input=StrictJson.object(StrictJson.parse(request.producerInput(),MAX),java.util.Set.of("schema","slot","basis","saved","previous","transition"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(input.get("schema"))) && slot.name().equals(StrictJson.text(input.get("slot")))
                && batch.original().basis().equals(ExactRef.fromJson(input.get("basis")))
                && retained.saved.equals(DomainBodies.BodyRef.fromJson(input.get("saved")))
                && retained.previous.equals(DomainBodies.BodyRef.fromJson(input.get("previous")))
                && retained.transition.equals(FamilyOrdinaryRestoreMigration.Transition.fromJson(input.get("transition"))),
                "ordinary Family import lost its original SAVE or actual replaced owner");
        // The saved member was selected by the independent original writer. Recheck its exact physical
        // identity/bytes for the registered CAS without reopening that writer for every verifier callback.
        byte[] expected=FamilyOrdinaryRestoreMigration.derive(slot,read(same,retained.saved),read(same,retained.previous),retained.transition);
        StrictJson.require(Arrays.equals(expected,actual) && Arrays.equals(actual,archive.readArtifact(same,request.originalBody(),MAX))
                && request.evidence().containsAll(List.of(batch.original().basis(),retained.saved.payload(),retained.previous.payload(),
                        batch.original().material())),"ordinary Family original producer replay differs");
        requireBatch(batch,same);
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",ContinuityJson.digest(head.toJson()))
                .put("input",authorization.inputSha256()).put("output",authorization.outputSha256())));
    }
    static DomainBodies.ImportRequest request(Slot slot, DomainBodies.BodyRef saved, DomainBodies.BodyRef previous,
            FamilyOrdinaryRestoreMigration.Transition transition, List<ExactRef> originals, ExactRef body) {
        var input = StrictJson.object().put("schema", SCHEMA).put("slot", slot.name());
        input.set("basis", transition.restorationBasis().toJson());
        input.set("saved", saved.toJson());
        input.set("previous", previous.toJson());
        input.set("transition", transition.toJson());
        String identity = "family-ordinary-restore-" + slot.name() + "-" + transition.restorationBasis().sha256()
                + "-" + previous.payload().sha256();
        var evidence = new LinkedHashSet<>(originals);
        evidence.addAll(List.of(saved.payload(), previous.payload(), body, transition.savedMaterial()));
        return new DomainBodies.ImportRequest(slot, FamilyDomainSource.schema(slot), body, StrictJson.canonical(input, MAX),
                List.copyOf(evidence), identity);
    }

    /** Recover the prior daemon's exact registered canonical receipt. */
    static void requireRecordedImport(ContinuityStorePort.Session same, WriterContracts.Layout layout,
            long attachmentSequence, DomainBodies.ImportRequest expected, DomainBodies.BodyRef previous,
            DomainBodies.BodyRef current) throws IOException {
        var head = same.head();
        var events = new java.util.ArrayList<WriterContracts.Pin>();
        Set<Path> suffix = new java.util.HashSet<>();
        for (long sequence = Math.addExact(attachmentSequence, 1); sequence <= head.state().sequence(); sequence++)
            suffix.add(layout.event(sequence));
        for (var pin : head.documents()) {
            if (suffix.contains(Path.of(pin.reference().path()).toAbsolutePath().normalize())) events.add(pin);
        }
        if (events.isEmpty()) throw new IOException("committed Family output has no recorded import after its actual attachment");
        String evidenceId = "domain-body:" + expected.slot().name() + ":" + expected.evidenceId();
        for (var edge : same.readHistoricalTransitions(events)) {
            var details = ContinuityJson.parseObject(edge.details(), ContinuityJson.DOCUMENT_MAX_BYTES);
            if (!DomainBodies.IMPORT_KIND.equals(edge.kind()) || !evidenceId.equals(details.path("evidence_id").textValue())) continue;
            var recorded = same.requireHistoricalImport(expected.slot(), edge.sequence(), ContinuityJson.digest(edge.after().toJson()));
            var request = recorded.request();
            StrictJson.require(recorded.body().equals(current) && previous.equals(DomainBodies.reference(recorded.predecessor().state(), expected.slot()).orElse(null))
                    && request.evidenceId().equals(expected.evidenceId()) && request.originalBody().equals(expected.originalBody())
                    && Arrays.equals(request.producerInput(), expected.producerInput()) && request.evidence().equals(expected.evidence()),
                    "recorded Family import changed its exact stable attachment, predecessor, output or evidence");
            return;
        }
        throw new IOException("committed Family output lacks its exact recorded ordinary import");
    }

    private void requireContext(RootRuntimeContext actual,ContinuityStorePort.Session same)throws IOException {
        synchronized(this) { StrictJson.require(writer!=null && current==actual,"ordinary Family restore lost its installed physical context"); }
        writer.requireSession(same); same.requireWriter(lock);
    }
    private void requireBatch(Batch batch,ContinuityStorePort.Session same)throws IOException {
        requireContext(batch.context(),same);
        batch.original().scope().requireCurrent(same);
    }
    private static Map<Slot, Body> readBodies(ContinuityStorePort.Session same, ContinuityState head) throws IOException {
        var result = new EnumMap<Slot, Body>(Slot.class);
        for (Slot slot : SLOTS) {
            var original = reference(head, slot);
            result.put(slot, new Body(original, read(same, original)));
        }
        return result;
    }
    private static DomainBodies.BodyRef reference(ContinuityState head,Slot slot)throws IOException {
        var value=DomainBodies.reference(head,slot).orElseThrow(()->new IOException("actual ordinary Family source body absent: "+slot));
        StrictJson.require(value.slot()==slot && value.contractSchema().equals(FamilyDomainSource.schema(slot)),"ordinary Family source schema differs");
        return value;
    }
    private static byte[] read(ContinuityStorePort.Session same,DomainBodies.BodyRef body)throws IOException {
        var pin=same.capturePin(body.payload(),MAX);
        StrictJson.require(pin.identity().equals(body.identity()),"ordinary Family original body native identity changed");
        byte[] bytes=same.readPinned(pin,MAX); same.verifyPin(pin); return bytes;
    }
    private static WriterContracts.Receipt readReceipt(RootRuntimeContext actual,ContinuityStorePort.Session same,
            Slot slot,DomainBodies.PreparedImport prepared)throws IOException {
        if(prepared==null)throw new IOException("ordinary Family UNKNOWN import has no retained preparation");
        long sequence=Math.addExact(prepared.predecessor().state().sequence(),1);
        Path expected=actual.core().configuration().ledger().event(sequence).toAbsolutePath().normalize();
        var pins=same.head().documents().stream().filter(pin->Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(expected)).toList();
        if(pins.size()!=1)throw new IOException("ordinary Family import outcome remains UNKNOWN; no replay");
        var edge=same.readHistoricalTransition(pins.getFirst());
        StrictJson.require(edge.sequence()==sequence && DomainBodies.IMPORT_KIND.equals(edge.kind()),"ordinary Family original import event changed");
        var recorded=same.requireHistoricalImport(slot,sequence,ContinuityJson.digest(edge.after().toJson()));
        same.requireCommitted(prepared,recorded.receipt()); return recorded.receipt();
    }
}
