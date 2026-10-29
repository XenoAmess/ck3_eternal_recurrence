package org.xar.ck3.control.nativebridge.capabilities.finance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadResult;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceNativeReads;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec.PlanningFrame;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanSource;
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource;

/** One prospective source read. Root must install this exact instance with an actual qualified native source witness. */
public final class NativeFinanceReads {
    public static final String BACKEND = "ck3-1.20.0.4-native-construction-refund-source-v1";
    public static final String LOAN_BACKEND = "ck3-1.20.0.4-native-holy-order-loan-source-v2";
    private final ReadContract<ConstructionRefundSource.Result> cancelQuote;

    public record CancelQuoteRequest(int provinceId, BigInteger captureEpoch) {
        public CancelQuoteRequest {
            StrictJson.require(provinceId > 0 && captureEpoch != null && captureEpoch.signum() > 0
                    && captureEpoch.compareTo(StrictJson.UINT64_MAX) <= 0, "exact cancellation source request required");
        }
        public OpportunityJson.Obj arguments() {
            var fields = new LinkedHashMap<String, OpportunityJson.Value>();
            fields.put("province_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(provinceId)));
            fields.put("capture_epoch", new OpportunityJson.Text(captureEpoch.toString()));
            return new OpportunityJson.Obj(fields);
        }
    }

    public NativeFinanceReads(ExactRef actualNativeReadSourceWitness) {
        cancelQuote = new ReadContract<>("finance.construction-refund-source.v1", new OperationKey(ConstructionRefundSource.OPERATION),
                Optional.empty(), "finance.construction-refund-source.v1", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP, actualNativeReadSourceWitness,
                request -> {
                    CancelQuoteRequest parameters = parameters(request);
                    ObjectNode fields = StrictJson.object().put("province_id", parameters.provinceId())
                            .put("capture_epoch", parameters.captureEpoch().toString());
                    // The actual encoder adds only expected_revision from the native ReadPermit.
                    return new NativeRequest(ConstructionRefundSource.OPERATION, Optional.empty(), new RawJson(StrictJson.canonical(fields)));
                }, NativeFinanceReads::decode);
    }

    public record HolyLoanSourceRequest(BigInteger captureEpoch) {
        public HolyLoanSourceRequest {
            StrictJson.require(captureEpoch != null && captureEpoch.signum() > 0
                    && captureEpoch.compareTo(StrictJson.UINT64_MAX) <= 0, "exact loan source capture nonce required");
        }
        public OpportunityJson.Obj arguments() {
            var fields = new LinkedHashMap<String, OpportunityJson.Value>();
            fields.put("capture_epoch", new OpportunityJson.Text(captureEpoch.toString()));
            return new OpportunityJson.Obj(fields);
        }
    }
    /** Independent source witness; the refund constructor never installs or authorizes this operation. */
    public static ReadContract<HolyLoanSource.Result> holyLoanSource(ExactRef actualLoanNativeSourceWitness) {
        return new ReadContract<>("finance.holy-order-loan-source.v2", new OperationKey(HolyLoanSource.OPERATION),
                Optional.empty(), "finance.holy-order-loan-source.v2", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP, actualLoanNativeSourceWitness,
                request -> {
                    HolyLoanSourceRequest parameters = loanParameters(request);
                    ObjectNode fields = StrictJson.object().put("capture_epoch", parameters.captureEpoch().toString());
                    return new NativeRequest(HolyLoanSource.OPERATION, Optional.empty(), new RawJson(StrictJson.canonical(fields)));
                }, NativeFinanceReads::decodeLoan);
    }

    public ReadContract<ConstructionRefundSource.Result> cancelQuote() { return cancelQuote; }
    public List<ReadContract<?>> registeredContracts() { return List.of(cancelQuote); }


    /**
     * Data custody for one already successful central read. The caller supplies the archive borrowed
     * from the original Root writer session. No native request, archive repair or cold replay runs.
     */
    public ArchivedRefundAssessment bindCurrentRefund(ActionPorts.OutcomeArchive originalArchive,
            PlanningReadResult.Known<ConstructionRefundSource.Result> currentKnown) {
        Objects.requireNonNull(originalArchive, "originalArchive");
        Objects.requireNonNull(currentKnown, "currentKnown");
        PlanningReadReceipt original = currentKnown.receipt();
        ExactRef originalRef = currentKnown.originalReceipt();
        StrictJson.require(original.contractId().equals(cancelQuote.contractId())
                && original.request().operation().equals(cancelQuote.operation()),
                "current refund read must retain its exact owning contract");
        // Central read publication already owns the original. Never preserve a missing read here.
        StrictJson.require(originalRef.equals(originalArchive.readReferenceOf(original))
                && original.equals(originalArchive.loadRead(originalRef)),
                "refund read does not retain its actual original archive locator and complete receipt");
        ConstructionRefundSource.Result decoded = cancelQuote.decode(original);
        StrictJson.require(decoded instanceof ConstructionRefundSource.Candidate
                && currentKnown.value() instanceof ConstructionRefundSource.Candidate,
                "available original refund source required; unavailable remains unqualified");
        var source = (ConstructionRefundSource.Candidate) decoded;
        var published = (ConstructionRefundSource.Candidate) currentKnown.value();
        StrictJson.require(Arrays.equals(source.toJson(), published.toJson()),
                "published refund copy differs from its actual original read");
        return new ArchivedRefundAssessment(originalRef, source);
    }

