package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One retained continuity envelope; none of these values grants Game submission permission. */
public final class WriterContracts {
    public static final String ACTION_LIFECYCLE_KIND = "java_action_lifecycle";
    public static final String ACTION_LIFECYCLE_FIELD = "java_action_lifecycle_head";
    public static final String ORDINARY_CYCLE_KIND = "java_ordinary_cycle";
    public static final String ORDINARY_BATCH_KIND = "java_ordinary_batch";
    /** Actual private M7 ACTIVE first-pair basis, independent from an ordinary completed batch. */
    public static final String ORDINARY_NEXT_BASELINE_KIND = "JAVA_ORDINARY_NEXT_BASELINE_V1";
    public static final String ORDINARY_CYCLE_FIELD = "java_ordinary_cycle_state";
    public static final String ORDINARY_SAVED_CYCLE_FIELD = "java_ordinary_saved_cycle";
    public static final String ORDINARY_CYCLE_REBIND_FIELD = "java_ordinary_cycle_rebind";
    public static final String ORDINARY_BATCH_BOUNDARY_FIELD = "java_ordinary_batch_boundary";
    public static final String GAMEPLAY_ENTRY_KIND = "java_gameplay_entry";
    public static final String DRIVER_HISTORY_BASELINE_FIELD = "java_driver_history_baseline";
    public static final String GAMEPLAY_ENTRY_FIELD = "java_gameplay_entry_state";
    /** Private factual Driver read publication only; authority revalidates its complete typed proof. */
    public static final String DRIVER_ACTION_HISTORY_KIND = "JAVA_DRIVER_ACTION_HISTORY_V1";
    public static final String DRIVER_ACTION_HISTORY_FIELD = "java_driver_action_history_v1";
    public static final String DRIVER_READ_HISTORY_KIND = "JAVA_DRIVER_READ_HISTORY_V1";
    public static final String DRIVER_READ_HISTORY_FIELD = "java_driver_read_history";
    /** Bound for original native archive packets; each caller still supplies its narrower input limit. */
    public static final int MAX_PIN_BYTES = 64 * 1024 * 1024 + 4;
    /** One bounded configured writer identity, shared by App, sole writer and transaction codec. */
    public static final int MAXIMUM_CONFIGURED_SOURCES = 128;
    public static final List<String> PRESERVED_RUNTIME_FIELDS = List.of("pending_cycle", "pending_checkpoint",
            "pending_actions", "unknown_requests", "unknown_actions", "UNKNOWN", "NEXT", "next_sequence",
            "next_control_sequence", "next_ordinary_sequence");
    private WriterContracts() { }

    /** Physical CREATE_NEW targets before an anchor FileRef can truthfully exist. */
    public record InitialLayout(Path snapshot,Path anchor,String machineId) {
        public InitialLayout {
            Objects.requireNonNull(snapshot);Objects.requireNonNull(anchor);StrictJson.text(machineId);
            StrictJson.require(snapshot.isAbsolute()&&anchor.isAbsolute()&&snapshot.normalize().equals(snapshot)
                    &&anchor.normalize().equals(anchor)&&snapshot.getParent()!=null&&snapshot.getFileName().toString().endsWith(".json")
                    &&anchor.getFileName().toString().endsWith(".json")
                    &&snapshot.getParent().equals(anchor.getParent())&&!snapshot.equals(anchor),"distinct canonical same-root genesis targets required");
        }
        public Path lock(){return originalLock(snapshot);}
        public Path events(){return snapshot.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");}
    }
    private static Path originalLock(Path snapshot) {
        String name=snapshot.getFileName().toString();return snapshot.resolveSibling(name.substring(0,name.length()-5)+".lock");
    }
    public record Layout(Path snapshot, ExactRef anchor, String machineId) {
        public Layout {
            Objects.requireNonNull(snapshot); Objects.requireNonNull(anchor); StrictJson.text(machineId);
            snapshot = snapshot.toAbsolutePath().normalize();
            StrictJson.require(snapshot.getParent() != null && snapshot.getFileName().toString().endsWith(".json"),
                    "existing canonical JSON ledger required");
        }
        public Path lock() {
            return originalLock(snapshot);
        }
        public Path events() { return snapshot.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS"); }
        public Path event(long sequence) {
            StrictJson.safe(sequence, 1);
            return events().resolve(String.format(java.util.Locale.ROOT, "%08d.json", sequence));
        }
        /** Ordinary WindowLedger source index: hash(kind,evidence_id), without a second hash. */
        public Path sourceIndex(String sourceKey) {
            requireDigest(sourceKey); return events().resolve("source-" + sourceKey + ".json");
        }
    }

