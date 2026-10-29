package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Shared Start/archived replay parser of the actual independent campaign-root result token. */
public record GameplayEntryRoot(PlanningReadReceipt original, BigInteger player, int dateRaw, String governmentKey) {
    public GameplayEntryRoot { Objects.requireNonNull(original); Objects.requireNonNull(player); StrictJson.require(player.signum()>0,"positive actual root actor required"); StrictJson.text(governmentKey); }
    public static final OperationKey OPERATION=new OperationKey("query-campaign-root-context-v1");
    public static GameplayEntryRoot decode(PlanningReadReceipt receipt) {
        StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay && receipt.request().operation().equals(OPERATION)
                && receipt.original().nativeOk(),"real successful gameplay campaign-root read required");
        Obj result=object(parse(receipt.original().originalResultToken().orElseThrow().bytes()),"original root token");
        Obj envelope=object(parse(receipt.original().originalFrame().bytes()),"original root result frame");
        StrictJson.require(new Text("command_result").equals(envelope.get("type")) && new IntegerValue(BigInteger.ONE).equals(envelope.get("protocol_version"))
                && new Text(receipt.requestId()).equals(envelope.get("request_id")) && new Bool(true).equals(envelope.get("ok"))
                && result.equals(envelope.get("result")),"original campaign root result token differs from its actual frame");
        StrictJson.require(new Text(OPERATION.value()).equals(result.get("step")) && bool(result.get("accepted"),"accepted"),"native root ACK binding differs");
        Obj root=object(result.get("campaign_root_context"),"campaign_root_context");
        StrictJson.require(result.get("status").equals(root.get("status")) && integer(result.get("query_sequence"),"query_sequence").signum()>0,
                "native root envelope status or actual query sequence differs");
        var frame=receipt.request().before().frame();
        StrictJson.require(new Text("available").equals(root.get("status")) && integer(root.get("schema_version"),"schema_version").equals(BigInteger.ONE)
                && integer(root.get("snapshot_revision"),"snapshot_revision").equals(frame.identity().nativeRevision()),"independent available root revision required");
        int date=integer(root.get("date_raw"),"date_raw").intValueExact(); BigInteger actor=integer(root.get("player_character_id"),"player_character_id");
        StrictJson.require(frame.identity().dateRaw().equals(BigInteger.valueOf(date)) && frame.identity().player().equals(actor)
                && bool(root.get("player_character_alive"),"player_character_alive"),"actual root date/living player differs from the read frame");
        Obj government=object(root.get("government"),"government"); String key=text(government.get("key"),"government.key");
        StrictJson.require("feudal_government".equals(key),"selected ordinary Start requires actual feudal root");
        Obj provenance=object(root.get("provenance"),"provenance");
        StrictJson.require("1.20.0.4".equals(text(provenance.get("game_version"),"game_version"))
                && "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518".equalsIgnoreCase(text(provenance.get("executable_sha256"),"executable_sha256")),"root exact native build provenance differs");
        return new GameplayEntryRoot(receipt,actor,date,key);
    }
}
