package org.xar.ck3.control.wave2.finance.giftpending;

/** Raw existing producer input to the actual typed reducer and canonical candidate. This never writes. */
public final class GiftPendingTransitionAdapter {
    private GiftPendingTransitionAdapter() { }
    public static byte[] begin(byte[] originalLedger, byte[] originalBeginRequest) {
        return GiftPendingCodec.encodeLedger(GiftPendingReducer.begin(GiftPendingCodec.decodeLedger(originalLedger),
                GiftPendingCodec.decodeBegin(originalBeginRequest)));
    }
    public static byte[] markAck(byte[] originalLedger, String requestId, byte[] originalAck) {
        return GiftPendingCodec.encodeLedger(GiftPendingReducer.markAck(GiftPendingCodec.decodeLedger(originalLedger),
                requestId, GiftPendingCodec.decodeAck(originalAck)));
    }
    public static byte[] markRestore(byte[] originalLedger, String requestId) {
        return GiftPendingCodec.encodeLedger(GiftPendingReducer.markRestore(GiftPendingCodec.decodeLedger(originalLedger), requestId));
    }
    public static byte[] complete(byte[] originalLedger, String requestId, byte[] originalReceipt) {
        return GiftPendingCodec.encodeLedger(GiftPendingReducer.complete(GiftPendingCodec.decodeLedger(originalLedger),
                requestId, GiftPendingCodec.decodeReceipt(originalReceipt)));
    }
    public static GiftColdRecovery.Resolution resolveCold(byte[] originalLedger, String requestId, byte[] originalRecovery) {
        return GiftColdRecovery.resolve(GiftPendingCodec.decodeLedger(originalLedger), requestId,
                GiftColdRecoveryCodec.decodeRecovery(originalRecovery));
    }
}
