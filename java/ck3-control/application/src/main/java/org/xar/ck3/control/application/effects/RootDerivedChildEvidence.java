package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable locator DATA. Only the real Root derived-child authority can qualify its canonical origins. */
public record RootDerivedChildEvidence(long actualHeadSequence, String actualHeadDigest, String handlerId,
        ExactRef parentReceipt, String parentBodySha256, String childBodySha256, int childOrdinal,
        ExactRef parentNative, ExactRef parentDriver, ExactRef beforeNative, ExactRef beforeDriver,
        ExactRef parentImplementation, ExactRef parentDecoder, ExactRef childImplementation, ExactRef childDecoder,
        ExactRef childVerifier, java.util.Optional<ExactRef> sourceQualification, List<ExactRef> previousChildren) {
    public static final String SCHEMA = "xar.java.root-derived-child-admission/v1";
    public static final int MAX_BYTES = 131072;
    private static final Set<String> FIELDS = Set.of("schema", "actual_head_sequence", "actual_head_digest", "handler_id",
            "parent_receipt", "parent_body_sha256", "child_body_sha256", "child_ordinal", "parent_native", "parent_driver",
            "before_native", "before_driver", "parent_implementation", "parent_decoder", "child_implementation",
            "child_decoder", "child_verifier", "source_qualification", "previous_children");
    public RootDerivedChildEvidence {
        StrictJson.safe(actualHeadSequence, 0); digest(actualHeadDigest); StrictJson.text(handlerId);
        digest(parentBodySha256); digest(childBodySha256);
        StrictJson.require(childOrdinal >= 1 && childOrdinal <= 256, "bounded exact canonical child ordinal required");
        for (ExactRef original : List.of(parentReceipt, parentNative, parentDriver, beforeNative, beforeDriver,
                parentImplementation, parentDecoder, childImplementation, childDecoder, childVerifier)) original(original);
        Objects.requireNonNull(sourceQualification);sourceQualification.ifPresent(RootDerivedChildEvidence::original);
        previousChildren = List.copyOf(previousChildren); previousChildren.forEach(RootDerivedChildEvidence::original);
        StrictJson.require(previousChildren.size() == childOrdinal - 1
                && previousChildren.stream().distinct().count() == previousChildren.size(), "ordered distinct preceding original children required");
    }
    public RootDerivedChildEvidence(long actualHeadSequence,String actualHeadDigest,String handlerId,
            ExactRef parentReceipt,String parentBodySha256,String childBodySha256,int childOrdinal,
            ExactRef parentNative,ExactRef parentDriver,ExactRef beforeNative,ExactRef beforeDriver,
            ExactRef parentImplementation,ExactRef parentDecoder,ExactRef childImplementation,ExactRef childDecoder,
            ExactRef childVerifier,ExactRef sourceQualification,List<ExactRef> previousChildren) {
        this(actualHeadSequence,actualHeadDigest,handlerId,parentReceipt,parentBodySha256,childBodySha256,childOrdinal,
                parentNative,parentDriver,beforeNative,beforeDriver,parentImplementation,parentDecoder,childImplementation,childDecoder,
                childVerifier,java.util.Optional.of(sourceQualification),previousChildren);
    }
    private static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "exact lowercase SHA256 required"); }
    private static void original(ExactRef value) { Objects.requireNonNull(value); StrictJson.require(value.bytes() > 0, "nonempty exact original required"); }
    public RawJson encode() {
        ObjectNode n = StrictJson.object().put("schema", SCHEMA).put("actual_head_sequence", actualHeadSequence)
                .put("actual_head_digest", actualHeadDigest).put("handler_id", handlerId).put("parent_body_sha256", parentBodySha256)
                .put("child_body_sha256", childBodySha256).put("child_ordinal", childOrdinal);
        n.set("parent_receipt", parentReceipt.toJson()); n.set("parent_native", parentNative.toJson()); n.set("parent_driver", parentDriver.toJson());
        n.set("before_native", beforeNative.toJson()); n.set("before_driver", beforeDriver.toJson());
        n.set("parent_implementation", parentImplementation.toJson()); n.set("parent_decoder", parentDecoder.toJson());
        n.set("child_implementation", childImplementation.toJson()); n.set("child_decoder", childDecoder.toJson());
        n.set("child_verifier", childVerifier.toJson()); n.set("source_qualification", ExactRef.optionalToJson(sourceQualification));
        ArrayNode previous = n.putArray("previous_children"); previousChildren.forEach(ref -> previous.add(ref.toJson()));
        return new RawJson(StrictJson.canonical(n, MAX_BYTES));
    }
    public static RootDerivedChildEvidence decode(RawJson raw) {
        StrictJson.require(raw.bytes().length <= MAX_BYTES, "derived child locator exceeds its closed limit");
        ObjectNode n = StrictJson.object(StrictJson.parse(raw.bytes(), MAX_BYTES), FIELDS.stream().filter(field->!field.equals("source_qualification")).collect(java.util.stream.Collectors.toUnmodifiableSet()),Set.of("source_qualification"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema"))), "wrong Root derived-child schema");
        StrictJson.require(n.get("previous_children").isArray(), "explicit previous_children array required");
        var previous = new java.util.ArrayList<ExactRef>(); n.get("previous_children").forEach(value -> previous.add(ExactRef.fromJson(value)));
        return new RootDerivedChildEvidence(StrictJson.integer(n.get("actual_head_sequence"), BigInteger.ZERO,
                BigInteger.valueOf(9_007_199_254_740_991L)).longValueExact(), StrictJson.text(n.get("actual_head_digest")),
                StrictJson.text(n.get("handler_id")), ExactRef.fromJson(n.get("parent_receipt")),
                StrictJson.text(n.get("parent_body_sha256")), StrictJson.text(n.get("child_body_sha256")),
                StrictJson.integer(n.get("child_ordinal"), BigInteger.ONE, BigInteger.valueOf(256)).intValueExact(),
                ExactRef.fromJson(n.get("parent_native")), ExactRef.fromJson(n.get("parent_driver")),
                ExactRef.fromJson(n.get("before_native")), ExactRef.fromJson(n.get("before_driver")),
                ExactRef.fromJson(n.get("parent_implementation")), ExactRef.fromJson(n.get("parent_decoder")),
                ExactRef.fromJson(n.get("child_implementation")), ExactRef.fromJson(n.get("child_decoder")),
                ExactRef.fromJson(n.get("child_verifier")), ExactRef.optionalFromJson(n.get("source_qualification")), previous);
    }
    public static RootDerivedChildEvidence requireGuard(GuardEvidence guard, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(guard.supportingEvidence().size() == 2, "exact Root basis plus one derived-child locator required");
        ExactRef original = guard.supportingEvidence().getLast(); RawJson raw = archive.loadMaterial(original);
        StrictJson.require(original.bytes() == raw.bytes().length && original.sha256().equals(ActionCodec.sha256(raw.bytes())), "derived-child original bytes changed");
        var proof = decode(raw);
        StrictJson.require(proof.beforeNative().equals(guard.nativeEvidence()), "derived-child original native frame differs from Root guard");
        return proof;
    }
}
