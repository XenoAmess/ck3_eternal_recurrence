package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Typed construction edges. Missing actual producers always reject, including during frontend startup. */
final class RootDeferredAuthorities {
    private RootDeferredAuthorities() { }
    static final class ActionGuard implements ActionPorts.GuardPort {
        private volatile ActionPorts.GuardPort actual;
        synchronized void bind(ActionPorts.GuardPort next) { if (actual != null) throw new IllegalStateException("gameplay guard already bound"); actual = Objects.requireNonNull(next); }
        @Override public GuardEvidence verify(WriterContracts.Head head, ActionCommand command) {
            ActionPorts.GuardPort value = actual; if (value == null) return RootFixtureQualifiedScope.required().guard(head,command); return value.verify(head, command);
        }
    }
    static final class ReadGuard implements PlanningReadCoordinator.ReadGuardPort {
        private volatile PlanningReadCoordinator.ReadGuardPort actual;
        private volatile PlanningReadCoordinator.ReadGuardPort bootstrap;
        boolean bootstrapOnly() { return actual == null && bootstrap != null; }
        synchronized void bindBootstrap(PlanningReadCoordinator.ReadGuardPort next) {
            if (actual != null || bootstrap != null) throw new IllegalStateException("initial gameplay read guard already installed or closed");
            bootstrap = Objects.requireNonNull(next);
        }
        synchronized void bind(PlanningReadCoordinator.ReadGuardPort next) { if (actual != null) throw new IllegalStateException("gameplay read guard already bound"); actual = Objects.requireNonNull(next); }
        @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,
                ReadContract<?> contract,java.util.function.Supplier<T> work) {
            Objects.requireNonNull(work);
            PlanningReadCoordinator.ReadGuardPort value=actual;
            if(value!=null) {
                try { return value.withOriginalReadSource(head,request,contract,work); }
                finally { StrictJson.require(actual==value,"original read source changed its admitted gameplay guard"); }
            }
            var fixture=RootFixtureQualifiedScope.optional();
            if(fixture.isPresent()) {
                var retained=fixture.orElseThrow();
                try { return retained.withOriginalReadSource(head,request,contract,work); }
                finally { StrictJson.require(actual==null&&RootFixtureQualifiedScope.required()==retained,
                        "unadmitted fixture read source escaped its original callback"); }
            }
            PlanningReadCoordinator.ReadGuardPort entry=bootstrap;
            if(entry==null)throw new IllegalStateException("actual complete Driver/readiness read guard is absent");
            try { return entry.withOriginalReadSource(head,request,contract,work); }
            finally { StrictJson.require(actual==null&&bootstrap==entry,"bootstrap read source changed its original entry guard"); }
        }
        @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
            PlanningReadCoordinator.ReadGuardPort value=actual;
            if(value==null)throw new IllegalStateException("bootstrap entry has no admitted current-original gameplay read guard");
            return value.verifyOriginalCurrent(head,request,contract);
        }
        @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            PlanningReadCoordinator.ReadGuardPort value = actual;
            if (value != null) return value.verify(head, request, contract);
            if(RootFixtureQualifiedScope.optional().isPresent())return RootFixtureQualifiedScope.required().readGuard(head,request,contract);
            PlanningReadCoordinator.ReadGuardPort entry = bootstrap;
            if (entry == null) throw new IllegalStateException("actual complete Driver/readiness read guard is absent");
            return entry.verify(head, request, contract);
        }
    }
    static final class TerminalActions implements ActionPorts.GuardPort {
        private volatile RootLifecycleActionGuard actual;
        synchronized void bind(RootLifecycleActionGuard next) {
            if (actual != null) throw new IllegalStateException("actual terminal action authority already bound"); actual = Objects.requireNonNull(next);
        }
        @Override public GuardEvidence verify(WriterContracts.Head head, ActionCommand command) {
            RootLifecycleActionGuard retained = actual;
            if (retained == null) throw new IllegalStateException("actual terminal physical source authority is absent"); return retained.verify(head, command);
        }
    }
    static final class TerminalReads implements PlanningReadCoordinator.ReadGuardPort {
        private volatile RootLifecycleReadGuard actual;
        synchronized void bind(RootLifecycleReadGuard next) {
            if (actual != null) throw new IllegalStateException("actual terminal read authority already bound"); actual = Objects.requireNonNull(next);
        }
        @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            RootLifecycleReadGuard retained = actual;
            if (retained == null) throw new IllegalStateException("actual terminal read source authority is absent"); return retained.verify(head, request, contract);
        }
    }
    static final class Intent implements ActionPorts.IntentPreparationPort {
        private volatile RootDomainIntentPreparation actual;
        synchronized void bind(RootDomainIntentPreparation next) { if (actual != null) throw new IllegalStateException("gameplay pending producers already bound"); actual = Objects.requireNonNull(next); }
        @Override public void prepare(ContinuityStorePort.Session borrowed, ActionCommand command) {
            if (command.origin() instanceof CommandOrigin.Frontend) return;
            RootDomainIntentPreparation value = actual; if (value == null) {RootFixtureQualifiedScope.required().prepare(borrowed,command);return;} value.prepare(borrowed, command);
        }
    }
    static final class Attempts implements ActionPorts.AttemptCompletionPort {
        private final org.xar.ck3.control.continuity.writer.ContinuityWriter writer;
        private volatile org.xar.ck3.control.application.driver.DriverCapabilityRuntime actual;
        private org.xar.ck3.control.application.driver.DriverActionHistoryPublisher histories;
        Attempts(org.xar.ck3.control.continuity.writer.ContinuityWriter writer) { this.writer = Objects.requireNonNull(writer); }
        synchronized void bind(org.xar.ck3.control.application.driver.DriverCapabilityRuntime next,
                org.xar.ck3.control.application.driver.DriverActionHistoryPublisher histories) {
            Objects.requireNonNull(next);Objects.requireNonNull(histories);
            if (actual != null) throw new IllegalStateException("actual attempt cache and history observers already bound");
            this.histories=histories;actual=next;
        }
        @Override public void afterAttempt(ContinuityStorePort.Session borrowed, ActionReceipt receipt) {
            try {
                writer.requireSession(borrowed);
                org.xar.ck3.control.application.driver.DriverCapabilityRuntime runtime = actual;
                if (runtime != null) { runtime.afterMarriageAttempt(borrowed, receipt); histories.completed(borrowed,receipt);return; }
                if (receipt.command().origin() instanceof CommandOrigin.Frontend) return;
                RootFixtureQualifiedScope.required().completed(borrowed,receipt);
            } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }
    }
    static final class DerivedReplay implements org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.DerivedGuardVerifier {
        private final org.xar.ck3.control.continuity.writer.ContinuityWriter writer;
        DerivedReplay(org.xar.ck3.control.continuity.writer.ContinuityWriter writer){this.writer=Objects.requireNonNull(writer);}
        private volatile org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.DerivedGuardVerifier actual;
        synchronized void bind(org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.DerivedGuardVerifier next) {
            if(actual!=null)throw new IllegalStateException("actual derived-child original verifier already bound");actual=Objects.requireNonNull(next);
        }
        @Override public void verify(WriterContracts.Head head,ActionReceipt child,GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
            if(RootFixtureGuardEvidence.matches(guard,archive)){
                try{RootFixtureGuardEvidence.verify(head,child,guard,archive,writer.borrowedSession());return;}
                catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            }
            var retained=actual;
            if(retained==null)throw new IllegalStateException("actual derived-child ancestry verifier is absent");retained.verify(head,child,guard,archive);
        }
    }
    static final class ReadBarrier implements ActionPorts.IntentBarrierPort {
        private volatile org.xar.ck3.control.application.driver.DriverReadHistoryPublisher actual;
        synchronized void bind(org.xar.ck3.control.application.driver.DriverReadHistoryPublisher next) {
            if(actual!=null)throw new IllegalStateException("original READ barrier already bound");actual=Objects.requireNonNull(next);
        }
        @Override public void check(ContinuityStorePort.Session same,ActionCommand command) {
            var installed=actual;
            if(installed!=null){installed.requireBeforeIntent(same,command);return;}
            if(command.origin() instanceof CommandOrigin.Frontend)return;
            RootFixtureQualifiedScope.required().barrier(same,command);
        }
    }
    static final class Transition implements WriterContracts.TransitionAuthority {
        private volatile WriterContracts.TransitionAuthority actual;
        synchronized void bind(WriterContracts.TransitionAuthority next) { if (actual != null) throw new IllegalStateException("domain transition already bound"); actual = Objects.requireNonNull(next); }
        private WriterContracts.TransitionAuthority required() throws IOException {
            WriterContracts.TransitionAuthority value = actual; if (value == null) throw new IOException("actual domain reducer is absent during frontend startup"); return value;
        }
        @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
            throw new IOException("actual original locked Head required");
        }
        @Override public String revalidate(WriterContracts.Head head, WriterContracts.Request request) throws IOException { return required().revalidate(head, request); }
        @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) throws IOException { return required().reduce(predecessor, request); }
    }
}

