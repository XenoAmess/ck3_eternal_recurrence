package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Full/CASH C++ tokens through the sole software receiver. ACK envelopes and
 * HELLO are explicit software fixtures; no Game, Driver or public finance readiness. */
final class NativePersonalCashPortTest {
    private static final String STEP="query-war-cash-current-resources-v1",CAP="game.query.war-cash-current-resources.v1";
    private static final String STEP_V2="query-war-cash-current-resources-v2",CAP_V2="game.query.war-cash-current-resources.v2";
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final String BRIDGE="software-personal-cash1210",ADAPTER="ck3-1.21.0-msvc-x64";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String CASH_SHA="2776f9887cbe051e628c55c36dc7d00d6810d4bd4e7abba09c540654e31564b3";
    private static final String FULL_SHA="5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550";
    private record Cpp(byte[] full,byte[] state,String snapshotId,BigInteger revision,byte[] cash) { }

    @Test void matchingCppCashRetainsPositiveRevisionOriginalTokenAndActualFullCustody() throws Exception {
        try(var f=new Fixture(true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashReceived(before,until));
            assertSame(before.frame(),cash.fullFrame());assertEquals(until,cash.validUntil());
            assertEquals(1,cash.cash().frame().playedCharacterId());assertEquals(BigInteger.TEN,cash.cash().frame().snapshotRevision());
            assertEquals(123456,cash.cash().frame().dateRaw());assertTrue(cash.cash().activeWarIds().isEmpty());assertTrue(cash.cash().playerArmyIds().isEmpty());
            assertEquals(new BigInteger("-1234567"),cash.cash().metrics().currentTreasury().value().raw());
            assertEquals(new BigInteger("500000"),cash.cash().metrics().monthlyGrossIncome().value().raw());
            assertEquals(new BigInteger("720000"),cash.cash().metrics().monthlyTotalExpenses().value().raw());
            assertEquals(new BigInteger("-220000"),cash.cash().metrics().monthlyNetIncome().value().raw());
            var original=NativeWire.object(NativeWire.parse(cash.original().originalResultToken().orElseThrow().bytes()));
            assertFalse(original.path("advertised").booleanValue());assertFalse(original.path("war_cash_current_resources").path("formal_action_ready").booleanValue());
            assertFalse(original.path("war_cash_current_resources").path("complete_snapshot").booleanValue());
            original(f,cash.original(),f.source.cpp.cash());cash.requireOriginal(f.actual,until);
            Object role=cash;assertFalse(role instanceof NativeGameTransport.FullClockRead);assertFalse(role instanceof NativeGameTransport.CoreRead);
            assertFalse(role instanceof NativeFreshSnapshotPort.Received);
            zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
        }
    }
    @Test void softwareCashV1PreservesZeroAndNonnegativeFullScopeWithoutSignedRelabeling() throws Exception {
        int[] units={0,1048575};
        try(var f=new Fixture(softwareArmyScope(units,units),true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashReceived(before,until));
            assertEquals(java.util.Arrays.stream(units).mapToObj(BigInteger::valueOf).toList(),cash.cash().playerArmyIds());
            cash.requireOriginal(f.actual,until);original(f,cash.original(),f.source.cpp.cash());counts(f,1,1);
            zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
        }
    }
    @Test void softwareCashV1NegativeFullOrCashScopeKeepsOriginalPositiveAckAndCannotReplay() throws Exception {
        for(int[][] pair:new int[][][]{{{-2080374784},{0}},{{-2080374784},{-2080374784}},{{0},{-1}},{{0},{0,0}}}) {
            try(var f=new Fixture(softwareArmyScope(pair[0],pair[1]),true,null,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashReceived(before,until));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());assertTrue(ack.nativeOk());
                original(f,ack,f.source.cpp.cash());zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
            }
        }
    }

    @Test void explicitV2CapabilityPreservesSignedFullScopeAndDoesNotUpgradeDefaultV1() throws Exception {
        for(int[] units:new int[][]{{Integer.MIN_VALUE,1,-2080374782,2130706435},{0,-2080374783,2130706434}})
        try(var f=new Fixture(softwareSignedScope(units,units),false,true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,0);
            var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashSignedScopeReceived(before,until));
            assertEquals(java.util.Arrays.stream(units).mapToObj(BigInteger::valueOf).toList(),cash.cash().playerArmyIds());
            assertEquals(org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.PlayerArmyIdDomain.FLORIN_SIGNED_FULL,cash.cash().playerArmyIdDomain());
            original(f,cash.original(),f.source.cpp.cash(),STEP_V2);cash.requireOriginal(f.actual,until);
            zero(f.actual.readPersonalCashSignedScopeReceived(before,until));zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
        }
    }
    @Test void v1CapabilityDoesNotAuthorizeV2AndItsUnusedFullCanStillReadOriginalV1() throws Exception {
        try(var f=new Fixture(softwareArmyScope(new int[]{0},new int[]{0}),true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            zero(f.actual.readPersonalCashSignedScopeReceived(before,until));counts(f,1,0);
            var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashReceived(before,until));
            original(f,cash.original(),f.source.cpp.cash());counts(f,1,1);
        }
    }
    @Test void v2StepAndSchemaCannotBeRelabeledFromV1EvenWithSignedCapability() throws Exception {
        var cpp=softwareSignedScope(new int[]{-2},new int[]{-2});
        for(String changed:List.of("step","schema")) {
            var token=NativeWire.object(NativeWire.parse(cpp.cash()));
            if(changed.equals("step"))token.put("step",STEP);
            else NativeWire.object(token.get("war_cash_current_resources")).put("schema","xar.ck3.war-cash-current-resources.v1");
            byte[] malformed=StrictJson.canonical(token);
            try(var f=new Fixture(cpp,false,true,malformed,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var absent=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashSignedScopeReceived(before,until));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,absent.original());assertTrue(ack.nativeOk());
                original(f,ack,malformed,STEP_V2);zero(f.actual.readPersonalCashSignedScopeReceived(before,until));counts(f,1,1);
            }
        }
    }
    @Test void signedV2CashScopeRejectsFullGenerationMismatchSentinelDuplicateAndOrderMismatch() throws Exception {
        for(int[][] pair:new int[][][]{{{-2080374784},{-2046820352}},{{0},{-1}},{{-2080374784},{-2080374784,-2080374784}},{{0,-2080374783},{-2080374783,0}}}) {
            try(var f=new Fixture(softwareSignedScope(pair[0],pair[1]),false,true,null,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var absent=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashSignedScopeReceived(before,until));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,absent.original());assertTrue(ack.nativeOk());
                original(f,ack,f.source.cpp.cash(),STEP_V2);zero(f.actual.readPersonalCashSignedScopeReceived(before,until));counts(f,1,1);
            }
        }
    }
    @Test void malformedFullUnitScopeIsRefusedAtIngressBeforeAnyCashQuery() throws Exception {
        // Full ingress canonicalizes first. A missing unit sentinel or duplicate
        // complete identity cannot be used to manufacture a held Full cash source.
        for(int[] invalid:new int[][]{{-1},{0,0},{-2080374784,-2080374784}})
            try(var f=new Fixture(softwareSignedScope(invalid,new int[]{0}),false,true,null,false)) {
                var until=f.clock.instant().plusSeconds(30);
                assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,f.actual.readFullClockFrameReceived(until));
                counts(f,1,0);
            }
    }

    @Test void unknownV2RetainsItsIdenticalRequestAcrossBothVersionEntrypoints() throws Exception {
        try(var f=new Fixture(softwareSignedScope(new int[]{-2},new int[]{-2}),false,true,null,true)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            var absent=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashSignedScopeReceived(before,until));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,absent.original());
            assertArrayEquals(f.source.cashRequests.getLast(),unknown.originalRequestPacket());
            assertSame(absent,f.actual.readPersonalCashSignedScopeReceived(before,until));
            assertSame(absent,f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
        }
    }
    @Test void v2ReceiptCannotExtendDeadlineOrSurviveExpiryCloseOrSupersedingFull() throws Exception {
        for(String changed:List.of("extended","expired","closed","newer-full"))
            try(var f=new Fixture(softwareSignedScope(new int[]{-2},new int[]{-2}),false,true,null,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashSignedScopeReceived(before,until));
                if(changed.equals("extended"))assertThrows(IOException.class,()->cash.requireOriginal(f.actual,until.plusNanos(1)));
                else {
                    if(changed.equals("expired"))f.clock.set(cash.validUntil());
                    else if(changed.equals("closed"))f.actual.close();
                    else assertInstanceOf(NativeGameTransport.FullClockReceived.class,f.actual.readFullClockFrameReceived(until));
                    assertThrows(IOException.class,()->cash.requireOriginal(f.actual,until));
                }
                counts(f,changed.equals("newer-full")?2:1,1);
            }
    }

    @Test void sameWalletRuleAndOriginalAckApplyToBothExplicitVersionEntrypoints() throws Exception {
        for(boolean signed:List.of(false,true))for(long changed:List.of(0L,-1234566L,-1234568L,Long.MIN_VALUE,Long.MAX_VALUE)) {
            // V2 scope and every changed wallet are synthetic DATA, never a requalified Cash14 oracle.
            var input=signed?softwareSignedScope(new int[]{-2},new int[]{-2}):cpp();
            var token=NativeWire.object(NativeWire.parse(input.cash())).deepCopy();
            ((ObjectNode)token.get("war_cash_current_resources").get("current_treasury")).put("raw",changed);
            byte[] negative=org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson.encode(token);
            try(var f=new Fixture(input,!signed,signed,negative,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var held=NativeWire.object(NativeWire.parse(before.frame().state().bytes()));
                assertEquals(new BigInteger("-1234567"),held.get("played_character_gold").get("raw").bigIntegerValue());
                var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,versionedCash(f,before,until,signed));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());
                assertTrue(ack.nativeOk());assertTrue(unavailable.reason().contains("wallet"));
                original(f,ack,negative,signed?STEP_V2:STEP);
                zero(f.actual.readPersonalCashReceived(before,until));zero(f.actual.readPersonalCashSignedScopeReceived(before,until));counts(f,1,1);
            }
        }
    }

    @Test void bothVersionsKeepFormatterCoercionsOutAndNullWalletUnknown() throws Exception {
        for(boolean signed:List.of(false,true))for(String branch:List.of("monthly-unavailable","wallet-null","wallet-missing","wallet-float")) {
            var input=signed?softwareSignedScope(new int[]{-2},new int[]{-2}):cpp();
            // Explicit software mutation; originals remain hash-pinned and unchanged.
            var token=NativeWire.object(NativeWire.parse(input.cash())).deepCopy();
            var raw=(ObjectNode)token.get("war_cash_current_resources");var ready=(ObjectNode)raw.get("readiness");
            for(String stem:List.of("gross_income","total_expenses","net_income")) {
                raw.putNull("player_monthly_"+stem).put("monthly_"+stem+"_unavailable_reason","synthetic_monthly_unavailable");
                ready.put("monthly_"+stem+"_ready",false);
            }
            boolean known=branch.equals("monthly-unavailable"),floating=branch.equals("wallet-float");
            if(floating)((ObjectNode)raw.get("current_treasury")).set("raw",StrictJson.parse("-1234567.0".getBytes(StandardCharsets.UTF_8)));
            else if(!known) {
                if(branch.equals("wallet-null"))raw.putNull("current_treasury");else raw.remove("current_treasury");
                raw.put("current_treasury_unavailable_reason","synthetic_wallet_unavailable").put("status","unavailable");
                ready.put("current_treasury_ready",false).put("same_frame_ready",false);
            }
            byte[] data=org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson.encode(token);
            if(floating)assertTrue(NativeWire.parse(data).get("war_cash_current_resources").get("current_treasury").get("raw").isFloatingPointNumber());
            try(var f=new Fixture(input,!signed,signed,data,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var read=versionedCash(f,before,until,signed);NativeActionPort.AckReceived ack;
                if(floating)ack=assertInstanceOf(NativeActionPort.AckReceived.class,
                        assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,read).original());
                else {
                    var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,read);ack=cash.original();
                    var wallet=cash.cash().metrics().currentTreasury();assertEquals(known,wallet.known());
                    if(known)assertEquals(new BigInteger("-1234567"),wallet.value().raw());
                    else assertEquals(branch.equals("wallet-null")?org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.Presence.NULL:
                            org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.Presence.MISSING,wallet.presence());
                    assertFalse(cash.cash().metrics().monthlyNetIncome().known());cash.requireOriginal(f.actual,until);
                }
                assertTrue(ack.nativeOk());original(f,ack,data,signed?STEP_V2:STEP);
                zero(f.actual.readPersonalCashReceived(before,until));zero(f.actual.readPersonalCashSignedScopeReceived(before,until));counts(f,1,1);
            }
        }
    }
    private static NativeGameTransport.PersonalCashRead versionedCash(Fixture f,NativeGameTransport.FullClockReceived before,
            Instant until,boolean signed)throws InterruptedException {
        return signed?f.actual.readPersonalCashSignedScopeReceived(before,until):f.actual.readPersonalCashReceived(before,until);
    }

    @Test void foreignFullExpiredReadAndMissingCapabilityPerformNoCashIo() throws Exception {
        try(var owner=new Fixture(true,null,false);var foreign=new Fixture(true,null,false)) {
            var before=owner.full();foreign.actual.awaitHello(before.validUntil());
            zero(foreign.actual.readPersonalCashReceived(before,owner.clock.instant().plusSeconds(30)));counts(owner,1,0);counts(foreign,0,0);
        }
        try(var f=new Fixture(true,null,false)) {
            var before=f.full();f.clock.set(before.validUntil());
            zero(f.actual.readPersonalCashReceived(before,f.clock.instant().plusSeconds(5)));counts(f,1,0);
        }
        try(var missing=new Fixture(false,null,false)) {
            var before=missing.full();zero(missing.actual.readPersonalCashReceived(before,missing.clock.instant().plusSeconds(30)));counts(missing,1,0);
        }
    }

    @Test void failedBackgroundPolicyDoesNotConsumeTheOriginalCashReadSource() throws Exception {
        try(var f=new Fixture(true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);f.source.backgroundReady=false;
            zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,0);
            f.source.backgroundReady=true;assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
        }
    }
    @Test void wrongActorRevisionAndScopeKeepTheActualPositiveAckInsteadOfZeroDispatch() throws Exception {
        for(String changed:List.of("actor","revision","scope")) {
            // Explicit negative software DATA derived from the retained actual C++ token, never a positive oracle.
            var token=NativeWire.object(NativeWire.parse(cashCpp())).deepCopy();var raw=(ObjectNode)token.get("war_cash_current_resources");
            if(changed.equals("actor")) {
                raw.put("played_character_id",2);
                for(String expense:List.of("current","all_raised")) {
                    var row=(ObjectNode)raw.path("military_expenses").get(expense);row.put("owner_character_id",2).put("resource_id","2");
                }
            } else if(changed.equals("revision"))raw.put("snapshot_revision",11);else raw.putArray("player_army_ids").add(7);
            byte[] negative=StrictJson.canonical(token);
            try(var f=new Fixture(true,negative,false)) {
                var before=f.full();var until=f.clock.instant().plusSeconds(30);
                var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashReceived(before,until));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());assertTrue(ack.nativeOk());
                original(f,ack,negative);if(changed.equals("scope"))assertTrue(unavailable.reason().contains("scope"));
                zero(f.actual.readPersonalCashReceived(before,until));counts(f,1,1);
                assertArrayEquals(negative,ack.originalResultToken().orElseThrow().bytes());
            }
        }
    }
    @Test void unknownKeepsItsIdenticalOriginalRequestAndCannotLeakToAnotherIssuerOrReplay() throws Exception {
        try(var f=new Fixture(true,null,true);var foreign=new Fixture(true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashReceived(before,until));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,unavailable.original());
            assertEquals(NativeWire.decodeExecuteRequest(f.source.cashRequests.getLast()).requestId(),unknown.requestId());
            assertArrayEquals(f.source.cashRequests.getLast(),unknown.originalRequestPacket());
            assertSame(unavailable,f.actual.readPersonalCashReceived(before,until));
            assertSame(unknown,assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.actual.readPersonalCashReceived(before,until)).original());
            zero(foreign.actual.readPersonalCashReceived(before,until));counts(f,1,1);counts(foreign,0,0);
        }
    }
    @Test void receivedCashCustodyRejectsForeignExtendedExpiredClosedAndSupersedingFull() throws Exception {
        for(String changed:List.of("foreign","extended","expired","closed","newer-full"))try(var f=new Fixture(true,null,false)) {
            var before=f.full();var until=f.clock.instant().plusSeconds(30);
            var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.actual.readPersonalCashReceived(before,until));
            if(changed.equals("foreign")) {
                try(var other=new Fixture(true,null,false)) {other.actual.awaitHello(until);assertThrows(IOException.class,()->cash.requireOriginal(other.actual,until));counts(other,0,0);}
            } else if(changed.equals("extended"))assertThrows(IOException.class,()->cash.requireOriginal(f.actual,until.plusNanos(1)));
            else {
                if(changed.equals("expired"))f.clock.set(cash.validUntil());
                else if(changed.equals("closed"))f.actual.close();
                else assertInstanceOf(NativeGameTransport.FullClockReceived.class,f.actual.readFullClockFrameReceived(until));
                assertThrows(IOException.class,()->cash.requireOriginal(f.actual,until));
            }
            counts(f,changed.equals("newer-full")?2:1,1);
        }
    }

    private static void zero(NativeGameTransport.PersonalCashRead read) {
        var absent=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,read);
        var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,absent.original());
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.proof().stage());assertEquals(0,zero.proof().requestBytesWritten());
    }
    private static void counts(Fixture f,int full,int cash) {
        assertEquals(full,f.source.fullQueries);assertEquals(cash,f.source.cashRequests.size());assertEquals(full+cash,f.source.writes);
    }
    private static void original(Fixture f,NativeActionPort.AckReceived ack,byte[] token) throws Exception { original(f,ack,token,STEP); }
    private static void original(Fixture f,NativeActionPort.AckReceived ack,byte[] token,String expectedStep) throws Exception {
        assertArrayEquals(token,ack.originalResultToken().orElseThrow().bytes());assertArrayEquals(f.source.cashAck,ack.originalPacket());
        assertArrayEquals(f.source.cashRequests.getLast(),ack.outbound().orElseThrow().originalPacket());
        var request=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());assertEquals(ack.requestId(),request.requestId());assertEquals(expectedStep,request.step());
        assertEquals(Optional.of(BigInteger.TEN),request.expectedRevision());assertEquals(Optional.of(BigInteger.TEN),request.expectedSnapshotRevision());
        assertEquals(0,NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).size());
        var custody=ack.custody().orElseThrow();custody.verify(ack);
        assertTrue(custody.writeEntered().order().compareTo(custody.writeCompleted().order())<0);
        assertTrue(custody.writeCompleted().order().compareTo(custody.responseReceived().order())<0);
    }

    private static byte[] cashCpp() throws Exception {
        String path=System.getProperty("xar.native.personalCash1210.cpp.path");
        String bytes=System.getProperty("xar.native.personalCash1210.cpp.bytes");
        String sha=System.getProperty("xar.native.personalCash1210.cpp.sha256");
        byte[] body;
        if(path==null&&bytes==null&&sha==null) {
            try(var input=NativePersonalCashPortTest.class.getResourceAsStream("/newnative/personal-cash1210/actual-cpp-cash-matching-full002.json")) {
                if(input==null)throw new IOException("exact C++ CASH resource missing");body=input.readNBytes(3068);
            }
        } else {
            path=required("xar.native.personalCash1210.cpp.path");
            assertEquals("3067",required("xar.native.personalCash1210.cpp.bytes"));assertEquals(CASH_SHA,required("xar.native.personalCash1210.cpp.sha256"));
            var file=Path.of(path);if(!file.isAbsolute())throw new IOException("absolute actual C++ CASH fixture required");
            try(var input=Files.newInputStream(file)){body=input.readNBytes(3068);}
        }
        exact(body,3067,CASH_SHA);
        // The producer file includes console CRLF outside its JSON value. Preserve all original value bytes;
        // use the protocol lexer to select that value, without JSON decoding/re-encoding it.
        var output=new ByteArrayOutputStream();String q=Character.toString(34);
        output.writeBytes(("{"+q+"result"+q+":").getBytes(StandardCharsets.UTF_8));output.writeBytes(body);output.write('}');
        return NativeWire.token(output.toByteArray(),"result");
    }
    private static String required(String name) throws IOException {
        String value=System.getProperty(name);if(value==null||value.isBlank())throw new IOException("required exact C++ fixture property: "+name);return value;
    }
    private static Cpp cpp() throws Exception {
        String override=System.getProperty("xar.native.personalCash1210.full.path");byte[] body;
        if(override!=null) {
            if(override.isBlank())throw new IOException("nonblank explicit C++ Full fixture path required");
            var file=Path.of(override);if(!file.isAbsolute())throw new IOException("absolute C++ Full fixture required");
            try(var input=Files.newInputStream(file)){body=input.readNBytes(1172);}
        } else try(var input=NativePersonalCashPortTest.class.getResourceAsStream("/newnative/personal-cash1210/full-snapshot-producer-002.json")) {
            if(input==null)throw new IOException("exact C++ Full002 resource missing");body=input.readNBytes(1172);
        }
        exact(body,1171,FULL_SHA);var snapshot=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(body)));
        return new Cpp(body,snapshot.state().value(),snapshot.snapshotId(),snapshot.revision(),cashCpp());
    }
    /** Derived software scope boundaries; never presented as new C++ or live Native observations. */
    private static Cpp softwareArmyScope(int[] fullIds,int[] cashIds) throws Exception {
        var base=cpp();var full=NativeWire.object(NativeWire.parse(base.full()));var state=NativeWire.object(full.get("state"));
        var rows=state.putArray("player_armies");
        for(int id:fullIds) {
            var row=rows.addObject().put("army_id",id).put("owner_character_id",1).put("current_province_id",1)
                    .put("move_target_observable",false).put("controllable",true).put("in_combat",false).put("retreating",false)
                    .put("army_state_code",1).put("army_state","regular").put("route_source_count",0).put("route_read_status","complete_empty");
            row.putNull("move_target_province_id");row.putArray("route_province_ids");
        }
        var cash=NativeWire.object(NativeWire.parse(base.cash()));var raw=NativeWire.object(cash.get("war_cash_current_resources"));
        var ids=raw.putArray("player_army_ids");for(int id:cashIds)ids.add(id);
        return new Cpp(StrictJson.canonical(full),StrictJson.canonical(state),base.snapshotId(),base.revision(),StrictJson.canonical(cash));
    }
    private static Cpp softwareSignedScope(int[] fullIds,int[] cashIds) throws Exception {
        var base=softwareArmyScope(fullIds,cashIds);var token=NativeWire.object(NativeWire.parse(base.cash()));
        token.put("step",STEP_V2);NativeWire.object(token.get("war_cash_current_resources")).put("schema","xar.ck3.war-cash-current-resources.v2");
        return new Cpp(base.full(),base.state(),base.snapshotId(),base.revision(),StrictJson.canonical(token));
    }
    private static void exact(byte[] body,int bytes,String sha) throws Exception {
        assertEquals(bytes,body.length);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
    }
    private static ObjectNode hello(boolean cash) { return hello(cash,false); }
    private static ObjectNode hello(boolean cash,boolean signed) {
        var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        var caps=hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);if(cash)caps.add(CAP);if(signed)caps.add(CAP_V2);return hello;
    }
    private static final class Fixture implements AutoCloseable {
        final MutableClock clock=new MutableClock(Instant.now());final Replay source;final NativeGameTransport actual;
        Fixture(boolean capability,byte[] negative,boolean drop) throws Exception { this(cpp(),capability,negative,drop); }
        Fixture(Cpp input,boolean capability,byte[] negative,boolean drop) throws Exception { this(input,capability,false,negative,drop); }
        Fixture(Cpp input,boolean capability,boolean signedCapability,byte[] negative,boolean drop) throws Exception {
            source=new Replay(input,hello(capability,signedCapability),negative,drop,clock);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"cash1210-software","cash1210-software",GAME,"cash1210-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
            actual=new NativeGameTransport(source,config,32,32,List.of(),clock,Duration.ofSeconds(60));
        }
        NativeGameTransport.FullClockReceived full() throws Exception {
            var received=assertInstanceOf(NativeGameTransport.FullClockReceived.class,actual.readFullClockFrameReceived(clock.instant().plusSeconds(60)));
            assertArrayEquals(source.cpp.state(),received.frame().state().bytes());var read=received.original();
            NativeFreshSnapshotPort.verifyOriginal(read.acknowledgement(),read.originalFrame(),read.snapshotReceived());return received;
        }
        @Override public void close() throws IOException {actual.close();}
    }
    private static final class MutableClock extends Clock {
        private Instant now;MutableClock(Instant now){this.now=now;}
        void set(Instant next){assertFalse(next.isBefore(now));now=next;}
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC software fixture only");return this;}
        @Override public Instant instant(){return now;}
    }

    private static final class Replay implements NativePacketPort {
        final Cpp cpp;final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<byte[]> cashRequests=new ArrayList<>();
        final byte[] negative;final boolean drop;final MutableClock clock;int fullQueries,writes;boolean closed,backgroundReady=true;byte[] cashAck;
        Replay(Cpp cpp,ObjectNode hello,byte[] negative,boolean drop,MutableClock clock) throws IOException {
            this.cpp=cpp;this.negative=negative==null?null:negative.clone();this.drop=drop;this.clock=clock;packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify() throws IOException {if(closed)throw new IOException("software source closed");}
        @Override public void verifyCoreControlWindowPolicy() throws IOException {verify();if(!backgroundReady)throw new IOException("software background policy failed");}
        private void check(Instant until) throws IOException {verify();if(!clock.instant().isBefore(until))throw new IOException("software deadline expired");}
        @Override public void awaitConnection(Instant until) throws IOException {check(until);}
        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);if(packets.isEmpty())throw new IOException("software response absent after query write");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] raw,Instant until) throws IOException {
            check(until);var request=NativeWire.decodeExecuteRequest(raw);writes++;
            if(request.step().equals(NativeFreshSnapshotPort.STEP)) {
                fullQueries++;assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
                var body=replaceOnce(new String(cpp.full(),StandardCharsets.UTF_8),field("read_request_id","full-producer-original"),field("read_request_id",request.requestId()));
                byte[] snapshot=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
                assertArrayEquals(cpp.state(),assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(snapshot)).state().value());
                // The independent READ ACK is a software protocol fixture, not a Native-produced ACK.
                var result=StrictJson.object().put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id",cpp.snapshotId()).put("revision",cpp.revision());
                packets.add(snapshot);packets.add(response(request.requestId(),StrictJson.canonical(result)));
            } else {
                assertTrue(request.step().equals(STEP)||request.step().equals(STEP_V2));assertEquals(Optional.of(cpp.revision()),request.expectedRevision());
                assertEquals(Optional.of(cpp.revision()),request.expectedSnapshotRevision());cashRequests.add(raw.clone());
                if(drop)return;
                byte[] token=negative==null?cpp.cash():negative;cashAck=response(request.requestId(),token);
                var ack=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(cashAck));
                assertArrayEquals(token,ack.result().token().orElseThrow().value());packets.add(cashAck.clone());
            }
        }
        private static byte[] response(String id,byte[] token) throws IOException {
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);envelope.putNull("result");
            String q=Character.toString(34);
            String body=replaceOnce(new String(StrictJson.canonical(envelope),StandardCharsets.UTF_8),q+"result"+q+":null",q+"result"+q+":"+new String(token,StandardCharsets.UTF_8));
            return NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
        }
        private static String field(String name,String value){String q=Character.toString(34);return q+name+q+":"+q+value+q;}
        private static String replaceOnce(String body,String token,String replacement){int i=body.indexOf(token);assertTrue(i>=0);assertEquals(i,body.lastIndexOf(token));return body.substring(0,i)+replacement+body.substring(i+token.length());}
        @Override public void close(){closed=true;}
    }
}
