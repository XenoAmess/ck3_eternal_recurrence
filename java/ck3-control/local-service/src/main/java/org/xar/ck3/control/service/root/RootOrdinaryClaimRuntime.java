package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Concrete original-writer claim registration, actual legacy import and same-context products.
 * No public constructor accepts a SeedAuthority, PermitAuthority, imported State or Ready callback.
 */
public final class RootOrdinaryClaimRuntime {
    public static final String MANIFEST_SCHEMA = "xar.java.ordinary-original-claim-census/v1";
    public static final String PERMIT_GAP = "INCOMPLETE_ORDINARY_NEXT_INTENT: no source-bound independent event/save consumption verifier is selected; ACK, outgoing send, new event instance or window disappearance cannot release an earlier claim";
    private RootOrdinaryClaimRuntime() { }
    public record Sources(ExactRef runtime, ExactRef originalProducer, ExactRef domainReducer, ExactRef pureClaimReducer,
            ExactRef legacyClaimProducer, ExactRef legacyHostRelease, List<ExactRef> completeProducers) {
        public Sources {
            completeProducers = List.copyOf(completeProducers);
            StrictJson.require(!completeProducers.isEmpty() && completeProducers.size() <= 64
                    && completeProducers.stream().distinct().count() == completeProducers.size(), "complete unique ordinary claim producer closure required");
            for (ExactRef source : List.of(runtime, originalProducer, domainReducer, pureClaimReducer, legacyClaimProducer, legacyHostRelease))
                StrictJson.require(source.bytes() > 0 && completeProducers.contains(source), "actual ordinary implementation is outside the complete selected producer closure");
            completeProducers.forEach(source -> StrictJson.require(source.bytes() > 0, "empty source cannot authorize an ordinary original import"));
        }
    }
    public static final class PermitUnavailable extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        public PermitUnavailable() { super(PERMIT_GAP); }
    }
    /** Explicit refusal is the original default trust policy. It is never represented as a successful verifier. */
    static final class SourceConsumptionAuthority implements OrdinaryClaimDomain.PermitAuthority {
        @Override public OrdinaryOnceClaims.Permit requireNextIntent(Session same, OrdinaryOnceClaims.State before, OrdinaryOnceClaims.Request request) {
            Objects.requireNonNull(same); Objects.requireNonNull(before); Objects.requireNonNull(request);
            throw new PermitUnavailable();
        }
        @Override public void verifyOriginal(OrdinaryOnceClaims.State before, OrdinaryOnceClaims.Request request, OrdinaryOnceClaims.Permit permit) {
            Objects.requireNonNull(before); Objects.requireNonNull(request); Objects.requireNonNull(permit);
            throw new PermitUnavailable();
        }
    }
    public static Prepared prepareOrdinary(Path writerLock,Sources sources) {
        return new Prepared(writerLock,sources,true);
    }
    public static final class Prepared {
        private final Path originalWriterLock;
        private final Sources sources;
        private final boolean ordinary;
        private final OrdinaryClaimDomain claims;
        private final DomainBodies.Registration registration;
        private final IdentityHashMap<RootRuntimeContext, Installed> installed = new IdentityHashMap<>();
        private final Map<ExactRef, Ticket> originalCaptures = new LinkedHashMap<>();
        private RootApplicationAssembly.Core core;
        private volatile RootRuntimeContext current;
        public Prepared(Path originalWriterLock, Sources sources) {this(originalWriterLock,sources,false);}
        private Prepared(Path originalWriterLock,Sources sources,boolean ordinary) {
            this.ordinary=ordinary;
            this.originalWriterLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();
            this.sources = Objects.requireNonNull(sources);
            claims = new OrdinaryClaimDomain(this.originalWriterLock, new OriginalArtifacts(), new SourceConsumptionAuthority());
            registration = claims.registration(sources.completeProducers(), this::readOriginalSeed);
        }
        /** Pre-Core definitions only. Core construction and historical domain reads do not invoke live minting. */
        public DomainBodies.Registration registration() { return registration; }
        public List<DomainBodies.Registration> domainRegistrations() { return List.of(registration); }
        public Sources sources() { return sources; }
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            Objects.requireNonNull(actual);
            StrictJson.require(core == null && actual.writer().originalLockPath().equals(originalWriterLock)
                    && actual.archive().writer() == actual.writer(), "ordinary claims bind once to the actual sole writer/archive authority");
            core = actual;
        }
        /** Before physical Driver binding this creates definitions only; no seed or permit is inferred. */
        public synchronized Installed install(RootRuntimeContext context) throws IOException {
            requireCore(context); current=context; Installed old = installed.get(context); if (old != null) return old;
            StrictJson.require(installed.size() < 64, "bounded physical ordinary runtime history required");
            if(!ordinary) {
            for (Class<?> actual : List.of(RootOrdinaryClaimRuntime.class, RootOrdinaryClaimOriginals.class, OrdinaryClaimDomain.class, OrdinaryOnceClaims.class))
                context.game().launchPlan().sources().requireLoadedClass(actual);
            for (ExactRef source : sources.completeProducers()) {
                var observed = SharedSourceFiles.observe(Path.of(source.path()));
                StrictJson.require(observed.source().bytes() == source.bytes() && observed.source().sha256().equals(source.sha256()), "ordinary source pin changed before installation");
                SharedSourceFiles.assertUnchanged(observed);
            }
            }
            Installed actual = new Installed(this, context); installed.put(context, actual); return actual;
        }
        /** Root invokes this only after actual physical Driver binding and before ordinary Ready. */
        public void importOriginal(RootRuntimeContext context, Session same, Instant deadline) throws IOException {
            Installed actual = install(context); actual.requireContext(context); var root = requireCore(context);
            root.writer().requireSession(same); context.requireCurrent(deadline);
            DomainBodies.Read existing = same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
            if (existing instanceof DomainBodies.Available) {
                OrdinaryOnceClaims.State retained = requireRetainedOriginal(same);
                StrictJson.require(retained.machineId().equals(context.game().machineId()), "retained ordinary domain belongs to another machine");
                return; // Existing canonical claims are retained; this cannot replace them with an empty import.
            }
            StrictJson.require(existing instanceof DomainBodies.Unavailable unavailable
                    && unavailable.reason() == DomainBodies.Reason.UNIMPORTED,
                    "invalid, replaced, incompatible or unavailable existing claims cannot be initialized as a new seed");
            Complete frame;
            try { frame = context.adopted().observations().observe(deadline); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("actual ordinary claim source observation interrupted", interrupted); }
            requireFrame(context, frame); var archive = context.archive().withSession(same);
            var basis = NativeEffectEvidence.basis(frame);
            Complete reconstructed = context.frameLoader().load(basis, archive);
            StrictJson.require(reconstructed.equals(frame), "ordinary seed source was not reconstructed from the original Native packet and Driver facts");
            Path directory = originalDirectory(frame);
            var captured = RootOrdinaryClaimOriginals.capture(directory);
            var retained = new ArrayList<ExactRef>(); var originals = StrictJson.object(); var rows = originals.putArray("claims");
            for (var original : captured.originals()) {
                root.writer().requireSession(same); var pin = same.capturePin(original.source(), RootOrdinaryClaimOriginals.MAX_FILE_BYTES);
                byte[] bytes = same.readPinned(pin, RootOrdinaryClaimOriginals.MAX_FILE_BYTES);
                StrictJson.require(Arrays.equals(bytes, original.bytes()), "actual legacy source changed before archive import");
                ExactRef copy = archive.preserveMaterial(new RawJson(bytes));
                StrictJson.require(Arrays.equals(archive.loadMaterial(copy).bytes(), bytes), "legacy claim original archive readback differs");
                retained.add(copy); same.verifyPin(pin);
                var row = rows.addObject(); row.set("source", original.source().toJson()); row.set("retained", copy.toJson());
                var file = original.witness().nativeFile(); row.putObject("file_identity")
                        .put("volume_serial_decimal", file.volumeSerialDecimal()).put("file_id_decimal", file.fileIdDecimal())
                        .put("creation_filetime_decimal", file.creationFiletimeDecimal()).put("last_write_filetime_decimal", file.lastWriteFiletimeDecimal());
            }
            captured.requireUnchanged(); var head = same.head();
            originals.put("schema", MANIFEST_SCHEMA).put("machine_id", context.game().machineId()).put("observed_at_utc", context.clock().instant().toString())
                    .put("head_sequence", head.state().sequence()).put("head_digest", head.digest()).put("claim_directory", directory.toString());
            originals.putObject("source_frame").set("native_frame", basis.nativeFrame().toJson());
            ((ObjectNode) originals.get("source_frame")).set("driver_facts", basis.driverFacts().toJson());
            var directoryIdentity = captured.identity(); originals.putObject("directory_identity")
                    .put("volume_serial_decimal", directoryIdentity.volumeSerialDecimal()).put("file_id_decimal", directoryIdentity.fileIdDecimal())
                    .put("creation_filetime_decimal", directoryIdentity.creationFiletimeDecimal());
            byte[] manifestBytes = StrictJson.canonical(originals, OrdinaryOnceClaims.MAX_BYTES);
            ExactRef manifest = archive.preserveMaterial(new RawJson(manifestBytes));
            StrictJson.require(Arrays.equals(archive.loadMaterial(manifest).bytes(), manifestBytes), "complete original census archive readback differs");
            var ticket = new Ticket(context, frame, captured, List.copyOf(retained), manifestBytes, head.state().sequence(), head.digest());
            synchronized (this) {
                StrictJson.require(originalCaptures.isEmpty(), "one actual original import capture per canonical claim domain; failed attempts are not silently replayed");
                originalCaptures.put(manifest, ticket);
            }
            // Both preview and commit invoke the real registered OrdinaryClaimDomain reducer in this original writer lock.
            // The SeedAuthority below rechecks the exact capture token, original files, native directory and current head.
            OrdinaryOnceClaims.State seed = readOriginalSeed(manifest, head.state());
            claims.importOriginal(same, manifest, seed); root.writer().requireSession(same);
            var imported = same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
            StrictJson.require(imported instanceof DomainBodies.Available available
                    && Arrays.equals(available.canonicalBody(), OrdinaryOnceClaims.encode(seed)), "actual canonical ordinary reducer import/readback differs");
            context.requireCurrent(deadline);
        }
        /** A genuine fresh observed campaign starts its own empty automation claims, never a legacy directory import. */
        public void initializeFresh(RootRuntimeContext context,Session same,FreshCampaignContext actual)throws IOException {
            install(context).requireContext(context);requireCore(context).writer().requireSession(same);actual.requireCurrent(same);
            StrictJson.require(actual.context()==context,"fresh ordinary claims crossed the actual physical campaign");
            var existing=same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
            if(existing instanceof DomainBodies.Available){requireRetainedOriginal(same);return;}
            if(!(existing instanceof DomainBodies.Unavailable missing)||missing.reason()!=DomainBodies.Reason.UNIMPORTED)
                throw new IOException("fresh ordinary claims cannot erase an unavailable existing domain");
            actual.requireInitializationPredecessor(same,same.head());var basis=actual.preserveOriginal(same);
            claims.initializeFresh(same,basis,new OrdinaryOnceClaims.State(context.game().machineId(),List.of(),List.of(),List.of()));
            actual.requireCurrent(same);
        }
        /** Read-only cold qualification of an already committed domain under the same actual writer.
         * It does not invoke SeedAuthority, consume a permit, publish bytes or grant a fresh claim.
         * The writer verifies the original canonical history and native payload identity.
         */
        public OrdinaryOnceClaims.State requireRetainedOriginal(Session same) throws IOException {
            var root = requireCore(); root.writer().requireSession(same);
            var head = same.head();
            DomainBodies.Read read = same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
            StrictJson.require(read instanceof DomainBodies.Available, "complete original committed claim domain is unavailable; never replace it with an empty seed");
            var actual = (DomainBodies.Available) read;
            StrictJson.require(actual.reference().contractSchema().equals(OrdinaryOnceClaims.SCHEMA), "retained ordinary claim contract changed");
            OrdinaryOnceClaims.State retained = OrdinaryOnceClaims.decode(actual.canonicalBody());
            StrictJson.require(retained.machineId().equals(root.configuration().machineId())
                    && Arrays.equals(OrdinaryOnceClaims.encode(retained), actual.canonicalBody()), "retained claim machine or canonical body differs");
            var archive = root.archive().withSession(same);
            for (var claim : retained.claims()) {
                byte[] original = archive.loadMaterial(claim.original()).bytes();
                StrictJson.require(Arrays.equals(original, OrdinaryOnceClaims.encodeClaim(claim.claim())), "cold retained claim differs from its original immutable publication");
            }
            for (var blocker : retained.legacyBlockers()) {
                var original = RootOrdinaryClaimOriginals.decodeLegacy(archive.loadMaterial(blocker.originalClaim()).bytes());
                StrictJson.require(original.gamePid() == blocker.gamePid() && original.actorId() == blocker.actorId()
                        && original.interactionKey().equals(blocker.interactionKey()) && original.recipientId() == blocker.recipientId(),
                        "cold unresolved blocker differs from its retained complete legacy original");
            }
            // No positive consumption could have been committed by this selected refusing authority.
            // A changed source closure cannot import historical permission through an equal JSON shape.
            StrictJson.require(retained.consumptions().isEmpty() && retained.claims().stream().allMatch(row -> row.claim().lineage().isEmpty()),
                    "historical next-intent consumption requires its original qualified source authority");
            for (var pin : actual.headSources()) same.verifyPin(pin);
            same.verifyPin(same.capturePin(actual.reference().payload(), OrdinaryOnceClaims.MAX_BYTES));
            var after = same.head();
            StrictJson.require(Arrays.equals(head.state().canonicalBytes(), after.state().canonicalBytes()) && head.documents().equals(after.documents())
                    && head.absent().equals(after.absent()) && head.indexRepairs().equals(after.indexRepairs())
                    && head.snapshotNeedsRecovery() == after.snapshotNeedsRecovery(), "cold retained qualification lost its original locked head");
            return retained;
        }
        private OrdinaryOnceClaims.State readOriginalSeed(ExactRef manifest, ContinuityState actualHead) {
            try {
                RootApplicationAssembly.Core root = requireCore(); Session same = root.writer().borrowedSession(); root.writer().requireSession(same);
                var actual=current;
                if(actual!=null&&FreshCampaignContext.isOriginal(actual,same,manifest)) {
                    var fresh=FreshCampaignContext.replayOriginal(actual,same,manifest);
                    StrictJson.require(actualHead.machineId().equals(fresh.observation().machineId()),
                            "fresh ordinary claims belong to another writer machine");
                    return new OrdinaryOnceClaims.State(actualHead.machineId(),List.of(),List.of(),List.of());
                }
                Ticket ticket; synchronized (this) { ticket = originalCaptures.get(manifest); }
                StrictJson.require(ticket != null, "source JSON or a constructor cannot mint an actual original claim census");
                requireCore(ticket.context()); requireFrame(ticket.context(), ticket.frame());
                StrictJson.require(actualHead.machineId().equals(ticket.context().game().machineId()) && actualHead.sequence() == ticket.headSequence()
                        && same.head().digest().equals(ticket.headDigest()), "ordinary original import lost its actual locked predecessor");
                byte[] raw = root.archive().withSession(same).loadMaterial(manifest).bytes();
                StrictJson.require(Arrays.equals(raw, ticket.manifestBytes()), "actual complete source census changed");
                var node = StrictJson.object(StrictJson.parse(raw, OrdinaryOnceClaims.MAX_BYTES), Set.of("schema", "machine_id", "observed_at_utc", "head_sequence", "head_digest",
                        "claim_directory", "source_frame", "directory_identity", "claims"));
                StrictJson.require(MANIFEST_SCHEMA.equals(StrictJson.text(node.get("schema"))), "original claim census version changed");
                var originalFrame = StrictJson.object(node.get("source_frame"), Set.of("native_frame", "driver_facts"));
                var before = root.frameLoader().load(new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(originalFrame.get("native_frame")), ExactRef.fromJson(originalFrame.get("driver_facts"))), root.archive().withSession(same));
                StrictJson.require(before.equals(ticket.frame()) && originalDirectory(before).equals(ticket.captured().directory()), "actual original census crossed its Native/Driver source");
                ticket.captured().requireUnchanged();
                for (int index = 0; index < ticket.retained().size(); index++)
                    StrictJson.require(Arrays.equals(root.archive().withSession(same).loadMaterial(ticket.retained().get(index)).bytes(), ticket.captured().originals().get(index).bytes()), "retained original claim bytes changed");
                return ticket.captured().state(actualHead.machineId(), ticket.retained());
            } catch (IOException failure) { throw new UncheckedIOException("actual original claim source replay unavailable", failure); }
        }
        private synchronized RootApplicationAssembly.Core requireCore() {
            StrictJson.require(core != null, "actual original Core has not been bound to ordinary claims"); return core;
        }
        private RootApplicationAssembly.Core requireCore(RootRuntimeContext context) {
            var actual = requireCore(); StrictJson.require(Objects.requireNonNull(context).core() == actual
                    && context.writer() == actual.writer() && context.archive() == actual.archive(), "ordinary runtime crossed the actual sole writer/archive Core"); return actual;
        }
        private final class OriginalArtifacts implements OrdinaryClaimDomain.Artifacts {
            @Override public ExactRef publish(Session same, byte[] original) {
                try { var root = requireCore(); root.writer().requireSession(same); return root.archive().withSession(same).preserveMaterial(new RawJson(original)); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public byte[] read(ExactRef original) {
                try { var root = requireCore(); var same = root.writer().borrowedSession(); root.writer().requireSession(same); return root.archive().withSession(same).loadMaterial(original).bytes(); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
        }
    }
    public static final class Installed {
        private final Prepared prepared; private final RootRuntimeContext context;
        private Installed(Prepared prepared, RootRuntimeContext context) { this.prepared = prepared; this.context = context; }
        public void requireContext(RootRuntimeContext actual) { StrictJson.require(actual == context && prepared.requireCore(actual) == context.core(), "ordinary claim products belong to another actual context"); }
        /** Product identity only. The domain still rejects every action until its real original import exists. */
        public OrdinaryClaimDomain claims() { return prepared.claims; }
        public boolean nextIntentConsumptionVerifierInstalled() { return false; }
    }
    private record Ticket(RootRuntimeContext context, Complete frame, RootOrdinaryClaimOriginals.Captured captured, List<ExactRef> retained,
            byte[] manifestBytes, long headSequence, String headDigest) {
        private Ticket { retained = List.copyOf(retained); manifestBytes = manifestBytes.clone(); }
        @Override public byte[] manifestBytes() { return manifestBytes.clone(); }
    }
    private static void requireFrame(RootRuntimeContext context, Complete actual) {
        StrictJson.require(actual.identity().machineId().equals(context.game().machineId()) && actual.identity().game().equals(context.game().generation())
                && actual.source().equals(context.source()) && actual.sessionId().equals(context.game().sessionId()), "ordinary original capture is not from the actual physical Native/Driver source");
    }
    private static Path originalDirectory(Complete actual) {
        Obj paths = OpportunityJson.object(actual.semantic().get("capability_session_paths"), "actual source-bound capability paths");
        String originalDriver = OpportunityJson.text(paths.get("driver_state_path"), "actual original Driver state path");
        Path path = Path.of(originalDriver);
        StrictJson.require(path.isAbsolute() && path.getParent() != null, "actual source-bound Driver state parent is unavailable");
        return path.toAbsolutePath().normalize().getParent().resolve("ordinary-interaction-actions");
    }
}