    /** Strict recorded data import against that same current central read, never a cold read permit. */
    public ArchivedRefundAssessment decodeCurrentRefundRecord(byte[] recorded,
            ActionPorts.OutcomeArchive originalArchive,
            PlanningReadResult.Known<ConstructionRefundSource.Result> currentKnown) {
        ObjectNode row = StrictJson.object(StrictJson.parse(Objects.requireNonNull(recorded, "recorded")),
                Set.of("schema", "original_read", "refund_assessment"));
        StrictJson.require(ArchivedRefundAssessment.SCHEMA.equals(StrictJson.text(row.get("schema"))),
                "exact original refund data schema required");
        ArchivedRefundAssessment actual = bindCurrentRefund(originalArchive, currentKnown);
        StrictJson.require(actual.originalRead().equals(ExactRef.fromJson(row.get("original_read"))),
                "refund data changed its original central read locator");
        ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(row.get("refund_assessment")), actual.source);
        return actual;
    }

    /** Immutable historical data only. This type has no read/action permission or funding mutator. */
    public static final class ArchivedRefundAssessment {
        public static final String SCHEMA = "xar.ck3.archived-construction-refund-assessment.v1";
        private final ExactRef originalRead;
        private final ConstructionRefundSource.Candidate source;
        private ArchivedRefundAssessment(ExactRef originalRead, ConstructionRefundSource.Candidate source) {
            this.originalRead = Objects.requireNonNull(originalRead);
            this.source = Objects.requireNonNull(source);
        }
        public ExactRef originalRead() { return originalRead; }
        public ConstructionRefundSource.RefundAssessment refundAssessment() { return source.refundAssessment(); }
        public byte[] toJson() {
            ObjectNode row = StrictJson.object().put("schema", SCHEMA);
            row.set("original_read", originalRead.toJson());
            row.set("refund_assessment", StrictJson.parse(refundAssessment().toJson()));
            return StrictJson.canonical(row);
        }
    }

