package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.ArrayList;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Actual installed NS/M3 transport custody. Evidence is archived DATA, never a
 * capability: only the installed port may open a new held physical/current scope.
 */
public final class SameGameTransportContinuity {
    public static final String EVIDENCE_SCHEMA = "xar.java-same-game-transport-evidence/v2";

    public enum Purpose { PENDING_REBIND, FINALIZED_METADATA_ONLY }

    public record Evidence(Purpose purpose, SessionIdentity beforeOwner, SessionIdentity afterOwner,
            ActionReceipt canonicalParent, SemanticEvidence semantic, long canonicalSequence,
            String canonicalEventIdentity, String canonicalHeadDigest, ExactRef canonicalMetadata,
            ExactRef beforeDriver, ExactRef afterDriver, ExactRef beforeObligation,
            ExactRef afterObligation, ExactRef privateProof, List<ExactRef> privateMaterials) {
        public Evidence {
            Objects.requireNonNull(purpose); Objects.requireNonNull(beforeOwner); Objects.requireNonNull(afterOwner);
            Objects.requireNonNull(canonicalParent); Objects.requireNonNull(semantic);
            StrictJson.safe(canonicalSequence, 1); WriterContracts.requireDigest(canonicalEventIdentity);
            WriterContracts.requireDigest(canonicalHeadDigest);
            StrictJson.require(beforeOwner.machineId().equals(afterOwner.machineId())
                    && beforeOwner.game().equals(afterOwner.game()),
                    "transport continuation must retain the exact original OS Game; restore is a separate private route");
            var parent = canonicalParent.command();
            StrictJson.require(parent.origin().machineId().equals(beforeOwner.machineId())
                    && parent.origin().game().equals(beforeOwner.game()),
                    "transport evidence changed its exact historical parent owner");
            StrictJson.require(semantic.frame().machineId().equals(afterOwner.machineId())
                    && semantic.frame().game().equals(afterOwner.game()),
                    "transport semantic evidence crossed the actual same Game owner");
            for (ExactRef ref : List.of(canonicalMetadata, beforeDriver, afterDriver,
                    beforeObligation, afterObligation, privateProof)) {
                StrictJson.require(Objects.requireNonNull(ref).bytes() > 0, "transport originals must be nonempty");
            }
            privateMaterials=List.copyOf(Objects.requireNonNull(privateMaterials));
            StrictJson.require(!privateMaterials.isEmpty()&&privateMaterials.size()<=1024,
                    "actual private binding material closure must be present and bounded");
            for(ExactRef ref:privateMaterials)StrictJson.require(ref.bytes()>0,"private binding material must be nonempty");
        }

        public List<ExactRef> references(OutcomeArchive archive) {
            Objects.requireNonNull(archive);
            var parent = archive.receiptReferenceOf(canonicalParent);
            StrictJson.require(archive.loadReceipt(parent).equals(canonicalParent),
                    "transport evidence lost its exact retained original parent receipt");
            return java.util.stream.Stream.concat(java.util.stream.Stream.concat(semantic.references().stream(),
                    java.util.stream.Stream.of(parent, canonicalMetadata, beforeDriver, afterDriver,
                            beforeObligation, afterObligation, privateProof)),privateMaterials.stream()).distinct().toList();
        }

        public ObjectNode toJson(OutcomeArchive archive) {
            references(archive);
            ObjectNode row = StrictJson.object(); row.put("schema", EVIDENCE_SCHEMA);
            row.put("purpose", purpose.name());
            row.set("before_owner", OrdinaryCycleTransitions.sessionToJson(beforeOwner));
            row.set("after_owner", OrdinaryCycleTransitions.sessionToJson(afterOwner));
            row.set("parent_receipt_ref", archive.receiptReferenceOf(canonicalParent).toJson());
            row.set("semantic", OrdinaryCycleTransitions.semanticToJson(semantic));
            row.put("canonical_sequence", canonicalSequence); row.put("canonical_event_identity", canonicalEventIdentity);
            row.put("canonical_head_digest", canonicalHeadDigest); row.set("canonical_metadata", canonicalMetadata.toJson());
            row.set("before_driver", beforeDriver.toJson()); row.set("after_driver", afterDriver.toJson());
            row.set("before_obligation", beforeObligation.toJson()); row.set("after_obligation", afterObligation.toJson());
            row.set("private_proof", privateProof.toJson());var materials=row.putArray("private_materials");
            privateMaterials.forEach(ref->materials.add(ref.toJson()));return row;
        }
    }

    public static Evidence fromJson(ObjectNode original, OutcomeArchive archive) {
        Objects.requireNonNull(archive);
        ObjectNode row = StrictJson.object(original, Set.of("schema", "purpose", "before_owner", "after_owner",
                "parent_receipt_ref", "semantic", "canonical_sequence", "canonical_event_identity",
                "canonical_head_digest", "canonical_metadata", "before_driver", "after_driver",
                "before_obligation", "after_obligation", "private_proof", "private_materials"));
        StrictJson.require(EVIDENCE_SCHEMA.equals(StrictJson.text(row.get("schema"))), "known transport evidence schema required");
        ExactRef parentRef = ExactRef.fromJson(row.get("parent_receipt_ref"));
        ActionReceipt parent = archive.loadReceipt(parentRef);
        StrictJson.require(archive.receiptReferenceOf(parent).equals(parentRef), "transport parent original reference changed");
        var materials=row.get("private_materials");
        StrictJson.require(materials!=null&&materials.isArray()&&materials.size()>0&&materials.size()<=1024,
                "actual private binding material closure array is required");
        List<ExactRef> references=new ArrayList<>();materials.forEach(value->references.add(ExactRef.fromJson(value)));
        return new Evidence(Purpose.valueOf(StrictJson.text(row.get("purpose"))),
                OrdinaryCycleTransitions.sessionFromJson(row.get("before_owner")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("after_owner")), parent,
                OrdinaryCycleTransitions.semanticFromJson(row.get("semantic")),
                StrictJson.integer(row.get("canonical_sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(row.get("canonical_event_identity")), StrictJson.text(row.get("canonical_head_digest")),
                ExactRef.fromJson(row.get("canonical_metadata")), ExactRef.fromJson(row.get("before_driver")),
                ExactRef.fromJson(row.get("after_driver")), ExactRef.fromJson(row.get("before_obligation")),
                ExactRef.fromJson(row.get("after_obligation")), ExactRef.fromJson(row.get("private_proof")),references);
    }

    /** Actual NS adapter prepares in a physical lease, closes it, then revalidates its private source custody for work. */
    public interface Scope {
        Evidence evidence();
        void requireCurrent(ContinuityStorePort.Session same) throws IOException;
        /** Independent actual postcheck at the new canonical child head; never extends the old M3 cause. */
        void requireCommitted(ContinuityStorePort.Session same, WriterContracts.Receipt actualCycleCommit) throws IOException;
    }

    @FunctionalInterface public interface Work<T> {
        T run(Scope actual) throws IOException;
    }

    /** Installed once by the actual Root constructor; no public caller can replace it. */
    public interface Port {
        <T> T withCurrent(ContinuityStorePort.Session same, SessionIdentity beforeOwner,
                SessionIdentity afterOwner, ActionCommand exactParent, Instant deadline, Work<T> work)
                throws IOException, InterruptedException;
        /** Replays the actual NS canonical Rebind/finalized original; this grants historical DATA only. */
        void requireRecorded(ContinuityStorePort.Session same, Evidence original) throws IOException;
    }

    private SameGameTransportContinuity() { }
}
