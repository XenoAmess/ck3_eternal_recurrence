package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Immutable custody of the actual same-session campaign-root read used by a family leaf. */
public final class FamilyRootBinding {
    private FamilyRootBinding() { }
    public record Basis(FamilyHeirLegality.Binding binding, ExactRef originalRootReceipt) {
        public Basis { Objects.requireNonNull(binding); Objects.requireNonNull(originalRootReceipt);
            need(binding.originalCampaignRoot().equals(originalRootReceipt),"root binding and original receipt reference differ"); }
    }
    /** Reopens the exact archived original query through Root's existing immutable read archive. No native query. */
    @FunctionalInterface public interface Originals {
        PlanningReadResult.Known<OpportunityJson.Obj> read(ExactRef originalReceipt);
        /** Exact-frame default. Root may override only with its source-bound current or historical lineage admission. */
        default Basis bind(ExactRef originalReceipt,Context target) {
            var original=Objects.requireNonNull(read(originalReceipt));
            need(original.originalReceipt().equals(originalReceipt),"family original archive returned a different root receipt");
            return fromOriginal(original,target);
        }
    }
    public enum QualifiedOrigin { CURRENT_CANONICAL_READ, HISTORICAL_CANONICAL_READ }
    /** The actual Root adapter must consume the publisher's private proof. Implementing this port is not qualification. */
    public interface ReadLineageAdmission {
        QualifiedOrigin origin();
        void verifyOriginal(PlanningReadResult.Known<OpportunityJson.Obj> original,Context target);
    }
    public static Basis fromOriginal(PlanningReadResult.Known<OpportunityJson.Obj> root,Context target) {
        return rederive(root,target,false);
    }
    /** Preserves the original query frame; the explicit Root issuer reopens its proof both before and after interpretation. */
    public static Basis fromQualifiedOriginal(PlanningReadResult.Known<OpportunityJson.Obj> root,Context target,ReadLineageAdmission actual) {
        Objects.requireNonNull(root);Objects.requireNonNull(target);Objects.requireNonNull(actual);
        var origin=Objects.requireNonNull(actual.origin(),"explicit actual Root lineage origin required");
        actual.verifyOriginal(root,target);
        need(actual.origin()==origin,"actual Root lineage issuer changed its explicit origin");
        try {return rederive(root,target,true);}
        finally {
            actual.verifyOriginal(root,target);
            need(actual.origin()==origin,"actual Root lineage issuer changed its explicit origin");
        }
    }
    private static Basis rederive(PlanningReadResult.Known<OpportunityJson.Obj> root,Context c,boolean admittedReadLineage) {
        Objects.requireNonNull(root); Objects.requireNonNull(c);
        PlanningReadReceipt receipt=root.receipt(); var request=receipt.request();
        need(receipt.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID) &&
                request.operation().equals(FinanceReadContracts.Query.ROOT.operation()) &&
                FinanceReadContracts.rootCapture(request.arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY,
                "family subject must come from the one actual versioned public campaign-root contract");
        var originalBefore=request.before();
        need(receipt.original().nativeOk() && request.source().equals(c.source()) && request.sessionId().equals(c.sessionId()),
                "campaign-root subject crossed actual family source/session");
        if(admittedReadLineage) {
            var original=originalBefore.frame();var target=c.before().frame();
            need(originalBefore.machineId().equals(c.before().machineId())&&originalBefore.game().equals(c.before().game())
                    &&originalBefore.observationVersion()==c.before().observationVersion()
                    &&original.episodeRunId().equals(target.episodeRunId())&&original.snapshotId().equals(target.snapshotId())
                    &&original.identity().equals(target.identity())&&original.revision().compareTo(target.revision())<=0,
                    "qualified ROOT lineage crossed Game, player, episode, original Native identity or regressed public revision");
        } else need(originalBefore.equals(c.before()),"campaign-root subject crossed actual family frame without publisher lineage admission");
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.paused() && guard.mapReady() && guard.playerAlive() && guard.binding().observed().equals(originalBefore) &&
                    guard.binding().source().equals(c.source()) && guard.binding().sessionId().equals(c.sessionId()) &&
                    guard.binding().operation().equals(request.operation()) &&
                    guard.binding().connectionGeneration().equals(c.connectionGeneration()),
                    "campaign-root original guards do not bind the original query paused frame");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "campaign-root original guard changed between query observations");
        JsonNode frame=parse(receipt.original().originalFrame());
        closed(frame,"type","protocol_version","request_id","ok","result");
        eq(frame,"type","command_result"); eq(frame,"protocol_version",BigInteger.ONE);
        eq(frame,"request_id",receipt.requestId()); yes(frame,"ok");
        JsonNode token=parse(receipt.original().originalResultToken().orElseThrow());
        need(field(frame,"result").equals(token),"root original frame differs from retained result token");
        OpportunityJson.Obj normalized=CampaignRootContextJson.normalizeNativeResult(
                InteractionArguments.app(object(token)),originalBefore.frame().identity().dateRaw(),originalBefore.frame().identity().nativeRevision());
        JsonNode original=OpportunityJson.toNode(normalized), nested=field(original,"campaign_root_context");
        eq(original,"status","available"); eq(nested,"status","available");
        eq(nested,"player_character_id",c.actor()); yes(nested,"player_character_alive");
        JsonNode provenance=field(nested,"provenance");
        eq(provenance,"game_version",c.build().version());
        need(text(provenance,"executable_sha256").equalsIgnoreCase(c.build().sha256()),"root subject exact source differs");
        JsonNode projected=OpportunityJson.toNode(root.value());
        need(field(projected,"campaign_root_context").equals(nested),"root projected body differs from original full normalizer");
        eq(projected,"query_sequence",positive64(original,"query_sequence"));
        eq(projected,"queried_snapshot_id",originalBefore.frame().snapshotId());
        eq(projected,"queried_revision",originalBefore.frame().revision()); eq(projected,"queried_native_revision",originalBefore.frame().identity().nativeRevision());
        List<JsonNode> primary=list(nested,"held_title_partition",65536,row->row).stream().filter(row->bool(row,"primary")).toList();
        need(primary.size()==1,"family needs exactly one original public primary-title partition row");
        BigInteger heir=nullableNumber(primary.getFirst(),"first_heir_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
        return new Basis(new FamilyHeirLegality.Binding(c,positive64(original,"query_sequence"),
                heir==null?OptionalLong.empty():OptionalLong.of(heir.longValueExact()),root.originalReceipt()),root.originalReceipt());
    }

    /** Canonical leaf app arguments; only the original root reference and its rederived data are added. */
    public static OpportunityJson.Obj arguments(Basis basis,OpportunityJson.Obj flatArguments) {
        ObjectNode args=InteractionArguments.parseApp(flatArguments);
        closed(args,"expected_native_revision"); eq(args,"expected_native_revision",basis.binding().context().revision());
        args.set("root_binding",encode(basis));
        return InteractionArguments.app(args);
    }
    public static Basis decodeArguments(PlanningReadRequest leaf,Context context,Originals originals) {
        Objects.requireNonNull(leaf); Objects.requireNonNull(originals);
        need(leaf.before().equals(context.before()) && leaf.source().equals(context.source()) && leaf.sessionId().equals(context.sessionId()),
                "family leaf binding differs from its actual query context");
        ObjectNode args=InteractionArguments.parseApp(leaf.arguments());
        closed(args,"expected_native_revision","root_binding"); eq(args,"expected_native_revision",context.revision());
        JsonNode binding=field(args,"root_binding");
        closed(binding,"root_query_sequence","observed_first_heir_character_id","original_root_receipt");
        ExactRef ref=InteractionArguments.ref(field(binding,"original_root_receipt"));
        Basis actual=Objects.requireNonNull(originals.bind(ref,context));
        need(actual.originalRootReceipt().equals(ref)&&actual.binding().context().equals(context),
                "family root issuer changed the exact original receipt or target query context");
        need(binding.equals(encode(actual)),"family root binding differs from retained original query");
        return actual;
    }
    public static ObjectNode encode(Basis basis) {
        ObjectNode out=F.objectNode().put("root_query_sequence",basis.binding().rootQuerySequence());
        if(basis.binding().observedFirstHeir().isPresent()) out.put("observed_first_heir_character_id",basis.binding().observedFirstHeir().getAsLong());
        else out.putNull("observed_first_heir_character_id");
        InteractionArguments.ref(out.putObject("original_root_receipt"),basis.originalRootReceipt());
        return out;
    }
}
