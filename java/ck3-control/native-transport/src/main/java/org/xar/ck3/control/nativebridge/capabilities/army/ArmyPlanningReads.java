package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** General preview/H1 actual read transport. Retreat keeps its existing exact service and token composition. */
public final class ArmyPlanningReads {
    public static final String PREVIEW="game.command.preview-move-army-N-to-N",HORIZON="game.command.query-route-contact-horizon-v1-N";
    public record Selection(PlanningRequest request,MilitaryReadObservation.Kind kind,int subject,int target,List<Integer> hostiles) {
        public Selection {
            Objects.requireNonNull(request);Objects.requireNonNull(kind);hostiles=List.copyOf(hostiles);
            require(subject>=0&&target>0,"public Army/private Province scope");
            if(kind==MilitaryReadObservation.Kind.CONTACT_HORIZON) {
                require(hostiles.equals(MilitaryPlanInputs.hostiles(request)),"complete current hostile scope required");
                org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit.horizonStep(subject,target,hostiles);
            }else require(hostiles.isEmpty(),"preview has no arbitrary hostile override");
        }
        public String step(){return kind==MilitaryReadObservation.Kind.ROUTE_PREVIEW?"preview-move-army-"+subject+"-to-"+target:org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit.horizonStep(subject,target,hostiles);}
        public Context context(){return new Context(request.before(),request.source(),request.sessionId(),request.deadline());}
    }
    private final PlanningReadPort reads;private final ActionPorts.OutcomeArchive archive;private final NativeEffectEvidence.FrameLoader frames;
    private final java.util.function.Supplier<ContinuityStorePort.Session> session;
    private final RootReadContractCatalog.Family<Selection,MilitaryReadObservation> previews,horizons;
    public ArmyPlanningReads(ExactRef definition,ExactRef strictDecoder,PlanningReadPort actualReads,ActionPorts.OutcomeArchive actualArchive,
            NativeEffectEvidence.FrameLoader originalFrames,java.util.function.Supplier<ContinuityStorePort.Session> currentSession) {
        reads=Objects.requireNonNull(actualReads);archive=Objects.requireNonNull(actualArchive);frames=Objects.requireNonNull(originalFrames);session=Objects.requireNonNull(currentSession);
        previews=family("ordinary-route-preview",MilitaryReadObservation.Kind.ROUTE_PREVIEW,PREVIEW,definition,strictDecoder);
        horizons=family("ordinary-contact-horizon",MilitaryReadObservation.Kind.CONTACT_HORIZON,HORIZON,definition,strictDecoder);
    }
    public List<RootReadContractCatalog.Family<?,?>> families(){return List.of(previews,horizons);}
    public PlanningReadResult<MilitaryReadObservation> collect(ContinuityStorePort.Session borrowed,RootReadContractCatalog catalog,Selection selected) {
        Objects.requireNonNull(borrowed);var contract=catalog.issue(selected.kind()==MilitaryReadObservation.Kind.ROUTE_PREVIEW?previews:horizons,selected);var context=selected.context();
        return reads.read(borrowed,contract,new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),arguments(selected),context.deadline()));
    }
    private RootReadContractCatalog.Family<Selection,MilitaryReadObservation> family(String id,MilitaryReadObservation.Kind kind,String capability,ExactRef definition,ExactRef decoder) {
        return new RootReadContractCatalog.Family<>(id,Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(capability),definition,decoder,ArmyPlanningReads::key,s->new OperationKey(s.step()),s->{
            require(s.kind()==kind,"wrong typed military read family");subject(s);
            return new ReadContract<>(id+"-"+ArmyReadKey.digest(key(s)),new OperationKey(s.step()),Optional.of(capability),capability,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definition,
                    (request,requestId)->{verify(request,s);return new NativeRequest(s.step(),Optional.of(capability),new RawJson(new byte[]{'{','}'}));},receipt->{verify(receipt.request(),s);return decode(s,receipt);},receipt->{verify(receipt.request(),s);return decode(s,receipt);},
                    (original,value,current,semantic)->{
                        verify(original.request(),s);verify(current,s);
                        require(org.xar.ck3.control.application.planning.military.NativeMilitaryInputView.sameNativeOperands(s.request().observations().snapshot(),semantic),"route native military operands changed after original read");
                        require(value.equals(decode(s,original)),"canonical route value differs from original complete decoder");
                    });
        });
    }
    public MilitaryReadObservation decode(Selection selected,PlanningReadReceipt receipt) {
        verify(receipt.request(),selected);var raw=ArmyNativeReadEvidence.result(ArmyNativeReadEvidence.contextForRequest(selected.context(),receipt.request()),receipt);var originals=archive.withSession(session.get());
        var before=RootGuardEvidence.loadFrame(receipt.before().binding(),originals,frames);var after=RootGuardEvidence.loadFrame(receipt.after().binding(),originals,frames);
        require(before.semantic().equals(selected.request().observations().snapshot())&&before.identity().equals(selected.request().before())
                &&after.identity().equals(before.identity())&&after.source().equals(before.source())&&after.sessionId().equals(before.sessionId())
                &&after.connectionGeneration().equals(before.connectionGeneration())&&after.fullBindingSha256().equals(before.fullBindingSha256())&&after.semantic().equals(before.semantic()),"military query crossed the full current native/Driver source");
        yes(raw.get("accepted"));equal(raw.get("status"),"available");
        if(selected.kind()==MilitaryReadObservation.Kind.ROUTE_PREVIEW) {
            require(names(raw).equals(Set.of("step","accepted","status","route_preview")),"exact native route preview envelope required");
            Obj preview=ArmyRouteOptionalCodec.normalize(DriverJson.object(bytes(object(raw.get("route_preview"))),DriverJson.MAX_NATIVE_BYTES));
            var p=OpportunityJson.toNode(preview);require(unit(p.get("army_id")).value()==selected.subject()&&id(p.get("origin_province_id")).value()==origin(selected)
                    &&id(p.get("target_province_id")).value()==selected.target(),"preview source/target differs");equal(p.get("status"),"available");
            List<PositiveId> route=array(p.get("route_province_ids"),ArmyJson::id);var remaining=new java.util.ArrayList<>(route);
            if(!remaining.isEmpty()&&remaining.getFirst().value()==origin(selected))remaining.removeFirst();
            require(selected.target()==origin(selected)&&remaining.isEmpty()||!remaining.isEmpty()&&remaining.getLast().value()==selected.target(),"preview endpoint differs");
            ((com.fasterxml.jackson.databind.node.ObjectNode)p).put("previewed_date_raw",selected.context().dateRaw());raw.set("route_preview",p);
        }else {
            var required=Set.of("step","accepted","status","query_sequence","snapshot_revision","route_contact_horizon");var extras=new java.util.HashSet<>(names(raw));
            require(extras.containsAll(required),"H1 original envelope missing fields");extras.removeAll(required);require(Set.of("physical_army_inventory","physical_army_inventory_diagnostics","backend_id").containsAll(extras)
                    &&(!extras.contains("physical_army_inventory_diagnostics")||extras.contains("physical_army_inventory")),"unknown H1 sidecar or diagnostics without inventory");
            positive(raw.get("query_sequence"));equal(raw.get("snapshot_revision"),selected.context().nativeRevision());if(raw.has("backend_id"))require(!text(raw.get("backend_id")).isBlank(),"H1 backend missing");
            Obj horizon=DriverJson.object(bytes(object(raw.get("route_contact_horizon"))),DriverJson.MAX_NATIVE_BYTES);
            Obj subjectRoute=OpportunityJson.object(horizon.get("subject_route"),"subject route");List<Integer> route=MilitaryPlanInputs.ids(subjectRoute.get("route_province_ids"));
            var query=new MilitaryTimeline.Query(selected.subject(),origin(selected),selected.target(),selected.hostiles(),route);MilitaryTimeline.decode(horizon,selected.request(),query);
            if(raw.has("physical_army_inventory")) {
                var checked=PhysicalArmyInventoryCheck.mailbox(DriverJson.object(bytes(object(raw.get("physical_army_inventory"))),DriverJson.MAX_NATIVE_BYTES),before.semantic(),after.semantic(),horizon,
                        integer(raw.get("query_sequence")),selected.subject(),selected.hostiles());
                raw.set("physical_army_inventory_check",OpportunityJson.toNode(checked.json()));
            }
        }
        var c=selected.context();raw.put("queried_snapshot_id",c.before().frame().snapshotId()).put("queried_revision",c.before().frame().revision()).put("queried_native_revision",c.nativeRevision())
                .put("queried_connection_generation",before.connectionGeneration()).put("queried_episode_run_id",c.before().frame().episodeRunId());
        return new MilitaryReadObservation(selected.kind(),DriverJson.object(bytes(raw),DriverJson.MAX_NATIVE_BYTES));
    }
    private static Obj subject(Selection selection){var matches=OpportunityJson.array(selection.request().observations().snapshot().get("player_armies"),"player armies").stream().map(value->OpportunityJson.object(value,"army"))
            .filter(row->new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(selection.subject())).equals(row.get("army_id"))).toList();
        require(matches.size()==1&&new OpportunityJson.Bool(true).equals(matches.getFirst().get("controllable")),"query subject must be exactly one current controllable public Army");return matches.getFirst();}
    private static int origin(Selection selected){return OpportunityJson.integer(subject(selected).get("current_province_id"),"origin Province").intValueExact();}
    private static RawJson key(Selection selected){var n=empty().put("step",selected.step()).put("origin",origin(selected)).put("snapshot_sha256",DriverJson.sha256(DriverJson.encode(selected.request().observations().snapshot())));
        n.set("context",parse(ArmyReadKey.key(new ArmyCalls.RetreatPreview(new ArmyCalls.Revision(new Present<>(selected.request().before().frame().revision())),new PublicUnitId(selected.subject()),new PositiveId(selected.target())),selected.context()).bytes()));return new RawJson(bytes(n));}
    private static Obj arguments(Selection selected){return DriverJson.object(bytes(empty()),DriverJson.MAX_NATIVE_BYTES);}
    private static void verify(PlanningReadRequest request,Selection selected){var c=selected.context();require(request.before().equals(c.before())&&request.source().equals(c.source())&&request.sessionId().equals(c.sessionId())
            &&request.operation().value().equals(selected.step())&&request.arguments().equals(arguments(selected)),"military read changed current source or original operation");}
}
