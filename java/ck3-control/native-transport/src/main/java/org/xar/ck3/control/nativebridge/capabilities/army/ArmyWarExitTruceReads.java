package org.xar.ck3.control.nativebridge.capabilities.army;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** One actual original-pending truce family. It cannot grant ordinary readiness, history or action permission. */
public final class ArmyWarExitTruceReads {
    public static final String FAMILY="army-war-exit-truce-reconciliation-v1";
    public static final String CAPABILITY="game.command.query-raiktor-actual-truce-expiry-v1-N";
    public record Sources(ExactRef definition,ExactRef decoder) {
        public Sources { for(var ref:List.of(definition,decoder))StrictJson.require(ref.bytes()>0,"actual truce definition/decoder source required"); }
    }
    public record Selection(ReconciliationIdentity identity,ActionCommand original,ActionState.Attempt attempt,
            Complete originalBefore,Complete actualAfter,Instant deadline) {
        public Selection {
            Objects.requireNonNull(identity);Objects.requireNonNull(original);Objects.requireNonNull(attempt);
            Objects.requireNonNull(originalBefore);Objects.requireNonNull(actualAfter);Objects.requireNonNull(deadline);
            NativeWarExitEffects.requireOriginalRequest(PlanningReadRequest.newReconciliation(identity,
                    ArmyWarExitTruceReads.query(original,originalBefore,actualAfter).operation(),ArmyWarExitTruceReads.query(original,originalBefore,actualAfter).arguments(actualAfter),deadline),
                    original,attempt,originalBefore,actualAfter);
        }
        public NativeWarExitEffects.TruceQuery query(){return ArmyWarExitTruceReads.query(original,originalBefore,actualAfter);}
        public Context facts(){return new Context(identity.factual(),identity.source(),identity.sessionId(),deadline);}
        public ArmyCalls.Truce call(){return new ArmyCalls.Truce(new ArmyCalls.Revision(new Present<>(identity.factual().frame().revision())),new PositiveId(query().towardCharacterId()));}
    }
    public record Issued(ReadContract<ArmyClosedReads.Truce> contract,PlanningReadRequest request) {
        public Issued { Objects.requireNonNull(contract);Objects.requireNonNull(request);requireProfile(contract);request.origin().requireReconciliation(); }
    }
    private final PlanningReadPort reads;
    private final Sources sources;
    private final RootReadContractCatalog.Family<Selection,ArmyClosedReads.Truce> family;
    public ArmyWarExitTruceReads(Sources sources,PlanningReadPort actualReads) {
        this.sources=Objects.requireNonNull(sources);reads=Objects.requireNonNull(actualReads);
        family=new RootReadContractCatalog.Family<>(FAMILY,Selection.class,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,
                Optional.of(CAPABILITY),sources.definition(),sources.decoder(),ArmyWarExitTruceReads::key,s->s.query().operation(),s->{
            var recipe=primitive(s);
            return new ReadContract<>(FAMILY+"-"+ArmyReadKey.digest(key(s)),s.query().operation(),Optional.of(CAPABILITY),
                    CAPABILITY,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.RECONCILIATION_OBSERVATION,sources.definition(),
                    (request,id)->{verify(s,request);return recipe.request();},receipt->decode(s,receipt),receipt->decode(s,receipt),
                    (original,value,current,semantic)->{
                        verify(s,current);StrictJson.require(original.request().origin().equals(current.origin())
                                &&original.request().source().equals(current.source())&&original.request().sessionId().equals(current.sessionId())
                                &&original.request().operation().equals(current.operation())&&original.request().arguments().equals(current.arguments()),
                                "original pending truce cannot be rebound to another query");
                    });
        });
    }
    public Sources sources(){return sources;}
    public List<RootReadContractCatalog.Family<?,?>> families(){return List.of(family);}
    public Issued issue(RootReadContractCatalog catalog,Selection selected) {
        Objects.requireNonNull(catalog);Objects.requireNonNull(selected);var contract=catalog.issue(family,selected);
        var request=PlanningReadRequest.newReconciliation(selected.identity(),selected.query().operation(),selected.query().arguments(selected.actualAfter()),selected.deadline());
        verify(selected,request);return new Issued(contract,request);
    }
    public PlanningReadResult<ArmyClosedReads.Truce> collect(Session same,RootReadContractCatalog catalog,Selection selected) {
        var issued=issue(catalog,selected);return reads.read(same,issued.contract(),issued.request());
    }
    /** Original decoder only. Catalog identity, private Root guard replay and archive exact bytes remain independent requirements. */
    public ArmyClosedReads.Truce replay(RootReadContractCatalog catalog,Selection selected,PlanningReadReceipt original) {
        var issued=issue(catalog,selected);StrictJson.require(issued.contract().contractId().equals(original.contractId()),"truce original installed contract ID differs");
        return issued.contract().replay(original);
    }
    public static void requireProfile(ReadContract<?> contract) {
        Objects.requireNonNull(contract);StrictJson.require(contract.contractId().matches(FAMILY+"-[0-9a-f]{64}")
                &&contract.operation().value().matches("query-raiktor-actual-truce-expiry-v1-[1-9][0-9]{0,9}")
                &&contract.requiredCapability().equals(Optional.of(CAPABILITY))&&contract.permissionKey().equals(CAPABILITY)
                &&contract.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,"not the sole original-pending truce profile");
    }
    private static NativeWarExitEffects.TruceQuery query(ActionCommand original,Complete before,Complete after) {
        return NativeWarExitEffects.truceQuery(original,before,after).orElseThrow(()->new IllegalArgumentException("original war must be absent with a bound positive opponent"));
    }
    private static void verify(Selection selected,PlanningReadRequest request) {
        ArmyReconciliationReadEvidence.context(selected.identity(),request);
        NativeWarExitEffects.requireOriginalRequest(request,selected.original(),selected.attempt(),selected.originalBefore(),selected.actualAfter());
    }
    private static ArmyClosedReads.Truce decode(Selection selected,PlanningReadReceipt original) {
        verify(selected,original.request());
        var context=ArmyReconciliationReadEvidence.context(selected.identity(),original.request());
        ArmyReconciliationReadEvidence.result(selected.identity(),original);
        // The original token retains integer versus floating-point syntax across the strict decoder boundary.
        var value=ArmyClosedReadCodec.decodeToken(selected.call(),context,original.original().originalResultToken().orElseThrow().bytes());
        StrictJson.require(value instanceof ArmyClosedReads.Truce,"original truce decoder changed domain");return (ArmyClosedReads.Truce)value;
    }
    private static ArmyNativeRecipes.Primitive primitive(Selection selected) {
        var recipe=ArmyNativeRecipes.prepare(selected.call(),selected.facts(),new ArmyNativeRecipes.NoFacts(),false);
        StrictJson.require(recipe instanceof ArmyNativeRecipes.Primitive,"truce observation is not a primitive");
        var p=(ArmyNativeRecipes.Primitive)recipe;
        StrictJson.require(p.effect()==ArmyNativeRecipes.Effect.READ_ONLY&&p.wire()==ReadContract.WireProfile.EXECUTE_STEP
                &&p.request().step().equals(selected.query().operation().value())&&p.permissionKey().equals(CAPABILITY)
                &&p.request().requiredCapability().equals(Optional.of(CAPABILITY)),"truce observation differs from its sole typed native recipe");return p;
    }
    private static RawJson key(Selection selected) {
        var n=ArmyJson.empty();n.set("identity",ReconciliationIdentityCodec.encode(selected.identity()));
        n.put("original_body_sha256",ActionCodec.bodySha256(selected.original()));
        n.put("original_before_binding_sha256",selected.originalBefore().fullBindingSha256());
        n.put("actual_after_binding_sha256",selected.actualAfter().fullBindingSha256());
        n.set("arguments",OpportunityJson.toNode(selected.query().arguments(selected.actualAfter())));return new RawJson(StrictJson.canonical(n));
    }
}
