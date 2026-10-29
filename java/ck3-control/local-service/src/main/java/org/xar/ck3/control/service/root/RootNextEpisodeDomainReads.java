package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Private NEXT or restored-FIRST domain reads borrow current physical originals without ordinary readiness or READ publication. */
public final class RootNextEpisodeDomainReads {
    private RootNextEpisodeDomainReads() { }

    @FunctionalInterface public interface PhysicalWork<T> {
        T run(RootLifecycleAuthority.SnapshotLease actual) throws IOException;
    }

    /** Root supplies the exact finite domain contract objects; callers cannot extend an installed instance. */
    static Installed install(RootRuntimeContext context, RootLifecycleAuthority actualPhysical,
            List<ReadContract<?>> actualAllowed) {
        return new Installed(context, actualPhysical, actualAllowed);
    }

    public static final class Installed {
        private final RootRuntimeContext context;
        private final RootLifecycleAuthority physical;
        private final RootReadContractCatalog catalog;
        private final Set<ReadContract<?>> allowed;
        private final ThreadLocal<Active> current = new ThreadLocal<>();
        private Installed(RootRuntimeContext context, RootLifecycleAuthority actualPhysical,
                List<ReadContract<?>> actualAllowed) {
            this.context = Objects.requireNonNull(context); physical = Objects.requireNonNull(actualPhysical);
            catalog = context.readCatalog();
            allowed = allowedContracts(catalog, actualAllowed);
        }

        /** The original private Core proof owns the candidate scope and the domain-import continuation. */
        <T> Captured<T> read(ContinuityStorePort.Session same, RootApplicationAssembly.EpisodeDomainInitializationProof proof,
                ReadContract<T> contract, Obj arguments, Instant deadline) throws IOException {
            Objects.requireNonNull(arguments); Objects.requireNonNull(deadline); Objects.requireNonNull(proof);
            requireContract(contract); context.writer().requireSession(same); proof.requireCurrent(same, context);
            require(context.clock().instant().isBefore(deadline) && !deadline.isAfter(proof.deadline()),
                    "episode domain read crossed its original private stage deadline");
            require(current.get() == null, "another episode domain read owns this physical callback");
            WriterContracts.Head original = same.head();
            Captured<T> captured = physical.withSnapshot(same, deadline, lease -> {
                proof.requireCurrent(same, context); lease.assertCurrent(same);
                Complete frame = lease.ordinary().orElseThrow(() -> new IOException("episode domain read lacks actual living native/Driver originals"));
                requireFrame(frame, proof); requireLivingPaused(frame);
                SessionPorts.SemanticEvidence semantic = physical.semantic(same, proof.afterSession(), lease);
                var request = new PlanningReadRequest(frame.identity(), context.source(), frame.sessionId(), contract.operation(), arguments, deadline);
                var active = new Active(same, proof, lease, frame, semantic, request, contract, original);
                current.set(active);
                try {
                    var queries = new PlanningReadCoordinator(catalog, context.core().journal(), this::guard,
                            context.transport(), context.archive(), context.clock());
                    PlanningReadResult<T> result = queries.read(same, contract, request);
                    assertActive(active, same, context, request, contract); unchanged(same, original);
                    var archive = context.archive().withSession(same);
                    var refs = new ArrayList<ExactRef>();
                    refs.addAll(List.of(frame.originalEvidence(), semantic.semantic(), semantic.driverStamp(), semantic.originalDriver(),
                            lease.freshFacts().semanticFactsEvidence(), lease.originalHello(), lease.originalHeartbeat()));
                    lease.sourceQualification().proof().ifPresent(refs::add);
                    refs.addAll(List.of(contract.sourceRef(), decoderSource(contract), context.source().sourceRef()));
                    if (result instanceof PlanningReadResult.Known<T> known) refs.add(known.originalReceipt());
                    var pins = new ArrayList<WriterContracts.Pin>();
                    for (ExactRef ref : refs) {
                        var pin = same.capturePin(ref, WriterContracts.MAX_PIN_BYTES); same.verifyPin(pin); pins.add(pin);
                    }
                    if (result instanceof PlanningReadResult.Known<T> known)
                        require(archive.loadRead(known.originalReceipt()).equals(known.receipt()), "episode domain read lost its actual immutable receipt");
                    return new Captured<>(this, proof, contract, result, frame, semantic, lease.sourceQualification().proof(),
                            original.state().sequence(), original.digest(), List.copyOf(pins));
                } finally { current.remove(); }
            });
            unchanged(same, original); proof.requireCurrent(same, context); return captured;
        }

