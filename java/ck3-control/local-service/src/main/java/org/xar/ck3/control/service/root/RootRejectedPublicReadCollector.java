package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.reads.PlanningPublicReadCollection;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;

/** Same-Root cached readback for an actual rejected query. It cannot observe, retry, issue an action or mint a Known read. */
public final class RootRejectedPublicReadCollector {
    private RootRejectedPublicReadCollector() { }
    public sealed interface Result<T> permits Positive,Rejected { }
    public static final class Positive<T> implements Result<T> {
        private final PlanningReadResult.Known<T> actual;
        private Positive(PlanningReadResult.Known<T> actual){this.actual=actual;}
        public PlanningReadResult.Known<T> actual(){return actual;}
    }
    /** Constructor is private: callers receive only the actual coordinator token joined to the actual physical cached scope. */
    public static final class Rejected<T> implements Result<T> {
        private final RootRuntimeContext context;
        private final Session same;
        private final Complete before;
        private final Complete readback;
        private final PlanningPublicReadCollection.Rejected<T> original;
        private final Thread thread=Thread.currentThread();
        private final String head;
        private boolean active=true;
        private Rejected(RootRuntimeContext context,Session same,Complete before,Complete readback,
                PlanningPublicReadCollection.Rejected<T> original)throws IOException {
            this.context=context;this.same=same;this.before=before;this.readback=readback;this.original=original;head=same.head().digest();
        }
        public PlanningPublicReadCollection.Rejected<T> original()throws IOException{requireCurrent();return original;}
        public Complete before()throws IOException{requireCurrent();return before;}
        public Complete readback()throws IOException{requireCurrent();return readback;}
        public void requireCurrent()throws IOException {
            require(active&&thread==Thread.currentThread(),"rejected public READ escaped its owning callback/thread lifetime");
            requireContext(context,same,before);
            require(head.equals(same.head().digest()),"rejected public READ changed its original writer head");
            original.requireOriginal(same,context.archive().withSession(same));
            context.collector().requireHeldFrame(same,readback);
        }
        /** Optional replay witness. This records DATA artifacts only, never a command-history row or a new attempt. */
        public PlanningPublicReadCollection.Recorded record()throws IOException {
            requireCurrent();var result=original.record(same,context.readCatalog(),context.archive().withSession(same));requireCurrent();return result;
        }
    }
    @FunctionalInterface public interface ResultWork<T,R> { R present(Result<T> actual)throws IOException; }
    /** The supplied work invokes the existing installed domain collection once; presentation stays inside the exact cached-frame scope. */
    public static <T,R> R collect(RootRuntimeContext context,Complete held,Session same,
            PlanningPublicReadCollection.ReadWork<T> actualCollection,ResultWork<T,R> present)throws IOException {
        Objects.requireNonNull(actualCollection);Objects.requireNonNull(present);requireContext(context,same,held);
        OutcomeArchive bound=context.archive().withSession(same);
        var result=PlanningPublicReadCollection.collect(same,context.readCatalog(),bound,actualCollection);
        if(result instanceof PlanningPublicReadCollection.Positive<T> positive){
            requireContext(context,same,held);R value=present.present(new Positive<>(positive.actual()));requireContext(context,same,held);return value;
        }
        var rejected=(PlanningPublicReadCollection.Rejected<T>)result;
        // This sole physical source entry reads already received Native bytes and the same frozen Driver/SEM.
        // It neither captures nor pumps the native endpoint, and cannot borrow STATUS_ONLY readiness.
        return context.collector().withHeldReadScope(same,context.collector().identity(),rejected.request().deadline(),readback->{
            requireContext(context,same,held);context.collector().requireHeldFrame(same,readback);
            rejected.requireOriginal(same,bound);
            verifyReadback(held,readback,rejected.request(),rejected.before(),same,bound,context.frameLoader());
            var qualified=new Rejected<>(context,same,held,readback,rejected);
            try {qualified.requireCurrent();R value=present.present(qualified);qualified.requireCurrent();return value;}
            finally {qualified.active=false;}
        });
    }
    @FunctionalInterface public interface RecordedWork<T> {
        T read(PlanningPublicReadCollection.Recorded original,Complete before,Complete actualReadback)throws IOException;
    }
    /** Cold original DATA replay gains no failed-attempt token. Actual same-Root cache qualification must be obtained again. */
    public static <T> T withRecorded(RootRuntimeContext context,Complete held,Session same,RawJson metadata,java.time.Instant currentDeadline,
            RecordedWork<T> work)throws IOException {
        Objects.requireNonNull(work);requireContext(context,same,held);var bound=context.archive().withSession(same);
        var original=PlanningPublicReadCollection.replay(context.readCatalog(),bound,metadata);
        return context.collector().withHeldReadScope(same,context.collector().identity(),Objects.requireNonNull(currentDeadline),readback->{
            requireContext(context,same,held);context.collector().requireHeldFrame(same,readback);
            verifyReadback(held,readback,original.request(),original.before(),same,bound,context.frameLoader());
            T result=work.read(original,held,readback);
            context.collector().requireHeldFrame(same,readback);requireContext(context,same,held);return result;
        });
    }
    /** Sole typed DATA matcher used by the production scopes and the actual software collector regression. No Root qualification is returned. */
    static void verifyReadback(Complete held,Complete actualReadback,PlanningReadRequest request,PlanningReadGuard before,
            Session same,OutcomeArchive bound,org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames)throws IOException {
        Objects.requireNonNull(held);Objects.requireNonNull(actualReadback);Objects.requireNonNull(request);Objects.requireNonNull(before);
        require(request.origin() instanceof CommandOrigin.Gameplay&&before.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&before.paused()&&before.mapReady()&&before.playerAlive(),"rejected READ requires its original living paused ordinary guard");
        require(request.before().equals(held.identity())&&request.source().equals(held.source())&&request.sessionId().equals(held.sessionId())
                &&before.binding().source().equals(held.source())&&before.binding().sessionId().equals(held.sessionId())
                &&before.binding().operation().equals(request.operation())&&before.originalBindingSha256().equals(held.fullBindingSha256()),
                "rejected READ crossed its original complete public planning frame/source/session");
        RootGuardEvidence.requireHistory(before.binding(),bound,same);
        Complete replayed=RootGuardEvidence.loadFrame(before.binding(),bound,frames);
        require(replayed.identity().equals(held.identity())&&replayed.source().equals(held.source())&&replayed.sessionId().equals(held.sessionId())
                &&replayed.connectionGeneration().equals(held.connectionGeneration())&&replayed.fullBindingSha256().equals(held.fullBindingSha256())
                &&replayed.semantic().equals(held.semantic()),"rejected READ complete before frame no longer matches its original archived Native/Driver/SEM");
        require(actualReadback.identity().equals(held.identity())&&actualReadback.source().equals(held.source())
                &&actualReadback.sessionId().equals(held.sessionId())&&actualReadback.connectionGeneration().equals(held.connectionGeneration())
                &&actualReadback.fullBindingSha256().equals(held.fullBindingSha256())&&actualReadback.semantic().equals(held.semantic()),
                "rejected READ crossed its exact already received physical owner/frame/SEM readback");
    }
    private static void requireContext(RootRuntimeContext context,Session same,Complete held)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(same);Objects.requireNonNull(held);
        context.writer().requireSession(same);context.game().verify();
        var root=context.core().sessionAccess().current();
        require(root==context.actions()&&root.ownedBy(context.core())&&!root.isRetired()&&root.writer()==context.writer()
                &&root.archive()==context.archive()&&root.driver()==context.adopted(),"rejected READ crossed the actual current Core/Root/writer/archive");
        require(held.source().equals(context.source())&&held.sessionId().equals(root.identity().sessionId())
                &&held.identity().game().equals(root.identity().game())&&context.adopted().session().game().equals(root.identity().game()),
                "rejected READ belongs to another actual Root physical Game/source/session");
        context.collector().requireHeldFrame(same,held);
    }
    private static void require(boolean value,String reason){StrictJson.require(value,reason);}
}
