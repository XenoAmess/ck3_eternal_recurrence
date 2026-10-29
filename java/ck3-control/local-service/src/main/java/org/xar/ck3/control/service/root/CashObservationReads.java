package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.finance.WarPaymentExtrasCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.service.root.CashObservationPublicCodec.*;

/** Parameterized private cash observation family retained by the same pre-Core Finance Prepared owner. */
public final class CashObservationReads {
    public static final String FAMILY="public-finance-cash-observation-v1";
    public static final String PERMISSION="allow_private_war_cash_query";
    public record Sources(ExactRef definition,ExactRef decoder) {
        public Sources {for(var source:List.of(definition,decoder))require(source.bytes()>0,"actual selected cash definition/decoder required");}
    }
    public record Selection(Complete current,Request input,Optional<RawJson> actualAppliedMaterial,Instant deadline) {
        public Selection {Objects.requireNonNull(current);Objects.requireNonNull(input);Objects.requireNonNull(actualAppliedMaterial);Objects.requireNonNull(deadline);
            require(current.identity().frame().revision().equals(input.expectedRevision()),"cash expected public revision differs from actual held Root frame");
            require((input instanceof Construction)==actualAppliedMaterial.isPresent(),"construction requires the actual known durable applied projection, including known empty");
            var n=PublicDataJson.object(new RawJson(org.xar.ck3.control.application.driver.DriverJson.encode(current.semantic())));
            require(n.path("paused").isBoolean()&&n.path("paused").booleanValue()&&n.path("map_ready").isBoolean()&&n.path("map_ready").booleanValue()
                    &&n.path("played_character").path("alive").isBoolean()&&n.path("played_character").path("alive").booleanValue(),"cash requires a living paused map");
            if(input instanceof Current c&&c.sampling().value().isPresent())require("1.20.0.4".equals(n.path("diagnostics").path("hello").path("expected_ck3_version").asText())
                &&"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518".equalsIgnoreCase(n.path("diagnostics").path("hello").path("expected_ck3_sha256").asText()),"payment observer control requires exact build4 before Native dispatch");}
        public OperationKey operation(){return new OperationKey(input instanceof Termination t?"query-war-cash-termination-send-costs-v1-"+t.warId()+"-"+t.outcome().wire():"query-war-cash-current-resources-v1");}
        public OpportunityJson.Obj arguments(){ObjectNode n=CashObservationCodec.arguments(input);actualAppliedMaterial.ifPresent(a->n.set("actual_applied_material",PublicDataJson.object(a)));
            return org.xar.ck3.control.application.driver.DriverJson.object(PublicDataJson.encode(n).bytes(),RawJson.MAXIMUM_BYTES);}
        public PlanningReadRequest request(){return new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),operation(),arguments(),deadline);}
    }
    private final Sources sources;
    private final RootReadContractCatalog.Family<Selection,Response> family;
    public CashObservationReads(Sources actual) {
        sources=Objects.requireNonNull(actual);
        family=new RootReadContractCatalog.Family<>(FAMILY,Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.definition(),sources.decoder(),CashObservationReads::key,Selection::operation,s->
            new ReadContract<>(FAMILY+"-"+ActionCodec.sha256(key(s).bytes()),s.operation(),Optional.empty(),PERMISSION,ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.definition(),
                (request,id)->{verify(s,request);RawJson fields=new RawJson(new byte[]{'{','}'});
                    if(s.input() instanceof Current c)fields=WarPaymentExtrasCodec.requestFields(c.sampling().value().map(x->WarPaymentExtrasCodec.Mode.valueOf(x.name())),c.window().value().map(Window::wire),s.current().source().machineId());
                    return new NativeRequest(s.operation().value(),Optional.empty(),fields);},receipt->decode(s,receipt),receipt->decode(s,receipt)));
    }
    public Sources sources(){return sources;}
    public List<RootReadContractCatalog.Family<?,?>> families(){return List.of(family);}
    public ReadContract<Response> contract(RootReadContractCatalog catalog,Selection selection){return catalog.issue(family,selection);}
    public PlanningReadResult<Response> read(Session same,RootRuntimeContext context,Selection selection)throws IOException {
        context.writer().requireSession(same);
        require(context.source().equals(selection.current().source())&&context.game().sessionId().equals(selection.current().sessionId())
                &&context.game().generation().equals(selection.current().identity().game()),"cash observation crossed the installed same physical Finance Game");
        return context.reads().read(same,contract(context.readCatalog(),selection),selection.request());
    }
    private static RawJson key(Selection s){ObjectNode n=CashObservationCodec.arguments(s.input());n.put("full_binding_sha256",s.current().fullBindingSha256()).put("session_id",s.current().sessionId())
            .put("source_sha256",s.current().source().sourceRef().sha256());s.actualAppliedMaterial().ifPresent(a->n.set("actual_applied_material",PublicDataJson.object(a)));return PublicDataJson.encode(n);}
    private static void verify(Selection s,PlanningReadRequest actual){require(actual.equals(s.request()),"cash query changed original source/frame/session/arguments/deadline");}
    private static Response decode(Selection s,PlanningReadReceipt receipt){verify(s,receipt.request());require(receipt.original().nativeOk(),"cash read was rejected");return CashObservationCodec.normalize(s,receipt);}
}