        /** Only a live private read callback may lend its actual physical snapshot to a source-owned read admission. */
        public <T> Optional<T> withCurrent(ContinuityStorePort.Session same, RootRuntimeContext actualContext,
                PlanningReadRequest request, ReadContract<?> contract, PhysicalWork<T> work) throws IOException {
            Objects.requireNonNull(work); Active active = current.get(); if (active == null) return Optional.empty();
            assertActive(active, same, actualContext, request, contract);
            T result = Objects.requireNonNull(work.run(active.lease()), "physical domain admission cannot return null");
            assertActive(active, same, actualContext, request, contract); return Optional.of(result);
        }

        private PlanningReadGuard guard(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            Active active = current.get(); require(active != null, "episode domain read has no live private physical callback");
            try {
                assertActive(active, active.same(), context, request, contract); unchanged(active.same(), head);
                require(head.digest().equals(active.original().digest()), "episode domain query crossed its exact captured writer point");
                pinSource(active.same(), contract.sourceRef()); pinSource(active.same(), decoderSource(contract));
                pinSource(active.same(), context.source().sourceRef());
                contract.requiredCapability().ifPresent(capability -> require(active.lease().bridgeCapabilities().contains(capability),
                        "actual physical HELLO does not advertise this precise read capability"));
                var archive = context.archive().withSession(active.same());
                var values = active.lease().bridgeCapabilities().stream().sorted().<OpportunityJson.Value>map(OpportunityJson.Text::new).toList();
                var capabilities = new Obj(java.util.Map.of("bridge_capabilities", new OpportunityJson.Arr(values)));
                RawJson capabilityBytes = new RawJson(DriverJson.encode(capabilities));
                ExactRef capabilityRef = archive.preserveMaterial(capabilityBytes);
                require(capabilityBytes.equals(archive.loadMaterial(capabilityRef)), "physical HELLO capability projection changed in archive");
                var originals = new RootGuardEvidence.PhysicalReadOriginals(active.frame(), active.semantic(), active.lease().originalHello(),
                        active.lease().originalHeartbeat(), active.lease().sourceQualification().proof(), capabilityRef);
                String authorityId = context.core().authorityId();
                ExactRef basis = RootGuardEvidence.preservePhysicalRead(originals, contract.operation(), authorityId, archive, head);
                Instant until = active.lease().validUntil().isBefore(request.deadline()) ? active.lease().validUntil() : request.deadline();
                GuardEvidence binding = new GuardEvidence(new CommandOrigin.Gameplay(active.frame().identity()), context.source(),
                        active.frame().sessionId(), active.frame().connectionGeneration(), contract.operation(), active.frame().originalEvidence(),
                        active.lease().originalHello(), authorityId, active.frame().observedAt(), until, List.of(basis));
                require(RootGuardEvidence.loadFrame(binding, archive, context.frameLoader()).equals(active.frame()),
                        "physical read guard's archived native/Driver originals differ from the actual captured frame");
                RootGuardEvidence.requireHistory(binding, archive, active.same());
                assertActive(active, active.same(), context, request, contract);
                return new PlanningReadGuard(binding, true, true, true, active.frame().fullBindingSha256());
            } catch (IOException failure) { throw new UncheckedIOException("actual episode domain read guard unavailable", failure); }
        }

        private void assertActive(Active active, ContinuityStorePort.Session same, RootRuntimeContext actualContext,
                PlanningReadRequest request, ReadContract<?> contract) throws IOException {
            require(current.get() == active && active.same() == same && actualContext == context && active.request().equals(request)
                    && active.contract() == contract, "episode domain physical callback crossed its original request/context/contract/writer");
            context.writer().requireSession(same); requireContract(contract); active.proof().requireCurrent(same, context);
            unchanged(same, active.original()); active.lease().assertCurrent(same); active.lease().sourceQualification().assertCurrent(same);
            requireFrame(active.frame(), active.proof()); requireLivingPaused(active.frame());
            require(context.clock().instant().isBefore(request.deadline()) && context.clock().instant().isBefore(active.lease().validUntil()),
                    "episode domain physical callback expired");
        }

        private void requireFrame(Complete frame, RootApplicationAssembly.EpisodeDomainInitializationProof proof) {
            var currentFrame = proof.currentSemantic().frame();
            var currentDriver = proof.currentDriver().session();
            require(currentDriver.actorId().equals(currentFrame.frame().identity().player())
                    && currentDriver.episodeRunId().equals(currentFrame.frame().episodeRunId()),
                    "domain initialization current Driver and physical SEM disagree on the actual player/episode");
            require(frame.source().equals(context.source()) && frame.identity().machineId().equals(context.game().machineId())
                    && frame.identity().game().equals(context.game().generation()) && frame.sessionId().equals(context.game().sessionId())
                    && frame.identity().frame().episodeRunId().equals(currentFrame.frame().episodeRunId())
                    && frame.identity().frame().identity().player().equals(currentFrame.frame().identity().player())
                    && frame.identity().frame().identity().dateRaw().equals(currentFrame.frame().identity().dateRaw())
                    && proof.afterSession().machineId().equals(frame.identity().machineId())
                    && proof.afterSession().game().equals(frame.identity().game())
                    && proof.afterSession().sessionId().equals(frame.sessionId())
                    && proof.source().equals(context.source()), "episode domain physical frame crossed the actual adopted Game/source/session");
        }

