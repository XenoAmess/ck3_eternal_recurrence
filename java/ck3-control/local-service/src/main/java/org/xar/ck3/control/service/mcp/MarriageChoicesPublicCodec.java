package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageChoicesProjection;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.MarriageChoices;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public representation of the original typed marriage read. Missing, null and provided revision remain distinct. */
public final class MarriageChoicesPublicCodec {
    private static final BigInteger UINT64_MAX=new BigInteger("18446744073709551615");
    private static final BigInteger SAFE_MAX=BigInteger.valueOf(9_007_199_254_740_991L);
    public sealed interface ExpectedRevision permits MissingRevision,NullRevision,ProvidedRevision { }
    public record MissingRevision() implements ExpectedRevision { }
    public record NullRevision() implements ExpectedRevision { }
    public record ProvidedRevision(BigInteger value) implements ExpectedRevision {
        public ProvidedRevision {Objects.requireNonNull(value);StrictJson.require(value.signum()>=0&&value.compareTo(UINT64_MAX)<=0,"expected_revision must be uint64");}
    }
    public record Request(ExpectedRevision expectedRevision) {
        public Request {Objects.requireNonNull(expectedRevision);}
        public void requireCurrent(BigInteger actualPublicRevision) {
            Objects.requireNonNull(actualPublicRevision);
            if(expectedRevision instanceof ProvidedRevision provided)StrictJson.require(provided.value().equals(actualPublicRevision),"marriage choices expected_revision is stale");
        }
    }
    /** The complete typed producer and its exact original receipt are retained, never a later published frame. */
    public record Response(PlanningReadResult.Known<MarriageChoices> original) {
        public Response {Objects.requireNonNull(original);FamilyMarriageChoicesProjection.project(original);}
    }
    private MarriageChoicesPublicCodec() { }
    public static Request decode(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Missing)return new Request(new MissingRevision());
        StrictJson.require(arguments instanceof PublicBindings.Value,"public marriage arguments must be an object; outer null is not keyword arguments");
        var object=McpJson.object(McpJson.parse(((PublicBindings.Value)arguments).original().bytes()));
        McpJson.fields(object,Set.of("expected_revision"),Set.of());
        if(!object.has("expected_revision"))return new Request(new MissingRevision());
        JsonNode value=object.get("expected_revision");
        if(value.isNull())return new Request(new NullRevision());
        BigInteger revision;
        if(value.isIntegralNumber()) {
            revision=value.bigIntegerValue();StrictJson.require(revision.signum()>=0&&revision.compareTo(SAFE_MAX)<=0,"numeric expected_revision must be a nonnegative JS-safe integer; use a decimal string for uint64");
        } else {
            StrictJson.require(value.isTextual()&&value.textValue().matches("0|[1-9][0-9]{0,19}"),"expected_revision must be a canonical uint64 decimal string or safe integer");
            revision=new BigInteger(value.textValue());
        }
        return new Request(new ProvidedRevision(revision));
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);var object=JsonNodeFactory.instance.objectNode();
        if(request.expectedRevision() instanceof NullRevision)object.putNull("expected_revision");
        if(request.expectedRevision() instanceof ProvidedRevision value)object.put("expected_revision",value.value().toString());
        return raw(object);
    }
    public static RawJson encode(Response response) {
        var actual=FamilyMarriageChoicesProjection.project(Objects.requireNonNull(response).original());
        ObjectNode result=McpJson.object(OpportunityJson.toNode(actual.value())).deepCopy();
        for(String key:List.of("query_sequence","queried_revision","queried_native_revision"))decimal(result,key);
        // The installed native producer validates choice IDs as positive int32 and
        // diagnostic roles as signed int32. Their original numeric domain, including -1, stays intact.
        McpJson.publicNumbers(result);return raw(result);
    }
    private static void decimal(ObjectNode object,String field) {
        JsonNode original=object.get(field);StrictJson.require(original!=null&&original.isIntegralNumber(),"original typed marriage integer is missing or changed: "+field);
        object.put(field,original.bigIntegerValue().toString());
    }
    private static RawJson raw(JsonNode value) {return new RawJson(McpJson.utf8(value.toString()));}
}
