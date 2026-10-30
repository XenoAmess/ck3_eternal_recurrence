package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.io.UncheckedIOException;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionRecordCodec;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/**
 * Test helper for recovery DATA only. Decodes existing immutable artifacts using
 * NativeArchiveDataCodec, ActionRecordCodec, ActionReceiptCodec, RawJson.
 * No live Native transport, no writer creation, no current source qualification.
 */
public final class PortableRecoveryDataArchive {

    private final OrdinaryCycleTransitions.SessionAuthority authority;
    private final NativeArchiveDataCodec codec;
    private final Map<ExactRef, byte[]> exactBytes = new HashMap<>();
    private final Map<ExactRef, ActionReceipt> receiptCache = new HashMap<>();
    private final Map<ExactRef, ActionRecord> recordCache = new HashMap<>();
    private final Map<ExactRef, PlanningReadReceipt> readCache = new HashMap<>();
    private final Map<ExactRef, NativeRequest> requestCache = new HashMap<>();
    private final Map<ExactRef, NativeActionPort.DispatchOutcome> dispatchCache = new HashMap<>();
    private final Map<ExactRef, RawJson> materialCache = new HashMap<>();
    private final Map<ActionReceipt, ExactRef> receiptRefs = new HashMap<>();
    private final Map<ActionRecord, ExactRef> recordRefs = new HashMap<>();
    private final Map<PlanningReadReceipt, ExactRef> readRefs = new HashMap<>();
    private final Map<NativeRequest, ExactRef> requestRefs = new HashMap<>();
    private final Map<NativeActionPort.DispatchOutcome, ExactRef> dispatchRefs = new HashMap<>();
    private final Map<RawJson, ExactRef> materialRefs = new HashMap<>();

    public PortableRecoveryDataArchive(OrdinaryCycleTransitions.SessionAuthority authority) {
        this.authority = Objects.requireNonNull(authority);
        this.codec = new NativeArchiveDataCodec(this::readBytes);
    }

    public ActionPorts.OutcomeArchive proxy() {
        return new OutcomeArchiveImpl(this);
    }

    public static byte[] readExact(ExactRef original, int maximumBytes) throws IOException {
        Objects.requireNonNull(original);
        if (maximumBytes < 1 || maximumBytes > WriterContracts.MAX_PIN_BYTES
                || original.bytes() < 0 || original.bytes() > maximumBytes) {
            throw new IOException("explicit finite original DATA bound required");
        }
        byte[] bytes = java.nio.file.Files.readAllBytes(java.nio.file.Path.of(original.path()));
        if (bytes.length != original.bytes() || bytes.length > maximumBytes) {
            throw new IOException("retained DATA length differs from original ref");
        }
        try {
            String digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
            if (!digest.equals(original.sha256())) {
                throw new IOException("retained DATA hash differs from original ref");
            }
        } catch (java.security.NoSuchAlgorithmException impossible) {
            throw new IllegalStateException(impossible);
        }
        return bytes;
    }

    private byte[] readBytes(ExactRef original, int maximumBytes) throws IOException {
        Objects.requireNonNull(original);
        if (maximumBytes < 1 || maximumBytes > WriterContracts.MAX_PIN_BYTES
                || original.bytes() < 0 || original.bytes() > maximumBytes) {
            throw new IOException("explicit finite original DATA bound required");
        }
        byte[] bytes = exactBytes.get(original);
        if (bytes == null) {
            bytes = readExact(original, maximumBytes);
            exactBytes.put(original, bytes);
        }
        return bytes.clone();
    }

    private RawJson token(ExactRef original) throws IOException {
        return new RawJson(readBytes(original, RawJson.MAXIMUM_BYTES));
    }

    private ActionReceipt loadReceipt(ExactRef original) throws IOException {
        if (receiptCache.containsKey(original)) return receiptCache.get(original);
        byte[] bytes = readBytes(original, StrictJson.EXPLICIT_MAX_BYTES);
        ActionReceipt receipt = ActionReceiptCodec.decodeReceipt(bytes, this.proxy());
        receiptCache.put(original, receipt);
        receiptRefs.put(receipt, original);
        return receipt;
    }

    private ActionRecord loadRecord(ExactRef original) throws IOException {
        if (recordCache.containsKey(original)) return recordCache.get(original);
        byte[] bytes = readBytes(original, StrictJson.EXPLICIT_MAX_BYTES);
        ActionRecord record = ActionRecordCodec.decode(bytes, this.proxy());
        recordCache.put(original, record);
        recordRefs.put(record, original);
        return record;
    }

    private PlanningReadReceipt loadRead(ExactRef original) throws IOException {
        if (readCache.containsKey(original)) return readCache.get(original);
        PlanningReadReceipt read = codec.decodeRead(original);
        var metadata = StrictJson.parse(readBytes(original, StrictJson.EXPLICIT_MAX_BYTES));
        ExactRef dispatchRef = ExactRef.fromJson(metadata.get("original_ref"));
        dispatchCache.put(dispatchRef, read.original());
        dispatchRefs.put(read.original(), dispatchRef);
        readCache.put(original, read);
        readRefs.put(read, original);
        return read;
    }

    private NativeRequest loadRequest(ExactRef original) throws IOException {
        if (requestCache.containsKey(original)) return requestCache.get(original);
        NativeRequest request = codec.decodePreparedRequestData(original);
        requestCache.put(original, request);
        requestRefs.put(request, original);
        return request;
    }

