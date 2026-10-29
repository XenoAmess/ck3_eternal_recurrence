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
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration;
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
    private record Batch(RootRuntimeContext context, RootRestorationOriginalProof proof,
            RootRestorationOriginalProof.Original source, RestoreCheckpointService.ReboundOrigin origin,
            Map<Slot,Retained> slots) { }
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
        Batch batch;
        synchronized(this) { batch=batches.get(source.basis().sha256()); }
        if(batch==null) {
            var episode=new Episode(source.pair().frame().frame().episodeRunId(),source.pair().frame().frame().identity().player());
            var slots=new EnumMap<Slot,Retained>(Slot.class);
            for(Slot slot:SLOTS) {
                // The restore reducer retains the attachment predecessor's complete domains. Preserve them,
                // including any UNKNOWN commitment, while separately pinning the actual original SAVE source.
                var saved=reference(source.originalSavedHead(),slot);
                var previous=reference(source.attachmentHead(),slot);
                byte[] savedBytes=read(same,saved), previousBytes=read(same,previous);
                var transition=new FamilyOrdinaryRestoreMigration.Transition(data.savedOwner(),data.previousOwner(),
                        data.restoredOwner(),episode,source.material().reference(),source.basis(),saved.payload(),previous.payload());
                var output=FamilyOrdinaryRestoreMigration.derive(slot,savedBytes,previousBytes,transition);
                slots.put(slot,new Retained(saved,previous,savedBytes,previousBytes,transition,output));
            }
            batch=new Batch(actual,proof,source,origin,Map.copyOf(slots));
            synchronized(this) {
                StrictJson.require(batches.size()<192 && batches.putIfAbsent(source.basis().sha256(),batch)==null,
                        "bounded ordinary Family restore history exhausted or raced its original writer");
            }
        }
        requireBatch(batch,same);
        var result=new java.util.ArrayList<DomainBodies.BodyRef>();
        for(Slot slot:SLOTS) {
            requireBatch(batch,same); var retained=batch.slots().get(slot);
            var read=same.readDomain(slot);
            if(!(read instanceof DomainBodies.Available known))throw new IOException("ordinary Family current full body unavailable: "+slot);
            FamilyOrdinaryRestoreMigration.requireCompatibleCurrent(slot,retained.savedBytes,retained.previousBytes,known.canonicalBody(),retained.transition);
            if(retained.attempted && retained.receipt==null)retained.receipt=readReceipt(actual,same,slot,retained.prepared);
            if(retained.receipt!=null)same.requireCommitted(retained.prepared,retained.receipt);
            if(Arrays.equals(retained.output,known.canonicalBody())) { result.add(known.reference()); continue; }
            if(retained.attempted)throw new IOException("ordinary Family original import remains UNKNOWN; never reissue it");
            StrictJson.require(known.reference().equals(retained.previous),"ordinary Family actual CAS predecessor native identity changed");
            var output=archive.preserveArtifact(same,retained.output,MAX);
            var input=StrictJson.object().put("schema",SCHEMA).put("slot",slot.name());
            input.set("basis",batch.source().basis().toJson()); input.set("saved",retained.saved.toJson());
            input.set("previous",retained.previous.toJson()); input.set("transition",retained.transition.toJson());
            byte[] bytes=StrictJson.canonical(input,MAX);
            String identity="family-ordinary-restore-"+slot.name()+"-"+batch.source().basis().sha256()+"-"+retained.previous.payload().sha256();
            var evidence=new LinkedHashSet<ExactRef>(batch.source().evidence());
            evidence.addAll(List.of(retained.saved.payload(),retained.previous.payload(),output,batch.source().material().reference()));
            var request=new DomainBodies.ImportRequest(slot,FamilyDomainSource.schema(slot),output,bytes,List.copyOf(evidence),identity);
            synchronized(this) {
                StrictJson.require(authorizations.size()<576 || authorizations.containsKey(identity),"bounded ordinary Family import custody exhausted");
                var authorization=new Authorization(batch,slot,ActionCodec.sha256(bytes),ActionCodec.sha256(retained.output));
                var prior=authorizations.putIfAbsent(identity,authorization);
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
                && batch.source().basis().equals(ExactRef.fromJson(input.get("basis")))
                && retained.saved.equals(DomainBodies.BodyRef.fromJson(input.get("saved")))
                && retained.previous.equals(DomainBodies.BodyRef.fromJson(input.get("previous")))
                && retained.transition.equals(FamilyOrdinaryRestoreMigration.Transition.fromJson(input.get("transition"))),
                "ordinary Family import lost its original SAVE or actual replaced owner");
        byte[] expected=FamilyOrdinaryRestoreMigration.derive(slot,read(same,retained.saved),read(same,retained.previous),retained.transition);
        StrictJson.require(Arrays.equals(expected,actual) && Arrays.equals(actual,archive.readArtifact(same,request.originalBody(),MAX))
                && request.evidence().containsAll(List.of(batch.source().basis(),retained.saved.payload(),retained.previous.payload(),
                        batch.source().material().reference())),"ordinary Family original producer replay differs");
        requireBatch(batch,same);
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",ContinuityJson.digest(head.toJson()))
                .put("input",authorization.inputSha256()).put("output",authorization.outputSha256())));
    }
    private void requireContext(RootRuntimeContext actual,ContinuityStorePort.Session same)throws IOException {
        synchronized(this) { StrictJson.require(writer!=null && current==actual,"ordinary Family restore lost its installed physical context"); }
        writer.requireSession(same); same.requireWriter(lock);
    }
    private void requireBatch(Batch batch,ContinuityStorePort.Session same)throws IOException {
        requireContext(batch.context(),same); batch.proof().requireCurrent(same);
        batch.source().requireImportPredecessor(same,same.head()); batch.origin().requireOriginal(same);
        StrictJson.require(batch.origin()==batch.context().requireRestoredOrigin(same),"ordinary Family restore changed its private origin issuer");
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
