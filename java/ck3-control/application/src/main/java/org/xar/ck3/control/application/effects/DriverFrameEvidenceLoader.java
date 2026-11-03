package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Objects;
import java.util.function.Consumer;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure replay of the actual native packet plus the complete original Driver, using the sole production assembler. */
public final class DriverFrameEvidenceLoader implements NativeEffectEvidence.FrameLoader {
    private final DriverObservationAssembler assembler;
    private final boolean scopedDriverDecode;
    // Bounds on retained original bytes and decoded entries, not a whole-JVM/RSS budget.
    private static final int MAX_COMPLETE_ENTRIES = 4;
    private static final long MAX_COMPLETE_ORIGINAL_BYTES = 64L * 1024 * 1024;
    private final ThreadLocal<ContinuityStorePort.Session> driverSession = new ThreadLocal<>();
    private final ThreadLocal<LinkedHashMap<byte[], DriverStateSnapshot.Complete>> completeDrivers = new ThreadLocal<>();
    private final ThreadLocal<long[]> completeOriginalBytes = new ThreadLocal<>();
    private volatile Object driverOwner;
    private volatile Consumer<ContinuityStorePort.Session> driverOwnerGate;

    /** Legacy assembly remains a strict decoder and never activates DATA reuse. */
    public DriverFrameEvidenceLoader(DriverObservationAssembler sameProductionAssembler) { this(sameProductionAssembler, false); }
    public DriverFrameEvidenceLoader(DriverObservationAssembler sameProductionAssembler, boolean scopedDriverDecode) {
        assembler = Objects.requireNonNull(sameProductionAssembler); this.scopedDriverDecode = scopedDriverDecode;
    }

    /** One actual archive owner supplies only a Session eligibility check, never a decoded value. */
    public synchronized void bindDriverDecodeOwner(Object actualOwner, Consumer<ContinuityStorePort.Session> ownerGate) {
        if (!scopedDriverDecode || driverOwner != null)
            throw new IllegalStateException("scoped Driver decoder requires one explicit owner binding");
        Objects.requireNonNull(actualOwner); Objects.requireNonNull(ownerGate);
        driverOwnerGate = ownerGate; driverOwner = actualOwner;
    }

    /** The archive invokes this only after installing its actual same-thread Session scope. */
    public <T> T inCompleteDriverDecodeScope(Object actualOwner, ContinuityStorePort.Session session,
            ActionPorts.OutcomeArchive archive, ActionPorts.CheckedArchiveRead<T> operation) throws IOException {
        Objects.requireNonNull(operation); Objects.requireNonNull(archive);
        if (!scopedDriverDecode || actualOwner != driverOwner || driverOwnerGate == null)
            throw new IllegalStateException("actual bound Driver decoder owner required");
        driverOwnerGate.accept(Objects.requireNonNull(session));
        var before = driverSession.get();
        if (before != null && before != session)
            throw new IllegalStateException("different Sessions cannot share complete Driver DATA");
        if (before != null) return operation.read(archive);
        var freshEntries = new LinkedHashMap<byte[], DriverStateSnapshot.Complete>(4, 0.75f, true);
        long[] freshBytes = new long[1];
        try {
            driverSession.set(session); completeDrivers.set(freshEntries); completeOriginalBytes.set(freshBytes);
            return operation.read(archive);
        } finally {
            freshEntries.clear(); completeDrivers.remove(); completeOriginalBytes.remove(); driverSession.remove();
        }
    }

    /** No Complete may be supplied by a caller: insertion always follows this exact strict decoder. */
    public DriverStateSnapshot.Complete decodeCompleteDriverBytes(byte[] original) {
        var entries = completeDrivers.get();
        if (!scopedDriverDecode || entries == null) return DriverStateSnapshot.decodeComplete(original);
        driverOwnerGate.accept(driverSession.get());
        try {
            // Public entry never trusts a caller-owned array to stay unchanged during decode/keying.
            byte[] privateOriginal = Objects.requireNonNull(original).clone();
            byte[] matching = null;
            for (byte[] key : entries.keySet()) if (Arrays.equals(key, privateOriginal)) { matching = key; break; }
            if (matching != null) return entries.get(matching);
            DriverStateSnapshot.Complete decoded = DriverStateSnapshot.decodeComplete(privateOriginal);
            if (privateOriginal.length > MAX_COMPLETE_ORIGINAL_BYTES) return decoded;
            long[] retained = completeOriginalBytes.get();
            while (!entries.isEmpty() && (entries.size() >= MAX_COMPLETE_ENTRIES
                    || retained[0] + privateOriginal.length > MAX_COMPLETE_ORIGINAL_BYTES)) {
                var oldest = entries.entrySet().iterator(); var removed = oldest.next();
                retained[0] -= removed.getKey().length; oldest.remove();
            }
            // The map never exposes or changes any private pre-decode cloned byte-array key.
            entries.put(privateOriginal, decoded); retained[0] += privateOriginal.length;
            return decoded;
        } catch (RuntimeException | Error failure) {
            entries.clear(); completeOriginalBytes.get()[0] = 0; throw failure;
        }
    }
    @Override public DriverObservationAssembler.Complete load(NativeEffectEvidence.FrameBasis basis, ActionPorts.OutcomeArchive archive) {
        var full = loadFull(basis, archive);
        var result = assembler.assemble(full.actual(), full.facts(), full.originalEvidence());
        StrictJson.require(result instanceof DriverObservationAssembler.Complete, "archived native/complete Driver no longer rebuild an accepted original semantic frame");
        return (DriverObservationAssembler.Complete) result;
    }
    /** Complete retained native/Driver DATA, including unavailable/dead player scopes. No ordinary identity is invented. */
    public DriverObservationAssembler.FullSnapshot loadFull(NativeEffectEvidence.FrameBasis basis, ActionPorts.OutcomeArchive archive) {
        var manifest = archive.loadFullMaterial(basis.driverFacts()); RootGuardChecks.exact(basis.driverFacts(), manifest.bytes());
        byte[] nativePacket = archive.loadNativeFrame(basis.nativeFrame()); RootGuardChecks.exact(basis.nativeFrame(), nativePacket);
        StrictJson.require(nativePacket.length >= 5
                && nativePacket.length <= org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES + 4,
                "bounded archived original native frame required");
        nativePacket = nativePacket.clone();
        var driverReference = DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(), manifest);
        var driver = archive.loadFullMaterial(driverReference); RootGuardChecks.exact(driverReference, driver.bytes());
        if (scopedDriverDecode)
            return DriverObservationEvidenceReader.projectOriginalsWithScopedDriverDecode(basis.driverFacts(), manifest,
                    driver, nativePacket, basis.nativeFrame(), assembler, this);
        return DriverObservationEvidenceReader.projectOriginals(basis.driverFacts(), manifest, driver, nativePacket,
                basis.nativeFrame(), assembler);
    }
}
