package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.NativeWire;

/** One fixed source-bound read route. The composition root registers this exact contract once. */
public final class PlayerReligionContextRead {
    public static final String STEP = "query-player-religion-context-v1";
    public static final String PERMISSION = "allow_private_player_religion_context_query";
    public static final String DOMAIN = "player_religion_context_v1";
    public static final String CONTRACT_ID = "religion/player-religion-context-v1";
    public static final OperationKey OPERATION = new OperationKey(STEP);

    /** Narrow original producer pins; Root qualification still binds the complete deployed native closure. */
    public record Sources(ExactRef pythonProducer, ExactRef nativeMailbox, ExactRef nativeContext) {
        public Sources {
            Objects.requireNonNull(pythonProducer); Objects.requireNonNull(nativeMailbox); Objects.requireNonNull(nativeContext);
            need(pythonProducer.bytes() > 0 && nativeMailbox.bytes() > 0 && nativeContext.bytes() > 0,
                    "actual original religion producer sources required");
        }
    }
    @FunctionalInterface public interface ReadAdmission {
        void verify(Sources sources, PlanningReadRequest actualRequest);
    }
    /** Query transport identities are independent of the component's owner-pump capture epoch. */
    public record Metadata(String queriedSnapshotId, BigInteger queriedRevision, BigInteger queriedNativeRevision,
            int queryDateRaw, BigInteger queriedPlayerCharacterId, String backendId, String status) {
        public Metadata {
            need(queriedSnapshotId != null && !queriedSnapshotId.isEmpty(), "actual queried snapshot identity required");
            range(queriedRevision, BigInteger.ONE, U64); range(queriedNativeRevision, BigInteger.ONE, U64);
            NativeCharacterId.of(queriedPlayerCharacterId);
            need(backendId != null && !backendId.isEmpty(), "actual religion backend required");
            need("observed".equals(status) || "unavailable".equals(status), "native religion status differs");
        }
    }
    public record Observation(PlayerReligionContext context, Metadata metadata) {
        public Observation {
            Objects.requireNonNull(context); Objects.requireNonNull(metadata);
            need(metadata.backendId().equals("ck3-" + context.gameVersion() + "-native-player-religion-context-v1"),
                    "religion backend does not belong to component build");
            need(metadata.status().equals(context.available() ? "observed" : "unavailable"),
                    "religion source status differs from component availability");
            context.requireAvailableFrame(BigInteger.valueOf(metadata.queryDateRaw()), metadata.queriedPlayerCharacterId());
        }
    }

    private final PlanningReadPort reads;
    private final ReadContract<Observation> contract;

    public PlayerReligionContextRead(PlanningReadPort reads, Sources sources, ReadAdmission admission) {
        this.reads = Objects.requireNonNull(reads); Objects.requireNonNull(sources); Objects.requireNonNull(admission);
        this.contract = new ReadContract<>(CONTRACT_ID, OPERATION, Optional.empty(), PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, sources.pythonProducer(), (request, requestId) -> {
                    need(request.arguments().members().isEmpty(), "current-player religion query takes no additional fields");
                    admission.verify(sources, request);
                    return new NativeRequest(STEP, Optional.empty(), new RawJson(new byte[] {'{', '}'}));
                }, PlayerReligionContextRead::decode, PlayerReligionContextRead::decode);
    }
    public ReadContract<Observation> contract() { return contract; }

