package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed actual-player inventory read only. No caller artifact, owner, role, key, slot or lease selector. */
public final class CurrentLivingInventoryQuery {
    public static final String SCHEMA="xar.living-inventory.request/v1";
    public static final String SOURCE_SCHEMA="xar.living-inventory.source/v1";
    public static final String RESULT_SCHEMA="xar.living-inventory.result/v1";
    public static final String BACKEND="current267-fixed-living-inventory-v1";
    public static final String STEP="ck3_121003_living_inventory.query";
    public static final String CAPABILITY="game.living.inventory.query.v1";
    public static final String ACTION="query_inventory";
    public static final long MAXIMUM_FULL_ID=0xffff_fffeL;
    private CurrentLivingInventoryQuery() { }
    public static NativeRequest request(CoreFrame.Partial actual){
        Objects.requireNonNull(actual);StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");requirePrefix(actual.prefix());
        var build=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFrameAdapterId()).put("backend",BACKEND).put("action",ACTION);
        claim.set("expected_core",prefix(actual.prefix()));var fields=StrictJson.object();fields.set("living_inventory",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
    static void requirePrefix(CoreFrame.Prefix p){
        Objects.requireNonNull(p);StrictJson.require(p.speed()>=1&&p.speed()<=5&&p.paused()&&p.localPlayerId()>=0&&p.mapReady()
                &&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),"Actual paused living map Core required");
        // date_raw is any exact int32 guard DATA, including zero/negative. It grants no phase or Date authority.
    }
    static ObjectNode prefix(CoreFrame.Prefix p){return StrictJson.object().put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
            .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
            .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());}
    static void requireFullId(long id){StrictJson.require(id>=0&&id<=MAXIMUM_FULL_ID,"Full uint32 generation-aware ID except FFFFFFFF required");}
    static long fullId(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.ZERO,BigInteger.valueOf(MAXIMUM_FULL_ID)).longValueExact();}
    static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    static boolean bool(ObjectNode n,String key)throws IOException{var v=n.get(key);if(v==null||!v.isBoolean())throw new IOException("Actual Living inventory bool required: "+key);return v.booleanValue();}
    static void unsigned(BigInteger n,boolean positive){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&(!positive||n.signum()>0)&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Canonical uint64 required");}
    static BigInteger decimal(ObjectNode n,String key)throws IOException{String text=NativeWire.text(n.get(key));if(!text.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+key);var value=new BigInteger(text);unsigned(value,false);return value;}
    static void identity(ObjectNode n,String key,String expected)throws IOException{String value=NativeWire.text(n.get(key));if(key.equals("executable_sha256")?!value.equalsIgnoreCase(expected):!value.equals(expected))throw new IOException("Exact Living inventory identity mismatch: "+key);}
    static void requireActualText(String value) {
        Objects.requireNonNull(value);
        for (int i=0; i<value.length(); i++) {
            char ch=value.charAt(i);
            if (Character.isHighSurrogate(ch)) {
                StrictJson.require(i+1<value.length() && Character.isLowSurrogate(value.charAt(i+1)), "Unpaired actual-text surrogate");
                i++;
            } else StrictJson.require(!Character.isLowSurrogate(ch), "Unpaired actual-text surrogate");
        }
        StrictJson.require(value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=4096, "Actual UTF8 text exceeds4096bytes");
        // Empty, embeddedNUL, other controls and richtext are actual read DATA.
    }
    static String actualText(JsonNode value) throws IOException {
        if (value==null || !value.isTextual()) throw new IOException("Actual text must be a string");
        String text=value.textValue();requireActualText(text);return text;
    }
}
