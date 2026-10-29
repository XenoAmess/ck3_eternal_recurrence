package org.xar.ck3.control.wave2.finance.giftpendingroute;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Read;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Recovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Baseline;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ResolvedOutcome;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.ColdResult;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.ColdUnresolved;

final class ColdUnresolvedSerializationTest {
    @Test void actualExceptionSerializationKeepsErrorMaterialAndUnknownPendingLedger() throws Exception {
        ColdResult material = material(); ColdUnresolved original = new ColdUnresolved(material);
        original.addSuppressed(new IllegalStateException("original independent-read diagnostic"));
        ColdUnresolved restored = roundtrip(original);
        assertEquals(original.getMessage(), restored.getMessage());
        assertEquals(original.getSuppressed()[0].getMessage(), restored.getSuppressed()[0].getMessage());
        assertEquals(material.originalResult().json(), restored.result().originalResult().json());
        assertEquals(material.recovery(), restored.result().recovery());
        assertEquals(material.classification(), restored.result().classification());
        assertArrayEquals(GiftPendingCodec.encodeLedger(material.ledger()), GiftPendingCodec.encodeLedger(restored.result().ledger()));
        assertEquals(GiftPendingReadRouteCodec.coldEvidence(material), GiftPendingReadRouteCodec.coldEvidence(restored.result()));
        assertEquals(GiftColdRecovery.Presence.NULL, restored.result().recovery().independentFactionStorageLookupComplete().presence());
        assertEquals(GiftColdRecovery.Presence.MISSING, restored.result().recovery().independentRecipientLookupComplete().presence());
        assertTrue(restored.result().ledger().blocksNewSubmission());
        assertEquals(PendingStatus.RESTORE_REQUERY_REQUIRED, restored.result().ledger().pending().orElseThrow().status());
        assertEquals(StrictJson.UINT64_MAX, restored.result().ledger().pending().orElseThrow().baseline().snapshotRevision());
        assertFalse(restored.result().classification().originalRequestReplayAllowed());
        assertFalse(restored.result().classification().actionRetryAllowed());
        assertTrue(StrictJson.parse(restored.result().originalResult().json().getBytes(StandardCharsets.UTF_8)).path("native").path("extension").isFloatingPointNumber());
        assertTrue(StrictJson.parse(GiftPendingCodec.encodeLedger(restored.result().ledger())).path("pending").path("ack").path("extension").isFloatingPointNumber());
    }

    @Test void unresolvedExceptionCannotCarryAResolvedClassification() {
        ColdResult material = material();
        ColdResult resolved = new ColdResult(material.originalResult(), material.recovery(),
                new GiftColdRecovery.Unchanged("gift-serial", "R744", BigInteger.valueOf(23456)), material.ledger());
        assertThrows(IllegalArgumentException.class, () -> new ColdUnresolved(resolved));
    }

    private static ColdUnresolved roundtrip(ColdUnresolved value) throws IOException, ClassNotFoundException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream output = new ObjectOutputStream(bytes)) { output.writeObject(value); }
        try (ObjectInputStream input = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray()))) {
            Object restored = input.readObject();
            if (!(restored instanceof ColdUnresolved result)) throw new IOException("cold unresolved exception required");
            return result;
        }
    }

    private static ColdResult material() {
        Baseline baseline = new Baseline(BigInteger.valueOf(771), BigInteger.valueOf(33011), StrictJson.UINT64_MAX,
                StrictJson.UINT64_MAX, BigInteger.valueOf(53144328), BigInteger.valueOf(32904), BigInteger.valueOf(100000000),
                BigInteger.valueOf(-12), BigInteger.valueOf(1000000), BigInteger.valueOf(500000), List.of(BigInteger.valueOf(33011)),
                BigInteger.valueOf(5000000), BigInteger.valueOf(25));
        PendingAction pending = new PendingAction("gift-serial", "serial-fixture", "R742",
                new ProcessIdentity(BigInteger.valueOf(12345), "20260916120000.000000+000"), baseline,
                BigInteger.valueOf(10000000), "a".repeat(64), PendingStatus.RESTORE_REQUERY_REQUIRED,
                Optional.of(new ObjectEvidence("{\"extension\":0.0,\"ok\":true}")));
        Ledger ledger = new Ledger(Optional.of(pending), Map.of("old-identity", ResolvedOutcome.UNCHANGED));
        Recovery recovery = new Recovery(Read.of(BigInteger.ONE), Read.of("independent_read_complete"), Read.of(true),
                Read.of(false), Read.of(true), Read.of("R744"), Read.of(BigInteger.valueOf(23456)),
                Read.of("20261019051054.525693+000"), Read.of("serial-fixture"), Read.of(true), Read.of(true),
                Read.nil(), Read.missing(), Read.of(false), Read.of(false), Read.nil(), Read.missing());
        return new ColdResult(new ObjectEvidence("{ \"native\":{\"extension\":0.0,\"failure_flags\":1},\"status\":\"independent_read_complete\" }"),
                recovery, new GiftColdRecovery.Unresolved(GiftColdRecovery.Reason.INDEPENDENT_POST_OBSERVATION_MISSING), ledger);
    }
}