        private void requireContract(ReadContract<?> contract) {
            requireAllowed(catalog, allowed, contract);
        }
        private ExactRef decoderSource(ReadContract<?> contract) {
            var matches = catalog.installed().stream().filter(value -> value.contract() == contract).toList();
            require(matches.size() == 1, "episode domain read has no unique installed original decoder");
            return matches.getFirst().decoderSource();
        }
    }

    /** Immutable captured originals; this is never an ordinary-ready or native action permission. */
    public static final class Captured<T> {
        private final Installed owner;
        private final RootApplicationAssembly.EpisodeDomainInitializationProof proof;
        private final ReadContract<T> contract;
        private final PlanningReadResult<T> result;
        private final Complete frame;
        private final SessionPorts.SemanticEvidence semantic;
        private final Optional<ExactRef> sourceProof;
        private final long originalSequence;
        private final String originalDigest;
        private final List<WriterContracts.Pin> pins;
        private Captured(Installed owner, RootApplicationAssembly.EpisodeDomainInitializationProof proof, ReadContract<T> contract,
                PlanningReadResult<T> result, Complete frame, SessionPorts.SemanticEvidence semantic, Optional<ExactRef> sourceProof,
                long originalSequence, String originalDigest, List<WriterContracts.Pin> pins) {
            this.owner = owner; this.proof = proof; this.contract = contract; this.result = result;
            this.frame = frame; this.semantic = semantic; this.sourceProof = sourceProof;
            this.originalSequence = originalSequence; this.originalDigest = originalDigest; this.pins = List.copyOf(pins);
        }
        public PlanningReadResult<T> result() { return result; }
        public Complete frame() { return frame; }
        public SessionPorts.SemanticEvidence semantic() { return semantic; }
        public Optional<ExactRef> sourceProof() { return sourceProof; }

        /** Replays retained originals at the current legal domain-import continuation; never reopens a live lease or issues a query. */
        public void requireOriginals(ContinuityStorePort.Session same, RootRuntimeContext actualContext,
                RootApplicationAssembly.EpisodeDomainInitializationProof actualProof) throws IOException {
            require(actualContext == owner.context && actualProof == proof,
                    "captured episode domain originals crossed their private proof/context");
            actualContext.writer().requireSession(same); proof.requireCurrent(same, actualContext); owner.requireContract(contract);
            same.requireHistoricalState(originalSequence, originalDigest); for (var pin : pins) same.verifyPin(pin);
            if (!(result instanceof PlanningReadResult.Known<T> known))
                throw new IOException("unavailable episode domain query has no business original to import");
            var archive = actualContext.archive().withSession(same);
            PlanningReadReceipt read = archive.loadRead(known.originalReceipt());
            require(read.equals(known.receipt()) && read.request().source().equals(actualContext.source())
                    && read.request().sessionId().equals(actualContext.game().sessionId()) && read.request().before().equals(frame.identity()),
                    "captured episode domain read changed its exact archived request/receipt/frame/source/session");
            // T has no generic value-equality contract. Captured cannot accept caller-supplied Known values;
            // the sole source-owned pure parser must revalidate its exact archived receipt instead.
            contract.replay(read);
            for (PlanningReadGuard guard : List.of(read.before(), read.after())) {
                RootGuardEvidence.requireHistory(guard.binding(), archive, same);
                var point = RootGuardEvidence.writerPoint(guard.binding(), archive);
                require(point.sequence() == originalSequence && point.digest().equals(originalDigest),
                        "captured episode domain read replaced its original writer history point");
                require(RootGuardEvidence.sourceQualification(guard.binding(), archive).equals(sourceProof)
                        && RootGuardEvidence.loadFrame(guard.binding(), archive, actualContext.frameLoader()).equals(frame),
                        "captured episode domain read lost its actual complete frame/source originals");
                var driver = RootGuardEvidence.originalDriverSource(guard.binding(), archive);
                require(driver.driverRef().equals(semantic.originalDriver()) && driver.stampRef().equals(semantic.driverStamp()),
                        "captured episode domain read changed the original full Driver or typed stamp");
            }
            require(semantic.frame().equals(frame.identity()) && semantic.originalNativePacket().equals(frame.originalEvidence())
                    && semantic.observedAt().equals(frame.observedAt()), "captured episode domain SEM differs from its actual read frame");
            actualContext.semanticVerifier().verify(same, proof.afterSession(), semantic);
            if (sourceProof.isPresent()) {
                ExactRef proof = sourceProof.orElseThrow();
                byte[] proofBytes = actualContext.originals().read(same, proof, 16 << 20);
                require(proof.bytes() == proofBytes.length && proof.sha256().equals(DriverJson.sha256(proofBytes)),
                        "captured episode domain source qualification original changed");
                requireCapturedSourceProof(proofBytes, actualContext.source().machineId(), frame.sessionId(),
                        actualContext.source().sourceRef());
            }
            for (var pin : pins) same.verifyPin(pin); proof.requireCurrent(same, actualContext);
        }
    }

