package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Independent native observations. These values never attribute release, payment, or custody to an action. */
public final class PrisonerMaterial12004 {
    public static final String EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final Set<String> COMMON = Set.of("schema", "build_version", "executable_sha256", "available",
            "unavailable_reason", "snapshot_revision", "date_raw", "actor_character_id", "target_character_id");
    private PrisonerMaterial12004() { }
    public record Frame(BigInteger nativeRevision, int dateRaw, long actor, long target) {
        public Frame {
            StrictJson.require(nativeRevision != null && nativeRevision.signum() > 0
                    && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 native revision required");
            StrictJson.require(actor > 0 && actor < 0xffff_ffffL && target > 0 && target < 0xffff_ffffL
                    && actor != target, "distinct valid full actor-target pair required");
        }
    }
    public sealed interface Custody permits UnavailableCustody, Dead, Free, HeldByPlayer, HeldByOther { Frame frame(); }
    public record UnavailableCustody(Frame frame, String reason) implements Custody {
        public UnavailableCustody { Objects.requireNonNull(frame); StrictJson.text(reason); }
    }
    public record Dead(Frame frame) implements Custody { public Dead { Objects.requireNonNull(frame); } }
    public record Free(Frame frame) implements Custody { public Free { Objects.requireNonNull(frame); } }
    public record HeldByPlayer(Frame frame) implements Custody { public HeldByPlayer { Objects.requireNonNull(frame); } }
    public record HeldByOther(Frame frame, long jailer) implements Custody {
        public HeldByOther { Objects.requireNonNull(frame); StrictJson.require(jailer > 0 && jailer < 0xffff_ffffL
                && jailer != frame.actor(), "other jailer must be a different valid full character ID"); }
    }
    public sealed interface NamedModifier permits ModifierAbsent, ModifierPresent { }
    public record ModifierAbsent() implements NamedModifier { }
    public record ModifierPresent(BigInteger value) implements NamedModifier { public ModifierPresent { Objects.requireNonNull(value); } }
    public sealed interface ReleaseMaterial permits AvailableMaterial, UnavailableMaterial { Frame frame(); }
    public record AvailableMaterial(Frame frame, BigInteger targetOpinionOfActor, NamedModifier releasedFromPrison) implements ReleaseMaterial {
        public AvailableMaterial { Objects.requireNonNull(frame); Objects.requireNonNull(targetOpinionOfActor); Objects.requireNonNull(releasedFromPrison); }
    }
    public record UnavailableMaterial(Frame frame, String reason) implements ReleaseMaterial {
        public UnavailableMaterial { Objects.requireNonNull(frame); StrictJson.text(reason); }
    }
    public sealed interface KeeperOpinion permits AvailableKeeperOpinion, UnavailableKeeperOpinion { Frame frame(); }
    public record AvailableKeeperOpinion(Frame frame, int actorOpinionOfTarget) implements KeeperOpinion {
        public AvailableKeeperOpinion { Objects.requireNonNull(frame); }
    }
    public record UnavailableKeeperOpinion(Frame frame, String reason) implements KeeperOpinion {
        public UnavailableKeeperOpinion { Objects.requireNonNull(frame); StrictJson.text(reason); }
    }
    public record Comparison(Frame before, Frame after, BigInteger totalOpinionDelta, BigInteger namedModifierDelta) {
        public Comparison { Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(totalOpinionDelta);
            Objects.requireNonNull(namedModifierDelta); StrictJson.require(before.actor() == after.actor() && before.target() == after.target()
                    && after.dateRaw() >= before.dateRaw(), "comparison pair changed or time reversed"); }
        public boolean namedRelationImproved() { return namedModifierDelta.signum() > 0; }
        public boolean releaseCausationObserved() { return false; }
        public boolean custodyChangeObserved() { return false; }
    }
    public static Custody decodeCustody(byte[] bytes, Frame frame) { return decodeCustody(StrictJson.parse(bytes), frame); }
    public static Custody decodeCustody(JsonNode value, Frame frame) {
        StrictJson.require(frame.dateRaw() > 0, "original custody consumer requires a positive date");
        exact(value, "target_alive is_imprisoned jailer_character_id custody_state");
        common(value, frame, "prisoner-retained-target-state");
        String state = StrictJson.text(value.get("custody_state"));
        if (!bool(value.get("available"))) {
            StrictJson.require(state.equals("unavailable"), "unavailable custody state required");
            nil(value, "target_alive", "is_imprisoned", "jailer_character_id");
            return new UnavailableCustody(frame, StrictJson.text(value.get("unavailable_reason")));
        }
        emptyReason(value);
        return switch (state) {
            case "dead" -> { no(value.get("target_alive")); nil(value, "is_imprisoned", "jailer_character_id"); yield new Dead(frame); }
            case "free" -> { StrictJson.trueValue(value.get("target_alive")); no(value.get("is_imprisoned")); nil(value, "jailer_character_id"); yield new Free(frame); }
            case "held_by_player", "held_by_other" -> {
                StrictJson.trueValue(value.get("target_alive")); StrictJson.trueValue(value.get("is_imprisoned"));
                long jailer = StrictJson.integer(value.get("jailer_character_id"), 1, 0xffff_fffeL);
                StrictJson.require((jailer == frame.actor()) == state.equals("held_by_player"), "custody state/jailer mismatch");
                yield jailer == frame.actor() ? new HeldByPlayer(frame) : new HeldByOther(frame, jailer);
            }
            default -> throw new IllegalArgumentException("unsupported custody state");
        };
    }
    public static ReleaseMaterial decodeReleaseMaterial(byte[] bytes, Frame frame) { return decodeReleaseMaterial(StrictJson.parse(bytes), frame); }
    public static ReleaseMaterial decodeReleaseMaterial(JsonNode value, Frame frame) {
        StrictJson.require(frame.dateRaw() > 0, "original release material consumer requires a positive date");
        exact(value, "target_opinion_of_actor released_from_prison release_causation_observed custody_change_observed");
        common(value, frame, "prisoner-release-material-opinion");
        no(value.get("release_causation_observed")); no(value.get("custody_change_observed"));
        ObjectNode modifier = StrictJson.object(value.get("released_from_prison"), Set.of("observed", "present", "value"));
        boolean observed = bool(modifier.get("observed")), present = bool(modifier.get("present"));
        if (!bool(value.get("available"))) {
            StrictJson.require(!observed && !present, "unavailable named modifier cannot be observed");
            nil(value, "target_opinion_of_actor"); nil(modifier, "value");
            return new UnavailableMaterial(frame, StrictJson.text(value.get("unavailable_reason")));
        }
        emptyReason(value); StrictJson.require(observed, "available material requires actual named observation");
        NamedModifier named;
        if (present) named = new ModifierPresent(integer(modifier.get("value")));
        else { nil(modifier, "value"); named = new ModifierAbsent(); }
        return new AvailableMaterial(frame, integer(value.get("target_opinion_of_actor")), named);
    }
    public static KeeperOpinion decodeKeeperOpinion(byte[] bytes, Frame frame) { return decodeKeeperOpinion(StrictJson.parse(bytes), frame); }
    public static KeeperOpinion decodeKeeperOpinion(JsonNode value, Frame frame) {
        exact(value, "actor_opinion_of_target"); common(value, frame, "prisoner-keeper-opinion");
        if (!bool(value.get("available"))) {
            nil(value, "actor_opinion_of_target");
            return new UnavailableKeeperOpinion(frame, StrictJson.text(value.get("unavailable_reason")));
        }
        emptyReason(value);
        return new AvailableKeeperOpinion(frame, (int) StrictJson.integer(value.get("actor_opinion_of_target"), Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
    public static Comparison compare(AvailableMaterial before, AvailableMaterial after) {
        Objects.requireNonNull(before); Objects.requireNonNull(after);
        return new Comparison(before.frame(), after.frame(), after.targetOpinionOfActor().subtract(before.targetOpinionOfActor()),
                sum(after.releasedFromPrison()).subtract(sum(before.releasedFromPrison())));
    }
    public static byte[] encode(Custody custody) {
        ObjectNode node = base(custody.frame(), "prisoner-retained-target-state");
        switch (custody) {
            case UnavailableCustody unavailable -> { node.put("available", false).put("unavailable_reason", unavailable.reason()).put("custody_state", "unavailable"); node.putNull("target_alive").putNull("is_imprisoned").putNull("jailer_character_id"); }
            case Dead ignored -> { node.put("target_alive", false).putNull("is_imprisoned").putNull("jailer_character_id").put("custody_state", "dead"); }
            case Free ignored -> { node.put("target_alive", true).put("is_imprisoned", false).putNull("jailer_character_id").put("custody_state", "free"); }
            case HeldByPlayer held -> { node.put("target_alive", true).put("is_imprisoned", true).put("jailer_character_id", held.frame().actor()).put("custody_state", "held_by_player"); }
            case HeldByOther held -> { node.put("target_alive", true).put("is_imprisoned", true).put("jailer_character_id", held.jailer()).put("custody_state", "held_by_other"); }
        }
        return StrictJson.canonical(node);
    }
    public static byte[] encode(ReleaseMaterial material) {
        ObjectNode node = base(material.frame(), "prisoner-release-material-opinion").put("release_causation_observed", false).put("custody_change_observed", false);
        ObjectNode modifier = node.putObject("released_from_prison");
        if (material instanceof AvailableMaterial available) {
            node.put("target_opinion_of_actor", available.targetOpinionOfActor()); modifier.put("observed", true);
            if (available.releasedFromPrison() instanceof ModifierPresent present) modifier.put("present", true).put("value", present.value());
            else modifier.put("present", false).putNull("value");
        } else {
            node.put("available", false).put("unavailable_reason", ((UnavailableMaterial) material).reason()).putNull("target_opinion_of_actor");
            modifier.put("observed", false).put("present", false).putNull("value");
        }
        return StrictJson.canonical(node);
    }
    public static byte[] encode(KeeperOpinion opinion) {
        ObjectNode node = base(opinion.frame(), "prisoner-keeper-opinion");
        if (opinion instanceof AvailableKeeperOpinion available) node.put("actor_opinion_of_target", available.actorOpinionOfTarget());
        else node.put("available", false).put("unavailable_reason", ((UnavailableKeeperOpinion) opinion).reason()).putNull("actor_opinion_of_target");
        return StrictJson.canonical(node);
    }
    private static BigInteger sum(NamedModifier modifier) { return modifier instanceof ModifierPresent present ? present.value() : BigInteger.ZERO; }
    private static ObjectNode base(Frame frame, String suffix) {
        return StrictJson.object().put("schema", "xar.ck3." + suffix + "-12004-v1").put("build_version", "1.20.0.4")
                .put("executable_sha256", EXE_SHA256).put("available", true).put("unavailable_reason", "")
                .put("snapshot_revision", frame.nativeRevision()).put("date_raw", frame.dateRaw())
                .put("actor_character_id", frame.actor()).put("target_character_id", frame.target());
    }
    private static void exact(JsonNode value, String fields) { Set<String> keys = new java.util.HashSet<>(COMMON); keys.addAll(ListOf.words(fields)); StrictJson.object(value, keys); }
    private static void common(JsonNode value, Frame frame, String suffix) {
        Objects.requireNonNull(frame);
        StrictJson.require(StrictJson.text(value.get("schema")).equals("xar.ck3." + suffix + "-12004-v1")
                && StrictJson.text(value.get("build_version")).equals("1.20.0.4")
                && StrictJson.text(value.get("executable_sha256")).equalsIgnoreCase(EXE_SHA256), "exact .4 material source required");
        bool(value.get("available")); string(value.get("unavailable_reason"));
        StrictJson.integer(value.get("snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
        StrictJson.integer(value.get("date_raw"), frame.dateRaw(), frame.dateRaw());
        StrictJson.integer(value.get("actor_character_id"), frame.actor(), frame.actor());
        StrictJson.integer(value.get("target_character_id"), frame.target(), frame.target());
    }
    private static void emptyReason(JsonNode value) { StrictJson.require(string(value.get("unavailable_reason")).isEmpty(), "available material reason must be empty"); }
    private static String string(JsonNode value) { StrictJson.require(value != null && value.isTextual(), "actual JSON string required"); if (!value.textValue().isEmpty()) StrictJson.text(value); return value.textValue(); }
    private static BigInteger integer(JsonNode value) { StrictJson.require(value != null && value.isIntegralNumber(), "exact native integer required"); return value.bigIntegerValue(); }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue(); }
    private static void no(JsonNode value) { StrictJson.require(!bool(value), "actual JSON false required"); }
    private static void nil(JsonNode value, String... fields) { for (String field : fields) StrictJson.require(value.has(field) && value.get(field).isNull(), "explicit JSON null required: " + field); }
    private static final class ListOf { private ListOf() { } static Set<String> words(String value) { return Set.of(value.split(" ")); } }
}