    public record Request(String kind, byte[] details, List<ExactRef> evidence) {
        public Request {
            StrictJson.text(kind); details = canonical(details); evidence = List.copyOf(evidence);
            StrictJson.require(evidence.size() <= 64, "finite transition evidence");
            ObjectNode row = object(details);
            StrictJson.text(row.get("evidence_id"));
            var source = row.get("source");
            StrictJson.require(source != null && !source.isNull() && !source.isMissingNode()
                    && (!source.isContainerNode() || !source.isEmpty())
                    && (!source.isTextual() || !source.textValue().isEmpty())
                    && (!source.isBoolean() || source.booleanValue())
                    && (!source.isNumber() || source.doubleValue() != 0), "exact event source");
        }
        @Override public byte[] details() { return details.clone(); }
        public ObjectNode detailsObject() { return object(details); }
        public String identity() {
            ObjectNode row = StrictJson.object(); row.put("kind", kind); row.set("details", detailsObject());
            return ContinuityJson.digest(row);
        }
        public String sourceKey() {
            ObjectNode row = StrictJson.object(); row.put("kind", kind);
            row.set("evidence_id", detailsObject().get("evidence_id")); return ContinuityJson.digest(row);
        }
    }

    /** Native Win32 file identities are decimal strings, never JavaScript Number. */
    public record FileIdentity(String volumeSerialDecimal, String fileIdDecimal,
                               String creationFiletimeDecimal, String modifiedInstant, long bytes) {
        public FileIdentity {
            for (String value : List.of(volumeSerialDecimal, fileIdDecimal, creationFiletimeDecimal)) {
                StrictJson.require(value.matches("0|[1-9][0-9]*"), "canonical native identity");
            }
            java.time.Instant.parse(modifiedInstant); StrictJson.safe(bytes, 0);
        }
        public ObjectNode toJson(){ObjectNode row=StrictJson.object();row.put("volume_serial_decimal",volumeSerialDecimal);row.put("file_id_decimal",fileIdDecimal);row.put("creation_filetime_decimal",creationFiletimeDecimal);row.put("modified_instant",modifiedInstant);row.put("bytes",bytes);return row;}
        public static FileIdentity fromJson(com.fasterxml.jackson.databind.JsonNode value){var row=StrictJson.object(value,java.util.Set.of("volume_serial_decimal","file_id_decimal","creation_filetime_decimal","modified_instant","bytes"));return new FileIdentity(StrictJson.text(row.get("volume_serial_decimal")),StrictJson.text(row.get("file_id_decimal")),StrictJson.text(row.get("creation_filetime_decimal")),StrictJson.text(row.get("modified_instant")),StrictJson.integer(row.get("bytes"),0,StrictJson.MAX_SAFE_INTEGER));}
    }
    public record Pin(ExactRef reference, FileIdentity identity) {
        public Pin {
            Objects.requireNonNull(reference); Objects.requireNonNull(identity);
            StrictJson.require(reference.bytes() == identity.bytes(), "exact reference and native identity size binding");
        }
        public ObjectNode toJson(){ObjectNode row=StrictJson.object();row.set("ref",reference.toJson());row.set("identity",identity.toJson());return row;}
        public static Pin fromJson(com.fasterxml.jackson.databind.JsonNode value){var row=StrictJson.object(value,java.util.Set.of("ref","identity"));return new Pin(ExactRef.fromJson(row.get("ref")),FileIdentity.fromJson(row.get("identity")));}
    }
    public record Head(ContinuityState state, List<Pin> documents, List<Path> absent,
                       List<IndexRepair> indexRepairs, boolean snapshotNeedsRecovery) {
        public Head {
            Objects.requireNonNull(state); documents = List.copyOf(documents); absent = List.copyOf(absent);
            indexRepairs = List.copyOf(indexRepairs);
        }
        public String digest() { return ContinuityJson.digest(state.toJson()); }
    }
    /** Actual canonical edge DATA only. No missing original evidence or warm Prepared is reconstructed. */
    public record HistoricalTransition(long sequence,String kind,byte[] details,String eventIdentity,
            ContinuityState before,ContinuityState after,Pin eventPin) {
        public HistoricalTransition {
            StrictJson.safe(sequence,1);StrictJson.text(kind);details=canonical(details);requireDigest(eventIdentity);
            Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(eventPin);
            StrictJson.require(before.machineId().equals(after.machineId())&&before.sequence()==sequence-1&&after.sequence()==sequence
                    &&eventIdentity.equals(StrictJson.text(after.toJson().get("last_event_identity"))),"historical edge state/identity/sequence differs");
        }
        @Override public byte[] details(){return details.clone();}
    }

