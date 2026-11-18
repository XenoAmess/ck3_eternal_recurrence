package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;

/** Publishes one complete batch observation through the runtime's existing bounded guarded sink.
 * Telemetry failure is visible after the original complete report; it cannot replay a batch. */
final class RootWorkerBatchLog {
    @FunctionalInterface interface Sink { void append(byte[] completeLine)throws IOException; }
    @FunctionalInterface interface Observation { void write(byte[] originalBody)throws IOException; }
    private RootWorkerBatchLog(){ }

    static void publish(byte[] originalBody,Sink managed,Observation observation)throws IOException {
        Objects.requireNonNull(originalBody);Objects.requireNonNull(managed);Objects.requireNonNull(observation);
        if(originalBody.length==0||originalBody.length>=RootOrdinaryRuntimeAssembly.MAX_WORKER_BATCH_LOG_BYTES) {
            var failure=new IOException("complete worker batch row exceeds the finite log byte budget");
            observeFailure(originalBody,observation,failure);throw failure;
        }
        byte[] line=Arrays.copyOf(originalBody,originalBody.length+1);line[originalBody.length]=10;
        try{managed.append(line);}
        catch(IOException|RuntimeException failure) {
            observeFailure(originalBody,observation,failure);throw failure;
        }
        observation.write(originalBody);
    }
    private static void observeFailure(byte[] original,Observation observation,Exception failure) {
        try{observation.write(original);}
        catch(IOException|RuntimeException outputFailure){if(outputFailure!=failure)failure.addSuppressed(outputFailure);}
    }
}