    public PlanningReadResult<Observation> query_player_religion_context_v1(PlanningReadRequest request) {
        Objects.requireNonNull(request);
        need(request.operation().equals(OPERATION), "religion query requires its exact registered operation");
        return reads.read(contract, request);
    }
    /** Final-lock consumers borrow the original writer session; no nested writer or second transport is opened. */
    public PlanningReadResult<Observation> query_player_religion_context_v1(Session borrowed, PlanningReadRequest request) {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(request);
        need(request.operation().equals(OPERATION), "religion query requires its exact registered operation");
        return reads.read(borrowed, contract, request);
    }
    // Source verification removed; fields retained for trace.
    public static Observation decode(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        need(receipt.contractId().equals(CONTRACT_ID) && receipt.request().operation().equals(OPERATION)
                        && receipt.request().arguments().members().isEmpty(),
                "religion receipt does not belong to registered read");
        ObjectNode result = originalResult(receipt);
        equal(result, "step", STEP); yes(result, "accepted"); yes(result, "private_build");
        yes(result, "read_only"); no(result, "advertised"); equal(result, "domain_key", DOMAIN);
        PlayerReligionContext.Build build = PlayerReligionContext.Build.exact(text(result, "game_version"), text(result, "executable_sha256"));
        need(build == connectedBuild(receipt), "religion query result differs from actual connected native build");
        equal(result, "backend_id", "ck3-" + build.version() + "-native-player-religion-context-v1");
        equal(result, "snapshot_revision", nativeRevision(receipt)); equal(result, "date_raw", date(receipt));
        PlayerReligionContext context = PlayerReligionContext.decode(field(result, "player_religion_context"));
        need(context.exactBuild() == build, "nested religion context differs from native envelope build");
        context.requireAvailableFrame(date(receipt), player(receipt));
        String status = text(result, "status");
        need(status.equals(context.available() ? "observed" : "unavailable"), "native religion source status differs");
        Metadata metadata = new Metadata(receipt.request().before().frame().snapshotId(),
                receipt.request().before().frame().revision(), nativeRevision(receipt),
                date(receipt).intValueExact(), player(receipt), text(result, "backend_id"), status);
        return new Observation(context, metadata);
    }
    private static ObjectNode originalResult(PlanningReadReceipt receipt) {
        try {
            NativeWire.Frame parsed = NativeWire.decode(receipt.original().originalPacket());
            need(parsed instanceof NativeWire.CommandResult, "original native religion packet must be command_result");
            NativeWire.CommandResult packet = (NativeWire.CommandResult) parsed;
            need(packet.requestId().equals(receipt.requestId()) && packet.nativeOk() && receipt.original().nativeOk()
                    && Arrays.equals(packet.payload().value(), receipt.original().originalFrame().bytes()),
                    "original religion packet/request/frame mismatch");
            ObjectNode frame = object(NativeWire.parse(packet.payload().value()));
            ObjectNode result = object(field(frame, "result"));
            need(receipt.original().originalResultToken().isPresent()
                    && parse(receipt.original().originalResultToken().orElseThrow()).equals(result),
                    "original religion result token differs from complete native packet");
            return result;
        } catch (IOException failure) {
            throw new IllegalArgumentException("malformed original native religion packet", failure);
        }
    }
    public static PlayerReligionContext.Build connectedBuild(PlanningReadReceipt receipt) {
        try {
            NativeWire.Frame original = NativeWire.decode(originalPacket(receipt.before().binding().capabilityEvidence()));
            need(original instanceof NativeWire.Hello, "guard must bind actual original native hello");
            NativeWire.Hello hello = (NativeWire.Hello) original;
            var origin=receipt.request().origin();
            boolean reconciliation=origin instanceof org.xar.ck3.control.application.action.CommandOrigin.Reconciliation;
            need(!reconciliation||java.util.List.of("query-player-religion-conversion-result-private-v1","county-conversion-task-result-private-v1").contains(receipt.request().operation().value()),"ordinary context HELLO cannot use a reconciliation origin");
            need(hello.pid() == origin.game().pid()
                    && hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration())
                    && hello.buildMatch() && hello.adapterStatus().equals("ready"),
                    "original religion hello process/connection drift");
            for (PlayerReligionContext.Build build : PlayerReligionContext.Build.values())
                if (build.sha256().equalsIgnoreCase(hello.gameSha256())) return build;
            throw new IllegalArgumentException("unrecognized actual native religion build SHA");
        } catch (IOException failure) {
            throw new IllegalArgumentException("malformed actual native religion hello", failure);
        }
    }
    /** Root's event ReadPublication bridge consumes this exact native/Python-compatible JSON view. */
    public static ObjectNode flattened(Observation observation) {
        Objects.requireNonNull(observation);
        PlayerReligionContext context = observation.context(); Metadata metadata = observation.metadata();
        ObjectNode result = context.encode();
        result.put("backend_id", metadata.backendId()).put("domain_key", DOMAIN)
                .put("status", metadata.status()).put("read_only", true).put("advertised", false)
                .put("exact_ck3_build", context.gameVersion()).put("exe_sha256", context.exactBuild().sha256())
                .put("queried_snapshot_id", metadata.queriedSnapshotId())
                .put("queried_revision", metadata.queriedRevision())
                .put("queried_native_revision", metadata.queriedNativeRevision())
                .put("snapshot_revision", metadata.queriedNativeRevision()).put("query_date_raw", metadata.queryDateRaw());
        return result;
    }
}
