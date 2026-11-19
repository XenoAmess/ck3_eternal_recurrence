package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile.Kind;

/** Synthetic protocol DATA/negative cases only. No packet is claimed to originate from C++ or an application-main ticket. */
final class OpeningReadProfileProtocolTest {
    private static final String READER="a".repeat(64),ABI="b".repeat(64);
    private static final OpeningReadProfile PROFILE=new OpeningReadProfile(new OpeningReadProfile.SourcePins(READER,ABI));
    private static final OpeningReadProfile.Frame FRAME=new OpeningReadProfile.Frame(BigInteger.valueOf(3),BigInteger.valueOf(24000),BigInteger.valueOf(-2130706431));

    @Test void observedUnavailableRemainsNullDataAndCannotInstallALiveRead() {
        for(Kind kind:Kind.values()) {
            ObjectNode row=unavailable(kind);RawJson raw=raw(row);var data=PROFILE.decodeData(kind,raw,FRAME);
            assertFalse(data.available());assertTrue(data.frame().isEmpty());assertTrue(data.government().isEmpty());assertTrue(data.progress().isEmpty());
            assertArrayEquals(raw.bytes(),data.original().bytes());assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
            ObjectNode bad=row.deepCopy();bad.putNull("unavailable_reason");reject(kind,bad);
            bad=row.deepCopy();bad.put("date_raw",0);reject(kind,bad);
            bad=row.deepCopy();((ObjectNode)bad.get("readiness")).put("same_frame_ready",true);reject(kind,bad);
            bad=row.deepCopy();bad.put("action_ready",true);reject(kind,bad);
        }
    }
    @Test void exactSchemaFieldsetBuildPinsAndBooleanRolesCannotDrift() {
        ObjectNode original=unavailable(Kind.SCOPE);
        for(String key:List.of("schema","government","origin","provenance","read_only")) {ObjectNode bad=original.deepCopy();bad.remove(key);reject(Kind.SCOPE,bad);}
        ObjectNode bad=original.deepCopy();bad.put("campaign_root_context",true);reject(Kind.SCOPE,bad);
        bad=original.deepCopy();bad.put("schema",Kind.CURRENT.schema());reject(Kind.SCOPE,bad);
        bad=original.deepCopy();bad.put("read_only",false);reject(Kind.SCOPE,bad);
        bad=original.deepCopy();bad.put("full_governance_ready",true);reject(Kind.SCOPE,bad);
        for(String field:List.of("profile_id","adapter_id","game_version","executable_sha256","reader_source_sha256","abi_manifest_sha256")) {
            bad=original.deepCopy();((ObjectNode)bad.get("provenance")).put(field,"unqualified-other-value");reject(Kind.SCOPE,bad);
        }
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.SourcePins(READER.toUpperCase(),ABI));
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.SourcePins("0",ABI));
    }
    @Test void completeGovernmentFlagsKeepNativeOrderAndDuplicatesAsDataOnly() {
        ObjectNode row=available(Kind.SCOPE);var government=row.putObject("government");government.put("key","feudal_government").put("native_flag_count",3);
        government.putArray("flags").add("government_is_feudal").add("second_flag").add("government_is_feudal");
        var data=PROFILE.decodeData(Kind.SCOPE,raw(row),FRAME);
        assertEquals(List.of("government_is_feudal","second_flag","government_is_feudal"),data.government().orElseThrow().flags());
        assertThrows(UnsupportedOperationException.class,()->data.government().orElseThrow().flags().add("caller"));
        assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
        ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("government")).put("native_flag_count",2);reject(Kind.SCOPE,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("government")).put("native_flag_count",3.0);reject(Kind.SCOPE,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("government")).putArray("flags").add("government_is_feudal").add(0).add("second_flag");reject(Kind.SCOPE,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("origin")).put("main_owner_observed",true);reject(Kind.SCOPE,bad);
    }
    @Test void completeSignedActorAndUnsignedRevisionNeverNarrowIntoLegacyIdentities() {
        for(BigInteger actor:List.of(BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE))) {
            BigInteger rev=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
            var expected=new OpeningReadProfile.Frame(rev,BigInteger.valueOf(Integer.MIN_VALUE),actor);
            ObjectNode row=available(Kind.SCOPE);row.put("native_revision",rev).put("snapshot_id","native:"+rev).put("date_raw",Integer.MIN_VALUE).put("player_character_id",actor);
            var g=row.putObject("government");g.put("key","actual_software_definition").put("native_flag_count",0);g.putArray("flags");
            var data=PROFILE.decodeData(Kind.SCOPE,raw(row),expected);assertEquals(expected,data.frame().orElseThrow());
            assertThrows(IllegalArgumentException.class,()->PROFILE.decodeData(Kind.SCOPE,raw(row),FRAME));
        }
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.Frame(BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.Frame(BigInteger.ONE,BigInteger.ZERO,BigInteger.valueOf(-1)));
        ObjectNode bad=available(Kind.SCOPE);bad.put("native_revision",3.0);reject(Kind.SCOPE,bad);
        bad=available(Kind.SCOPE);bad.put("snapshot_id","native:03");reject(Kind.SCOPE,bad);
    }
    @Test void focusPresenceCounterTypesRangesAndOriginDoNotInventCurrentEvidence() {
        ObjectNode row=current();var data=PROFILE.decodeData(Kind.CURRENT,raw(row),FRAME);
        assertEquals(BigInteger.valueOf(Long.MAX_VALUE),data.progress().orElseThrow().xpTotalRaw().orElseThrow());
        assertEquals(BigInteger.valueOf(20),data.progress().orElseThrow().xpWithinLevelRaw().orElseThrow());
        assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
        for(String field:List.of("xp_total_raw","xp_within_level_raw","xp_per_level","unspent_perk_points","used_perk_points")) {
            ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put(field,-1);reject(Kind.CURRENT,bad);
            bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put(field,"1");reject(Kind.CURRENT,bad);
        }
        for(String field:List.of("xp_per_level","unspent_perk_points","used_perk_points")) {
            ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put(field,BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE));reject(Kind.CURRENT,bad);
        }
        ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("xp_total_raw",BigInteger.valueOf(Long.MAX_VALUE).add(BigInteger.ONE));reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("xp_within_level_raw",100000000);reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_focus")).put("presence","absent");
        for(String key:List.of("key","lifestyle_key"))((ObjectNode)bad.get("current_focus")).putNull(key);
        var absent=(ObjectNode)bad.get("current_lifestyle_progress");absent.put("presence","absent");
        for(String key:List.of("lifestyle_key","xp_total_raw","xp_within_level_raw","xp_per_level","unspent_perk_points","used_perk_points"))absent.putNull(key);
        reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("presence","absent");reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_focus")).put("presence","unknown");reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("lifestyle_key","other_style");reject(Kind.CURRENT,bad);
        bad=row.deepCopy();var origin=(ObjectNode)bad.get("origin");origin.put("source_kind","application_main_ticket").put("main_owner_observed",true).put("ticket_sequence",0).put("pump_epoch",1).put("thread_id",1);reject(Kind.CURRENT,bad);
    }
    private static ObjectNode current() {
        ObjectNode row=available(Kind.CURRENT);row.putObject("current_focus").put("presence","present").put("key","observed_focus").put("lifestyle_key","observed_style");
        row.putObject("current_lifestyle_progress").put("presence","present").put("lifestyle_key","observed_style").put("xp_total_raw",Long.MAX_VALUE)
                .put("xp_within_level_raw",20).put("xp_per_level",1000).put("unspent_perk_points",1).put("used_perk_points",2);return row;
    }
    private static ObjectNode available(Kind kind) {
        ObjectNode row=unavailable(kind);row.put("status","available").putNull("unavailable_reason");row.put("native_revision",FRAME.nativeRevision()).put("snapshot_id",FRAME.snapshotId())
                .put("date_raw",FRAME.dateRaw()).put("player_character_id",FRAME.playerCharacterId());
        var ready=(ObjectNode)row.get("readiness");ready.fieldNames().forEachRemaining(k->ready.put(k,true));
        ((ObjectNode)row.get("origin")).put("source_kind","offline_fixture");return row;
    }
    private static ObjectNode unavailable(Kind kind) {
        ObjectNode row=StrictJson.object().put("schema",kind.schema()).put("status","unavailable").put("unavailable_reason","synthetic_protocol_data_not_cpp")
                .put("read_only",true).put("full_governance_ready",false).put("action_ready",false);
        for(String key:List.of("native_revision","snapshot_id","date_raw","player_character_id"))row.putNull(key);
        var ready=row.putObject("readiness");ready.put("same_frame_ready",false);
        if(kind==Kind.SCOPE){row.putNull("government");ready.put("government_key_ready",false).put("government_flags_ready",false);}
        else {row.putNull("current_focus");row.putNull("current_lifestyle_progress");ready.put("current_focus_ready",false).put("lifestyle_progress_ready",false);}
        var origin=row.putObject("origin");origin.put("source_kind","unavailable").putNull("ticket_sequence").putNull("pump_epoch").putNull("thread_id").put("main_owner_observed",false);
        row.putObject("provenance").put("profile_id",kind.profile()).put("adapter_id",OpeningReadProfile.ADAPTER).put("game_version",OpeningReadProfile.VERSION)
                .put("executable_sha256",OpeningReadProfile.EXECUTABLE).put("reader_source_sha256",READER).put("abi_manifest_sha256",ABI);return row;
    }
    private static RawJson raw(ObjectNode row){return new RawJson(StrictJson.canonical(row));}
    private static void reject(Kind kind,ObjectNode row){assertThrows(IllegalArgumentException.class,()->PROFILE.decodeData(kind,raw(row),FRAME));}
}
