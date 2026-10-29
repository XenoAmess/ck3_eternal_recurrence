package org.xar.ck3.control.replenishment;

/** In-process host port. It performs no network, native, file, or ledger operations. */
public final class ReplenishmentFacade {
    public byte[] projectObserved(byte[] input) {
        return ReplenishmentCodec.encodeProjection(ReplenishmentPolicy.projectObservedReplenishmentV1(
                ReplenishmentCodec.decodeObservedInput(input)));
    }

    public byte[] calculateChunk(byte[] input) {
        ReplenishmentModel.ChunkInput value = ReplenishmentCodec.decodeChunkInput(input);
        return ReplenishmentCodec.encodeCalculation(ReplenishmentPolicy.sameInputChunkQ(
                value.maximumSoldiers(), value.effectiveCurrentSoldiers(), value.preparedFractionRaw(),
                value.nativeChunkCanReplenish()));
    }
}