    private NativeActionPort.DispatchOutcome loadDispatch(ExactRef original) throws IOException {
        if (dispatchCache.containsKey(original)) return dispatchCache.get(original);
        NativeActionPort.DispatchOutcome dispatch = codec.decodeDispatchData(original);
        dispatchCache.put(original, dispatch);
        dispatchRefs.put(dispatch, original);
        return dispatch;
    }

    private RawJson loadMaterial(ExactRef original) throws IOException {
        readBytes(original, RawJson.MAXIMUM_BYTES);
        if (materialCache.containsKey(original)) return materialCache.get(original);
        RawJson material = token(original);
        materialCache.put(original, material);
        materialRefs.put(material, original);
        return material;
    }

    private RawJson loadFullMaterial(ExactRef original) throws IOException {
        byte[] bytes = readBytes(original, WriterContracts.MAX_PIN_BYTES);
        if (materialCache.containsKey(original)) return materialCache.get(original);
        RawJson material = RawJson.fullMaterial(bytes);
        materialCache.put(original, material);
        materialRefs.put(material, original);
        return material;
    }

    @FunctionalInterface private interface Io<T> { T get() throws IOException; }
    private static <T> T io(Io<T> work) {
        try { return work.get(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }

    private ExactRef referenceOfReceipt(ActionReceipt receipt) {
        return Objects.requireNonNull(receiptRefs.get(receipt), "original object was not previously decoded");
    }

    private ExactRef referenceOfRecord(ActionRecord record) {
        return Objects.requireNonNull(recordRefs.get(record), "original object was not previously decoded");
    }

    private ExactRef referenceOfRead(PlanningReadReceipt read) {
        return Objects.requireNonNull(readRefs.get(read), "original object was not previously decoded");
    }

    private ExactRef referenceOfRequest(NativeRequest request) {
        return Objects.requireNonNull(requestRefs.get(request), "original object was not previously decoded");
    }

    private ExactRef referenceOfDispatch(NativeActionPort.DispatchOutcome dispatch) {
        return Objects.requireNonNull(dispatchRefs.get(dispatch), "original object was not previously decoded");
    }

    private ExactRef referenceOfMaterial(RawJson material) {
        return Objects.requireNonNull(materialRefs.get(material), "original object was not previously decoded");
    }

    private class OutcomeArchiveImpl implements ActionPorts.OutcomeArchive {
        private final PortableRecoveryDataArchive helper;

        OutcomeArchiveImpl(PortableRecoveryDataArchive helper) {
            this.helper = helper;
        }

        @Override
        public ExactRef preserve(NativeActionPort.DispatchOutcome original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public NativeActionPort.DispatchOutcome load(ExactRef original) {
            return io(() -> helper.loadDispatch(original));
        }

        @Override
        public ExactRef preserveRequest(NativeRequest original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public NativeRequest loadRequest(ExactRef original) {
            return io(() -> helper.loadRequest(original));
        }

        @Override
        public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) {
            return helper.referenceOfDispatch(original);
        }

        @Override
        public ExactRef requestReferenceOf(NativeRequest original) {
            return helper.referenceOfRequest(original);
        }

        @Override
        public ExactRef preserveRead(PlanningReadReceipt original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public PlanningReadReceipt loadRead(ExactRef original) {
            return io(() -> helper.loadRead(original));
        }

        @Override
        public ExactRef readReferenceOf(PlanningReadReceipt original) {
            return helper.referenceOfRead(original);
        }

        @Override
        public ExactRef preserveRecord(ActionRecord original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public ActionRecord loadRecord(ExactRef original) {
            return io(() -> helper.loadRecord(original));
        }

        @Override
        public ExactRef recordReferenceOf(ActionRecord original) {
            return helper.referenceOfRecord(original);
        }

        @Override
        public ExactRef preserveReceipt(ActionReceipt original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public ActionReceipt loadReceipt(ExactRef original) {
            return io(() -> helper.loadReceipt(original));
        }

        @Override
        public ExactRef receiptReferenceOf(ActionReceipt original) {
            return helper.referenceOfReceipt(original);
        }

        @Override
        public ExactRef preserveMaterial(RawJson original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public RawJson loadMaterial(ExactRef original) {
            return io(() -> helper.loadMaterial(original));
        }

        @Override
        public ExactRef materialReferenceOf(RawJson original) {
            return helper.referenceOfMaterial(original);
        }

        @Override
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) {
            throw new AssertionError("recovery must be DATA only");
        }

        @Override
        public byte[] loadNativeFrame(ExactRef original) {
            return io(() -> helper.readBytes(original, WriterContracts.MAX_PIN_BYTES));
        }

        @Override
        public byte[] readOriginalPacket(ExactRef original) {
            return io(() -> helper.readBytes(original, WriterContracts.MAX_PIN_BYTES));
        }

        @Override
        public RawJson loadFullMaterial(ExactRef original) {
            return io(() -> helper.loadFullMaterial(original));
        }

        @Override
        public ExactRef materialReference(String sha256, long bytes) {
            throw new IllegalStateException("actual immutable material digest lookup is unavailable");
        }

        @Override
        public OutcomeArchive withSession(ContinuityStorePort.Session borrowed) {
            return io(() -> { authority.require(borrowed); return this; });
        }

        @Override
        public <T> T inSession(ContinuityStorePort.Session borrowed, Function<OutcomeArchive, T> work) {
            return io(() -> { authority.require(borrowed); return work.apply(this); });
        }

    }
}
