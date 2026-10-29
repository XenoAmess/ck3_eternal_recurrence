package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;

/** Original seventeen-field context only; no transport/read/adoption authority.
 * Unavailable date/actor integers retain the original Python domain. */
public record NativePlayerReligionContext(String schema,String gameVersion,String executableSha256,
        boolean available,Optional<String> unavailableReason,BigInteger captureEpoch,BigInteger dateRaw,
        BigInteger playedCharacterId,OptionalLong riteId,OptionalLong faithId,OptionalLong religionId,
        OptionalLong faithMainRiteId,Optional<String> faithKey,Optional<String> religionKey,
        OptionalLong faithFervorRaw,OptionalLong spiritualFulfillmentRaw,int rawScale) {
    public static final BigInteger U64=new BigInteger("18446744073709551615");
    public static final Set<String> FIELDS=Set.of("schema","game_version","executable_sha256","available",
            "unavailable_reason","capture_epoch","date_raw","played_character_id","rite_id","faith_id",
            "religion_id","faith_main_rite_id","faith_key","religion_key","faith_fervor_raw",
            "spiritual_fulfillment_raw","raw_scale");
    public enum Build {
        CROZIER2("1.20.0.2","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D","ck3_12002_religion_context_v1"),
        CROZIER3("1.20.0.3","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6","ck3_12003_religion_context_v1"),
        CROZIER4("1.20.0.4","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518","ck3_12004_religion_context_v1");
        private final String version,sha256,schema;
        Build(String version,String sha256,String schema){this.version=version;this.sha256=sha256;this.schema=schema;}
        public String version(){return version;}public String sha256(){return sha256;}public String schema(){return schema;}
        public static Build exact(String version,String sha){
            Objects.requireNonNull(version);Objects.requireNonNull(sha);
            for(var build:values())if(build.version.equals(version)&&build.sha256.equalsIgnoreCase(sha))return build;
            throw new IllegalArgumentException("unknown exact native religion build");
        }
    }
    public NativePlayerReligionContext {
        need(Build.exact(gameVersion,executableSha256).schema().equals(schema),"context schema/build drift");
        Objects.requireNonNull(unavailableReason);Objects.requireNonNull(captureEpoch);
        Objects.requireNonNull(dateRaw);Objects.requireNonNull(playedCharacterId);
        need(captureEpoch.signum()>0&&captureEpoch.compareTo(U64)<=0,"capture epoch must be positive uint64");
        for(var id:new OptionalLong[]{riteId,faithId,religionId,faithMainRiteId}){
            Objects.requireNonNull(id);need(id.isEmpty()||id.getAsLong()>=0&&id.getAsLong()<=0xffff_ffffL,"uint32 context reference required");
        }
        Objects.requireNonNull(faithKey);Objects.requireNonNull(religionKey);
        Objects.requireNonNull(faithFervorRaw);Objects.requireNonNull(spiritualFulfillmentRaw);
        need(rawScale==100000,"context raw scale differs");
        need(available?unavailableReason.isEmpty()&&spiritualFulfillmentRaw.isPresent()
                :unavailableReason.filter(v->!v.isEmpty()).isPresent(),"context availability lost its reason/value");
    }
    public Build exactBuild(){return Build.exact(gameVersion,executableSha256);}
    public void requireAvailableFrame(BigInteger actualDate,BigInteger actualActor){
        Objects.requireNonNull(actualDate);Objects.requireNonNull(actualActor);
        if(available)need(dateRaw.equals(actualDate)&&playedCharacterId.equals(actualActor),"context player/date differs from actual queried frame");
    }
    public static NativePlayerReligionContext decode(JsonNode n){
        need(n!=null&&n.isObject(),"context object required");
        Set<String> keys=new HashSet<>();n.fieldNames().forEachRemaining(keys::add);need(keys.equals(FIELDS),"exact seventeen context fields required");
        return new NativePlayerReligionContext(text(n.get("schema")),text(n.get("game_version")),text(n.get("executable_sha256")),
            bool(n.get("available")),nullableText(n.get("unavailable_reason")),integer(n.get("capture_epoch")),
            integer(n.get("date_raw")),integer(n.get("played_character_id")),
            nullableU32(n.get("rite_id")),nullableU32(n.get("faith_id")),nullableU32(n.get("religion_id")),nullableU32(n.get("faith_main_rite_id")),
            nullableText(n.get("faith_key")),nullableText(n.get("religion_key")),nullableI64(n.get("faith_fervor_raw")),
            nullableI64(n.get("spiritual_fulfillment_raw")),scale(n.get("raw_scale")));
    }
    public ObjectNode encode(){
        var n=JsonNodeFactory.instance.objectNode().put("schema",schema).put("game_version",gameVersion)
            .put("executable_sha256",executableSha256).put("available",available).put("capture_epoch",captureEpoch)
            .put("date_raw",dateRaw).put("played_character_id",playedCharacterId).put("raw_scale",rawScale);
        text(n,"unavailable_reason",unavailableReason);text(n,"faith_key",faithKey);text(n,"religion_key",religionKey);
        number(n,"rite_id",riteId);number(n,"faith_id",faithId);number(n,"religion_id",religionId);number(n,"faith_main_rite_id",faithMainRiteId);
        number(n,"faith_fervor_raw",faithFervorRaw);number(n,"spiritual_fulfillment_raw",spiritualFulfillmentRaw);return n;
    }
    public static BigInteger integer(JsonNode n){need(n!=null&&n.isIntegralNumber(),"exact JSON integer required");return n.bigIntegerValue();}
    private static String text(JsonNode n){need(n!=null&&n.isTextual(),"JSON text required");return n.textValue();}
    private static boolean bool(JsonNode n){need(n!=null&&n.isBoolean(),"JSON boolean required");return n.booleanValue();}
    private static Optional<String> nullableText(JsonNode n){need(n!=null,"required nullable text missing");return n.isNull()?Optional.empty():Optional.of(text(n));}
    private static OptionalLong nullableI64(JsonNode n){need(n!=null,"required nullable integer missing");if(n.isNull())return OptionalLong.empty();var value=integer(n);need(value.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&value.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"signed64 context value required");return OptionalLong.of(value.longValueExact());}
    private static int scale(JsonNode n){need(integer(n).equals(BigInteger.valueOf(100000)),"context raw scale differs");return 100000;}
    private static OptionalLong nullableU32(JsonNode n){var value=nullableI64(n);need(value.isEmpty()||value.getAsLong()>=0&&value.getAsLong()<=0xffff_ffffL,"uint32 reference required");return value;}
    private static void text(ObjectNode n,String key,Optional<String> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
    private static void number(ObjectNode n,String key,OptionalLong value){if(value.isPresent())n.put(key,BigInteger.valueOf(value.getAsLong()));else n.putNull(key);}
    private static void need(boolean value,String reason){if(!value)throw new IllegalArgumentException(reason);}
}
