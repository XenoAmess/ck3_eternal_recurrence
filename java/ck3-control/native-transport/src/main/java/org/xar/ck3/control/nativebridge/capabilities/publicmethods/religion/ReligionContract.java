package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Original public argument identities. A declaration is deliberately separate from an installed business route. */
public final class ReligionContract {
    private ReligionContract() { }
    public enum Presence { MISSING, NULL, VALUE }
    public enum Field {
        EXPECTED_REVISION, HOLY_SITE_ID, ACTION, BASE_AMOUNT, CK3_BUILD, FAITH_FULL_IDS,
        RECIPIENT_CHARACTER_ID, TARGET_RITE_ID, MAX_PIETY_COST_RAW, ACTION_ID, REQUEST_ID,
        CANDIDATE_CHARACTER_ID, EXPECTED_ACTIVE_TASK_ID, EXPECTED_INCUMBENT_CHARACTER_ID,
        PROVINCE_ID, REPLACE_EXISTING_TASK, SUBMITTED_REQUEST_ID, DOCTRINE_KEY, TENET_KEY,
        INCLUDE_KNOWLEDGE_CATALOGUE, REQUESTED_TITLE_ID, EXPECTED_EVENT_INSTANCE_ID,
        OPERATION, READ_STAGE, OPTION_KEY, TIMEOUT_SECONDS, POLICY_POSITIVE, RESERVE_GOLD_RAW,
        RESERVE_TREASURY_RAW, RESERVE_PIETY_RAW, RESERVE_BARTER_GOODS_RAW,
        EXPECTED_PREVIEW_IDENTITY_SHA256, TYPE_KEY, BARONY_TITLE_ID;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Value permits IntegerValue, TextValue, BooleanValue, DecimalValue, IdsValue, Absent { }
    public record IntegerValue(BigInteger value) implements Value { public IntegerValue { Objects.requireNonNull(value); } }
    public record TextValue(String value) implements Value { public TextValue { Objects.requireNonNull(value); } }
    public record BooleanValue(boolean value) implements Value { }
    public record DecimalValue(BigDecimal value) implements Value { public DecimalValue { Objects.requireNonNull(value); } }
    public record IdsValue(List<BigInteger> values) implements Value { public IdsValue { values=List.copyOf(values); } }
    public record Absent(Presence presence) implements Value { public Absent { StrictJson.require(presence!=Presence.VALUE,"absence must retain missing or null"); } }
    public record Argument(Field field, Value value) { public Argument { Objects.requireNonNull(field);Objects.requireNonNull(value); } }
    public record Method(String name, List<Field> fields, List<Field> required) {
        public Method { StrictJson.text(name);fields=List.copyOf(fields);required=List.copyOf(required);StrictJson.require(fields.containsAll(required)&&fields.stream().distinct().count()==fields.size(),"one original typed field contract required"); }
    }
    public record Request(Method method, List<Argument> arguments) {
        public Request {
            Objects.requireNonNull(method);arguments=List.copyOf(arguments);
            StrictJson.require(arguments.stream().map(Argument::field).toList().equals(method.fields()),"request must retain every original field in its declared order");
        }
        public Value value(Field field) { return arguments.stream().filter(a->a.field()==field).findFirst().orElseThrow().value(); }
        public BigInteger integer(Field field) { var v=value(field);StrictJson.require(v instanceof IntegerValue,"typed integer required: "+field);return ((IntegerValue)v).value(); }
        public String text(Field field) { var v=value(field);StrictJson.require(v instanceof TextValue,"typed text required: "+field);return ((TextValue)v).value(); }
        public boolean bool(Field field) { var v=value(field);StrictJson.require(v instanceof BooleanValue,"typed Boolean required: "+field);return ((BooleanValue)v).value(); }
        public BigInteger expectedRevision() { return integer(Field.EXPECTED_REVISION); }
    }
    /** Immutable validated JSON presentation. The native typed decoder runs before this public boundary is constructed. */
    public record Response(Method method, RawJson business) { public Response { Objects.requireNonNull(method);Objects.requireNonNull(business); } }
}
