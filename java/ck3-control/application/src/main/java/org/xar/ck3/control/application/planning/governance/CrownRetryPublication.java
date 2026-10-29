package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** One CROWN domain publisher. Projection, writer commit and reusable observation custody are distinct. */
public final class CrownRetryPublication implements DomainBodies.Verifier {
    public static final String INPUT_SCHEMA = "xar.java-crown-retry-publication-input/v2";
    public static final int MAX_BODY_BYTES = 1_048_576;

    /** Exact metadata is separate from the original v1 body/hint. No legacy identity is reconstructed. */
    public record Input(ObservationIdentity currentObserved, ObservationIdentity queryObserved, G2Source source, ExactRef previousBody,
            ExactRef crownReadback, ExactRef crownReceipt, ExactRef finalTermsConsume, ExactRef finalTermsReceipt, List<ExactRef> runtimeSources) {
        public Input {
            Objects.requireNonNull(currentObserved); Objects.requireNonNull(queryObserved); Objects.requireNonNull(source); Objects.requireNonNull(previousBody);
            Objects.requireNonNull(crownReadback); Objects.requireNonNull(crownReceipt); Objects.requireNonNull(finalTermsConsume); Objects.requireNonNull(finalTermsReceipt);
            runtimeSources = List.copyOf(runtimeSources);
            requireQueryJoin(queryObserved, currentObserved);
            BigInteger actor = currentObserved.frame().identity().player();
            NativeCharacterId.of(actor);
            StrictJson.require(currentObserved.frame().identity().dateRaw().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                    "native signed32 CDate required");
            StrictJson.require(source.machineId().equals(currentObserved.machineId()) && source.sourceRef().bytes() > 0
                    && previousBody.bytes() > 0 && crownReadback.bytes() > 0 && finalTermsConsume.bytes() > 0
                    && crownReceipt.bytes() > 0 && finalTermsReceipt.bytes() > 0
                    && !runtimeSources.isEmpty() && runtimeSources.size() <= 16
                    && runtimeSources.stream().allMatch(ref -> ref.bytes() > 0), "complete original source custody required");
        }
    }
    /** Root supplies raw retained producer inputs plus the independently current held Native/Driver join. */
    public record Material(ObservationIdentity actualCurrent, G2Source actualSource, byte[] previousBody,
            byte[] crownReadback, byte[] finalTermsConsume) {
        public Material {
            Objects.requireNonNull(actualCurrent); Objects.requireNonNull(actualSource);
            previousBody = previousBody.clone(); crownReadback = crownReadback.clone(); finalTermsConsume = finalTermsConsume.clone();
        }
        @Override public byte[] previousBody() { return previousBody.clone(); }
        @Override public byte[] crownReadback() { return crownReadback.clone(); }
        @Override public byte[] finalTermsConsume() { return finalTermsConsume.clone(); }
    }
    public interface MaterialPort {
        /** Called inside the original writer lock. Read actual sources/current frame; never dispatch a command. */
        Material capture(WriterContracts.Head actualHead, Input input, Instant callerDeadline) throws IOException;
        /** Re-read the held current Native/Driver identity using this caller's deadline. */
        void requireCurrent(WriterContracts.Head actualHead, Input original,
                ObservationIdentity current, G2Source currentSource, Instant callerDeadline) throws IOException;
    }
    @FunctionalInterface public interface ImmutableBodyPort {
        /** CREATE_NEW immutable publication and actual native file identity/readback belong to Root's storage adapter. */
        ExactRef publish(String evidenceId, byte[] body) throws IOException;
    }
    /** Constructor is private: a parsed Input, projected deadline, ACK or DomainBodies.PreparedImport cannot mint this. */
    public static final class ImportProof {
        private final CrownRetryPublication issuer;
        private final Input input;
        private final DomainBodies.BodyRef body;
        private final WriterContracts.Receipt committed;
        private ImportProof(CrownRetryPublication issuer, Input input, DomainBodies.BodyRef body, WriterContracts.Receipt committed) {
            this.issuer = issuer; this.input = input; this.body = body; this.committed = committed;
        }
        public Input input() { return input; }
        public DomainBodies.BodyRef body() { return body; }
        public WriterContracts.Receipt committed() { return committed; }
        public boolean authorizesAction() { return false; }
        public long savedDayCredit() { return 0; }
    }

