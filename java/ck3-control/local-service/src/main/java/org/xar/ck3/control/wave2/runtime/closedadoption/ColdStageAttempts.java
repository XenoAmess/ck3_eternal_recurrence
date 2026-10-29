package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;
import java.util.EnumMap;
import java.util.Objects;

/** Shared resource-submission state only. It supplies no Root approval, writer lock or Native authority. */
final class ColdStageAttempts {
    enum State { READY, SUBMITTED, SUCCEEDED, UNKNOWN }
    @FunctionalInterface interface BeforeSubmission { void verify() throws IOException,InterruptedException; }
    @FunctionalInterface interface Submission<T> { T run() throws IOException,InterruptedException; }
    private final Thread thread=Thread.currentThread();
    private final EnumMap<RootColdStageReview.Stage,State> states=new EnumMap<>(RootColdStageReview.Stage.class);

    State state(RootColdStageReview.Stage stage) { requireThread();return states.getOrDefault(stage,State.READY); }
    boolean submitted(RootColdStageReview.Stage stage) { return state(stage)!=State.READY; }
    void requireAvailable(RootColdStageReview.Stage stage) throws IOException {
        if(submitted(stage)) { throw new IOException("original cold stage already submitted; UNKNOWN and completed submissions are never replayed: "+stage); }
    }
    <T> T submit(RootColdStageReview.Stage stage,BeforeSubmission before,Submission<T> submission)
            throws IOException,InterruptedException {
        Objects.requireNonNull(stage);Objects.requireNonNull(before);Objects.requireNonNull(submission);
        requireAvailable(stage);before.verify();requireAvailable(stage);
        states.put(stage,State.SUBMITTED); // Write before entering CREATE / loader. A throw cannot undo this fact.
        try { T result=submission.run();states.put(stage,State.SUCCEEDED);return result; }
        catch(IOException|InterruptedException|RuntimeException|Error failure) { states.put(stage,State.UNKNOWN);throw failure; }
    }
    private void requireThread() {
        if(Thread.currentThread()!=thread) { throw new IllegalStateException("same actual cold submission thread required"); }
    }
}
