package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual restored Root's explicit original-ordinary custody consumer; it publishes no SAVE or process and grants no readiness. */
public final class RootSavedOrdinaryReopen {
    private RootSavedOrdinaryReopen() { }
    public static final class Reopened {
        private final RootRuntimeContext context;private final RestoreCheckpointService service;
        private final RestoreCheckpointService.RestoreBinding binding;private final RootRestorationOriginalProof proof;
        private final SavedAttachmentSourceStore.SavedMaterial material;
        private Reopened(RootRuntimeContext context,RestoreCheckpointService service,
                RestoreCheckpointService.RestoreBinding binding,RootRestorationOriginalProof proof,
                SavedAttachmentSourceStore.SavedMaterial material) {
            this.context=context;this.service=service;this.binding=binding;this.proof=proof;this.material=material;
        }
        public SavedAttachmentSourceStore.SavedMaterial material(){return material;}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);context.requireRestorationOriginal(same,binding);
            service.requireRetainedOriginal(same,binding);proof.requireCurrent(same);
            context.savedMaterials().requireOwn(material);material.requirePhysical(same);
            var driverSession=context.adopted().session();
            StrictJson.require(binding.pair().equals(material.pair())
                    &&binding.savedMaterial().witness().equals(material.witness())
                    &&binding.savedMaterial().session().equals(material.session())
                    &&binding.savedMaterial().sourceSemantic().equals(material.sourceSemantic())
                    &&binding.session().game().equals(context.game().generation())
                    &&binding.session().sessionId().equals(context.game().sessionId())
                    &&binding.session().machineId().equals(driverSession.machineId())
                    &&binding.session().game().equals(driverSession.game())
                    &&binding.session().sessionId().equals(driverSession.sessionId())
                    &&binding.source().equals(context.source()),
                    "reopened ordinary original or actual replacement context changed");
        }
    }
    /** Original archived authority for the pre-REBIND phase of the same physical successor. */
    public static final class Committed {
        private final RootRuntimeContext context;
        private final DriverBootstrap.Adopted driver;
        private final CommittedData original;

        private Committed(RootRuntimeContext context, DriverBootstrap.Adopted driver, CommittedData original) {
            this.context = context;
            this.driver = driver;
            this.original = original;
        }
        public CheckpointPair pair() { return original.pair(); }
        public CheckpointPair.FileWitness materialWitness() { return original.materialWitness(); }
        public WriterContracts.Pin attachment() { return original.edge().eventPin(); }
        public ContinuityState attachmentHead() { return original.edge().after(); }
        public SessionIdentity successor() { return original.successor(); }

        public void requireCurrent(ContinuityStorePort.Session same) throws IOException {
            context.writer().requireSession(same);
            requirePhysicalOwner(context, driver, attachment(), successor());
            if (context.adopted() != driver) throw new IOException("committed imported custody lost its exact installed Driver");
            requireAttachmentOrDomainImports(same, original);
        }

        /** Captures the four semantic originals from the actual installed, held successor on its new connection. */
        public SemanticEvidence captureSemantic(ContinuityStorePort.Session same, Instant deadline) throws IOException {
            requireCurrent(same);
            var physical = context.remainingDomains().lifecycle().physical();
            return physical.withSnapshot(same, deadline, lease -> {
                var frame = lease.ordinary().orElseThrow(() -> new IOException("same committed imported successor is not a living ordinary frame"));
                var prior = pair().frame().frame();
                if (!lease.fullSnapshot().actual().session().equals(driver.session()) || !frame.source().equals(context.source())
                        || !frame.sessionId().equals(successor().sessionId()) || !frame.identity().game().equals(successor().game())
                        || !frame.identity().frame().episodeRunId().equals(prior.episodeRunId())
                        || !frame.identity().frame().identity().dateRaw().equals(prior.identity().dateRaw())
                        || !frame.identity().frame().identity().player().equals(prior.identity().player()))
                    throw new IOException("new committed imported SEM crossed the original actor, date, source or successor connection");
                var semantic = physical.semantic(same, successor(), lease);
                requireCurrent(same);
                return semantic;
            });
        }
    }

    /** Exact v5 attachment DATA; its construction alone grants no current Game or writer authority. */
    record CommittedData(WriterContracts.HistoricalTransition edge, String attachmentDigest,
            CheckpointPair pair, CheckpointPair.FileWitness materialWitness, SessionIdentity successor) { }

    static CommittedData readImmediateCommitted(ContinuityStorePort.Session same, WriterContracts.Pin attachment) throws IOException {
        return readCommitted(same, attachment, true);
    }

    private static CommittedData readCommitted(ContinuityStorePort.Session same, WriterContracts.Pin attachment,
            boolean immediate) throws IOException {
        var head = same.head();
        var edge = same.readHistoricalTransition(attachment);
        var attached = edge.after().toJson();
        String digest = ContinuityJson.digest(attached);
        if (!SavedAttachmentAuthority.KIND.equals(edge.kind()) || !edge.eventPin().equals(attachment)
                || head.snapshotNeedsRecovery() || !head.indexRepairs().isEmpty()
                || immediate && (edge.sequence() != head.state().sequence() || !digest.equals(head.digest())))
            throw new IOException("a clean committed imported ordinary attachment is required in this canonical history");
        try {
            var details = ContinuityJson.parseObject(edge.details(), ContinuityJson.DOCUMENT_MAX_BYTES);
            var sources = SavedAttachmentSourceStore.Sources.decode(details.get(SavedAttachmentSourceStore.SOURCES_DETAIL));
            var origin = sources.importedOrigin().orElseThrow(() -> new IOException("actual imported ordinary material origin is absent"));
            var basis = SavedAttachmentSourceStore.importedRecoveryBasis(details)
                    .orElseThrow(() -> new IOException("actual committed imported attachment READ basis is absent"));
            var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(details.get(SavedAttachmentAuthority.PAIR_DETAIL)));
            var opening = ContinuityJson.object(attached.get("latest_binding"));
            var successor = new SessionIdentity(StrictJson.text(opening.get("machine_id")),
                    GameGeneration.fromJson(opening.get("game")), StrictJson.text(opening.get("session_id")));
            if (!pair.save().equals(sources.physicalSaveWitness().orElse(null))
                    || sources.kind() != SavedCheckpointMaterial.Kind.ORDINARY || !basis.departed().equals(origin.owner())
                    || !successor.equals(basis.successor()) || !successor.game().equals(GameGeneration.fromJson(attached.get("game_binding")))
                    || !basis.requestId().equals(StrictJson.text(details.get("evidence_id")))
                    || !basis.secondNative().reference().equals(sources.restoredNative())
                    || !sources.restoredNative().equals(ExactRef.fromJson(opening.get("original_native_packet"))))
                throw new IOException("committed imported material, READ or successor differs from the original attachment");
            return new CommittedData(edge, digest, pair, sources.material(), successor);
        } catch (IllegalArgumentException | java.time.DateTimeException invalid) {
            throw new IOException("invalid committed imported ordinary attachment DATA", invalid);
        }
    }

    static void requireAttachmentOrDomainImports(ContinuityStorePort.Session same, CommittedData original) throws IOException {
        var head = same.head();
        if (head.snapshotNeedsRecovery() || !head.indexRepairs().isEmpty())
            throw new IOException("committed imported ordinary custody requires a clean canonical head");
        same.verifyPin(original.edge().eventPin());
        if (!head.digest().equals(original.attachmentDigest()))
            same.requireDomainImportContinuation(original.edge().sequence(), original.attachmentDigest());
    }

    public static Committed reopenCommitted(RootRuntimeContext context, ContinuityStorePort.Session same,
            DriverBootstrap.Adopted driver, WriterContracts.Pin attachment, Instant deadline) throws IOException {
        Objects.requireNonNull(context).writer().requireSession(same);
        context.requireCurrent(deadline);
        driver.requireCommittedImported(attachment);
        var original = readCommitted(same, attachment, false);
        var result = new Committed(context, driver, original);
        result.requireCurrent(same);
        return result;
    }

    private static void requirePhysicalOwner(RootRuntimeContext context, DriverBootstrap.Adopted driver,
            WriterContracts.Pin attachment, SessionIdentity successor) throws IOException {
        driver.requireCommittedImported(attachment);
        var session = driver.session();
        var game = context.game();
        var transport = context.transport();
        driver.producer().requireSameTransport(transport, context.source());
        var diagnostics = transport.diagnostics();
        if (driver.status() != DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED || !context.source().equals(driver.source())
                || !successor.equals(new SessionIdentity(game.machineId(), game.generation(), game.sessionId()))
                || !successor.equals(new SessionIdentity(session.machineId(), session.game(), session.sessionId()))
                || diagnostics.session().filter(session::equals).isEmpty() || diagnostics.terminalFailure().isPresent())
            throw new IOException("committed imported ordinary custody requires its exact current Driver, Game and Native connection");
    }

    /** Called after the actual restored context is bound and before its domain initialization/Host publication. */
    public static Reopened reopen(RootRuntimeContext context,ContinuityStorePort.Session same,
            RestoreCheckpointService actualPreviousService,RestoreCheckpointService.RestoreBinding actualBinding)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(actualPreviousService);Objects.requireNonNull(actualBinding);
        context.writer().requireSession(same);context.requireRestorationOriginal(same,actualBinding);
        if(actualBinding.savedMaterial().kind()!=SavedCheckpointMaterial.Kind.ORDINARY)
            throw new IOException("FIRST checkpoint restoration cannot enter ordinary custody");
        String head=same.head().digest();
        var proof=RootRestorationOriginalProof.requireRetained(context,same,actualBinding);proof.requireCurrent(same);
        var retained=context.restorationOriginal(same);
        var original=RootRestorationOriginalProof.replayOriginal(context,same,retained.basis());
        original.requireImportPredecessor(same,same.head());
        StrictJson.require(original.material().kind()==SavedCheckpointMaterial.Kind.ORDINARY
                &&original.material().witness().equals(actualBinding.savedMaterial().witness())
                &&original.pair().equals(actualBinding.pair())
                &&original.semantic().equals(actualBinding.semantic())
                &&original.game().equals(actualBinding.session().game())
                &&original.sessionId().equals(actualBinding.session().sessionId())
                &&original.source().equals(context.source())
                &&ContinuityJson.same(original.attachmentHead().toJson(),actualBinding.attachment().head().toJson()),
                "private restored Root source/reducer proof differs from its actual ordinary admission");
        var material=actualPreviousService.reopenOrdinaryMaterial(same,actualBinding,context.savedMaterials(),
                actualBinding.session(),actualBinding.semantic());
        StrictJson.require(head.equals(same.head().digest()),"ordinary original custody import mutated the canonical writer");
        var result=new Reopened(context,actualPreviousService,actualBinding,proof,material);result.requireCurrent(same);return result;
    }
}