    private record Active(ContinuityStorePort.Session same, RootApplicationAssembly.EpisodeDomainInitializationProof proof,
            RootLifecycleAuthority.SnapshotLease lease, Complete frame, SessionPorts.SemanticEvidence semantic,
            PlanningReadRequest request, ReadContract<?> contract, WriterContracts.Head original) { }

    /** Historical DATA only; the live lease, immutable pins and original writer point remain checked by Captured. */
    static NativeSourceProofDocument requireCapturedSourceProof(byte[] original, String expectedMachineId,
            String expectedSessionId, ExactRef expectedSource) throws IOException {
        NativeSourceProofDocument document = NativeSourceProofCodec.decode(original);
        require(document.machineId().equals(expectedMachineId) && document.sessionId().equals(expectedSessionId)
                        && document.source().equals(expectedSource),
                "captured episode domain source proof changed its original machine/session/source");
        return document;
    }

    static Set<ReadContract<?>> allowedContracts(RootReadContractCatalog catalog, List<ReadContract<?>> actualAllowed) {
        Objects.requireNonNull(catalog); List<ReadContract<?>> copy = List.copyOf(actualAllowed);
        require(!copy.isEmpty() && copy.size() <= 16, "finite exact episode domain read allowlist required");
        Set<ReadContract<?>> allowed = Collections.newSetFromMap(new IdentityHashMap<>());
        for (ReadContract<?> contract : copy) {
            require(allowed.add(contract), "same episode domain contract cannot be allowed twice");
            requireAllowed(catalog, allowed, contract);
        }
        return Collections.unmodifiableSet(allowed);
    }
    static void requireAllowed(RootReadContractCatalog catalog, Set<ReadContract<?>> allowed, ReadContract<?> contract) {
        require(contract != null && allowed.contains(contract) && catalog.containsIdentity(contract),
                "read is not the identical Root-installed episode domain contract");
        require(contract.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP && contract.hasPureReplay(),
                "episode domain contract requires its source-owned living-map and explicit pure replay decoder");
    }
    private static void requireLivingPaused(Complete frame) {
        var row = frame.semantic(); require(OpportunityJson.bool(row.get("paused"), "paused")
                && OpportunityJson.bool(row.get("map_ready"), "map_ready"), "episode domain read requires an actual paused map");
        var player = OpportunityJson.object(row.get("played_character"), "played_character");
        require(OpportunityJson.bool(player.get("alive"), "alive")
                && OpportunityJson.integer(player.get("character_id"), "character_id").equals(frame.identity().frame().identity().player())
                && OpportunityJson.integer(row.get("episode_character_id"), "episode_character_id").equals(frame.identity().frame().identity().player()),
                "episode domain read lost its actual living new player/episode");
        require(row.members().containsKey("one_life_terminal_reason") && row.get("one_life_terminal_reason") == OpportunityJson.Nil.INSTANCE,
                "terminal or unavailable life state cannot supply episode domain initialization reads");
    }
    private static void pinSource(ContinuityStorePort.Session same, ExactRef source) throws IOException {
        require(source.bytes() > 0 && java.nio.file.Path.of(source.path()).isAbsolute(), "actual installed source file required");
        same.verifyPin(same.capturePin(source, WriterContracts.MAX_PIN_BYTES));
    }
    private static void unchanged(ContinuityStorePort.Session same, WriterContracts.Head expected) throws IOException {
        var actual = same.head(); require(actual.digest().equals(expected.digest()) && actual.documents().equals(expected.documents())
                && actual.absent().equals(expected.absent()) && actual.indexRepairs().equals(expected.indexRepairs())
                && actual.snapshotNeedsRecovery() == expected.snapshotNeedsRecovery(), "episode domain read changed its actual writer Head");
    }
}
