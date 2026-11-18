package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Opt-in actual money21 originals only. Normalization snapshot is derived DATA, never HELLO/Full/receipt authority. */
@EnabledIfSystemProperty(named="xar.native.cashMoneyBoundary.actual",matches="true")
final class MoneyActualBoundaryColdReadTest {
    @Test void actualSignedOverflowAndMonthlyFailureKeepTheSameOriginalFullWallet() throws Exception {
        byte[] base=read(0),baseFull=NativeWire.token(base,"full");
        for(int variant:new int[]{5,6,7,9}) {
            byte[] original=read(variant);assertArrayEquals(baseFull,NativeWire.token(original,"full"),"money edge must preserve actual0 Full token");
            var full=NativeWire.object(NativeWire.parse(baseFull));
            var snapshot=NativeWire.object(full.get("state")).deepCopy();snapshot.set("native_revision",full.get("revision"));
            var hello=snapshot.putObject("diagnostics").putObject("hello");
            hello.set("expected_ck3_version",snapshot.get("game_version"));hello.set("expected_ck3_sha256",snapshot.get("executable_sha256"));
            byte[] cashToken=NativeWire.token(original,"cash");
            var raw=NativeWire.object(NativeWire.parse(NativeWire.token(cashToken,"war_cash_current_resources")));
            assertEquals("xar.ck3.war-cash-current-resources.v2",raw.get("schema").textValue());
            var cash=RawCashCodec.normalize(SdkProjectionJson.encode(raw),SdkProjectionJson.encode(snapshot));
            assertTrue(cash.metrics().currentTreasury().known());
            assertEquals(BigInteger.valueOf(-1234567),cash.metrics().currentTreasury().value().raw());
            assertEquals(100000,cash.metrics().currentTreasury().value().scale());
            assertEquals(RawCashCodec.Presence.NULL,cash.metrics().monthlyNetIncome().presence());
            assertFalse(cash.metrics().currentMilitaryExpenses().available());assertFalse(cash.metrics().allRaisedMilitaryExpenses().available());
            if(variant==7||variant==9) {
                assertEquals(RawCashCodec.Presence.NULL,cash.metrics().monthlyGrossIncome().presence());
                assertEquals(RawCashCodec.Presence.NULL,cash.metrics().monthlyTotalExpenses().presence());
            } else {
                assertEquals(BigInteger.valueOf(variant==5?Long.MIN_VALUE:Long.MAX_VALUE),cash.metrics().monthlyGrossIncome().value().raw());
                assertEquals(BigInteger.valueOf(variant==5?1:-1),cash.metrics().monthlyTotalExpenses().value().raw());
                assertEquals("war_cash_monthly_net_income_overflow",raw.get("monthly_net_income_unavailable_reason").textValue());
            }
            assertFalse(raw.get("formal_action_ready").booleanValue());assertFalse(raw.get("true_treasury_observed").booleanValue());
        }
    }
    @Test void actualEarlyFullAndLateReadFailureRemainDifferentUnknownInputStates() throws Exception {
        byte[] baseFull=NativeWire.token(read(0),"full");var full=NativeWire.object(NativeWire.parse(baseFull));
        var snapshot=NativeWire.object(full.get("state")).deepCopy();snapshot.set("native_revision",full.get("revision"));
        var hello=snapshot.putObject("diagnostics").putObject("hello");
        hello.set("expected_ck3_version",snapshot.get("game_version"));hello.set("expected_ck3_sha256",snapshot.get("executable_sha256"));
        byte[] joined=SdkProjectionJson.encode(snapshot);
        for(int variant:new int[]{8,10}) {
            byte[] packet=read(variant);assertArrayEquals(baseFull,NativeWire.token(packet,"full"));
            var raw=NativeWire.object(NativeWire.parse(NativeWire.token(NativeWire.token(packet,"cash"),"war_cash_current_resources")));
            assertEquals("unavailable",raw.get("status").textValue());assertFalse(raw.path("readiness").path("same_frame_ready").booleanValue());
            for(String key:new String[]{"current_treasury","player_monthly_gross_income","player_monthly_total_expenses","player_monthly_net_income"})assertTrue(raw.get(key).isNull(),key);
            byte[] input=SdkProjectionJson.encode(raw);
            if(variant==8) {
                assertEquals(-1,raw.get("played_character_id").intValue());assertEquals(BigInteger.ZERO,raw.get("snapshot_revision").bigIntegerValue());
                assertThrows(IllegalArgumentException.class,()->RawCashCodec.normalize(input,joined));
            } else {
                var data=RawCashCodec.normalize(input,joined);assertFalse(data.metrics().currentTreasury().known());
                assertEquals(RawCashCodec.Presence.NULL,data.metrics().currentTreasury().presence());
                assertFalse(data.metrics().readiness().sameFrameReady().value());
                assertEquals(java.util.List.of(BigInteger.valueOf(-2080374784)),data.playerArmyIds());
            }
        }
    }

    private static byte[] read(int variant)throws Exception {
        String prefix="xar.native.personalCashV2.matched."+variant+".";
        Path path=Path.of(required(prefix+"path"));if(!path.isAbsolute())throw new IOException("absolute original packet path required");
        int count=Integer.parseInt(required(prefix+"bytes"));if(count<1||count>16384)throw new IOException("bounded original packet required");
        byte[] original;try(var input=Files.newInputStream(path)){original=input.readNBytes(count+1);}
        assertEquals(count,original.length);assertEquals(required(prefix+"sha256"),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        return original;
    }
    private static String required(String key)throws IOException {
        String value=System.getProperty(key);if(value==null||value.isBlank())throw new IOException("actual original property absent: "+key);return value;
    }
}
