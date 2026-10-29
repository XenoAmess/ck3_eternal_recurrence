package org.xar.ck3.control.g2.client;

import java.io.ByteArrayOutputStream;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.Flow;

/** One bounded response subscription, cancelled once on limit/deadline failure. */
final class BoundedG2BodySubscriber implements HttpResponse.BodySubscriber<byte[]> {
    static final class LimitExceeded extends RuntimeException {
        @java.io.Serial private static final long serialVersionUID = 1L;
        LimitExceeded() { super("response exceeded the explicit client byte budget"); }
    }

    private final int maximumBytes;
    private final ByteArrayOutputStream output;
    private final CompletableFuture<byte[]> body = new CompletableFuture<>();
    private Flow.Subscription subscription;
    private long observedBytes;
    private boolean complete;

    BoundedG2BodySubscriber(int maximumBytes) {
        if (maximumBytes < 1) throw new IllegalArgumentException("positive response budget required");
        this.maximumBytes = maximumBytes;
        this.output = new ByteArrayOutputStream(Math.min(maximumBytes, 8192));
    }

    @Override public CompletionStage<byte[]> getBody() { return body; }

    @Override public synchronized void onSubscribe(Flow.Subscription value) {
        Objects.requireNonNull(value, "subscription");
        if (subscription != null || body.isDone()) {
            value.cancel();
            return;
        }
        subscription = value;
        value.request(1);
    }

    @Override public synchronized void onNext(List<ByteBuffer> buffers) {
        if (body.isDone()) return;
        try {
            for (ByteBuffer source : buffers) {
                int incoming = source.remaining();
                observedBytes = Math.addExact(observedBytes, incoming);
                int allowed = Math.min(incoming, maximumBytes - output.size());
                byte[] chunk = new byte[Math.min(allowed, 8192)];
                while (allowed > 0) {
                    int count = Math.min(allowed, chunk.length);
                    source.get(chunk, 0, count);
                    output.write(chunk, 0, count);
                    allowed -= count;
                }
                if (source.hasRemaining()) {
                    abort(new LimitExceeded());
                    return;
                }
            }
            if (subscription != null) subscription.request(1);
        } catch (RuntimeException error) {
            abort(error);
        }
    }

    @Override public synchronized void onError(Throwable error) {
        body.completeExceptionally(Objects.requireNonNull(error, "error"));
    }

    @Override public synchronized void onComplete() {
        if (!body.isDone()) {
            complete = true;
            body.complete(output.toByteArray());
        }
    }

    synchronized void abort(Throwable error) {
        if (body.completeExceptionally(error) && subscription != null) subscription.cancel();
    }

    synchronized byte[] retainedBytes() { return output.toByteArray(); }
    synchronized long observedBytes() { return observedBytes; }
    synchronized boolean complete() { return complete; }
}
