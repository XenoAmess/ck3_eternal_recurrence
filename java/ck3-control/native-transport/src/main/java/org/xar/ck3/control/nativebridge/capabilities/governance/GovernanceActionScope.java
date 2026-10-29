package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.nativebridge.NativeGameTransport;

/** A scope around the existing coordinator, never another mutation authority or continuity writer. */
public final class GovernanceActionScope implements ActionCoordinatorPort {
    @FunctionalInterface public interface SessionWork<T> { T run(ContinuityStorePort.Session session) throws IOException, InterruptedException; }
    public interface SessionAccess { <T> T withSession(ActionCommand command, SessionWork<T> work) throws IOException, InterruptedException; }
    public static final class Context {
        private final Thread owner = Thread.currentThread();
        private final ActionCommand command;
        private final ContinuityStorePort.Session session;
        private final Optional<NativeGameTransport.MailboxScope> mailbox;
        private final Path writerLock;
        private boolean active = true;
        private final java.util.ArrayList<PlanningReadReceipt> preflight = new java.util.ArrayList<>();
        private Context(ActionCommand command, ContinuityStorePort.Session session, Optional<NativeGameTransport.MailboxScope> mailbox, Path writerLock) {
            this.command = command; this.session = session; this.mailbox = mailbox; this.writerLock = writerLock;
        }
        public ContinuityStorePort.Session session(ActionCommand expected) {
            current(expected); try { session.requireWriter(writerLock); } catch (IOException failure) { throw new UncheckedIOException(failure); } return session;
        }
        public NativeGameTransport.MailboxScope mailbox(ActionCommand expected) { current(expected); return mailbox.orElseThrow(() -> new IllegalStateException("original Council action has no live mailbox scope; no resubmit/replay")); }
        public void retainPreflight(ActionCommand expected, java.util.List<PlanningReadReceipt> originals) {
            current(expected); StrictJson.require(preflight.isEmpty() && !originals.isEmpty() && originals.size() <= 3002, "one bounded actual Council preflight chain required");
            preflight.addAll(java.util.List.copyOf(originals));
        }
        public java.util.List<PlanningReadReceipt> preflight(ActionCommand expected) { current(expected); return java.util.List.copyOf(preflight); }
        private void current(ActionCommand expected) {
            StrictJson.require(active && owner == Thread.currentThread() && CURRENT.get() == this && command.equals(expected), "governance action scope escaped its original thread/command/session");
        }
    }
    private static final ThreadLocal<Context> CURRENT = new ThreadLocal<>();
    private final ActionCoordinatorPort coordinator;
    private final ActionJournal journal;
    private final NativeGameTransport transport;
    private final SessionAccess sessions;
    private final Path originalWriterLock;
    public GovernanceActionScope(ActionCoordinatorPort soleCoordinator, ActionJournal originalJournal, NativeGameTransport transport, SessionAccess sessions, Path originalWriterLock) {
        this.coordinator = Objects.requireNonNull(soleCoordinator); this.journal = Objects.requireNonNull(originalJournal); this.transport = Objects.requireNonNull(transport);
        this.sessions = Objects.requireNonNull(sessions); this.originalWriterLock = Objects.requireNonNull(originalWriterLock);
        StrictJson.require(originalWriterLock.isAbsolute(), "original absolute writer lock required");
    }
    public static Context current(ActionCommand command) {
        Context context = CURRENT.get(); if (context == null) throw new IllegalStateException("Root's borrowed governance action scope is not installed"); context.current(command); return context;
    }
    @Override public ActionReceipt execute(ActionCommand command) {
        try { return sessions.withSession(command, borrowed -> execute(borrowed, command)); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("governance scope interrupted; retained action is never replayed", interrupted); }
        catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    @Override public ActionReceipt execute(ContinuityStorePort.Session borrowed, ActionCommand command) {
        return journal.locked(borrowed, locked -> {
            try {
                borrowed.requireWriter(originalWriterLock);
                // Even INTENT/SUBMITTING/UNKNOWN return the original canonical body. They open no mailbox or fresh preflight.
                if (locked.find(command.actionId()).isPresent()) return coordinator.execute(borrowed, command);
                if (!GovernanceActionPreparation.OPERATIONS.contains(command.operation().value())) return coordinator.execute(borrowed, command);
                if (!command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN))
                    return scoped(command, borrowed, Optional.empty(), () -> coordinator.execute(borrowed, command));
                return transport.withMailbox(command.deadline(), mailbox -> scoped(command, borrowed, Optional.of(mailbox), () -> coordinator.execute(borrowed, command)));
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IllegalStateException("Council scope interrupted; original action cannot be retried", interrupted);
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
            finally { try { borrowed.requireWriter(originalWriterLock); } catch (IOException failure) { throw new UncheckedIOException(failure); } }
        });
    }
    @Override public ActionReceipt reconcile(String actionId) {
        ActionCommand command = journal.locked(locked -> locked.find(actionId).orElseThrow(() -> new IllegalArgumentException("unknown original governance action")).command());
        try { return sessions.withSession(command, borrowed -> reconcile(borrowed, actionId)); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("governance reconciliation interrupted", interrupted); }
        catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    @Override public ActionReceipt reconcile(ContinuityStorePort.Session borrowed, String actionId) {
        return journal.locked(borrowed, locked -> {
            ActionCommand command = locked.find(actionId).orElseThrow(() -> new IllegalArgumentException("unknown original governance action")).command();
            try {
                borrowed.requireWriter(originalWriterLock);
                if (!GovernanceActionPreparation.OPERATIONS.contains(command.operation().value())) return coordinator.reconcile(borrowed, actionId);
                // No new mailbox after UNKNOWN. A separately qualified original-result recovery must be installed first.
                return scoped(command, borrowed, Optional.empty(), () -> coordinator.reconcile(borrowed, actionId));
            } catch (IOException failure) { throw new UncheckedIOException(failure);
            } finally { try { borrowed.requireWriter(originalWriterLock); } catch (IOException failure) { throw new UncheckedIOException(failure); } }
        });
    }
    /** Continuation keeps the original parent Session; it never enters a fresh governance mailbox. */
    @Override public CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token) throws IOException {
        Objects.requireNonNull(token);
        try { return sessions.withSession(token.originalParent(), borrowed -> continueOriginalComposite(borrowed, token)); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IOException("original composite continuation scope interrupted; no replay", interrupted);
        }
    }
    @Override public CompositeContinuationReport continueOriginalComposite(ContinuityStorePort.Session borrowed,
            CompositeContinuationToken token) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(token);
        borrowed.requireWriter(originalWriterLock);
        try {
            return journal.locked(borrowed, locked -> {
                try {
                    borrowed.requireWriter(originalWriterLock);
                    // Central source-owned continuation validates this original token and retained cursor.
                    return coordinator.continueOriginalComposite(borrowed, token);
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
                finally {
                    try { borrowed.requireWriter(originalWriterLock); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                }
            });
        } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }
    private <T> T scoped(ActionCommand command, ContinuityStorePort.Session borrowed, Optional<NativeGameTransport.MailboxScope> mailbox, java.util.function.Supplier<T> work) {
        StrictJson.require(CURRENT.get() == null, "nested governance action scope is not another submit route");
        Context context = new Context(command, borrowed, mailbox, originalWriterLock); Context previous = CURRENT.get(); CURRENT.set(context);
        try { return work.get(); } finally { context.active = false; if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
