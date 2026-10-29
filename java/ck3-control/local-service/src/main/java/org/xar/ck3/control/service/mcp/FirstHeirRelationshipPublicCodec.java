package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyCurrentRelation;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyCurrentRelationPublic;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRelationCapture;

/** Exact four original MCP arguments; public uint64 identities use decimal strings or safe numeric input. */
public final class FirstHeirRelationshipPublicCodec {
    private static final BigInteger U64=new BigInteger("18446744073709551615"),SAFE=BigInteger.valueOf(9007199254740991L);
    public record Capture(FamilyRelationCapture.Request request,Duration timeout){
        public Capture {Objects.requireNonNull(request);Objects.requireNonNull(timeout);StrictJson.require(!timeout.isZero()&&!timeout.isNegative(),"positive capture timeout required");}
    }
    public record Request(BigInteger expectedNativeRevision,Optional<Capture> capture){
        public Request {Objects.requireNonNull(expectedNativeRevision);capture=Objects.requireNonNull(capture);StrictJson.require(expectedNativeRevision.signum()>0&&expectedNativeRevision.compareTo(U64)<=0,"positive uint64 native revision required");}
        public void requireCurrent(BigInteger actual){StrictJson.require(expectedNativeRevision.equals(actual),"current first-heir expected native revision differs from the actual paused frame");}
    }
    public sealed interface Reply permits Relation,Captured { }
    public record Relation(FamilyCurrentRelation.Observation observation) implements Reply {public Relation {Objects.requireNonNull(observation);}}
    public record Captured(FamilyRelationCapture.Result result) implements Reply {public Captured {Objects.requireNonNull(result);}}
    private FirstHeirRelationshipPublicCodec(){ }
    public static Request decode(PublicMcpDirectory.Arguments arguments){return decode(Objects.requireNonNull(arguments).objectOrEmpty());}
    public static Request decode(RawJson arguments){
        var n=McpJson.object(McpJson.parse(arguments.bytes()));McpJson.fields(n,Set.of("expected_native_revision","guardian_capture_output_directory","guardian_capture_owned_game_pid","guardian_capture_timeout_seconds"),Set.of("expected_native_revision"));
        BigInteger revision=revision(n.get("expected_native_revision"));JsonNode output=n.get("guardian_capture_output_directory");
        JsonNode optionalPid=n.get("guardian_capture_owned_game_pid"),optionalTimeout=n.get("guardian_capture_timeout_seconds");
        StrictJson.require(optionalPid==null||optionalPid.isNull()||optionalPid.isIntegralNumber(),"owned Game PID must be an integer or null");
        StrictJson.require(optionalTimeout==null||optionalTimeout.isNumber(),"capture timeout must be numeric");
        // The original ordinary branch ignores capture-only values after their declared primitive types are checked.
        if(output==null||output.isNull())return new Request(revision,Optional.empty());
        String path=McpJson.text(output);StrictJson.require(!path.isEmpty(),"capture output directory required");
        JsonNode pid=n.get("guardian_capture_owned_game_pid");StrictJson.require(pid!=null&&pid.isIntegralNumber()&&pid.bigIntegerValue().signum()>0&&pid.bigIntegerValue().compareTo(BigInteger.valueOf(0xffff_ffffL))<=0,"guardian capture requires owned Game PID");
        JsonNode timeout=n.get("guardian_capture_timeout_seconds");BigDecimal seconds=BigDecimal.valueOf(360);
        if(timeout!=null){StrictJson.require(timeout.isNumber(),"capture timeout must be a finite positive number");seconds=timeout.decimalValue();}
        StrictJson.require(seconds.signum()>0,"capture timeout must be positive");
        long millis=seconds.movePointRight(3).setScale(0,RoundingMode.CEILING).longValueExact();
        return new Request(revision,Optional.of(new Capture(new FamilyRelationCapture.Request(Path.of(path),pid.longValue()),Duration.ofMillis(millis))));
    }
    public static RawJson encodeRequest(Request request){
        Objects.requireNonNull(request);var n=McpJson.object().put("expected_native_revision",request.expectedNativeRevision().toString());
        request.capture().ifPresent(value->{n.put("guardian_capture_output_directory",value.request().outputDirectory().toString()).put("guardian_capture_owned_game_pid",value.request().ownedGamePid());n.put("guardian_capture_timeout_seconds",BigDecimal.valueOf(value.timeout().toMillis(),3));});
        return new RawJson(McpJson.encode(n));
    }
    public static RawJson encode(Reply reply){
        Objects.requireNonNull(reply);return switch(reply){
            case Relation relation->new RawJson(DriverJson.encode(FamilyCurrentRelationPublic.encode(relation.observation())));
            case Captured captured->new RawJson(DriverJson.encode(captured.result().body()));
        };
    }
    private static BigInteger revision(JsonNode value){
        StrictJson.require(value!=null&&!value.isNull(),"expected_native_revision is required");BigInteger result;
        if(value.isIntegralNumber()){result=value.bigIntegerValue();StrictJson.require(result.compareTo(SAFE)<=0,"numeric native revision exceeds safe JSON integer range; use canonical decimal string");}
        else{StrictJson.require(value.isTextual()&&value.textValue().matches("[1-9][0-9]{0,19}"),"canonical positive native revision string or safe integer required");result=new BigInteger(value.textValue());}
        StrictJson.require(result.signum()>0&&result.compareTo(U64)<=0,"positive uint64 native revision required");return result;
    }
}