    private static CancelQuoteRequest parameters(PlanningReadRequest request) {
        ObjectNode fields = StrictJson.object(StrictJson.parse(OpportunityJson.encode(request.arguments())), Set.of("province_id", "capture_epoch"));
        return new CancelQuoteRequest((int) StrictJson.integer(fields.get("province_id"), 1, Integer.MAX_VALUE), u64(fields.get("capture_epoch")));
    }
    private static HolyLoanSourceRequest loanParameters(PlanningReadRequest request) {
        ObjectNode fields = StrictJson.object(StrictJson.parse(OpportunityJson.encode(request.arguments())), Set.of("capture_epoch"));
        return new HolyLoanSourceRequest(u64(fields.get("capture_epoch")));
    }
    private static ConstructionRefundSource.Result decode(PlanningReadReceipt receipt) {
        CancelQuoteRequest parameters = parameters(receipt.request());
        JsonNode observation = sourceObservation(receipt, ConstructionRefundSource.OPERATION, BACKEND, "construction_refund_source_v1");
        return ConstructionRefundSource.projectNative(StrictJson.canonical(observation), expectedFrame(receipt), parameters.captureEpoch(), parameters.provinceId());
    }
    private static HolyLoanSource.Result decodeLoan(PlanningReadReceipt receipt) {
        HolyLoanSourceRequest parameters = loanParameters(receipt.request());
        JsonNode observation = sourceObservation(receipt, HolyLoanSource.OPERATION, LOAN_BACKEND, "holy_order_loan_source_v2");
        return HolyLoanSource.projectNative(StrictJson.canonical(observation), expectedFrame(receipt), parameters.captureEpoch());
    }
    /** One strict original-frame/result-token boundary for both exact finance source reads. */
    private static JsonNode sourceObservation(PlanningReadReceipt receipt, String operation, String backend, String payloadField) {
        GovernanceNativeReads.verifyGuards(receipt);
        verifyOriginalWire(receipt, operation);
        ObjectNode frame = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()),
                Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require("command_result".equals(StrictJson.text(frame.get("type")))
                && StrictJson.integer(frame.get("protocol_version"), 1, 1) == 1
                && receipt.requestId().equals(StrictJson.text(frame.get("request_id"))), "finance original command result correlation mismatch");
        StrictJson.trueValue(frame.get("ok"));
        ObjectNode result = StrictJson.object(frame.get("result"), Set.of("step", "accepted", "status", "query_sequence",
                "snapshot_revision", payloadField, "backend_id"));
        StrictJson.require(operation.equals(StrictJson.text(result.get("step")))
                && operation.equals(receipt.request().operation().value())
                && backend.equals(StrictJson.text(result.get("backend_id"))), "finance native operation/backend differs");
        StrictJson.trueValue(result.get("accepted")); u64(result.get("query_sequence"));
        StrictJson.require(u64(result.get("snapshot_revision")).equals(receipt.request().before().frame().identity().nativeRevision()),
                "finance query confused public and native revisions");
        JsonNode observation = result.get(payloadField);
        StrictJson.require(observation.isObject() && observation.get("available") != null && observation.get("available").isBoolean(),
                "finance copied observation availability required");
        StrictJson.require((observation.get("available").booleanValue() ? "source_available" : "source_unavailable")
                .equals(StrictJson.text(result.get("status"))), "finance query status differs from actual copied source");
        StrictJson.require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent()
                && StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(result),
                "finance original native result token differs from full frame");
        return observation;
    }
    /** Rejoin the actual transport producer's packets; parsed JSON equality alone is insufficient custody. */
    private static void verifyOriginalWire(PlanningReadReceipt receipt, String operation) {
        try {
            var ack = receipt.original();
            StrictJson.require(ack.nativeOk() && ack.requestId().equals(receipt.requestId()), "finance original ACK identity/status differs");
            var frame = NativeWire.decode(ack.originalPacket());
            StrictJson.require(frame instanceof NativeWire.CommandResult, "finance actual packet is not a command result");
            var returned = (NativeWire.CommandResult) frame;
            StrictJson.require(returned.nativeOk() && returned.requestId().equals(receipt.requestId())
                    && Arrays.equals(returned.payload().value(), ack.originalFrame().bytes()),
                    "finance actual packet/payload/identity differs");
            StrictJson.require(returned.result().presence() == NativeWire.Presence.VALUE
                    && returned.result().token().isPresent() && ack.originalResultToken().isPresent()
                    && Arrays.equals(returned.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()),
                    "finance original result token differs from actual packet");
            var outbound = ack.outbound().orElseThrow(() -> new IllegalArgumentException("finance original outbound query unavailable"));
            StrictJson.require(outbound.requestId().equals(receipt.requestId()), "finance retained outbound identity differs");
            var sent = NativeWire.decodeExecuteRequest(outbound.originalPacket());
            StrictJson.require(sent.requestId().equals(receipt.requestId()) && sent.step().equals(operation)
                    && sent.expectedRevision().filter(receipt.request().before().frame().identity().nativeRevision()::equals).isPresent()
                    && sent.expectedSnapshotRevision().isEmpty(), "finance actual outbound query or native revision differs");
            JsonNode actualFields = StrictJson.parse(sent.normalizedAdditionalFields().value());
            JsonNode requestedFields = StrictJson.parse(OpportunityJson.encode(receipt.request().arguments()));
            StrictJson.require(actualFields.equals(requestedFields), "finance actual outbound arguments differ from typed query");
        } catch (IOException failure) {
            throw new IllegalArgumentException("finance actual original wire unavailable", failure);
        }
    }
    private static PlanningFrame expectedFrame(PlanningReadReceipt receipt) {
        var observed = receipt.request().before(); var sourceFrame = observed.frame(); var identity = sourceFrame.identity();
        return new PlanningFrame(sourceFrame.snapshotId(), sourceFrame.revision(), identity.nativeRevision(),
                identity.dateRaw(), identity.player(), sourceFrame.episodeRunId(), BigInteger.valueOf(observed.game().pid()),
                receipt.before().binding().connectionGeneration());
    }
    private static BigInteger u64(JsonNode value) {
        String wire = StrictJson.text(value);
        StrictJson.require(wire.matches("[1-9][0-9]{0,19}"), "canonical nonzero decimal uint64 string required");
        BigInteger number = new BigInteger(wire);
        StrictJson.require(number.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 outside exact domain"); return number;
    }
}

