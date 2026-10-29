package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** The original optional resolver arguments, using the existing public event field and public64 contracts. */
public final class EventResolutionPublicCodec {
    private static final Set<String> FIELDS=Set.of("event_instance_id","expected_revision");
    private EventResolutionPublicCodec() { }
    public record Request(EventOptionPublicCodec.Field<Integer> eventInstanceId,
            EventOptionPublicCodec.Field<BigInteger> expectedRevision) {
        public Request {
            Objects.requireNonNull(eventInstanceId);Objects.requireNonNull(expectedRevision);
            if(eventInstanceId.presence()==EventOptionPublicCodec.Presence.VALUE)
                StrictJson.require(eventInstanceId.value()>0,"event_instance_id must be a positive full int32");
            if(expectedRevision.presence()==EventOptionPublicCodec.Presence.VALUE)
                StrictJson.require(expectedRevision.value().signum()>=0&&expectedRevision.value().bitLength()<=64,
                        "public expected_revision must be uint64");
        }
        public Optional<Integer> expectedInstance() {
            return eventInstanceId.presence()==EventOptionPublicCodec.Presence.VALUE?Optional.of(eventInstanceId.value()):Optional.empty();
        }
        public Optional<BigInteger> expectedPublicRevision() {
            return expectedRevision.presence()==EventOptionPublicCodec.Presence.VALUE?Optional.of(expectedRevision.value()):Optional.empty();
        }
    }
    public static Request decode(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Missing)
            return new Request(EventOptionPublicCodec.Field.missing(),EventOptionPublicCodec.Field.missing());
        StrictJson.require(arguments instanceof PublicBindings.Value,"resolve_active_event arguments must be an object or omitted");
        var parsed=StrictJson.parse(((PublicBindings.Value)arguments).original().bytes(),EventOptionPublicCodec.MAXIMUM_REQUEST_BYTES);
        StrictJson.require(parsed instanceof ObjectNode,"resolve_active_event arguments must be an object");ObjectNode n=(ObjectNode)parsed;
        n.fieldNames().forEachRemaining(name->StrictJson.require(FIELDS.contains(name),"unknown resolve_active_event field: "+name));
        EventOptionPublicCodec.Field<Integer> instance=!n.has("event_instance_id")?EventOptionPublicCodec.Field.missing():n.get("event_instance_id").isNull()?EventOptionPublicCodec.Field.nullValue()
                :EventOptionPublicCodec.Field.of((int)StrictJson.integer(n.get("event_instance_id"),1,Integer.MAX_VALUE));
        EventOptionPublicCodec.Field<BigInteger> revision=!n.has("expected_revision")?EventOptionPublicCodec.Field.missing():n.get("expected_revision").isNull()?EventOptionPublicCodec.Field.nullValue()
                :EventOptionPublicCodec.Field.of(EventOptionPublicCodec.decimal(n.get("expected_revision")));
        return new Request(instance,revision);
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);ObjectNode n=StrictJson.object();
        switch(request.eventInstanceId().presence()) {
            case MISSING -> { } case NULL -> n.putNull("event_instance_id");case VALUE -> n.put("event_instance_id",request.eventInstanceId().value());
        }
        switch(request.expectedRevision().presence()) {
            case MISSING -> { } case NULL -> n.putNull("expected_revision");case VALUE -> n.put("expected_revision",request.expectedRevision().value().toString());
        }
        return new RawJson(StrictJson.canonical(n,EventOptionPublicCodec.MAXIMUM_REQUEST_BYTES));
    }
}
