package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;

/** Borrowed original writer only. Domain adoption replays the exact reducer and native original evidence twice. */
public final class SwayCanonicalDomain {
    private final Path originalLock;
    private final Path originalLegacyLedger;
    private final ActionPorts.OutcomeArchive archive;
    private final List<ExactRef> producerSources;
    private final SchedulerVerifier scheduler;
    private final org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames;
    private static final String FRESH_SCHEMA = "xar.java.sway-actual-initial-entry/v1";
    private final ThreadLocal<FreshVerifier> activeFresh = new ThreadLocal<>();
    @FunctionalInterface public interface FreshVerifier {
        FreshVerified verify(ContinuityState actualHead, ExactRef originalEntry, ActionPorts.OutcomeArchive originals) throws IOException;
    }
    /** Empty automation history is established by a real new campaign entry, never by storage absence. */
    public record FreshVerified(String machineId, String episodeId, List<ExactRef> evidence) {
        public FreshVerified { require(machineId != null && !machineId.isBlank() && !machineId.equals("unknown") && episodeId != null && !episodeId.isBlank(), "actual initial entry machine/episode required"); evidence = List.copyOf(evidence); require(!evidence.isEmpty() && evidence.size() <= 63, "complete bounded initial entry originals required"); }
    }
    public interface SchedulerVerifier {
        SwaySchedulerCompletion.Continuation verify(ContinuityState actualHead, Ledger predecessor, SchedulerSaved change, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive originals) throws IOException;
        void verifyStage(Ledger predecessor, StageRecorded change, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive originals) throws IOException;
        void verifyFinal(ActionCommand parent, SwaySchedulerCompletion completion, ActionPorts.OutcomeArchive originals) throws IOException;
    }
    public record Loaded(Ledger ledger, DomainBodies.Available original) { public Loaded { Objects.requireNonNull(ledger); Objects.requireNonNull(original); } }
    public record PublicationWitness(ExactRef event, DomainBodies.BodyRef predecessor, DomainBodies.BodyRef result,
            ExactRef producerInput, long sequence, String eventIdentity, String previousHeadSha) {
        public PublicationWitness { Objects.requireNonNull(event); Objects.requireNonNull(predecessor); Objects.requireNonNull(result); Objects.requireNonNull(producerInput); StrictJson.safe(sequence, 1); WriterContracts.requireDigest(eventIdentity); WriterContracts.requireDigest(previousHeadSha); require(predecessor.slot() == DomainBodies.Slot.SWAY && result.slot() == DomainBodies.Slot.SWAY && predecessor.contractSchema().equals(SCHEMA) && result.contractSchema().equals(SCHEMA), "actual Sway publication references required"); }
    }
    public record Publication(Ledger ledger, PublicationWitness witness, WriterContracts.Receipt actual) { public Publication { Objects.requireNonNull(ledger); Objects.requireNonNull(witness); Objects.requireNonNull(actual); } }
    public record SavedScheduler(PublicationWitness witness, ExactRef originalRun, SwaySchedulerCompletion.Continuation continuation) { public SavedScheduler { Objects.requireNonNull(witness); Objects.requireNonNull(originalRun); Objects.requireNonNull(continuation); } }
    public record SchedulerOriginal(ExactRef source, ExactRef archived) { public SchedulerOriginal { Objects.requireNonNull(source); Objects.requireNonNull(archived); require(source.bytes() == archived.bytes() && source.sha256().equals(archived.sha256()), "whole original scheduler source/archive differ"); } }
    public SwayCanonicalDomain(Path originalLock, Path originalLegacyLedger, ActionPorts.OutcomeArchive archive, List<ExactRef> producerSources, SchedulerVerifier scheduler,
            org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames) {
        this.originalLock = Objects.requireNonNull(originalLock).toAbsolutePath().normalize(); this.archive = Objects.requireNonNull(archive);
        this.originalLegacyLedger = Objects.requireNonNull(originalLegacyLedger).toAbsolutePath().normalize();
        this.producerSources = List.copyOf(producerSources); require(!this.producerSources.isEmpty(), "complete Sway implementation source closure required"); this.scheduler = Objects.requireNonNull(scheduler);
        this.frames = Objects.requireNonNull(frames);
    }
    public Loaded load(ContinuityStorePort.Session borrowed) throws IOException {
        borrowed.requireWriter(originalLock); DomainBodies.Read read = borrowed.readDomain(DomainBodies.Slot.SWAY);
        if (!(read instanceof DomainBodies.Available available)) throw new IOException("SWAY original body is unavailable; missing is not clear state: " + read);
        require(available.reference().contractSchema().equals(SCHEMA), "Sway domain schema differs"); Ledger value = SwayFormalCodec.decode(available.canonicalBody());
        require(value.machineId().equals(borrowed.head().state().machineId()), "Sway actual writer machine differs"); return new Loaded(value, available);
    }
    /** Real NEXT producer. Root's private proof guards this preflight and the later commit, not a seed/empty import. */
    public DomainBodies.PreparedImport previewNext(ContinuityStorePort.Session borrowed,SwayNextEpisodeImport.Basis basis,ExactRef origin)throws IOException {
        try{return archive.inSession(borrowed,originals->{try{
            borrowed.requireWriter(originalLock);var before=load(borrowed);
            require(before.original().reference().equals(basis.predecessor()),"NEXT SWAY predecessor changed before preview");
            borrowed.requireHistoricalEpisodeWindowBaseline(basis.baseline());
            borrowed.requireDomainImportContinuation(basis.initializationHeadSequence(),basis.initializationHeadDigest());
            var reduced=SwayNextEpisodeImport.replay(borrowed.head().state(),before.ledger(),basis,origin,originals,frames);
            var body=originals.preserveMaterial(new RawJson(SwayFormalCodec.encode(reduced)));var input=StrictJson.object();input.put("schema",SwayNextEpisodeImport.INPUT_SCHEMA);input.set("origin",origin.toJson());
            var evidence=new java.util.ArrayList<ExactRef>();evidence.add(origin);evidence.addAll(basis.evidence());byte[] bytes=StrictJson.canonical(input,SwayFormalCodec.MAX);
            return borrowed.previewImport(new DomainBodies.ImportRequest(DomainBodies.Slot.SWAY,SCHEMA,body,bytes,evidence,"sway-next-"+ActionCodec.sha256(bytes)));
        }catch(IOException failure){throw new UncheckedIOException(failure);}});}catch(UncheckedIOException failure){throw failure.getCause();}
    }
    public DomainBodies.BodyRef commitNext(ContinuityStorePort.Session borrowed,DomainBodies.PreparedImport preview)throws IOException {
        try{return archive.inSession(borrowed,originals->{try{
            borrowed.requireWriter(originalLock);var input=StrictJson.object(StrictJson.parse(preview.request().producerInput(),SwayFormalCodec.MAX),java.util.Set.of("schema","origin"));
            SwayNativeWire.equals(input,"schema",SwayNextEpisodeImport.INPUT_SCHEMA);var origin=ExactRef.fromJson(input.get("origin"));var basis=SwayNextEpisodeImport.decode(originals.loadMaterial(origin).bytes());
            borrowed.requireHistoricalEpisodeWindowBaseline(basis.baseline());
            borrowed.requireDomainImportContinuation(basis.initializationHeadSequence(),basis.initializationHeadDigest());
            borrowed.commitImport(preview);var actual=load(borrowed).original().reference();
            require(actual.payload().sha256().equals(preview.request().originalBody().sha256()),"NEXT SWAY result differs from its actual previewed body");return actual;
        }catch(IOException failure){throw new UncheckedIOException(failure);}});}catch(UncheckedIOException failure){throw failure.getCause();}
    }
    public Ledger commit(ContinuityStorePort.Session borrowed, Change change, SwayTransitionCodec.Proofs proofs) throws IOException {
        return commitPublication(borrowed, change, proofs).ledger();
    }
    public Publication commitPublication(ContinuityStorePort.Session borrowed, Change change, SwayTransitionCodec.Proofs proofs) throws IOException {
        try { return archive.inSession(borrowed, scoped -> {
            try { return commitScoped(borrowed, change, proofs, scoped); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }
    private Publication commitScoped(ContinuityStorePort.Session borrowed, Change change, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive scoped) throws IOException {
        require(!(change instanceof Following), "legacy read-only Following cannot produce a new canonical transition; exact gameplay receipt required");
        borrowed.requireWriter(originalLock); Loaded before = load(borrowed); SwayTransitionCodec.Input input = new SwayTransitionCodec.Input(before.original().reference().payload(), change, proofs);
        byte[] producerInput = SwayTransitionCodec.encode(input);
        // The same replay used by Registration runs here and again inside original preview/commit lock.
        verifyOriginals(borrowed.head().state(), before.ledger(), change, proofs, scoped); Ledger reduced = SwayFormalState.reduce(before.ledger(), change);
        byte[] body = SwayFormalCodec.encode(reduced); ExactRef originalBody = scoped.preserveMaterial(new RawJson(body));
        String evidenceId = "sway-" + ActionCodec.sha256(producerInput);
        DomainBodies.ImportRequest request = new DomainBodies.ImportRequest(DomainBodies.Slot.SWAY, SCHEMA, originalBody, producerInput, proofs.all(), evidenceId);
        var prepared = borrowed.previewImport(request); var receipt = borrowed.commitImport(prepared); Loaded after = load(borrowed);
        require(receipt.disposition() != WriterContracts.Disposition.NO_CHANGE && receipt.head().sequence() == Math.addExact(prepared.predecessor().state().sequence(), 1), "domain publication needs its actual immediate retained event");
        var head = borrowed.head(); Path path = eventPath(receipt.head().sequence());
        var pin = head.documents().stream().filter(value -> Path.of(value.reference().path()).toAbsolutePath().normalize().equals(path)).findFirst().orElseThrow(() -> new IOException("actual domain publication event is absent from captured writer chain"));
        JsonNode event = event(borrowed, pin); JsonNode source = event.get("details").get("source");
        var witness = new PublicationWitness(pin.reference(), before.original().reference(), after.original().reference(), ExactRef.fromJson(source.get("producer_input")), receipt.head().sequence(), receipt.eventIdentity(), prepared.predecessor().digest());
        verifyPublication(borrowed, witness, scoped); return new Publication(after.ledger(), witness, receipt);
    }
    private Path eventPath(long sequence) { return originalLock.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve(String.format(java.util.Locale.ROOT, "%08d.json", sequence)).toAbsolutePath().normalize(); }
    private JsonNode event(ContinuityStorePort.Session borrowed, WriterContracts.Pin pin) throws IOException {
        JsonNode value = StrictJson.object(StrictJson.parse(borrowed.readPinned(pin, org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES), org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES), java.util.Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        java.time.Instant.parse(StrictJson.text(value.get("at_utc"))); borrowed.verifyPin(pin); return value;
    }
    private SwayTransitionCodec.Input verifyPublication(ContinuityStorePort.Session borrowed, PublicationWitness witness, ActionPorts.OutcomeArchive originals) throws IOException {
        var head = borrowed.head(); var pin = head.documents().stream().filter(value -> value.reference().equals(witness.event())).findFirst().orElseThrow(() -> new IOException("Sway publication is outside actual canonical writer chain"));
        require(Path.of(witness.event().path()).toAbsolutePath().normalize().equals(eventPath(witness.sequence())) && witness.sequence() <= head.state().sequence(), "Sway publication event path/sequence differs");
        JsonNode event = event(borrowed, pin);
        require(StrictJson.integer(event.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER) == witness.sequence() && StrictJson.text(event.get("kind")).equals(DomainBodies.IMPORT_KIND) && StrictJson.text(event.get("identity")).equals(witness.eventIdentity()) && StrictJson.text(event.get("previous_sha256")).equals(witness.previousHeadSha()), "Sway publication event identity differs");
        var historical = borrowed.requireHistoricalState(witness.sequence() - 1, witness.previousHeadSha());
        require(DomainBodies.reference(historical, DomainBodies.Slot.SWAY).equals(Optional.of(witness.predecessor())), "Sway input predecessor differs from actual immediate canonical event predecessor");
        JsonNode details = StrictJson.object(event.get("details"), java.util.Set.of("evidence_id", "machine_id", "source", "domain_body", "precondition_digest"));
        require(StrictJson.text(details.get("machine_id")).equals(head.state().machineId()) && DomainBodies.BodyRef.fromJson(details.get("domain_body")).equals(witness.result()), "Sway published body/machine differs");
        var after = ContinuityState.fromJson(event.get("after"), head.state().machineId());
        require(after.sequence() == witness.sequence() && DomainBodies.reference(after, DomainBodies.Slot.SWAY).equals(Optional.of(witness.result())) && StrictJson.text(after.toJson().get("last_event_identity")).equals(witness.eventIdentity()), "Sway actual event after-state differs");
        JsonNode source = StrictJson.object(details.get("source"), java.util.Set.of("original_body", "producer_input", "producer_sources", "evidence"));
        require(ExactRef.fromJson(source.get("producer_input")).equals(witness.producerInput()) && refs(source.get("producer_sources")).equals(producerSources) && witness.result().producerSources().equals(producerSources) && witness.predecessor().producerSources().equals(producerSources), "Sway actual publication producer closure differs");
        byte[] inputBytes = originals.loadMaterial(witness.producerInput()).bytes(); Ledger before = SwayFormalCodec.decode(originals.loadMaterial(witness.predecessor().payload()).bytes());
        var input = SwayTransitionCodec.decode(inputBytes, before);
        require(input.predecessor().equals(witness.predecessor().payload()) && refs(source.get("evidence")).equals(input.proofs().all()) && StrictJson.text(details.get("precondition_digest")).equals(ActionCodec.sha256(inputBytes)) && StrictJson.text(details.get("evidence_id")).equals("domain-body:SWAY:sway-" + ActionCodec.sha256(inputBytes)), "Sway original publication input/evidence differs");
        byte[] actual = originals.loadMaterial(witness.result().payload()).bytes();
        ExactRef original = ExactRef.fromJson(source.get("original_body")); require(Arrays.equals(originals.loadMaterial(original).bytes(), actual), "Sway immutable body differs from original producer output");
        verifyOriginals(historical, before, input.change(), input.proofs(), originals);
        require(Arrays.equals(SwayFormalCodec.encode(SwayFormalState.reduce(before, input.change())), actual), "Sway actual published body differs from shared reducer replay");
        borrowed.verifyPin(pin); return input;
    }
    private static List<ExactRef> refs(JsonNode values) { require(values != null && values.isArray() && values.size() <= 64, "bounded original reference list required"); var result = new java.util.ArrayList<ExactRef>(); values.forEach(value -> result.add(ExactRef.fromJson(value))); return List.copyOf(result); }
    public DomainBodies.Registration registration() {
        return new DomainBodies.Registration(DomainBodies.Slot.SWAY, SCHEMA, SwayFormalCodec.MAX, producerSources, new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState actualHead, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] actualBody) throws IOException {
                JsonNode incoming = StrictJson.parse(request.producerInput(), SwayFormalCodec.MAX);
                if (FRESH_SCHEMA.equals(SwayNativeWire.string(incoming, "schema"))) {
                    require(previous.isEmpty(), "fresh Sway initialization cannot erase an existing domain");
                    StrictJson.object(incoming, java.util.Set.of("schema", "original_entry"));
                    var basis = ExactRef.fromJson(incoming.get("original_entry"));
                    var verifier = Objects.requireNonNull(activeFresh.get(), "fresh Sway initialization requires its original scoped producer");
                    var verified = verifier.verify(actualHead, basis, archive);
                    require(request.evidence().equals(freshEvidence(basis, verified)), "fresh Sway initial original roster differs");
                    require(Arrays.equals(actualBody, SwayFormalCodec.encode(freshLedger(actualHead, basis, verified))), "fresh Sway body differs from its actual initial entry");
                    return ActionCodec.sha256(request.producerInput());
                }
                if(SwayNextEpisodeImport.INPUT_SCHEMA.equals(SwayNativeWire.string(incoming,"schema"))||SwayNextEpisodeImport.LEGACY_INPUT_SCHEMA.equals(SwayNativeWire.string(incoming,"schema"))) {
                    StrictJson.object(incoming,java.util.Set.of("schema","origin"));var origin=ExactRef.fromJson(incoming.get("origin"));
                    var basis=SwayNextEpisodeImport.decode(archive.loadMaterial(origin).bytes());
                    require((basis.format()==SwayNextEpisodeImport.Format.CURRENT)==SwayNextEpisodeImport.INPUT_SCHEMA.equals(SwayNativeWire.string(incoming,"schema")),"Sway origin/import versions differ");
                    require(previous.equals(Optional.of(basis.predecessor())),"NEXT SWAY actual original body changed");
                    var evidence=new java.util.ArrayList<ExactRef>();evidence.add(origin);evidence.addAll(basis.evidence());require(request.evidence().equals(evidence),"NEXT SWAY original source roster changed");
                    var before=SwayFormalCodec.decode(archive.loadMaterial(basis.predecessor().payload()).bytes());
                    var reduced=SwayNextEpisodeImport.replay(actualHead,before,basis,origin,archive,frames);
                    require(Arrays.equals(actualBody,SwayFormalCodec.encode(reduced)),"NEXT SWAY body differs from the real saved-source reducer");return ActionCodec.sha256(request.producerInput());
                }
                if ("xar.java.sway-explicit-original-import/v2".equals(SwayNativeWire.string(incoming, "schema"))) {
                    require(previous.isEmpty(), "existing Sway body cannot be reset by an initial import");
                    StrictJson.object(incoming, java.util.Set.of("schema", "original_source", "archived_original", "origin_read", "original_scheduler"));
                    ExactRef source = ExactRef.fromJson(incoming.get("original_source")), archived = ExactRef.fromJson(incoming.get("archived_original")), read = ExactRef.fromJson(incoming.get("origin_read"));
                    Optional<SchedulerOriginal> schedulerOriginal = schedulerOriginal(incoming.get("original_scheduler"));
                    require(request.evidence().equals(importEvidence(source, archived, read, schedulerOriginal)), "Sway initial original evidence differs");
                    Ledger expected = initial(source, archived, read, schedulerOriginal, archive); require(expected.machineId().equals(actualHead.machineId()) && Arrays.equals(actualBody, SwayFormalCodec.encode(expected)), "Sway initial body/source differs");
                    return ActionCodec.sha256(request.producerInput());
                }
                DomainBodies.BodyRef beforeRef = previous.orElseThrow(() -> new IOException("Sway original import is required; no implicit empty initialization"));
                require(beforeRef.contractSchema().equals(SCHEMA), "Sway predecessor contract differs");
                Ledger before = SwayFormalCodec.decode(archive.loadMaterial(beforeRef.payload()).bytes()); require(before.machineId().equals(actualHead.machineId()), "Sway replay machine drift");
                SwayTransitionCodec.Input input = SwayTransitionCodec.decode(request.producerInput(), before);
                require(input.predecessor().equals(beforeRef.payload()) && request.evidence().equals(input.proofs().all()), "Sway domain predecessor/evidence changed");
                verifyOriginals(actualHead, before, input.change(), input.proofs(), archive);
                Ledger expected = SwayFormalState.reduce(before, input.change()); require(Arrays.equals(SwayFormalCodec.encode(expected), actualBody), "Sway canonical body differs from actual native-source reducer");
                return ActionCodec.sha256(SwayTransitionCodec.encode(input));
            }
        });
    }
    /** Read-only qualification for Root's dedicated optional terminal. This grants only the actual scheduler result. */
    public org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.State verifySchedulerCompleted(ContinuityStorePort.Session borrowed, ExactRef originalRun) throws IOException {
        borrowed.requireWriter(originalLock); var originals = archive.withSession(borrowed); Loaded current = load(borrowed);
        var run = SwaySchedulerReplay.decodeRun(originals.loadMaterial(originalRun).bytes()); var materials = new java.util.ArrayList<ExactRef>(List.of(run.stage(), originalRun)); run.child().ifPresent(materials::add);
        var state = current.ledger().schedule().orElseThrow(() -> new IllegalArgumentException("actual scheduler state unavailable"));
        scheduler.verify(borrowed.head().state(), current.ledger(), new SchedulerSaved(state, originalRun), new SwayTransitionCodec.Proofs(run.reads(), Optional.empty(), Optional.empty(), materials), originals); return state;
    }
    /** Dedicated optional terminal: actual writer event, full original reducer, independent final read, all canonical children. */
    public void verifySchedulerCompleted(ContinuityStorePort.Session borrowed, ActionCommand parent, CompositeExecution retained, SwaySchedulerCompletion completion) throws IOException {
        borrowed.requireWriter(originalLock); completion.validateParent(parent); var originals = archive.withSession(borrowed); var head = borrowed.head();
        var canonical = ContinuityActionJournal.lookup(head.state(), parent.actionId(), originals).orElseThrow(() -> new IOException("actual optional parent is absent from canonical action chain"));
        require(canonical.bodySha256().equals(completion.bodySha256()) && Arrays.equals(ActionCodec.encodeCommand(canonical.command()), ActionCodec.encodeCommand(parent)), "scheduler parent differs from actual canonical command");
        CompositeExecution actual = switch(canonical.state()) { case ActionState.CompositeRunning value -> value.execution(); case ActionState.CompositeUnknown value -> value.execution(); case ActionState.CompositeSettled value -> value.execution(); default -> throw new IllegalArgumentException("actual Sway parent has no canonical composite child custody"); };
        require(actual.equals(retained), "retained Sway parent child history differs from actual canonical custody");
        var input = verifyPublication(borrowed, completion.witness(), originals);
        require(input.change() instanceof SchedulerSaved saved && saved.replay().equals(completion.originalRun()), "actual published domain input is not this SchedulerSaved execution");
        var publicationBefore = SwayFormalCodec.decode(originals.loadMaterial(completion.witness().predecessor().payload()).bytes());
        require(scheduler.verify(head.state(), publicationBefore, (SchedulerSaved)input.change(), input.proofs(), originals) == completion.continuation(), "scheduler continuation branch differs from actual service replay");
        var run = SwaySchedulerReplay.decodeRun(originals.loadMaterial(completion.originalRun()).bytes()); var stage = SwaySchedulerReplay.decodeStage(originals.loadMaterial(run.stage()).bytes());
        require(Arrays.equals(ActionCodec.encodeCommand(stage.command()), ActionCodec.encodeCommand(parent)), "scheduler original stage is not this parent command");
        verifySchedulerCompleted(borrowed, completion.originalRun()); scheduler.verifyFinal(parent, completion, originals);
        require(retained.children().size() == completion.childReceiptRefs().size() && completion.childReceiptRefs().equals(run.child().stream().toList()), "scheduler proof must retain every original parent child receipt");
        SwaySchedulerCompletion.Business classified = new SwaySchedulerCompletion.NoNewBusiness();
        for (int i = 0; i < retained.children().size(); i++) {
            var child = retained.children().get(i); var receipt = ContinuityActionJournal.lookup(head.state(), child.actionId(), originals).orElseThrow(() -> new IOException("actual scheduler child is absent from canonical action chain"));
            require(receipt.bodySha256().equals(child.bodySha256()) && receipt.settled() && originals.receiptReferenceOf(receipt).equals(completion.childReceiptRefs().get(i)), "scheduler child original body/receipt is not its actual complete canonical result");
            if (NativeRecordedEvidenceVerifier.settlement(receipt.state()) instanceof ActionState.Applied) {
                require(stage.command().operation().equals(OrdinarySwayPolicy.OPERATION) && OrdinarySwayPolicy.restoreStaged(stage.command()).decision().job().orElseThrow() == org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.Job.QUERY_SELECTED_TARGET && receipt.command().operation().value().startsWith(SwayNativeWire.START), "only this parent's actual fresh Start may be new Sway business");
                SwayActionLifecycle.verifyArchived(frames, head.state(), receipt, originals);
                var episode = load(borrowed).ledger().resolved().orElseThrow(); require(episode.identity().actionId().equals(child.actionId()), "new Start business differs from current canonical exact episode");
                classified = new SwaySchedulerCompletion.NewStartConfirmed(child.actionId(), child.bodySha256());
            }
        }
        require(classified.equals(completion.business()), "scheduler business classification differs from actual canonical child/native replay");
    }
    /** Read-only cold lookup of this parent's actual domain publication. No event means no completion or retry authority. */
    public Optional<SavedScheduler> savedScheduler(ContinuityStorePort.Session borrowed, ActionCommand parent) throws IOException {
        borrowed.requireWriter(originalLock); var originals = archive.withSession(borrowed); var head = borrowed.head();
        var documents = new java.util.ArrayList<>(head.documents()); java.util.Collections.reverse(documents);
        for (var pin : documents) {
            Path path = Path.of(pin.reference().path()).toAbsolutePath().normalize(); if (!path.getParent().equals(originalLock.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS")) || !path.getFileName().toString().matches("[0-9]{8,16}\\.json")) continue;
            JsonNode event = event(borrowed, pin); if (!StrictJson.text(event.get("kind")).equals(DomainBodies.IMPORT_KIND)) continue;
            JsonNode details = event.get("details"); var result = DomainBodies.BodyRef.fromJson(details.get("domain_body")); if (result.slot() != DomainBodies.Slot.SWAY) continue;
            ExactRef inputRef = ExactRef.fromJson(details.get("source").get("producer_input")); JsonNode raw = StrictJson.parse(originals.loadMaterial(inputRef).bytes(), SwayFormalCodec.MAX);
            if (!SwayTransitionCodec.SCHEMA.equals(StrictJson.text(raw.get("schema"))) || !"scheduler_saved".equals(StrictJson.text(raw.get("change").get("kind")))) continue;
            ExactRef runRef = ExactRef.fromJson(raw.get("change").get("replay")); var run = SwaySchedulerReplay.decodeRun(originals.loadMaterial(runRef).bytes()); var stage = SwaySchedulerReplay.decodeStage(originals.loadMaterial(run.stage()).bytes());
            if (!stage.command().actionId().equals(parent.actionId())) continue;
            require(Arrays.equals(ActionCodec.encodeCommand(stage.command()), ActionCodec.encodeCommand(parent)), "retained scheduler publication changed this parent's exact body");
            long sequence = StrictJson.integer(event.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER); String previousSha = StrictJson.text(event.get("previous_sha256"));
            var previous = borrowed.requireHistoricalState(sequence - 1, previousSha); var predecessor = DomainBodies.reference(previous, DomainBodies.Slot.SWAY).orElseThrow(() -> new IOException("published scheduler has no actual canonical predecessor body"));
            var witness = new PublicationWitness(pin.reference(), predecessor, result, inputRef, sequence, StrictJson.text(event.get("identity")), previousSha); var input = verifyPublication(borrowed, witness, originals);
            var before = SwayFormalCodec.decode(originals.loadMaterial(predecessor.payload()).bytes()); var continuation = scheduler.verify(previous, before, (SchedulerSaved)input.change(), input.proofs(), originals);
            return Optional.of(new SavedScheduler(witness, runRef, continuation));
        }
        return Optional.empty();
    }
    /** The sole explicit first-campaign producer. It creates automation history, not a claim about native active schemes. */
    public Ledger initializeFresh(ContinuityStorePort.Session borrowed, ExactRef originalEntry, FreshVerifier verifier) throws IOException {
        borrowed.requireWriter(originalLock); Objects.requireNonNull(originalEntry); Objects.requireNonNull(verifier);
        require(activeFresh.get() == null, "fresh Sway imports cannot nest");
        activeFresh.set(verifier);
        try { return archive.inSession(borrowed, scoped -> {
            try {
                require(DomainBodies.reference(borrowed.head().state(), DomainBodies.Slot.SWAY).isEmpty(), "fresh Sway initialization cannot reset an imported domain");
                var verified = verifier.verify(borrowed.head().state(), originalEntry, scoped);
                var ledger = freshLedger(borrowed.head().state(), originalEntry, verified);
                var input = StrictJson.object(); input.put("schema", FRESH_SCHEMA); input.set("original_entry", originalEntry.toJson());
                byte[] bytes = StrictJson.canonical(input); var body = scoped.preserveMaterial(new RawJson(SwayFormalCodec.encode(ledger)));
                var request = new DomainBodies.ImportRequest(DomainBodies.Slot.SWAY, SCHEMA, body, bytes, freshEvidence(originalEntry, verified), "sway-fresh-" + ActionCodec.sha256(bytes));
                borrowed.commitImport(borrowed.previewImport(request)); return load(borrowed).ledger();
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
        finally { activeFresh.remove(); }
    }
    private static Ledger freshLedger(ContinuityState head, ExactRef basis, FreshVerified verified) {
        require(head.machineId().equals(verified.machineId()), "fresh Sway initial entry belongs to another writer machine");
        return new Ledger(verified.machineId(), verified.episodeId(), Optional.empty(), Optional.empty(), List.of(), Optional.empty(), basis, Optional.empty());
    }
    private static List<ExactRef> freshEvidence(ExactRef basis, FreshVerified verified) {
        var refs = new java.util.LinkedHashSet<ExactRef>(); refs.add(basis); refs.addAll(verified.evidence()); return List.copyOf(refs);
    }
    /** Compatibility entry point now imports the entire actual original, including nonempty history. */
    public Ledger importEmptyOriginal(ContinuityStorePort.Session borrowed, ExactRef originalSource, ExactRef archivedOriginal, ExactRef originRead) throws IOException {
        return importOriginal(borrowed, originalSource, archivedOriginal, originRead, Optional.empty());
    }
    public Ledger importOriginal(ContinuityStorePort.Session borrowed, ExactRef originalSource, ExactRef archivedOriginal, ExactRef originRead, Optional<SchedulerOriginal> originalScheduler) throws IOException {
        borrowed.requireWriter(originalLock);
        try { return archive.inSession(borrowed, scoped -> {
            try {
                require(DomainBodies.reference(borrowed.head().state(), DomainBodies.Slot.SWAY).isEmpty(), "Sway domain already imported");
                borrowed.capturePin(originalSource, SwayFormalCodec.MAX); if (originalScheduler.isPresent()) borrowed.capturePin(originalScheduler.orElseThrow().source(), SwayFormalCodec.MAX); Ledger initial = initial(originalSource, archivedOriginal, originRead, originalScheduler, scoped);
                ObjectNode input = StrictJson.object(); input.put("schema", "xar.java.sway-explicit-original-import/v2"); input.set("original_source", originalSource.toJson()); input.set("archived_original", archivedOriginal.toJson()); input.set("origin_read", originRead.toJson());
                if (originalScheduler.isPresent()) { var scheduler = input.putObject("original_scheduler"); scheduler.set("source", originalScheduler.orElseThrow().source().toJson()); scheduler.set("archived", originalScheduler.orElseThrow().archived().toJson()); } else input.putNull("original_scheduler");
                byte[] bytes = StrictJson.canonical(input); ExactRef output = scoped.preserveMaterial(new RawJson(SwayFormalCodec.encode(initial)));
                DomainBodies.ImportRequest request = new DomainBodies.ImportRequest(DomainBodies.Slot.SWAY, SCHEMA, output, bytes, importEvidence(originalSource, archivedOriginal, originRead, originalScheduler), "sway-import-" + ActionCodec.sha256(bytes));
                borrowed.commitImport(borrowed.previewImport(request)); return load(borrowed).ledger();
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }
    private Ledger initial(ExactRef source, ExactRef archived, ExactRef originRef, Optional<SchedulerOriginal> originalScheduler, ActionPorts.OutcomeArchive originals) {
        require(Path.of(source.path()).toAbsolutePath().normalize().equals(originalLegacyLedger), "Sway initial source is not the selected original canonical ledger path");
        require(source.bytes() == archived.bytes() && source.sha256().equals(archived.sha256()), "archived original Sway ledger differs from pinned source");
        SwayLegacyImport.Imported imported = SwayLegacyImport.parse(archived, originals.loadMaterial(archived).bytes());
        PlanningReadReceipt origin = originals.loadRead(originRef); verifyRead(origin, originals); SwaySharedRoot.requirePublicCapture(origin); SwayNativeWire.Binding current = SwayNativeBindings.bind(origin, origin.request().operation());
        Path schedulerPath = originalLegacyLedger.resolveSibling("ordinary-sway-schedule-v1.json");
        Optional<org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.State> schedule;
        if (originalScheduler.isPresent()) {
            SchedulerOriginal original = originalScheduler.orElseThrow(); require(Path.of(original.source().path()).toAbsolutePath().normalize().equals(schedulerPath), "selected original scheduler path differs");
            schedule = Optional.of(org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire.decodeState(originals.loadMaterial(original.archived()).bytes()));
        } else {
            require(java.nio.file.Files.notExists(schedulerPath, java.nio.file.LinkOption.NOFOLLOW_LINKS), "original scheduler exists or absence is unavailable; full source-bound scheduler import required"); schedule = Optional.empty();
        }
        return new Ledger(current.before().machineId(), current.before().frame().episodeRunId(), Optional.empty(), Optional.empty(), List.of(), schedule, source, Optional.of(imported));
    }
    private static Optional<SchedulerOriginal> schedulerOriginal(JsonNode value) { return SwayFormalCodec.optional(value).map(row -> { StrictJson.object(row, java.util.Set.of("source", "archived")); return new SchedulerOriginal(ExactRef.fromJson(row.get("source")), ExactRef.fromJson(row.get("archived"))); }); }
    private static List<ExactRef> importEvidence(ExactRef source, ExactRef archived, ExactRef read, Optional<SchedulerOriginal> scheduler) { var refs = new java.util.ArrayList<ExactRef>(List.of(source, archived, read)); scheduler.ifPresent(value -> { refs.add(value.source()); refs.add(value.archived()); }); return List.copyOf(refs); }
    private void verifyOriginals(ContinuityState actualHead, Ledger before, Change change, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive originals) throws IOException {
        for (ExactRef ref : proofs.reads()) verifyRead(originals.loadRead(ref), originals);
        boolean crossGameRecovery = change instanceof Recovered recovered && !before.pending().orElseThrow().original().binding().before().game().equals(recovered.independent().binding().before().game());
        if (!(change instanceof StageRecorded) && !(change instanceof SchedulerSaved) && !(change instanceof HistoricalAttached) && !(change instanceof ScopeRebound) && !(change instanceof FollowingGameplay) && !crossGameRecovery) require(proofs.materials().isEmpty(), "native transition cannot accept unrelated material evidence");
        switch (change) {
            case StartIntent value -> {
                require(proofs.reads().size() == 1 && proofs.dispatch().isEmpty() && proofs.nativeFrame().isPresent(), "Start intent needs exact target read and original current snapshot");
                require(target(originals.loadRead(proofs.reads().get(0)), value.original().target()).equals(value.original()), "Start original target read differs");
                PlanningReadReceipt original = originals.loadRead(proofs.reads().getFirst()); require(proofs.nativeFrame().orElseThrow().equals(original.before().binding().nativeEvidence()), "Start mandatory context must retain the exact original guard snapshot");
                var actualFrame = org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(original.before().binding(), originals, frames);
                require(value.context() == context(actualFrame, value.original().binding()), "Start mandatory context differs from the actual rebuilt original native snapshot");
            }
            case StartAcknowledged value -> {
                require(proofs.reads().isEmpty() && proofs.nativeFrame().isEmpty() && proofs.dispatch().isPresent(), "Start ACK retains exactly its original dispatch");
                var pending = before.pending().orElseThrow(); NativeActionPort.AckReceived ack = ack(originals, proofs);
                require(SwayNativeWire.startAck(ack.originalFrame().bytes(), ack.requestId(), pending.actionId(), pending.original()).equals(value.acknowledgement()), "Start ACK differs from original native result");
            }
            case ReceiptRetained value -> {
                oneRead(proofs); var pending = before.pending().orElseThrow(); PlanningReadReceipt read = originals.loadRead(proofs.reads().get(0));
                SwayNativeWire.Binding binding = SwayNativeBindings.bind(read, new OperationKey(SwayNativeWire.RECEIPT + pending.original().target()));
                require(SwayNativeWire.receipt(read.original().originalFrame().bytes(), read.requestId(), binding, pending.actionId(), pending.original().target(), pending.original().captureEpoch()).equals(value.receipt()), "retained receipt differs from full original read");
            }
            case Recovered value -> {
                oneRead(proofs); require(target(originals.loadRead(proofs.reads().get(0)), value.independent().target()).equals(value.independent()), "recovery differs from original fresh exact target read");
                if (crossGameRecovery) { require(proofs.materials().size() == 1, "cross-Game pending recovery needs actual committed restoration source"); SwayRestorationProof.verify(originals, actualHead, proofs.materials().getFirst(), before, value.independent()); }
            }
            case HistoricalAttached value -> {
                oneRead(proofs); require(target(originals.loadRead(proofs.reads().get(0)), value.independent().target()).equals(value.independent()), "historical attachment differs from original fresh target read");
                require(proofs.materials().equals(List.of(value.restoreAttachment())), "historical attachment must retain its exact committed source");
                SwayRestorationProof.verify(originals, actualHead, value.restoreAttachment(), before, value.independent());
            }
            case LifecycleObserved value -> require(observe(before, proofs, originals).equals(value.state()), "Sway lifecycle differs from source-bound native composition");
            case StopIntent value -> { oneRead(proofs); require(target(originals.loadRead(proofs.reads().get(0)), value.target().target()).equals(value.target()), "Stop current target input differs"); }
            case StopAcknowledged value -> {
                require(proofs.reads().isEmpty() && proofs.nativeFrame().isEmpty() && proofs.dispatch().isPresent(), "Stop ACK retains exactly its original dispatch");
                var current = before.resolved().orElseThrow(); var stop = current.stop().orElseThrow(); var id = current.identity(); NativeActionPort.AckReceived ack = ack(originals, proofs);
                require(SwayNativeWire.stopAck(ack.originalFrame().bytes(), ack.requestId(), stop.submittedFrom(), stop.actionId(), id.targetCharacterId(), id.schemeInstanceId(), id.schemeInstanceGeneration()).equals(value.acknowledgement()), "Stop ACK differs from original pending result");
            }
            case StopObserved value -> {
                SwayLifecycle.State expected = observe(before, proofs, originals); require(expected.equals(value.state()), "Stop lifecycle differs from source-bound native composition");
                require(proofs.reads().stream().map(originals::loadRead).allMatch(read -> read.request().before().equals(value.queried())), "Stop observation query frame drift");
            }
            case Following value -> {
                oneRead(proofs); PlanningReadReceipt original = originals.loadRead(proofs.reads().get(0)); SwaySharedRoot.requirePublicCapture(original); SwayNativeBindings.bind(original, original.request().operation());
                require(original.request().before().equals(value.after()), "following frame differs from actual guarded native source");
            }
            case FollowingGameplay value -> {
                oneRead(proofs); require(proofs.materials().equals(List.of(value.receipt())), "gameplay Following requires its exact canonical receipt");
                PlanningReadReceipt original = originals.loadRead(proofs.reads().getFirst()); SwaySharedRoot.requirePublicCapture(original); SwayNativeBindings.bind(original, original.request().operation());
                require(original.request().before().equals(value.after()), "gameplay Following frame differs from actual guarded native source");
                ActionReceipt action = originals.loadReceipt(value.receipt());
                var canonical = ContinuityActionJournal.lookup(actualHead, action.command().actionId(), originals).orElseThrow(() -> new IOException("gameplay Following receipt is outside the canonical action chain"));
                require(originals.receiptReferenceOf(canonical).equals(value.receipt()) && canonical.settled() && canonical.visibleGameplay(), "gameplay Following needs an exact confirmed canonical gameplay result");
                require(canonical.command().before().equals(value.actionBefore()) && canonical.command().source().equals(original.request().source()) && canonical.command().sessionId().equals(original.request().sessionId()), "gameplay Following action origin differs from the original guarded read");
                require(atOrAfter(value.after(), SwayFollowingConsumption.observedAfter(canonical, originals, frames)), "gameplay Following read predates the actual confirmed result");
            }
            case SchedulerSaved value -> scheduler.verify(actualHead, before, value, proofs, originals);
            case StageRecorded value -> scheduler.verifyStage(before, value, proofs, originals);
            case ScopeRebound value -> {
                oneRead(proofs); var original = originals.loadRead(proofs.reads().getFirst()); var plane = SwayObservationReads.decode(original, SwayObservationReads.Kind.COMPLETION, before.resolved().orElseThrow().identity());
                require(plane.binding().before().equals(value.queried()) && proofs.materials().equals(List.of(value.restoreMaterial())), "scope rebind differs from actual fresh exact-instance query");
                SwayRestorationProof.verifyScope(originals, actualHead, value.restoreMaterial(), before, value.queried());
            }
        }
    }
    private static SwayLifecycle.State observe(Ledger before, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive originals) {
        require(!proofs.reads().isEmpty() && proofs.dispatch().isEmpty() && proofs.nativeFrame().isEmpty(), "lifecycle observation requires original query plane receipts");
        var current = before.resolved().orElseThrow(); var id = current.identity();
        Optional<org.xar.ck3.control.contracts.projection.ProjectionJson> completion = Optional.empty(), execution = Optional.empty(), termination = Optional.empty(), opinion = Optional.empty();
        org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity queried = null;
        for (ExactRef ref : proofs.reads()) {
            PlanningReadReceipt receipt = originals.loadRead(ref); SwayObservationReads.Kind kind = java.util.Arrays.stream(SwayObservationReads.Kind.values()).filter(value -> value.step().equals(receipt.request().operation().value())).findFirst().orElseThrow(() -> new IllegalArgumentException("unregistered Sway lifecycle source read"));
            SwayObservationReads.Plane plane = SwayObservationReads.decode(receipt, kind, id);
            if (queried == null) queried = plane.binding().before(); else require(queried.equals(plane.binding().before()), "Sway observation planes crossed complete query frame");
            switch (kind) {
                case COMPLETION -> { require(completion.isEmpty(), "duplicate completion plane"); completion = Optional.of(plane.normalized()); }
                case EXECUTION -> { require(execution.isEmpty(), "duplicate execution plane"); execution = Optional.of(plane.normalized()); }
                case TERMINATION -> { require(termination.isEmpty(), "duplicate termination plane"); termination = Optional.of(plane.normalized()); }
                case OPINION -> { require(opinion.isEmpty(), "duplicate opinion plane"); opinion = Optional.of(plane.normalized()); }
            }
        }
        return SwayLifecycle.observe(current.lifecycle(), SwayFormalCodec.m6Episode(current), new M6TerminalSourceComposition.Inputs(completion, execution, termination, opinion), Objects.requireNonNull(queried));
    }
    private static SwayNativeWire.TargetRead target(PlanningReadReceipt read, long target) { return SwayNativeWire.target(read.original().originalFrame().bytes(), read.requestId(), SwayNativeBindings.bind(read, new OperationKey(SwayNativeWire.TARGET + target)), target); }
    private static NativeActionPort.AckReceived ack(ActionPorts.OutcomeArchive archive, SwayTransitionCodec.Proofs proofs) {
        NativeActionPort.DispatchOutcome original = archive.load(proofs.dispatch().orElseThrow()); require(original instanceof NativeActionPort.AckReceived, "UNKNOWN cannot be changed into an ACK");
        NativeActionPort.AckReceived ack = (NativeActionPort.AckReceived)original;
        require(ack.nativeOk() && ack.originalResultToken().isPresent(), "native ACK result token required");
        JsonNode packet = StrictJson.parse(ack.originalFrame().bytes(), SwayFormalCodec.MAX), token = StrictJson.parse(ack.originalResultToken().orElseThrow().bytes(), SwayFormalCodec.MAX);
        require(packet.get("result") != null && packet.get("result").equals(token), "Sway ACK token differs from original full native frame"); return ack;
    }
    public static MandatoryContext context(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete original, SwayNativeWire.Binding binding) {
        require(original.identity().equals(binding.before()) && original.sessionId().equals(binding.sessionId()) && original.connectionGeneration().equals(binding.connectionGeneration()), "Start context crossed the actual rebuilt original native/Driver scope");
        // Native archive packets carry a LE uint32 frame. The one FrameLoader already strictly decoded and reassembled them.
        JsonNode state = org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(original.semantic());
        require(SwayNativeWire.bool(state, "paused") && SwayNativeWire.bool(state, "map_ready") && SwayNativeWire.signed(state, "date_raw") == binding.date(), "Start snapshot lost paused date/map binding");
        JsonNode actor = state.get("played_character"); require(actor != null && actor.isObject() && SwayNativeWire.bool(actor, "alive") && SwayNativeWire.integer(actor, "character_id", 1, 0xffff_ffffL) == binding.actor(), "Start snapshot actor differs");
        JsonNode event = state.get("active_event"), interaction = state.get("pending_character_interaction");
        if (event == null || interaction == null) return MandatoryContext.UNAVAILABLE;
        return event.isNull() && interaction.isNull() ? MandatoryContext.CLEAR : MandatoryContext.MANDATORY;
    }
    private static void oneRead(SwayTransitionCodec.Proofs proofs) { require(proofs.reads().size() == 1 && proofs.dispatch().isEmpty() && proofs.nativeFrame().isEmpty(), "exactly one original guarded read required"); }
    private void verifyRead(PlanningReadReceipt read, ActionPorts.OutcomeArchive originals) {
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(read, originals);
        for (GuardEvidence guard : List.of(read.before().binding(), read.after().binding())) org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(guard, originals, frames);
    }
}
