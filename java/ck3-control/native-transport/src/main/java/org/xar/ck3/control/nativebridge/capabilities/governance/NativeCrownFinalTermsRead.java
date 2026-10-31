package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;

/** The actual final-terms query is the sole producer of the native .4 Crown clock; CanEnact is not a clock. */
public final class NativeCrownFinalTermsRead {
    public record Terms(CrownFinalTerms.Readback readback,RawJson completeConsume,Optional<CrownCooldownCodec.ClockRequest> clock) {
        public Terms {Objects.requireNonNull(readback);Objects.requireNonNull(completeConsume);Objects.requireNonNull(clock);}
    }
    public record Consumed(CrownFinalTerms.Readback readback, RawJson completeConsume, CrownCooldownCodec.ClockRequest clock) {
        public Consumed { Objects.requireNonNull(readback); Objects.requireNonNull(completeConsume); Objects.requireNonNull(clock); }
    }
    private final String version;
    private final String sha256;
    private final ReadContract<Terms> contract;
    public NativeCrownFinalTermsRead(ExactRef actualNativeSource, String exactVersion, String exactSha256) {
        CouncilCodec.requireBuild(exactVersion, exactSha256); version = exactVersion; sha256 = exactSha256;
        contract = new ReadContract<>("governance.crown-final-terms-v2", new OperationKey(CrownFinalTerms.STEP), Optional.empty(),
                "governance.crown-final-terms-clock-v1", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, actualNativeSource, (request, requestId) -> {
                    StrictJson.require(request.arguments().members().isEmpty(), "actual Crown final-terms wire has no domain arguments");
                    return new NativeRequest(CrownFinalTerms.STEP, Optional.empty(), new RawJson(new byte[] {'{', '}'}));
                }, this::consumeTerms, this::consumeTerms);
    }
    public ReadContract<Terms> contract() { return contract; }
    /** Reuse the same actual original read for retry publication; never mint another query or partial law payload. */
    public Consumed consume(PlanningReadReceipt receipt) {
        var terms=consumeTerms(receipt);
        return new Consumed(terms.readback(),terms.completeConsume(),terms.clock().orElseThrow(()->new IllegalArgumentException("the complete native law result contains no qualified .4 cooldown/turn-tick pair")));
    }
    /** Complete law material remains useful when the optional .4 calendar observer is unavailable. */
    public Terms consumeTerms(PlanningReadReceipt receipt) {
        StrictJson.require(receipt.contractId().equals(contract.contractId()) && receipt.request().operation().equals(contract.operation())
                && receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "actual registered final-terms receipt required");
        var request = receipt.request();
        for (var guard : List.of(receipt.before(), receipt.after())) StrictJson.require(guard.binding().observed().equals(request.before())
                && guard.binding().source().equals(request.source()) && guard.binding().sessionId().equals(request.sessionId())
                && guard.paused() && guard.mapReady() && guard.playerAlive(), "native final-terms read lost its same living paused source frame");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "final-terms complete semantic binding changed");
        ObjectNode full = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require(StrictJson.text(full.get("type")).equals("command_result") && StrictJson.integer(full.get("protocol_version"), 1, 1) == 1
                && StrictJson.text(full.get("request_id")).equals(receipt.requestId()) && StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(full.get("result")), "final-terms original packet/result token correlation changed");
        StrictJson.trueValue(full.get("ok"));
        ObjectNode input = StrictJson.object().put("schema", CrownFinalTermsCodec.CONSUME_SCHEMA)
                .put("expected_revision", request.before().frame().revision()).put("request_id", receipt.requestId());
        input.set("before_snapshot", frame(receipt.before())); input.set("after_snapshot", frame(receipt.after())); input.set("command_result", full);
        RawJson complete = new RawJson(StrictJson.canonical(input));
        var readback = CrownFinalTermsCodec.decodeReadback(complete.bytes());
        Optional<CrownCooldownCodec.ClockRequest> clock=Optional.empty();
        if(readback.build()==CrownFinalTerms.Build.CK3_12004&&readback.payload().cooldown()!=null&&readback.payload().turnTick()!=null) {
            var observed=new CrownCooldownCodec.ClockRequest(readback.payload().cooldown(),readback.payload().dateRaw(),readback.payload().turnTick());
            CrownCooldown.interpret(observed.observation(),observed.dateRaw(),observed.turnTick());clock=Optional.of(observed);
        }
        return new Terms(readback,complete,clock);
    }
    private ObjectNode frame(PlanningReadGuard guard) {
        var observed = guard.binding().observed().frame(); var id = observed.identity();
        ObjectNode row = StrictJson.object().put("snapshot_id", observed.snapshotId()).put("revision", observed.revision())
                .put("native_revision", id.nativeRevision()).put("date_raw", id.dateRaw()).put("paused", guard.paused()).put("map_ready", guard.mapReady())
                .put("episode_run_id", observed.episodeRunId());
        row.putObject("played_character").put("character_id", id.player()).put("alive", guard.playerAlive());
        row.putObject("diagnostics").putObject("hello").put("expected_ck3_version", version).put("expected_ck3_sha256", sha256);
        return row;
    }
}
