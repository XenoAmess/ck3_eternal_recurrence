package org.xar.ck3.control.application.planning.events;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;

/** Reversible public representation. Root must first replay its actual installed archived effect verifier. */
public final class EventSelectionPublicResult {
    public static final String MARKER_FIELD="event_material_wire_encoding";
    public static final String MARKER="xar.event-material-public64/v1";
    public static final int MAXIMUM_BYTES=8*1024*1024;
    private static final BigInteger SAFE=BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);
    private static final BigInteger SIGNED_MIN=BigInteger.valueOf(Long.MIN_VALUE),SIGNED_MAX=BigInteger.valueOf(Long.MAX_VALUE);
    private static final BigInteger UNSIGNED_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private EventSelectionPublicResult() { }

    /** The producer and inverse parser share this explicit vocabulary. There is no suffix guessing. */
    private enum Integer64 {
        UNSIGNED(Set.of("revision","native_revision","starting_revision","ending_revision",
                "starting_native_revision","ending_native_revision","queried_revision","queried_native_revision",
                "snapshot_revision","connection_generation","capture_epoch","date_raw","query_date_raw",
                "file_id","file_index","volume_serial_number","filetime","birth_filetime","process_birth_filetime",
                "creation_filetime","last_write_filetime"),BigInteger.ZERO,UNSIGNED_MAX),
        SIGNED(Set.of("gold_raw","prestige_raw","piety_raw","fulfillment_raw","delta"),SIGNED_MIN,SIGNED_MAX),
        BOOLEAN_OR_SIGNED(Set.of("starting_value","ending_value"),SIGNED_MIN,SIGNED_MAX);
        private final Set<String> fields;
        private final BigInteger minimum,maximum;
        Integer64(Set<String> fields,BigInteger minimum,BigInteger maximum) {
            this.fields=fields;this.minimum=minimum;this.maximum=maximum;
        }
        private void requireRange(BigInteger value) {
            require(value.compareTo(minimum)>=0&&value.compareTo(maximum)<=0,"declared public64 leaf is out of range");
        }
        private static Optional<Integer64> field(String name) {
            for(var kind:values())if(kind.fields.contains(name))return Optional.of(kind);
            return Optional.empty();
        }
    }

    /** Receipt/material must have been recovered from the same Root archive and independently replayed. */
    public static RawJson encode(ActionReceipt actual,NativeEffectEvidence.Original verified) {
        Objects.requireNonNull(actual);Objects.requireNonNull(verified);
        require(actual.applied().isPresent(),"only an original Applied event receipt has public effect material");
        ActionCommand command=actual.command();var pair=verified.frames();
        require(command.expected().observerSchema().equals(NativeEventPostconditionPort.EVENT_SCHEMA)
                &&command.operation().value().matches("select-event-option-[1-9][0-9]{0,8}"),"exact native event receipt required");
        var applied=actual.applied().orElseThrow().observation();
        require(pair.before().identity().equals(command.before())&&pair.before().source().equals(command.source())
                &&pair.before().sessionId().equals(command.sessionId())&&pair.after().identity().equals(applied.after())
                &&pair.after().source().equals(applied.source())&&pair.after().sessionId().equals(applied.sessionId())
                &&pair.after().originalEvidence().equals(applied.originalEvidence()),"public material crossed its canonical command/after frame");
        ObjectNode original=tree(verified.compatibleResult().bytes());
        require(!original.has(MARKER_FIELD),"archived native material must not already claim a public encoding");
        ObjectNode selection=object(original.get("event_selection"));
        int option=Integer.parseInt(command.operation().value().substring("select-event-option-".length()));
        List<BigInteger> instances=command.expected().values().stream().filter(ExpectedInteger.class::isInstance)
                .map(ExpectedInteger.class::cast).filter(v->v.field().value().equals("old_instance_id")).map(ExpectedInteger::value).toList();
        require(instances.size()==1&&instances.getFirst().signum()>0&&instances.getFirst().bitLength()<=31,"one full native event instance required");
        BigInteger instance=instances.getFirst();
        require(command.operation().value().equals(StrictJson.text(original.get("step")))
                &&"postcondition".equals(StrictJson.text(original.get("progress_status")))
                &&"event_instance_advanced".equals(StrictJson.text(selection.get("status"))),"public original is not the actual event consumption result");
        StrictJson.trueValue(selection.get("postcondition_verified"));
        require(integer(selection.get("old_event_instance_id")).equals(instance)
                &&integer(selection.get("selected_option_number")).equals(BigInteger.valueOf(option))
                &&integer(selection.get("selected_native_option_index")).equals(BigInteger.valueOf(option-1L))
                &&integer(selection.get("starting_revision")).equals(command.before().frame().revision())
                &&integer(selection.get("ending_revision")).equals(applied.after().frame().revision())
                &&StrictJson.text(selection.get("starting_snapshot_id")).equals(command.before().frame().snapshotId())
                &&StrictJson.text(selection.get("ending_snapshot_id")).equals(applied.after().frame().snapshotId())
                &&StrictJson.text(selection.get("episode_run_id")).equals(applied.after().frame().episodeRunId()),"public material changed its actual instance/choice/frame");
        ObjectNode result=object(transform(original,false,0));result.put(MARKER_FIELD,MARKER);
        RawJson encoded=raw(result);
        require(tree(parse(encoded).bytes()).equals(original),"public64 roundtrip changed the original JSON domain");
        return encoded;
    }

    /** Wire/type validation and inverse projection only. Parsing grants no native effect or replay authority. */
    public static RawJson parse(RawJson encoded) {
        Objects.requireNonNull(encoded);ObjectNode wire=tree(encoded.bytes());
        require(wire.has(MARKER_FIELD)&&MARKER.equals(StrictJson.text(wire.get(MARKER_FIELD))),"declared event public64 encoding required");
        ObjectNode copy=wire.deepCopy();copy.remove(MARKER_FIELD);
        ObjectNode original=object(transform(copy,true,0));validateShape(original);
        return raw(original);
    }
    private static void validateShape(ObjectNode original) {
        String step=StrictJson.text(original.get("step"));
        require(step.matches("select-event-option-[1-9][0-9]{0,8}"),"public event step is malformed");
        BigInteger option=new BigInteger(step.substring("select-event-option-".length()));
        ObjectNode selection=object(original.get("event_selection"));
        require(integer(selection.get("selected_option_number")).equals(option)
                &&integer(selection.get("selected_native_option_index")).equals(option.subtract(BigInteger.ONE)),"public event native option differs");
        BigInteger instance=integer(selection.get("old_event_instance_id"));
        require(instance.signum()>0&&instance.bitLength()<=31,"public native event instance width differs");
        integer(selection.get("starting_revision"));integer(selection.get("ending_revision"));
        StrictJson.text(selection.get("starting_snapshot_id"));StrictJson.text(selection.get("ending_snapshot_id"));
        StrictJson.trueValue(selection.get("postcondition_verified"));
    }
    private static JsonNode transform(JsonNode node,boolean inverse,int depth) {
        require(node!=null&&depth<=96,"bounded present public event material required");
        if(node.isObject()) {
            ObjectNode result=StrictJson.object();
            for(var entry:node.properties()) {JsonNode value=entry.getValue();Optional<Integer64> kind=Integer64.field(entry.getKey());
                if(kind.isPresent()&&!value.isNull()&&!(kind.orElseThrow()==Integer64.BOOLEAN_OR_SIGNED&&value.isBoolean())) {
                    BigInteger integer=inverse?decimal(value):integer(value);kind.orElseThrow().requireRange(integer);
                    if(inverse)result.put(entry.getKey(),integer);else result.put(entry.getKey(),integer.toString());
                } else result.set(entry.getKey(),transform(value,inverse,depth+1));
            }
            return result;
        }
        if(node.isArray()) {
            ArrayNode result=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();for(JsonNode value:node)result.add(transform(value,inverse,depth+1));return result;
        }
        if(node.isIntegralNumber())require(node.bigIntegerValue().abs().compareTo(SAFE)<=0,"undeclared unsafe public event integer");
        else if(node.isFloatingPointNumber())require(Double.isFinite(node.doubleValue())&&node.decimalValue().abs().compareTo(new java.math.BigDecimal(SAFE))<=0,
                "unsafe public event decimal");
        return node.deepCopy();
    }
    private static ObjectNode tree(byte[] original) { return object(DriverJson.toNode(DriverJson.object(original,MAXIMUM_BYTES))); }
    private static RawJson raw(ObjectNode value) { byte[] bytes=DriverJson.encodeNode(value);require(bytes.length<=MAXIMUM_BYTES,"bounded public event material required");return new RawJson(bytes); }
    private static BigInteger integer(JsonNode value) {
        require(value!=null&&value.isIntegralNumber(),"exact integer public event leaf required");return value.bigIntegerValue();
    }
    private static BigInteger decimal(JsonNode value) {
        require(value!=null&&value.isTextual(),"canonical decimal public64 string required");String token=value.textValue();
        require(token.length()<=21&&token.matches("0|-?[1-9][0-9]*"),"canonical decimal public64 string required");return new BigInteger(token);
    }
    private static ObjectNode object(JsonNode value) { require(value!=null&&value.isObject(),"public event material object required");return (ObjectNode)value; }
    private static void require(boolean condition,String reason) { StrictJson.require(condition,reason); }
}