    private record ActivePublication(ContinuityStorePort.Session session, Input input, Instant callerDeadline) { }
    private final ThreadLocal<ActivePublication> activePublication = new ThreadLocal<>();
    private final Path originalWriterLock;
    private final String bodyContract;
    private final List<ExactRef> runtimeSources;
    private final List<ExactRef> producerSources;
    private final MaterialPort materials;
    private final ImmutableBodyPort bodies;
    public CrownRetryPublication(Path originalWriterLock, String bodyContract, List<ExactRef> runtimeSources,
            List<ExactRef> producerSources, MaterialPort materials, ImmutableBodyPort bodies) {
        this.originalWriterLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();
        StrictJson.text(bodyContract); this.bodyContract = bodyContract;
        this.runtimeSources = List.copyOf(runtimeSources); this.producerSources = List.copyOf(producerSources);
        StrictJson.require(!this.runtimeSources.isEmpty() && this.runtimeSources.size() <= 16
                && !this.producerSources.isEmpty() && this.producerSources.size() <= 32
                && this.runtimeSources.stream().allMatch(ref -> ref.bytes() > 0)
                && this.producerSources.stream().allMatch(ref -> ref.bytes() > 0), "actual installed runtime/producer closure required");
        this.materials = Objects.requireNonNull(materials); this.bodies = Objects.requireNonNull(bodies);
    }
    public DomainBodies.Registration registration() {
        return new DomainBodies.Registration(DomainBodies.Slot.CROWN, bodyContract, MAX_BODY_BYTES, producerSources, this);
    }

