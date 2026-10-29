package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeCharacterId;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

/** Typed in-process seam; original Driver consumers retain locks, persistence and admission. */
public final class SuccessionConsumerPort {
    public static final String SCHEMA = "xar.java-succession-request/v1";
    public record FreezeRequest(TurnBundle bundle, String episodeRunId, int episodeCharacterId) {
        public FreezeRequest { check(bundle != null, "turn bundle required"); nonempty(episodeRunId); NativeCharacterId.of(episodeCharacterId); }
    }
    public record ReconcileRequest(Expectation expectation, Snapshot snapshot, TurnBundle bundle) {
        public ReconcileRequest { check(expectation != null && snapshot != null && bundle != null, "complete reconciliation inputs required"); }
    }
    private SuccessionConsumerPort() { }

    public static Expectation decodeNormalizeRequest(byte[] body) {
        JsonNode value = request(body, "normalize", Set.of("schema", "operation", "expectation"));
        return SuccessionCodec.expectation(SuccessionCodec.field(value, "expectation"));
    }
    public static FreezeRequest decodeFreezeRequest(byte[] body) {
        JsonNode value = request(body, "freeze", Set.of("schema", "operation", "turn_bundle", "episode_run_id", "episode_character_id"));
        JsonNode id = SuccessionCodec.field(value, "episode_character_id");
        int episodeCharacterId = NativeCharacterId.fromJson(id).value();
        return new FreezeRequest(SuccessionCodec.turnBundle(SuccessionCodec.field(value, "turn_bundle"), true),
                SuccessionCodec.text(SuccessionCodec.field(value, "episode_run_id")), episodeCharacterId);
    }
    public static ReconcileRequest decodeReconcileRequest(byte[] body) {
        JsonNode value = request(body, "reconcile", Set.of("schema", "operation", "expectation", "post_snapshot", "post_turn_bundle"));
        return new ReconcileRequest(SuccessionCodec.expectation(SuccessionCodec.field(value, "expectation")),
                SuccessionCodec.snapshot(SuccessionCodec.field(value, "post_snapshot")), SuccessionCodec.turnBundle(SuccessionCodec.field(value, "post_turn_bundle"), false));
    }
    public static Expectation freeze(FreezeRequest request) {
        return SuccessionPolicy.freeze(request.bundle(), request.episodeRunId(), request.episodeCharacterId());
    }
    public static Reconciliation reconcile(ReconcileRequest request) {
        return SuccessionPolicy.reconcile(request.expectation(), request.snapshot(), request.bundle());
    }
    public static byte[] apply(byte[] body) {
        JsonNode value = SuccessionCodec.parse(body);
        String operation = SuccessionCodec.text(SuccessionCodec.field(value, "operation"));
        return switch (operation) {
            case "normalize" -> SuccessionCodec.encodeExpectation(decodeNormalizeRequest(body));
            case "freeze" -> SuccessionCodec.encodeExpectation(freeze(decodeFreezeRequest(body)));
            case "reconcile" -> SuccessionCodec.encodeReconciliation(reconcile(decodeReconcileRequest(body)));
            case "operating" -> {
                value = request(body, "operating", Set.of("schema", "operation", "snapshot", "previous_expectation"));
                JsonNode previous = SuccessionCodec.field(value, "previous_expectation");
                yield SuccessionCodec.operating(SuccessionCodec.encode(SuccessionCodec.field(value, "snapshot")), previous.isNull() ? null : SuccessionCodec.encode(previous));
            }
            default -> throw new IllegalArgumentException("unknown succession operation");
        };
    }
    private static JsonNode request(byte[] body, String operation, Set<String> fields) {
        JsonNode value = SuccessionCodec.parse(body); SuccessionCodec.exact(value, fields);
        check(SCHEMA.equals(SuccessionCodec.text(SuccessionCodec.field(value, "schema"))), "succession request schema changed");
        check(operation.equals(SuccessionCodec.text(SuccessionCodec.field(value, "operation"))), "succession operation differs from registered port"); return value;
    }
}
