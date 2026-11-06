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
    // Pure historical replay DATA only; original archive reads remain in the caller.
    private static final int MAX_REPLAY_ENTRIES = 16;
    private static final long MAX_REPLAY_ORIGINAL_BYTES = 64L * 1024 * 1024;
    private final ThreadLocal<LinkedHashMap<Object[], DriverObservationAssembler.Complete>> completeReplays = new ThreadLocal<>();
    private final ThreadLocal<long[]> replayOriginalBytes = new ThreadLocal<>();
    private final ThreadLocal<Object[]> replayPoint = new ThreadLocal<>();
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
        var freshReplays = new LinkedHashMap<Object[], DriverObservationAssembler.Complete>(16, 0.75f, true);
        try {
            driverSession.set(session); completeDrivers.set(freshEntries); completeOriginalBytes.set(freshBytes);
            completeReplays.set(freshReplays); replayOriginalBytes.set(new long[1]);
            return operation.read(archive);
        } finally {
            freshReplays.clear(); completeReplays.remove(); replayOriginalBytes.remove(); replayPoint.remove();
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
    /** Internally rebuilt DATA only: callers cannot provide a cached result or an already checked projection. */
    public DriverObservationAssembler.Result replayCompleteOriginals(org.xar.ck3.control.contracts.ExactRef manifestReference,
            org.xar.ck3.control.application.action.RawJson manifest, org.xar.ck3.control.application.action.RawJson fullDriver,
            byte[] framedNative, org.xar.ck3.control.contracts.ExactRef nativeReference) {
        var entries = completeReplays.get();
        if (!scopedDriverDecode || entries == null || framedNative == null)
            return DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(manifestReference, manifest,
                    fullDriver, framedNative, nativeReference, this);
        try {
            // The captured Reader reaches this at the original native-copy point, after its callbacks and bounds check.
            byte[] nativeBytes = framedNative.clone();
            Object[] before = beginReplayPoint();
            byte[] manifestBytes = null, driverBytes = null;
            Object[] matching = null;
            for (Object[] key : entries.keySet()) {
                if (!Objects.equals(key[0], manifestReference) || !Objects.equals(key[1], nativeReference)
                        || !Arrays.equals((byte[])key[4], nativeBytes)) continue;
                // Only a previously accepted native/manifest can reach the Driver-byte comparison early.
                if (manifestBytes == null) manifestBytes = manifest.bytes();
                if (!Arrays.equals((byte[])key[2], manifestBytes)) continue;
                if (driverBytes == null) driverBytes = fullDriver.bytes();
                if (Arrays.equals((byte[])key[3], driverBytes)) { matching = key; break; }
            }
            if (matching != null) {
                RootGuardChecks.exact(manifestReference, manifestBytes);
                RootGuardChecks.exact(nativeReference, nativeBytes);
                RootGuardChecks.exact(DriverObservationEvidenceReader.currentDriverReference(manifestReference, manifest), driverBytes);
                driverOwnerGate.accept(driverSession.get());
                if (sameReplayPoint(before)) return entries.get(matching);
            }
            // Preserve strict miss inputs and validation order; never recanonicalize or supply a caller's result.
            var result = DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(manifestReference,
                    manifest, fullDriver, nativeBytes, nativeReference, this);
            if (result instanceof DriverObservationAssembler.Complete complete && sameReplayPoint(before)) {
                if (manifestBytes == null) manifestBytes = manifest.bytes();
                if (driverBytes == null) driverBytes = fullDriver.bytes();
                long bytes = (long)manifestBytes.length + driverBytes.length + nativeBytes.length;
                if (bytes > MAX_REPLAY_ORIGINAL_BYTES) return result;
                long[] retained = replayOriginalBytes.get();
                while (!entries.isEmpty() && (entries.size() >= MAX_REPLAY_ENTRIES
                        || retained[0] + bytes > MAX_REPLAY_ORIGINAL_BYTES)) {
                    var oldest = entries.entrySet().iterator(); var removed = oldest.next();
                    Object[] key = removed.getKey();
                    retained[0] -= (long)((byte[])key[2]).length + ((byte[])key[3]).length + ((byte[])key[4]).length;
                    oldest.remove();
                }
                entries.put(new Object[]{manifestReference, nativeReference, manifestBytes, driverBytes, nativeBytes}, complete);
                retained[0] += bytes;
            }
            return result;
        } catch (RuntimeException | Error failure) {
            disableReplayPoint(); throw failure;
        }
    }
    /** Capture the actual point before replay; public matching metadata alone never grants DATA reuse. */
    private Object[] beginReplayPoint() {
        Object[] point = replayPoint.get();
        if (point != null && point.length == 0) return null;
        try {
            var same = driverSession.get(); var head = same.head(); var persisted = same.persistedHead();
            if (point == null) {
                point = new Object[]{head, persisted}; replayPoint.set(point); return point;
            }
            if (point[0] == head && point[1].equals(persisted)) return point;
        } catch (IOException unavailable) {
            // Only reuse eligibility failed; retain the original strict replay and its own error semantics.
        }
        disableReplayPoint(); return null;
    }
    private boolean sameReplayPoint(Object[] before) {
        if (before == null || replayPoint.get() != before) return false;
        try {
            var same = driverSession.get();
            if (before[0] == same.head() && before[1].equals(same.persistedHead())) return true;
        } catch (IOException unavailable) {
            // A failed freshness probe cannot mint a new point or replace strict DATA validation.
        }
        disableReplayPoint(); return false;
    }
    private void disableReplayPoint() {
        completeReplays.get().clear(); replayOriginalBytes.get()[0] = 0; replayPoint.set(new Object[0]);
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