    public record IndexRepair(Path path, long sequence, String identity) {
        public IndexRepair { Objects.requireNonNull(path); StrictJson.safe(sequence, 1); requireDigest(identity); }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("sequence", sequence); row.put("identity", identity); return row;
        }
    }
    public record Prepared(Head predecessor, Request request, List<Pin> sources,
                           List<Pin> evidence, ContinuityState reduced, String preconditionDigest) {
        public Prepared {
            Objects.requireNonNull(predecessor); Objects.requireNonNull(request); sources = List.copyOf(sources);
            evidence = List.copyOf(evidence); Objects.requireNonNull(reduced); requireDigest(preconditionDigest);
        }
    }
    public enum Disposition { COMMITTED, ALREADY_COMMITTED, NO_CHANGE }
    public record Receipt(Disposition disposition, ContinuityState head, String eventIdentity,
                          int writes, boolean recoveredCommittedReceipt) {
        public Receipt {
            Objects.requireNonNull(disposition); Objects.requireNonNull(head); requireDigest(eventIdentity);
            StrictJson.require(writes >= 0, "nonnegative ledger write count");
        }
    }

    /** Shared outer entry contract; the application's sole FixtureProofCodec validates the embedded business proof. */
    public record GameplayEntryFixture(String handlerId, ExactRef parentReceipt, byte[] businessEvidence) {
        public GameplayEntryFixture {
            StrictJson.text(handlerId); Objects.requireNonNull(parentReceipt);
            StrictJson.require(parentReceipt.bytes() > 0, "nonempty actual fixture parent receipt required");
            businessEvidence = canonical(Objects.requireNonNull(businessEvidence));
            StrictJson.text(object(businessEvidence).get("schema"));
        }
        @Override public byte[] businessEvidence() { return businessEvidence.clone(); }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object().put("handler_id", handlerId);
            row.set("parent_receipt", parentReceipt.toJson()); row.set("business_evidence", object(businessEvidence)); return row;
        }
        public static GameplayEntryFixture fromJson(com.fasterxml.jackson.databind.JsonNode value) {
            ObjectNode row = StrictJson.object(value, java.util.Set.of("handler_id", "parent_receipt", "business_evidence"));
            return new GameplayEntryFixture(StrictJson.text(row.get("handler_id")), ExactRef.fromJson(row.get("parent_receipt")),
                    ContinuityJson.canonical(ContinuityJson.object(row.get("business_evidence"))));
        }
    }

