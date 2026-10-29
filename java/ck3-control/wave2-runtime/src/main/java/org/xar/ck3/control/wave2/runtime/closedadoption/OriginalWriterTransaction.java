package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.CharBuffer;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;
import org.xar.ck3.control.recovery.RecoveryPreview;

/** One managed Java host drives the existing original writer; no separate JVM or native connection. */
public final class OriginalWriterTransaction {
    /** A transport envelope contains several independently bounded original metadata documents. */
    static final int MAX_PROTOCOL_BYTES = 262_144;
    public static final String PYTHON_BOOTSTRAP = "from tools.g2_saved_campaign.current_saved_continuity_v1 import serve_java_closed_partial_writer_v1; raise SystemExit(serve_java_closed_partial_writer_v1())";
    private OriginalWriterTransaction() { }
    public record Target(Path canonicalPath, ExactRef originalWriter) {
        public Target { Objects.requireNonNull(canonicalPath); Objects.requireNonNull(originalWriter);
            StrictJson.require(canonicalPath.isAbsolute(), "explicit Root-selected original canonical target"); }
    }
    /** Supplied by the sole Root process owner with its existing Win32 Job/finite deadline. */
    public interface ManagedProcess {
        InputStream stdout(); OutputStream stdin();
        ActualExit awaitActualExit() throws IOException, InterruptedException;
        void closeOwnedInput() throws IOException;
    }
    @FunctionalInterface public interface ManagedLauncher {
        /** Starts the fixed Python bootstrap in the original Root Job only after Java preflight passed. */
        ManagedProcess start(Target target) throws IOException;
    }
    /** Read-only additional scope check at the real original writer lock, never an action or continuation grant. */
    @FunctionalInterface public interface LockedRecheck {
        void verify(Target target) throws IOException;
    }
    public record ActualExit(long pid, String creationFiletime, int exitCode, boolean kernelExitObserved) {
        public ActualExit { StrictJson.safe(pid, 1);
            new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(creationFiletime); }
    }
    public record Document(RecoveryEvidence evidence, FileStatIdentity identity) {
        public Document { Objects.requireNonNull(evidence); Objects.requireNonNull(identity);
            StrictJson.require(identity.bytes().longValueExact() == evidence.reference().bytes(), "actual readback stat size"); }
        static Document decode(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("ref", "identity", "raw_utf8"));
            ExactRef reference = ExactRef.fromJson(row.get("ref"));
            RecoveryEvidence evidence = new RecoveryEvidence(reference, documentUtf8(row.get("raw_utf8")));
            return new Document(evidence, FileStatIdentity.fromJson(row.get("identity"), FileStatIdentity.SCHEMA));
        }
        private static byte[] documentUtf8(JsonNode value) {
            StrictJson.require(value != null && value.isTextual(), "raw readback UTF-8 text required");
            String text = value.textValue();
            StrictJson.require(!text.isEmpty() && text.length() <= RecoveryEvidence.MAX_BYTES, "bounded raw readback document required");
            try {
                var encoded = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(text));
                StrictJson.require(encoded.remaining() <= RecoveryEvidence.MAX_BYTES, "bounded raw readback UTF-8 document required");
                byte[] raw = new byte[encoded.remaining()]; encoded.get(raw); return raw;
            } catch (CharacterCodingException error) {
                throw new ContractViolationException("well-formed Unicode readback required",error);
            }
        }
        public ObjectNode value() { return object(StrictJson.parse(evidence.bytes())); }
    }
    public record Committed(Target target, Document head, Document event, Document index, ActualExit processExit,
            String inputDigest, String businessDigest, boolean idempotentReplay) {
        public Committed { Objects.requireNonNull(target); Objects.requireNonNull(head); Objects.requireNonNull(event); Objects.requireNonNull(index);
            Objects.requireNonNull(processExit); StrictJson.text(inputDigest); StrictJson.text(businessDigest); }
        public boolean gameActionsReplayed() { return false; }
    }
    public record Evaluation(ClosedAdoptionMaterial material, RecoveryPreview.Candidate candidate, String businessDigest,
            RecoveryPrerequisiteVerifier.Verified prerequisites) { }
    public static Evaluation evaluate(ClosedAdoptionMaterial material) {
        String business = ClosedPartialBusinessAuthority.verify(material.input(), material.sources(), material.business(), material.sourceVerifier());
        ClosedPartialAdmissionVerifier provider = new ClosedPartialAdmissionVerifier(material.sources(), material.publishedEpoch(),
                material.publishedPrefix(), material.originalSdk());
        String digest = ClosedFailureRecoveryReducer.inputDigest(material.input());
        RecoveryPrerequisiteVerifier.Check checked = provider.verify(material.input(), digest);
        if (checked instanceof RecoveryPrerequisiteVerifier.Unavailable missing) { throw new ContractViolationException("UNAVAILABLE: " + missing.reason()); }
        if (checked instanceof RecoveryPrerequisiteVerifier.Rejected rejected) { throw new ContractViolationException(rejected.reason()); }
        if (!(checked instanceof RecoveryPrerequisiteVerifier.Verified proof)) { throw new IllegalStateException("proof branch"); }
        RecoveryPreview result = ClosedFailureRecoveryReducer.preview(material.input(), (sameInput, sameDigest) -> {
            StrictJson.require(sameInput.equals(material.input()) && sameDigest.equals(digest), "scoped current Java prerequisite proof");
            return proof;
        });
        if (result instanceof RecoveryPreview.Unavailable missing) { throw new ContractViolationException("UNAVAILABLE: " + missing.reason()); }
        if (result instanceof RecoveryPreview.Rejected rejected) { throw new ContractViolationException(rejected.reason()); }
        if (!(result instanceof RecoveryPreview.Candidate candidate)) { throw new IllegalStateException("recovery branch"); }
        return new Evaluation(material, candidate, business, proof);
    }

    public static Committed execute(Target target, ClosedAdoptionMaterial.CurrentSource current, ManagedLauncher launcher)
            throws IOException, InterruptedException {
        return execute(target,current,launcher,ignored -> { });
    }
    public static Committed execute(Target target, ClosedAdoptionMaterial.CurrentSource current, ManagedLauncher launcher,
            LockedRecheck lockedRecheck) throws IOException, InterruptedException {
        Objects.requireNonNull(lockedRecheck);
        Evaluation preflight = evaluate(current.current()); ManagedProcess process = launcher.start(target);
        try { return run(target, current, process, preflight,lockedRecheck); }
        catch (IOException | InterruptedException | RuntimeException | Error error) {
            OriginalProcessCleanup.suppressing(process,error);
            throw error;
        }
    }
    private static Committed run(Target target, ClosedAdoptionMaterial.CurrentSource current, ManagedProcess process, Evaluation preflight,
            LockedRecheck lockedRecheck)
            throws IOException, InterruptedException {
        RecoveryPreview.Candidate candidate = preflight.candidate();
        ObjectNode start = StrictJson.object(); start.put("schema", "xar.java-original-closed-partial-writer-request/v1");
        start.put("machine_id", preflight.material().input().machineId()); start.put("canonical_path", target.canonicalPath().toString());
        start.set("writer_source_ref", target.originalWriter().toJson()); start.put("kind", "repair_required");
        start.set("details", StrictJson.parse(candidate.details()));
        start.set("expected_predecessor", StrictJson.parse(preflight.material().input().predecessor().bytes()));
        start.set("expected_reduced", StrictJson.parse(candidate.reducedState())); start.set("expected_committed", StrictJson.parse(candidate.committedState()));
        start.put("input_digest", candidate.inputDigest()); send(process.stdin(), start);
        ObjectNode locked = StrictJson.object(read(process.stdout()), Set.of("schema", "machine_id", "writer_source_ref", "canonical_path",
                "previous", "kind", "details", "input_digest"));
        equal(locked, "schema", "xar.java-original-writer-locked/v1"); equal(locked, "machine_id", preflight.material().input().machineId());
        equal(locked, "input_digest", candidate.inputDigest()); equal(locked, "kind", "repair_required");
        StrictJson.require(ExactRef.fromJson(locked.get("writer_source_ref")).equals(target.originalWriter())
                && Path.of(text(locked, "canonical_path")).equals(target.canonicalPath())
                && locked.get("details").equals(StrictJson.parse(candidate.details())), "original locked target/source/details");
        Evaluation again = evaluate(current.current());
        StrictJson.require(again.businessDigest().equals(preflight.businessDigest())
                && java.util.Arrays.equals(again.candidate().details(), candidate.details())
                && java.util.Arrays.equals(again.candidate().committedState(), candidate.committedState()),
                "same actual source and SDK cache qualification under the original writer lock");
        JsonNode previous = locked.get("previous");
        boolean repeated = previous.equals(StrictJson.parse(candidate.committedState()));
        StrictJson.require(repeated || previous.equals(StrictJson.parse(preflight.material().input().predecessor().bytes())),
                "actual canonical predecessor changed after preflight");
        lockedRecheck.verify(target);
        ObjectNode decision = StrictJson.object(); decision.put("schema", "xar.java-original-writer-locked-decision/v1"); decision.put("approved", true);
        decision.set("expected_predecessor", previous); decision.set("expected_reduced", StrictJson.parse(candidate.reducedState()));
        decision.set("expected_committed", StrictJson.parse(candidate.committedState())); decision.put("input_digest", candidate.inputDigest());
        send(process.stdin(), decision);
        ObjectNode completed = StrictJson.object(read(process.stdout()), Set.of("schema", "machine_id", "writer_source_ref", "input_digest",
                "lock_callbacks", "readback", "original_actions_replayed", "raw_pending_modified"));
        equal(completed, "schema", "xar.java-original-closed-partial-writer-readback/v1");
        equal(completed, "machine_id", preflight.material().input().machineId()); equal(completed, "input_digest", candidate.inputDigest());
        StrictJson.require(ExactRef.fromJson(completed.get("writer_source_ref")).equals(target.originalWriter()), "original actual readback writer program");
        StrictJson.integer(completed.get("lock_callbacks"), 1, 1);
        SettledQueryClassifier.falseValue(completed.get("original_actions_replayed")); SettledQueryClassifier.falseValue(completed.get("raw_pending_modified"));
        ObjectNode outputs = StrictJson.object(completed.get("readback"), Set.of("head", "event", "index"));
        Document head = Document.decode(outputs.get("head")), event = Document.decode(outputs.get("event")), index = Document.decode(outputs.get("index"));
        validateReadback(target, preflight, head, event, index);
        process.closeOwnedInput(); ActualExit exit = process.awaitActualExit();
        StrictJson.require(exit.kernelExitObserved() && exit.exitCode() == 0, "original writer actual process exit zero, not transport ACK");
        return new Committed(target, head, event, index, exit, candidate.inputDigest(), preflight.businessDigest(), repeated);
    }
    static void validateReadback(Target target, Evaluation evaluated, Document head, Document event, Document index) {
        RecoveryPreview.Candidate plan = evaluated.candidate();
        StrictJson.require(Path.of(head.evidence().reference().path()).equals(target.canonicalPath())
                && head.value().equals(StrictJson.parse(plan.committedState())), "actual canonical readback equals Java and original reducer");
        ObjectNode actualEvent = event.value(), actualIndex = index.value();
        StrictJson.integer(actualEvent.get("sequence"), plan.expectedSequence() + 1, plan.expectedSequence() + 1);
        equal(actualEvent, "kind", "repair_required"); equal(actualEvent, "identity", plan.eventIdentity());
        equal(actualEvent, "previous_sha256", plan.predecessorDigest());
        StrictJson.require(actualEvent.get("details").equals(StrictJson.parse(plan.details()))
                && actualEvent.get("after").equals(head.value()), "actual immutable original event after/details");
        StrictJson.integer(actualIndex.get("sequence"), plan.expectedSequence() + 1, plan.expectedSequence() + 1); equal(actualIndex, "identity", plan.eventIdentity());
        Path events = target.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        StrictJson.require(Path.of(event.evidence().reference().path()).equals(events.resolve(String.format(java.util.Locale.ROOT, "%08d.json", plan.expectedSequence() + 1)))
                && Path.of(index.evidence().reference().path()).equals(events.resolve("source-" + plan.sourceKey() + ".json")), "original event/source index exact paths");
    }
    static void send(OutputStream output, ObjectNode value) throws IOException { output.write(ClosedAdoptionJson.encode(value, MAX_PROTOCOL_BYTES)); output.write('\n'); output.flush(); }
    static JsonNode read(InputStream input) throws IOException {
        return StrictJson.parse(readFrame(input),MAX_PROTOCOL_BYTES);
    }
    /** Complete original UTF-8 frame body, excluding its transport newline; never a tree re-encoding. */
    static byte[] readFrame(InputStream input) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        for (int count = 0; count <= MAX_PROTOCOL_BYTES; count++) {
            int value = input.read(); if (value < 0) { throw new IOException("original writer exited before complete protocol line"); }
            if (value == '\n') { byte[] raw = bytes.toByteArray(); StrictJson.parse(raw,MAX_PROTOCOL_BYTES); return raw; } bytes.write(value);
        }
        throw new IOException("original writer protocol line exceeds finite 256 KiB transport bound");
    }
    private static ObjectNode object(JsonNode node) { return SettledQueryClassifier.object(node); }
    private static String text(ObjectNode row, String field) { return SettledQueryClassifier.text(row, field); }
    private static void equal(ObjectNode row, String field, String expected) { SettledQueryClassifier.equal(row, field, expected); }
}
