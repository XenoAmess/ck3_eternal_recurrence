package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningWire;
import org.xar.ck3.control.application.planning.family.FamilyNativePreparation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One physical Game's actual planner producer archives full requests before returning family commands. */
public final class RootFamilyPlanningOriginals implements FamilyNativePreparation.PlanningOriginalCapture {
    private static final int MAX_PLANNING_ORIGINAL_BYTES=Math.min(PlanningWire.MAX_BYTES,WriterContracts.MAX_PIN_BYTES);
    private final RootRuntimeContext context;
    private final LinkedHashMap<String,ExactRef> retained=new LinkedHashMap<>();
    public RootFamilyPlanningOriginals(RootRuntimeContext actual) {context=Objects.requireNonNull(actual);}
    public void requireContext(RootRuntimeContext actual) {StrictJson.require(context==actual,"family planning originals crossed physical Game context");}
    @Override public void capture(PlanningRequest original,ActionCommand command)throws IOException {
        var same=context.borrowedSession();context.writer().requireSession(same);
        context.collector().currentPlanning(same,original,command,command.deadline(),(exact,lease)->{
            FamilyNativePreparation.requireCommandFrame(command,lease.frame().semantic());
            ExactRef ref=context.archive().preserveArtifact(same,PlanningWire.encodeRequest(exact),MAX_PLANNING_ORIGINAL_BYTES);
            synchronized(retained) {
                String key=key(command);ExactRef prior=retained.putIfAbsent(key,ref);
                StrictJson.require(prior==null || prior.equals(ref),"same immutable family command changed its complete captured planning request");
                while(retained.size()>256)retained.remove(retained.keySet().iterator().next());
            }
            return null;
        });
    }
    public ExactRef reference(Session same,ActionCommand command)throws IOException {
        context.writer().requireSession(same);ExactRef ref;
        synchronized(retained) {ref=retained.get(key(command));}
        if(ref==null)throw new IOException("actual family command has no captured complete planning request; intent cannot reconstruct one");
        original(same,command,ref);return ref;
    }
    public PlanningRequest original(Session same,ActionCommand command,ExactRef ref)throws IOException {
        context.writer().requireSession(same);
        var original=PlanningWire.decodeRequest(context.archive().readArtifact(same,ref,MAX_PLANNING_ORIGINAL_BYTES));
        StrictJson.require(original.before().equals(command.before())&&original.source().equals(command.source())
                &&original.sessionId().equals(command.sessionId())&&original.deadline().equals(command.deadline())
                &&original.observations().actionSteps().contains(command.operation()),"archived complete family planning request differs from immutable command");
        FamilyNativePreparation.requireCommandFrame(command,original.observations().snapshot());return original;
    }
    private static String key(ActionCommand command) {return ActionCodec.sha256(ActionCodec.encodeCommand(command));}
}
