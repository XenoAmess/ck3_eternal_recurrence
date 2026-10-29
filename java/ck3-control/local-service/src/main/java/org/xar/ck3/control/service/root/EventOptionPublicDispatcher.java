package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;

/** One public selection enters the genuine current Root planning scope and its sole action writer. */
public final class EventOptionPublicDispatcher {
    /** Root resolves its current domain catalog, including after a committed session replacement. */
    @FunctionalInterface public interface RuntimeResolver {
        EventRuntimeInstaller resolve(RootApplicationSession actualCurrent) throws IOException;
    }
    private final RootSessionAccess sessions;
    private final RuntimeResolver events;
    private final Clock clock;
    private final Duration timeout;

    public EventOptionPublicDispatcher(RootSessionAccess sessions, RuntimeResolver events, Clock clock, Duration timeout) {
        this.sessions = Objects.requireNonNull(sessions); this.events = Objects.requireNonNull(events);
        this.clock = Objects.requireNonNull(clock); this.timeout = Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isZero() && !timeout.isNegative() && timeout.compareTo(Duration.ofMinutes(30)) <= 0,
                "finite positive public event deadline required");
    }

    /** An exception propagates the original outcome; this method never observes again or resubmits. */
    public EventOptionPublicResponse.Payload select(EventOptionPublicCodec.Request request) throws InterruptedException {
        Objects.requireNonNull(request);
        try {
            return sessions.withCurrent(root -> {
                EventRuntimeInstaller sameEvents = Objects.requireNonNull(events.resolve(root));
                return root.executePublicPlanningAction(clock.instant().plus(timeout), (actual, frame, driver, same) -> {
                    StrictJson.require(actual.before().equals(frame.identity()) && actual.source().equals(frame.source())
                                    && actual.sessionId().equals(frame.sessionId()),
                            "public event selection must retain its actual Root planning identity and source");
                    if (request.expectedRevision().presence() == EventOptionPublicCodec.Presence.VALUE)
                        StrictJson.require(request.expectedRevision().value().equals(actual.before().frame().revision()),
                                "public event expected_revision differs from the actual planning scope; no option was submitted");
                    Optional<Integer> instance = request.eventInstanceId().presence() == EventOptionPublicCodec.Presence.VALUE
                            ? Optional.of(request.eventInstanceId().value()) : Optional.empty();
                    return sameEvents.preparePublicSelection(actual, request.optionNumber().value(), instance);
                }, (receipt, scopedArchive, same) -> EventOptionPublicResponse.capture(receipt, scopedArchive,
                        sameEvents.publicSelectionResult(receipt)));
            });
        } catch (IOException failure) {
            throw new UncheckedIOException("public event selection did not produce a presentable original result; retain its actual outcome and do not resend", failure);
        }
    }

    public PublicBindings.TypedBinding<EventOptionPublicCodec.Request, EventOptionPublicResponse.Payload> register(
            PublicBindings sameRegistry, ExactRef actualThisSource) {
        Objects.requireNonNull(actualThisSource);
        StrictJson.require(actualThisSource.bytes() > 0, "actual public event dispatcher source required");
        return Objects.requireNonNull(sameRegistry).register(PublicMethod.SELECT_EVENT_OPTION,
                EventOptionPublicCodec.Request.class, EventOptionPublicResponse.Payload.class, this::select,
                EventOptionPublicCodec::decode, EventOptionPublicResponse.Payload::original,
                new PublicRoutes.Target(getClass().getName(), "select", actualThisSource), PublicRoutes.Status.DELEGATED,
                "actual current Root complete planning input, same event instance and native displayed option; sole writer and original archived effect result");
    }
}
