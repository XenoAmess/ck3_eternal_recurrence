package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Ordinary read stages use the current runtime's original writer and actual Army service, without an action intent. */
public final class OrdinaryRetreatRuntime implements OrdinaryActiveRetreatPolicy.StateReader,OrdinaryActiveRetreatPolicy.RetreatReadPort {
    private final RootRuntimeContext runtime;
    private final ArmyRetreatDomain domain;
    private final ArmyRetreatService service;
    private final ArmyRetreatFrames frames;
    public OrdinaryRetreatRuntime(RootRuntimeContext currentRuntime,ArmyRetreatDomain originalDomain,
            ArmyRetreatService actualService,ArmyRetreatFrames actualFrames) {
        runtime=Objects.requireNonNull(currentRuntime);domain=Objects.requireNonNull(originalDomain);
        service=Objects.requireNonNull(actualService);frames=Objects.requireNonNull(actualFrames);
    }
    @Override public OrdinaryActiveRetreatPolicy.DomainRead read(PlanningRequest request) {
        try {return locked(request,session->runtime.collector().currentPlanning(session,request,request.deadline(),
                (original,lease)->new OrdinaryActiveRetreatPolicy.KnownDomain(original.before(),domain.read(session).state())));}
        catch(IOException|IllegalArgumentException failure){return new OrdinaryActiveRetreatPolicy.UnavailableDomain(failure.getMessage());}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();return new OrdinaryActiveRetreatPolicy.UnavailableDomain("current retreat domain observation interrupted");}
    }
    @Override public OrdinaryActiveRetreatPolicy.ReadResult preview(PlanningRequest request,int selected,int target) {
        try {return locked(request,session->{
            current(request);
            var input=new ArmyCalls.RetreatPreview(new ArmyCalls.Revision(new Present<>(request.before().frame().revision())),new PublicUnitId(selected),new PositiveId(target));
            var result=service.preview(session,input,request.deadline());
            requireCurrent(request,result.captured().before());requireCurrent(request,result.captured().after());
            var evidence=new ArrayList<ExactRef>();evidence.add(result.durable().original().reference().payload());
            var archive=runtime.archive().withSession(session);
            evidence.add(archive.readReferenceOf(result.captured().control().receipt()));
            result.captured().route().ifPresent(route->evidence.add(archive.readReferenceOf(route.receipt())));
            return new OrdinaryActiveRetreatPolicy.ReadCompleted(request.before(),result.captured().after().source(),evidence);
        });}
        catch(IOException|IllegalArgumentException|IllegalStateException failure){return new OrdinaryActiveRetreatPolicy.ReadUnavailable(message(failure));}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();return new OrdinaryActiveRetreatPolicy.ReadUnavailable("actual retreat preview interrupted; original reducer state retained");}
    }
    @Override public OrdinaryActiveRetreatPolicy.ReadResult observe(PlanningRequest request) {
        try {return locked(request,session->{
            current(request);var result=service.observe(session,request.deadline());requireCurrent(request,result.current());
            var archive=runtime.archive().withSession(session);var evidence=new ArrayList<ExactRef>();
            evidence.add(result.durable().original().reference().payload());for(var read:result.originals())evidence.add(archive.readReferenceOf(read));
            return new OrdinaryActiveRetreatPolicy.ReadCompleted(request.before(),result.current().source(),evidence);
        });}
        catch(IOException|IllegalArgumentException|IllegalStateException failure){return new OrdinaryActiveRetreatPolicy.ReadUnavailable(message(failure));}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();return new OrdinaryActiveRetreatPolicy.ReadUnavailable("actual retreat lifecycle observation interrupted; UNKNOWN retained");}
    }
    private ArmyRetreatFrames.Current current(PlanningRequest request)throws IOException,InterruptedException {
        runtime.requireCurrent(request.deadline());var actual=frames.current(request.deadline());requireCurrent(request,actual);return actual;
    }
    private static void requireCurrent(PlanningRequest request,ArmyRetreatFrames.Current actual) {
        StrictJson.require(actual.actual().identity().equals(request.before())&&actual.actual().source().equals(request.source())
                &&actual.actual().sessionId().equals(request.sessionId())&&actual.actual().semantic().equals(request.observations().snapshot()),
                "ordinary retreat request differs from current complete native/Driver evidence");
    }
    @FunctionalInterface private interface Work<T>{T apply(ContinuityStorePort.Session session)throws IOException,InterruptedException;}
    private <T>T locked(PlanningRequest request,Work<T> work)throws IOException,InterruptedException {
        runtime.requireCurrent(request.deadline());
        try{return runtime.withSession(session->{try{return work.apply(session);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new InterruptedIo(interrupted);}});}
        catch(InterruptedIo interrupted){throw (InterruptedException)interrupted.getCause();}
    }
    private static String message(Exception failure){return failure.getMessage()==null?failure.getClass().getSimpleName():failure.getMessage();}
    private static final class InterruptedIo extends IOException {
        private static final long serialVersionUID=1L;
        InterruptedIo(InterruptedException cause){super(cause);}
    }
}