    /** One closed field contract for the actual ordinary or explicit fixture Entry producer. */
    public static ObjectNode gameplayEntryDetails(Request request) {
        Objects.requireNonNull(request);
        StrictJson.require(GAMEPLAY_ENTRY_KIND.equals(request.kind()), "exact gameplay entry event kind required");
        var fields = new java.util.HashSet<>(java.util.Set.of("evidence_id", "source", "action_id", "action_body_sha256", "start_receipt", "entry_basis",
                "full_driver", "driver_facts", "driver_version", "episode_epoch", "episode_id", "auxiliary_sha256", "frame", "game", "session_id"));
        if (request.detailsObject().has("fixture")) fields.add("fixture");
        ObjectNode details = StrictJson.object(request.detailsObject(), java.util.Set.copyOf(fields));
        if (details.has("fixture")) GameplayEntryFixture.fromJson(details.get("fixture"));
        return details;
    }

    /** Pure exact projection only. Physical Entry proof is still revalidated by the fixed application authority under the original writer lock. */
    public static void requireGameplayEntryReduction(ContinuityState before, ContinuityState after, Request request, boolean sequenced) {
        ObjectNode details = gameplayEntryDetails(request);
        ObjectNode expected = org.xar.ck3.control.continuity.FreshContinuityGenesis.entryPredecessor(before,request);
        StrictJson.require(!expected.has(DRIVER_HISTORY_BASELINE_FIELD) && !expected.has(GAMEPLAY_ENTRY_FIELD),
                "only absent first entry fields may initialize; null and retained history are not absence");
        ExactRef fullDriver = ExactRef.fromJson(details.get("full_driver"));
        StrictJson.require(fullDriver.bytes() > 0, "actual nonempty full Driver reference required");
        expected.set(DRIVER_HISTORY_BASELINE_FIELD, fullDriver.toJson());
        ObjectNode entry = details.deepCopy(); entry.put("schema", "xar.java.first-gameplay-entry-state/v1");
        expected.set(GAMEPLAY_ENTRY_FIELD, entry);
        if (sequenced) { expected.put("sequence", Math.addExact(before.sequence(), 1)); expected.put("last_event_identity", request.identity()); }
        StrictJson.require(ContinuityJson.same(expected, after.toJson()),
                "gameplay entry may publish only its exact source-produced full Driver baseline and entry details");
    }

    /** The host installs one reviewed authority. Requests cannot supply reducers or acceptance booleans. */
    public interface TransitionAuthority {
        /** Re-read actual domain preconditions. UNKNOWN must throw or remain unresolved without dispatch. */
        String revalidate(ContinuityState predecessor, Request request) throws java.io.IOException;
        /** Source-aware application authorities override this; callers receive the actual same-lock capture. */
        default String revalidate(Head predecessor, Request request) throws java.io.IOException {
            return revalidate(predecessor.state(), request);
        }
        /** Exactly the same pure reducer is used for preview and while the original writer lock is held. */
        ContinuityState reduce(ContinuityState predecessor, Request request) throws java.io.IOException;
    }

    /** Closed shared state projection; application owns typed semantic/native/source validation. */
    public static void requireDriverActionHistoryReduction(ContinuityState before,ContinuityState after,
            Request request,boolean sequenced) {
        StrictJson.require(DRIVER_ACTION_HISTORY_KIND.equals(request.kind()),"exact Driver action-history kind required");
        ObjectNode expected=before.toJson();expected.set(DRIVER_ACTION_HISTORY_FIELD,request.detailsObject());
        if(sequenced){expected.put("sequence",Math.addExact(before.sequence(),1));expected.put("last_event_identity",request.identity());}
        StrictJson.require(ContinuityJson.same(expected,after.toJson()),
                "Driver action-history publication may change only its exact request details field");
    }

    public static byte[] canonical(byte[] raw) { return ContinuityJson.canonical(object(Objects.requireNonNull(raw))); }
    public static ObjectNode object(byte[] raw) { return ContinuityJson.parseObject(raw, ContinuityJson.DOCUMENT_MAX_BYTES); }
    public static void requireDigest(String value) {
        StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA-256 required");
    }
}
