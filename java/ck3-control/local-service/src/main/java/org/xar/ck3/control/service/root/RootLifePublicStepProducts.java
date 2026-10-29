package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.LifeAdvanceEvidence;
import org.xar.ck3.control.application.advance.LifeAdvanceRootReplay;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Public EXECUTE adapters for the two actual installed Life composites. Preparation and clock
 * execution remain with the same Life owner and Root coordinator; no planner selects another step. */
public final class RootLifePublicStepProducts {
    private static final List<OperationKey> STEPS=List.of(new OperationKey("life-advance"),new OperationKey("life-advance-one-day"));
    private RootLifePublicStepProducts() { }

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);var context=actual.context();var life=actual.remainingDomains().life();
        var commands=life.commands();var replay=life.replay();var composite=life.composite();
        life.requireContext(context);
        var sources=new LinkedHashSet<ExactRef>();
        for(Class<?> type:List.of(RootLifePublicStepProducts.class,RootLifeRuntimeFactory.class,
                RootLifeAdvancePublicResult.class,RootPublicStepExecution.class))
            sources.add(actual.publicStepSource(Module.LOCAL_SERVICE,type));
        for(Class<?> type:List.of(LifeAdvanceCommands.class,LifeAdvanceComposite.class,
                LifeAdvanceRootReplay.class,LifeAdvanceEvidence.class))
            sources.add(actual.publicStepSource(Module.APPLICATION,type));
        RootPublicStepExecution.OwnerGuard owner=identical->{
            if(identical!=context||actual.context()!=context||actual.remainingDomains().life()!=life
                    ||life.commands()!=commands||life.replay()!=replay||life.composite()!=composite)
                throw new IOException("Life EXECUTE lost its identical installed Root/composite/command/replay owner");
            life.requireContext(context);
            StrictJson.require(life.installation().composites().size()==1
                    &&life.installation().composites().getFirst().handler()==composite
                    &&STEPS.stream().allMatch(composite::supports),"Life EXECUTE requires its actual installed two-step composite");
        };
        return bind(owner,List.copyOf(sources),(original,frame,known,same,caller)->{
            context.writer().requireSession(same);owner.requireContext(context);
            String id=RootPublicStepExecution.actionId(original,caller);
            // The sole producer owns provisional fields, empty reservations, native plan and readiness.
            ActionCommand command=commands.preparePublic(original,caller.step(),id);
            requirePrepared(original,caller,command);context.writer().requireSession(same);return command;
        },(receipt,archive,same,caller)->{
            context.writer().requireSession(same);owner.requireContext(context);
            ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),receipt,archive);
            // No ACTION publication or original returned material means unavailable. UNKNOWN is never
            // turned into a result, a new preparation, a retry, or a fabricated clock observation.
            return RootPublicStepExecution.legacyResult(receipt,archive,same,caller,(originalCall,numeric)->{
                replay.verify(same.head(),receipt,archive);
                var recorded=replay.readRecorded(receipt,archive);
                var original=recorded.originalCompatible().orElseThrow(
                        ()->new IOException("Life has no retained original compatible report; the original action must not be replayed"));
                StrictJson.require(DriverJson.object(numeric.bytes(),RawJson.MAXIMUM_BYTES)
                        .equals(DriverJson.object(original.body().bytes(),RawJson.MAXIMUM_BYTES)),
                        "public Life result differs from its installed owning archived replay");
                return RootLifeAdvancePublicResult.encode(numeric);
            });
        });
    }

    /** Typed protocol seam only. These callbacks cannot construct a Root, Ready, permit or original result. */
    static List<RootPublicStepExecution.Product> bind(RootPublicStepExecution.OwnerGuard owner,List<ExactRef> sources,
            RootPublicStepExecution.ActionPreparation preparation,RootPublicStepExecution.ActionResult result) {
        Objects.requireNonNull(owner);sources=List.copyOf(sources);Objects.requireNonNull(preparation);Objects.requireNonNull(result);
        var products=new ArrayList<RootPublicStepExecution.Product>();
        for(OperationKey step:STEPS) {
            StrictJson.require(LifeAdvanceComposite.accepts(step.value()),"public Life roster differs from its sole composite selector");
            products.add(new RootPublicStepExecution.Action("original-life:"+step.value(),step::equals,owner,
                    (original,frame,known,same,caller)->{
                        requireCaller(step,caller);caller.requireCurrent(original);
                        var command=Objects.requireNonNull(preparation.prepare(original,frame,known,same,caller));
                        requirePrepared(original,caller,command);return command;
                    },(receipt,archive,same,caller)->{
                        requireCaller(step,caller);
                        StrictJson.require(receipt.command().operation().equals(step),"Life public result crossed its caller's actual step");
                        return Objects.requireNonNull(result.present(receipt,archive,same,caller));
                    },sources));
        }
        return List.copyOf(products);
    }
    private static void requireCaller(OperationKey expected,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Objects.requireNonNull(caller);
        if(!expected.equals(caller.step())||caller.h2743())
            throw new IOException("Life EXECUTE requires the exact original step and no foreign before-frame claim");
    }
    private static void requirePrepared(PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller,ActionCommand command) {
        StrictJson.require(command.actionId().equals(RootPublicStepExecution.actionId(original,caller))
                &&command.operation().equals(caller.step())&&command.before().equals(original.before())
                &&command.source().equals(original.source())&&command.sessionId().equals(original.sessionId())
                &&command.deadline().equals(original.deadline()),"Life public preparation changed caller identity, source, frame, step or deadline");
    }
}
