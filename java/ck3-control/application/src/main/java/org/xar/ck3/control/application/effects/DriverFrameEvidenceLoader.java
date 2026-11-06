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
    // Diagnostics only. They never enable reuse, clear a cache, change a point, or supply authority.
    private static final java.util.concurrent.atomic.AtomicInteger REPLAY_DIAGNOSTIC_COMPLETIONS = new java.util.concurrent.atomic.AtomicInteger();
    private final ThreadLocal<long[]> replayDiagnostics = new ThreadLocal<>();
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
        checkedDriverOwner(Objects.requireNonNull(session));
        var before = driverSession.get();
        if (before != null && before != session)
            throw new IllegalStateException("different Sessions cannot share complete Driver DATA");
        if (before != null) { replayDiagnostic(3); return operation.read(archive); }
        replayDiagnostic(1);
        var freshEntries = new LinkedHashMap<byte[], DriverStateSnapshot.Complete>(4, 0.75f, true);
        long[] freshBytes = new long[1];
        var freshReplays = new LinkedHashMap<Object[], DriverObservationAssembler.Complete>(16, 0.75f, true);
        try {
            driverSession.set(session); completeDrivers.set(freshEntries); completeOriginalBytes.set(freshBytes);
            completeReplays.set(freshReplays); replayOriginalBytes.set(new long[1]);
            return operation.read(archive);
        } finally {
            replayDiagnostic(2);
            freshReplays.clear(); completeReplays.remove(); replayOriginalBytes.remove(); replayPoint.remove();
            freshEntries.clear(); completeDrivers.remove(); completeOriginalBytes.remove(); driverSession.remove();
        }
    }

    /** No Complete may be supplied by a caller: insertion always follows this exact strict decoder. */
    public DriverStateSnapshot.Complete decodeCompleteDriverBytes(byte[] original) {
        var entries = completeDrivers.get();
        if (!scopedDriverDecode || entries == null) return DriverStateSnapshot.decodeComplete(original);
        checkedDriverOwner(driverSession.get());
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
        replayDiagnostic(4);
        var entries = completeReplays.get();
        if (!scopedDriverDecode || entries == null || framedNative == null) {
            replayDiagnostic(5);
            return DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(manifestReference, manifest,
                    fullDriver, framedNative, nativeReference, this);
        }
        replayDiagnostic(6);
        try {
            // The captured Reader reaches this at the original native-copy point, after its callbacks and bounds check.
            byte[] nativeBytes = framedNative.clone();
            Object[] before = beginReplayPoint();
            byte[] manifestBytes = null, driverBytes = null;
            Object[] matching = null;
            boolean referenceSeen = false, nativeSeen = false, manifestSeen = false;
            for (Object[] key : entries.keySet()) {
                if (!Objects.equals(key[0], manifestReference) || !Objects.equals(key[1], nativeReference)) continue;
                referenceSeen = true;
                if (!Arrays.equals((byte[])key[4], nativeBytes)) continue;
                nativeSeen = true;
                // Only a previously accepted native/manifest can reach the Driver-byte comparison early.
                if (manifestBytes == null) manifestBytes = manifest.bytes();
                if (!Arrays.equals((byte[])key[2], manifestBytes)) continue;
                manifestSeen = true;
                if (driverBytes == null) driverBytes = fullDriver.bytes();
                if (Arrays.equals((byte[])key[3], driverBytes)) { matching = key; break; }
            }
            if (matching == null) replayDiagnostic(entries.isEmpty() ? 7 : !referenceSeen ? 8 : !nativeSeen ? 9 : !manifestSeen ? 10 : 11);
            else replayDiagnostic(12);
            if (matching != null) {
                RootGuardChecks.exact(manifestReference, manifestBytes);
                RootGuardChecks.exact(nativeReference, nativeBytes);
                RootGuardChecks.exact(DriverObservationEvidenceReader.currentDriverReference(manifestReference, manifest), driverBytes);
                checkedDriverOwner(driverSession.get());
                if (sameReplayPoint(before)) { replayDiagnostic(13); return entries.get(matching); }
            }
            // Preserve strict miss inputs and validation order; never recanonicalize or supply a caller's result.
            replayDiagnostic(14);
            var result = DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(manifestReference,
                    manifest, fullDriver, nativeBytes, nativeReference, this);
            if (!(result instanceof DriverObservationAssembler.Complete)) replayDiagnostic(15);
            if (result instanceof DriverObservationAssembler.Complete complete && sameReplayPoint(before)) {
                if (manifestBytes == null) manifestBytes = manifest.bytes();
                if (driverBytes == null) driverBytes = fullDriver.bytes();
                long bytes = (long)manifestBytes.length + driverBytes.length + nativeBytes.length;
                if (bytes > MAX_REPLAY_ORIGINAL_BYTES) { replayDiagnostic(17); return result; }
                long[] retained = replayOriginalBytes.get();
                while (!entries.isEmpty() && (entries.size() >= MAX_REPLAY_ENTRIES
                        || retained[0] + bytes > MAX_REPLAY_ORIGINAL_BYTES)) {
                    if (entries.size() >= MAX_REPLAY_ENTRIES) replayDiagnostic(18);
                    if (retained[0] + bytes > MAX_REPLAY_ORIGINAL_BYTES) replayDiagnostic(19);
                    var oldest = entries.entrySet().iterator(); var removed = oldest.next();
                    Object[] key = removed.getKey();
                    retained[0] -= (long)((byte[])key[2]).length + ((byte[])key[3]).length + ((byte[])key[4]).length;
                    oldest.remove();
                }
                entries.put(new Object[]{manifestReference, nativeReference, manifestBytes, driverBytes, nativeBytes}, complete);
                retained[0] += bytes; replayDiagnostic(16);
            }
            return result;
        } catch (RuntimeException | Error failure) {
            replayDiagnostic(27); disableReplayPoint(); throw failure;
        }
    }
    /** Capture the actual point before replay; public matching metadata alone never grants DATA reuse. */
    private Object[] beginReplayPoint() {
        Object[] point = replayPoint.get();
        if (point != null && point.length == 0) { replayDiagnostic(20); return null; }
        try {
            var same = driverSession.get(); var head = same.head(); var persisted = same.persistedHead();
            if (point == null) {
                point = new Object[]{head, persisted}; replayPoint.set(point); return point;
            }
            if (point[0] == head && point[1].equals(persisted)) return point;
            if (point[0] != head) replayHeadDifference(point, head);
            if (!point[1].equals(persisted)) replayDiagnostic(22);
        } catch (IOException unavailable) {
            replayDiagnostic(24);
            // Only reuse eligibility failed; retain the original strict replay and its own error semantics.
        }
        disableReplayPoint(); return null;
    }
    private boolean sameReplayPoint(Object[] before) {
        if (before == null || replayPoint.get() != before) return false;
        try {
            var same = driverSession.get();
            var head = same.head();
            if (before[0] == head) {
                if (before[1].equals(same.persistedHead())) return true;
                replayDiagnostic(22);
            } else replayHeadDifference(before, head);
        } catch (IOException unavailable) {
            replayDiagnostic(24);
            // A failed freshness probe cannot mint a new point or replace strict DATA validation.
        }
        replayDiagnostic(23); disableReplayPoint(); return false;
    }
    private void disableReplayPoint() {
        Object[] point = replayPoint.get();
        if (point == null || point.length != 0) replayDiagnostic(28);
        completeReplays.get().clear(); replayOriginalBytes.get()[0] = 0; replayPoint.set(new Object[0]);
    }
    /** Begin only at an outer planning caller; at most four normally completed rounds per Loader generation. */
    public boolean beginReplayDiagnostics() {
        if (replayDiagnostics.get() != null || REPLAY_DIAGNOSTIC_COMPLETIONS.get() >= 4) return false;
        long[] counts = new long[32]; counts[0] = scopedDriverDecode ? 1 : 0; counts[31] = -1;
        replayDiagnostics.set(counts); return true;
    }
    /** Called after the caller has released its own writer scope; returns DATA only and always clears diagnostics. */
    public long[] finishReplayDiagnostics(boolean completed) {
        long[] counts = replayDiagnostics.get();
        try {
            if (counts == null || !completed) return null;
            int before;
            do { before = REPLAY_DIAGNOSTIC_COMPLETIONS.get(); if (before >= 4) return null; }
            while (!REPLAY_DIAGNOSTIC_COMPLETIONS.compareAndSet(before, before + 1));
            return counts.clone();
        } finally { replayDiagnostics.remove(); }
    }
    private void replayDiagnostic(int slot) {
        try { long[] counts = replayDiagnostics.get(); if (counts != null && counts[slot] < Long.MAX_VALUE) counts[slot]++; }
        catch (Throwable diagnosticFailure) { }
    }
    private void checkedDriverOwner(ContinuityStorePort.Session session) {
        replayDiagnostic(25);
        try { driverOwnerGate.accept(session); }
        catch (RuntimeException | Error failure) { replayDiagnostic(26); throw failure; }
    }
    /** Pure metadata comparison only, after the original object-identity refusal. No file or permission read. */
    private void replayHeadDifference(Object[] point, org.xar.ck3.control.continuity.writer.WriterContracts.Head head) {
        replayDiagnostic(21);
        try {
            if (replayDiagnostics.get() == null) return;
            var previous = (org.xar.ck3.control.continuity.writer.WriterContracts.Head)point[0];
            replayDiagnostic(previous.state().sequence() == head.state().sequence() && previous.digest().equals(head.digest()) ? 29 : 30);
        } catch (Throwable diagnosticFailure) { }
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