    /** Root passes its actual borrowed Session. This service never opens another writer or installs a second registration. */
    public ImportProof publish(ContinuityStorePort.Session session, Input input, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(input); Objects.requireNonNull(callerDeadline);
        session.requireWriter(originalWriterLock);
        if (activePublication.get() != null) throw new IOException("CROWN publication cannot replace an active original import scope");
        activePublication.set(new ActivePublication(session, input, callerDeadline));
        try { return publishActive(session, input, callerDeadline); }
        finally { activePublication.remove(); }
    }
    private ImportProof publishActive(ContinuityStorePort.Session session, Input input, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(input); session.requireWriter(originalWriterLock);
        DomainBodies.Available before = available(session.readDomain(DomainBodies.Slot.CROWN));
        StrictJson.require(before.reference().payload().equals(input.previousBody()), "publication must start from the actual registered CROWN body");
        WriterContracts.Head head = session.head(); requirePrevious(head, Optional.of(before.reference()), input);
        Material material = materials.capture(head, input, callerDeadline); byte[] after = reduce(input, material);
        StrictJson.require(Arrays.equals(canonical(material.previousBody()), before.canonicalBody()), "retained previous source differs from same-lock body");
        String evidenceId = "crown-retry-" + sha256(encodeInput(input));
        ExactRef output = bodies.publish(evidenceId, after); requireBytes(output, after);
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CROWN, bodyContract, output,
                encodeInput(input), evidence(input), evidenceId);
        var prepared = session.previewImport(request);
        StrictJson.require(prepared.predecessor().digest().equals(head.digest()), "retry preview crossed its original writer head");
        var committed = session.commitImport(prepared);
        StrictJson.require(committed.disposition() != WriterContracts.Disposition.NO_CHANGE
                && session.head().digest().equals(ContinuityJson.digest(committed.head().toJson())), "actual same-writer CROWN publication required");
        DomainBodies.Available actual = available(session.readDomain(DomainBodies.Slot.CROWN));
        StrictJson.require(actual.reference().payload().equals(output) && Arrays.equals(actual.canonicalBody(), after)
                && actual.reference().contractSchema().equals(bodyContract), "published retry body/contract differs from actual writer readback");
        materials.requireCurrent(session.head(), input, input.currentObserved(), input.source(), callerDeadline);
        return new ImportProof(this, input, actual.reference(), committed);
    }

    @Override public String verify(ContinuityState actualHead, Optional<DomainBodies.BodyRef> previousBody,
            DomainBodies.ImportRequest request, byte[] actualOriginalBody) throws IOException {
        throw new IOException("CROWN retry qualification requires actual Head and original locked source custody");
    }
    @Override public String verify(WriterContracts.Head actualHead, Optional<DomainBodies.BodyRef> previousBody,
            DomainBodies.ImportRequest request, byte[] actualOriginalBody) throws IOException {
        StrictJson.require(request.slot() == DomainBodies.Slot.CROWN && request.contractSchema().equals(bodyContract), "unique CROWN retry contract required");
        ActivePublication active = activePublication.get();
        if (active == null) throw new IOException("CROWN live verification requires its original active publication caller");
        active.session().requireWriter(originalWriterLock);
        StrictJson.require(active.session().head().digest().equals(actualHead.digest()), "CROWN import verifier crossed its original active writer Session/head");
        Input input = decodeInput(request.producerInput()); requirePrevious(actualHead, previousBody, input);
        StrictJson.require(active.input().equals(input), "CROWN import verifier changed its complete original publication input");
        StrictJson.require(request.evidence().equals(evidence(input)), "complete ordered original retry evidence required");
        Material material = materials.capture(actualHead, input, active.callerDeadline()); byte[] expected = reduce(input, material);
        StrictJson.require(Arrays.equals(expected, canonical(actualOriginalBody)), "actual full retry producer/reducer differs from proposed CROWN body");
        ObjectNode proof = StrictJson.object(); proof.put("head", actualHead.digest());
        proof.put("input", sha256(encodeInput(input))); proof.put("body", sha256(expected));
        return ContinuityJson.digest(proof);
    }

    /** Exact Game custody is checked before exposing the unchanged v1 context to its existing pure match predicate. */
    public CrownRetryPolicy.Frame requireCurrentPublication(ImportProof proof, ContinuityStorePort.Session session,
            ObservationIdentity current, G2Source currentSource, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(proof); Objects.requireNonNull(session); Objects.requireNonNull(current); Objects.requireNonNull(currentSource); Objects.requireNonNull(callerDeadline);
        session.requireWriter(originalWriterLock);
        StrictJson.require(proof.issuer == this, "original privately issued CROWN import proof required");
        var old = proof.input.currentObserved(); var oldFrame = old.frame(); var newFrame = current.frame();
        StrictJson.require(old.machineId().equals(current.machineId()) && old.game().equals(current.game())
                && old.observationVersion() == current.observationVersion()
                && oldFrame.episodeRunId().equals(newFrame.episodeRunId())
                && oldFrame.identity().player().equals(newFrame.identity().player())
                && newFrame.identity().dateRaw().compareTo(oldFrame.identity().dateRaw()) >= 0
                && newFrame.identity().nativeRevision().compareTo(oldFrame.identity().nativeRevision()) >= 0
                && newFrame.revision().compareTo(oldFrame.revision()) >= 0
                && currentSource.machineId().equals(current.machineId())
                && currentSource.exactBuild().equals(proof.input.source().exactBuild()), "CROWN retry crossed exact Game/source/episode/actor or moved backwards");
        var actual = available(session.readDomain(DomainBodies.Slot.CROWN));
        StrictJson.require(actual.reference().equals(proof.body)
                && DomainBodies.reference(session.head().state(), DomainBodies.Slot.CROWN).filter(proof.body::equals).isPresent(),
                "retry proof is not the actual same-head CROWN body");
        materials.requireCurrent(session.head(), proof.input, current, currentSource, callerDeadline);
        return new CrownRetryPolicy.Frame(new CrownRetryPolicy.ContextKey(BigInteger.valueOf(current.game().pid()), newFrame.episodeRunId()),
                true, newFrame.identity().player(), newFrame.identity().dateRaw());
    }

    /** Pure full producer recomputation. The original pending/resolved value domains are preserved exactly. */
    public static byte[] reduce(Input input, Material material) {
        Objects.requireNonNull(input); Objects.requireNonNull(material);
        StrictJson.require(material.actualCurrent().equals(input.currentObserved()) && material.actualSource().equals(input.source()),
                "retry source material must bind the complete current Native/Driver frame");
        requireBytes(input.previousBody(), material.previousBody()); requireBytes(input.crownReadback(), material.crownReadback());
        requireBytes(input.finalTermsConsume(), material.finalTermsConsume());
        ObjectNode old = StrictJson.object(ContinuityJson.parseObject(material.previousBody(), MAX_BODY_BYTES), Set.of("pending", "resolved", "retry"));
        nullableObject(old.get("pending")); nullableObject(old.get("resolved")); nullableObject(old.get("retry"));
        StrictJson.require(old.get("pending").isNull(), "an original pending/UNKNOWN Crown command cannot publish a replacement retry");
        var crown = CrownAuthorityCodec.decodeReadback(material.crownReadback());
        var choice = CrownAuthorityPolicy.choose(crown);
        var terms = CrownFinalTermsCodec.decodeReadback(material.finalTermsConsume());
        var frame = input.currentObserved().frame(); var identity = frame.identity();
        StrictJson.require(terms.build() == CrownFinalTerms.Build.CK3_12004
                && CrownFinalTerms.Build.CK3_12004.version().equals(crown.sourceFrame().exactCk3Build())
                && CrownFinalTerms.Build.CK3_12004.sha256().equalsIgnoreCase(crown.sourceFrame().exeSha256())
                && crown.sourceFrame().playerCharacterId().equals(identity.player())
                && crown.sourceFrame().dateRaw().equals(identity.dateRaw())
                && crown.sourceFrame().queriedNativeRevision().compareTo(terms.queriedNativeRevision()) <= 0
                && terms.payload().actorCharacterId().equals(identity.player())
                && terms.payload().dateRaw().equals(identity.dateRaw()), "retry requires ordered exact .4 native queries for this full actor/date");
        ObjectNode consume = StrictJson.object(StrictJson.parse(material.finalTermsConsume()), Set.of("schema", "expected_revision", "request_id", "before_snapshot", "after_snapshot", "command_result"));
        bindActualAfter(consume.get("after_snapshot"), input.queryObserved());
        ObjectNode next = old.deepCopy(); next.putNull("retry");
        if (choice.status() != CrownAuthorityPolicy.Status.NATIVE_BLOCKED || choice.lawKey() == null) return canonical(next);
        var group = terms.payload().groups().stream().filter(value -> value.key() == CrownFinalTerms.GroupKey.CROWN_AUTHORITY).findFirst().orElseThrow();
        if (!Objects.equals(group.activeLawKey(), crown.activeLawKey())) return canonical(next);
        var target = group.candidates().stream().filter(value -> value.lawKey().equals(choice.lawKey())).findFirst().orElse(null);
        if (target == null || target.active() || target.finalStatus() != CrownFinalTerms.FinalStatus.ENGINE_BLOCKED) return canonical(next);
        if (terms.payload().cooldown() == null) return canonical(next);
        var clock = CrownCooldown.interpret(terms.payload().cooldown(), terms.payload().dateRaw(), terms.payload().turnTick());
        if (!clock.calendarDeadlineReady() || clock.queryRetryDateRaw() == null || clock.queryRetryDateRaw().compareTo(identity.dateRaw()) <= 0) return canonical(next);
        // The old v1 hint remains byte-domain compatible. Exact Game custody is in the distinct INPUT_SCHEMA archive.
        ObjectNode hint = next.putObject("retry"); ObjectNode context = hint.putObject("source_context");
        context.put("bridge_pid", input.currentObserved().game().pid()); context.put("episode_run_id", frame.episodeRunId());
        hint.put("actor_character_id", identity.player()); hint.put("law_key", choice.lawKey());
        hint.put("observed_date_raw", identity.dateRaw()); hint.put("retry_date_raw", clock.queryRetryDateRaw());
        return canonical(next);
    }

    public static byte[] encodeInput(Input input) {
        ObjectNode row = StrictJson.object(); row.put("schema", INPUT_SCHEMA);
        row.set("current_observation", ProposalLifecycleCodec.observation(input.currentObserved()));
        row.set("query_observation", ProposalLifecycleCodec.observation(input.queryObserved()));
        row.set("source", ProposalLifecycleCodec.source(input.source())); row.set("previous_body", input.previousBody().toJson());
        row.set("crown_readback", input.crownReadback().toJson()); row.set("crown_receipt", input.crownReceipt().toJson());
        row.set("final_terms_consume", input.finalTermsConsume().toJson()); row.set("final_terms_receipt", input.finalTermsReceipt().toJson());
        var refs = row.putArray("runtime_sources"); input.runtimeSources().forEach(ref -> refs.add(ref.toJson()));
        return StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES);
    }
    public static Input decodeInput(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES), Set.of("schema", "current_observation", "query_observation", "source", "previous_body", "crown_readback", "crown_receipt", "final_terms_consume", "final_terms_receipt", "runtime_sources"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "explicit retry publication input schema required");
        var refs = row.get("runtime_sources"); StrictJson.require(refs != null && refs.isArray(), "runtime source array required");
        var sources = new java.util.ArrayList<ExactRef>(); refs.forEach(value -> sources.add(ExactRef.fromJson(value)));
        return new Input(ProposalLifecycleCodec.decodeObservation(row.get("current_observation")), ProposalLifecycleCodec.decodeObservation(row.get("query_observation")), G2Wire.source(row.get("source")),
                ExactRef.fromJson(row.get("previous_body")), ExactRef.fromJson(row.get("crown_readback")), ExactRef.fromJson(row.get("crown_receipt")),
                ExactRef.fromJson(row.get("final_terms_consume")), ExactRef.fromJson(row.get("final_terms_receipt")), sources);
    }
    private void requirePrevious(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous, Input input) {
        StrictJson.require(head.state().machineId().equals(input.currentObserved().machineId()),
                "retry crossed writer machine");
        var body = previous.orElseThrow(() -> new IllegalArgumentException("missing CROWN is not an initialized clear body"));
        StrictJson.require(body.slot() == DomainBodies.Slot.CROWN && body.contractSchema().equals(bodyContract)
                && body.payload().equals(input.previousBody())
                && DomainBodies.reference(head.state(), DomainBodies.Slot.CROWN).filter(body::equals).isPresent(), "actual original CROWN import custody required");
    }
    private static List<ExactRef> evidence(Input input) {
        var result = new java.util.ArrayList<ExactRef>(); result.add(input.previousBody()); result.add(input.crownReadback());
        result.add(input.crownReceipt()); result.add(input.finalTermsConsume()); result.add(input.finalTermsReceipt()); result.add(input.source().sourceRef()); return List.copyOf(result);
    }
    /** Pure necessary join conditions; only the actual MaterialPort can prove the canonical READ ancestry. */
    public static void requireQueryJoin(ObservationIdentity query, ObservationIdentity current) {
        var q=query.frame(); var c=current.frame();
        StrictJson.require(query.machineId().equals(current.machineId()) && query.game().equals(current.game())
                && query.observationVersion()==current.observationVersion() && q.episodeRunId().equals(c.episodeRunId())
                && q.identity().equals(c.identity()) && c.revision().compareTo(q.revision())>=0,
                "query/current Crown join crossed exact Game, episode, actor, native revision/date or moved public revision backwards");
    }
    private static void bindActualAfter(JsonNode value, ObservationIdentity observed) {
        StrictJson.require(value != null && value.isObject(), "actual final-terms after snapshot required");
        var frame = observed.frame(); var id = frame.identity(); var actor = value.get("played_character");
        StrictJson.require(actor != null && actor.isObject() && text(value, "snapshot_id").equals(frame.snapshotId())
                && text(value, "episode_run_id").equals(frame.episodeRunId())
                && integer(value, "revision").equals(frame.revision()) && integer(value, "native_revision").equals(id.nativeRevision())
                && integer(value, "date_raw").equals(id.dateRaw()) && integer(actor, "character_id").equals(id.player()), "full final-terms after snapshot crossed original public/native/episode/actor identity");
    }
    private static String text(JsonNode value, String field) { return StrictJson.text(value.get(field)); }
    private static BigInteger integer(JsonNode value, String field) {
        JsonNode token = value.get(field); StrictJson.require(token != null && token.isIntegralNumber(), "actual integer frame token required"); return token.bigIntegerValue();
    }
    private static void nullableObject(JsonNode value) { StrictJson.require(value != null && (value.isNull() || value.isObject()), "explicit nullable original Crown object required"); }
    private static DomainBodies.Available available(DomainBodies.Read value) throws IOException {
        if (value instanceof DomainBodies.Available actual) return actual;
        throw new IOException("actual CROWN body unavailable; no implicit initialization or cold proof");
    }
    private static byte[] canonical(byte[] raw) { return canonical(ContinuityJson.parseObject(raw, MAX_BODY_BYTES)); }
    private static byte[] canonical(ObjectNode row) { return ContinuityJson.canonical(row, MAX_BODY_BYTES); }
    private static void requireBytes(ExactRef reference, byte[] raw) {
        StrictJson.require(raw.length == reference.bytes() && sha256(raw).equals(reference.sha256()), "actual original source bytes/SHA differ");
    }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("required SHA-256 unavailable", impossible); }
    }
}
