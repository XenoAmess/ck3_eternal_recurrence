package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;

/** Cold read only of Native-owner actual extracted production outer formatter output.
 * Missing exact producer pins fail; no software ACK fallback or live/Full role is created.
 */
final class NativeCashV2OuterCommandResultTest {
    @Test void actualPostGetterFailuresAreNegativeOuterResultsWithoutInnerCashData() throws Exception {
        for(String mode:List.of("wallet-drift","adapter-drift","revision-source-drift","owner-after-gross")) {
            byte[] raw=actual(mode);byte[] unchanged=raw.clone();
            var result=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(raw)));
            assertFalse(result.nativeOk(),mode);assertEquals(NativeWire.Presence.ABSENT,result.result().presence(),mode);
            assertTrue(result.result().token().isEmpty(),mode);
            var envelope=NativeWire.object(NativeWire.parse(raw));assertFalse(envelope.has("result"),mode);
            assertTrue(envelope.has("error"),mode);
            assertArrayEquals(unchanged,raw);
            // The original negative command_result is never a current-cash document.
            assertThrows(IllegalArgumentException.class,()->RawCashCodec.validateMonthlySourceContract(raw));
        }
    }

    @Test void actualPositiveOuterPartialUnknownAndOverflowPreserveTheFrozenCashContract() throws Exception {
        for(String mode:List.of("partial","monthly-unknown","net-overflow")) {
            byte[] raw=actual(mode);var result=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(raw)));
            assertTrue(result.nativeOk(),mode);assertEquals(NativeWire.Presence.VALUE,result.result().presence(),mode);
            byte[] inner=result.result().token().orElseThrow().value();
            byte[] cash=NativeWire.token(inner,"war_cash_current_resources");
            var original=NativeWire.object(NativeWire.parse(inner));var document=NativeWire.object(NativeWire.parse(cash));
            assertEquals("query-war-cash-current-resources-v2",original.path("step").textValue());
            assertEquals(RawCashCodec.SIGNED_SCOPE_SCHEMA,document.path("schema").textValue());
            RawCashCodec.validateMonthlySourceContract(cash);
            assertTrue(document.path("readiness").path("same_frame_ready").booleanValue());
            assertFalse(document.path("formal_action_ready").booleanValue());assertFalse(document.path("advertised").booleanValue());
            for(String expense:List.of("current","all_raised")) {
                var row=document.path("military_expenses").get(expense);
                assertEquals("unavailable",row.path("status").textValue());
                for(String key:List.of("resource_raw_native","gold_raw","treasury_raw"))assertTrue(row.get(key).isNull(),key);
            }
            if(mode.equals("monthly-unknown")) {
                assertFalse(document.path("readiness").path("monthly_net_income_ready").booleanValue());
                for(String stem:List.of("gross_income","total_expenses","net_income"))assertTrue(document.get("player_monthly_"+stem).isNull(),stem);
            } else if(mode.equals("net-overflow")) {
                assertTrue(document.get("player_monthly_net_income").isNull());
                assertEquals("war_cash_monthly_net_income_overflow",document.path("monthly_net_income_unavailable_reason").textValue());
                assertFalse(document.path("readiness").path("monthly_net_income_ready").booleanValue());
            } else assertFalse(document.get("player_monthly_net_income").isNull());
        }
    }

    @Test void actualStandaloneWar21CannotBeACashDocument() throws Exception {
        Path root=Path.of(required("xar.florinWar.cppPacketDir"));assertTrue(root.isAbsolute());
        String[][] pins={
            {"war-attacker", "2466", "9c406c3776427c4cbf23c9d971e4959a172968edc7c48b3768e81f40df10d0b8"},
            {"war-empty", "1370", "530c7ba6451edd2fd51975ffbb527348badff41e373ebfd2151294e3e2df758e"},
            {"war-zero-duplicates", "2475", "c5d5bf124b6d84ae549eee776d79f4a52810328f84415b1271e1d64edf4d1d22"}};
        for(String[] pin:pins) {
            byte[] bytes;try(var input=Files.newInputStream(root.resolve(pin[0]+".json"))){bytes=input.readNBytes(4097);}
            assertEquals(Integer.parseInt(pin[1]),bytes.length);
            assertEquals(pin[2],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            var frame=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(bytes)));assertTrue(frame.nativeOk());
            byte[] token=frame.result().token().orElseThrow().value();var document=NativeWire.object(NativeWire.parse(token));
            assertEquals("ck3_1210_active_wars_identity_v1",document.get("schema").textValue());
            assertFalse(document.get("full_snapshot_available").booleanValue());
            assertFalse(document.get("complete_active_wars_qualified").booleanValue());
            assertThrows(IllegalArgumentException.class,()->RawCashCodec.validateMonthlySourceContract(token));
        }
    }

    private static byte[] actual(String mode) throws Exception {
        String prefix="xar.native.personalCashV2.outer."+mode;
        Path path=Path.of(required(prefix+".path"));if(!path.isAbsolute())throw new IOException("absolute actual production outer packet required");
        int length=Integer.parseInt(required(prefix+".bytes"));if(length<1||length>16384)throw new IOException("bounded actual outer packet required");
        String expectedSha=required(prefix+".sha256");if(!expectedSha.matches("[0-9a-f]{64}"))throw new IOException("exact actual outer SHA256 required");
        byte[] bytes;try(var input=Files.newInputStream(path)){bytes=input.readNBytes(length+1);}
        assertEquals(length,bytes.length);assertEquals(expectedSha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return bytes;
    }
    private static String required(String property) throws IOException {
        String value=System.getProperty(property);if(value==null||value.isBlank())throw new IOException("required Native-owner actual outer pin missing: "+property);return value;
    }
}
