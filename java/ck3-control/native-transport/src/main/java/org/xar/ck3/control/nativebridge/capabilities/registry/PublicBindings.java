package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.nio.charset.StandardCharsets;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;

/**
 * Exact Root-installed JSON boundary for the Service inventory.
 * Each executable binding retains one request type, handler and result type.
 * Native admission and world-action authority remain with the guarded handler.
 */
public final class PublicBindings {
    public sealed interface Arguments permits Missing, Null, Value { }
    public record Missing() implements Arguments { }
    public record Null() implements Arguments { }
    public record Value(RawJson original) implements Arguments {
        public Value {
            Objects.requireNonNull(original);
            require(!isNull(original), "explicit JSON null requires the Null argument branch");
        }
    }
    @FunctionalInterface public interface Decoder<Q> { Q decode(Arguments arguments); }
    @FunctionalInterface public interface Encoder<R> { RawJson encode(R result); }

    /** A decoder-bound executable route; inventory declarations alone never implement this interface. */
    public sealed interface BoundBinding permits TypedBinding {
        PublicRoutes.Info info();
        Class<?> requestType();
        Class<?> resultType();
        RawJson invoke(Arguments arguments) throws InterruptedException;
    }
    public static final class TypedBinding<Q,R> implements BoundBinding {
        private final PublicRoutes.TypedRoute<Q,R> route;
        private final Class<Q> requestType;
        private final Class<R> resultType;
        private final Decoder<Q> decoder;
        private final Encoder<R> encoder;
        private TypedBinding(PublicRoutes.TypedRoute<Q,R> route, Class<Q> requestType, Class<R> resultType,
                Decoder<Q> decoder, Encoder<R> encoder) {
            this.route = route; this.requestType = requestType; this.resultType = resultType;
            this.decoder = decoder; this.encoder = encoder;
        }
        public PublicRoutes.TypedRoute<Q,R> route() { return route; }
        @Override public PublicRoutes.Info info() { return route.info(); }
        @Override public Class<Q> requestType() { return requestType; }
        @Override public Class<R> resultType() { return resultType; }
        public Q decode(Arguments arguments) {
            return requestType.cast(Objects.requireNonNull(decoder.decode(Objects.requireNonNull(arguments)),
                    "public request decoder must return a typed value"));
        }
        public R invokeTyped(Q request) throws InterruptedException {
            return resultType.cast(route.invoke(requestType.cast(Objects.requireNonNull(request))));
        }
        public RawJson encode(R result) {
            return Objects.requireNonNull(encoder.encode(resultType.cast(Objects.requireNonNull(result))),
                    "public result encoder must return validated JSON");
        }
        @Override public RawJson invoke(Arguments arguments) throws InterruptedException {
            return encode(invokeTyped(decode(arguments)));
        }
    }
    public record Coverage(List<PublicMethod> installed, List<PublicMethod> unimplemented,
            List<PublicMethod> retired) {
        public Coverage { installed = List.copyOf(installed); unimplemented = List.copyOf(unimplemented); retired = List.copyOf(retired); }
    }
    private final PublicRoutes routes = new PublicRoutes();
    private final EnumMap<PublicMethod,BoundBinding> bindings = new EnumMap<>(PublicMethod.class);
    private volatile boolean frozen;

    public synchronized <Q,R> TypedBinding<Q,R> register(PublicMethod method, Class<Q> requestType,
            Class<R> resultType, PublicRoutes.Handler<Q,R> handler, Decoder<Q> decoder, Encoder<R> encoder,
            PublicRoutes.Target target, PublicRoutes.Status status, String scope) {
        require(!frozen, "public bindings are frozen");
        Objects.requireNonNull(method); Objects.requireNonNull(requestType); Objects.requireNonNull(resultType);
        Objects.requireNonNull(handler); Objects.requireNonNull(decoder); Objects.requireNonNull(encoder);
        require(!requestType.isPrimitive() && !resultType.isPrimitive(), "public request/result must be reference types");
        PublicRoutes.TypedRoute<Q,R> route = routes.register(method, requestType, request -> {
            require(frozen, "public route cannot execute before complete Root freeze");
            return resultType.cast(Objects.requireNonNull(handler.invoke(request),
                    "public handler must return its registered result type"));
        }, target, status, scope);
        TypedBinding<Q,R> binding = new TypedBinding<>(route, requestType, resultType, decoder, encoder);
        bindings.put(method, binding);
        return binding;
    }
    /** A subset is explicit application scope, never an assertion that all 235 live methods exist. */
    public synchronized void freeze(Set<PublicMethod> required) {
        require(!frozen, "public bindings are already frozen");
        routes.freeze(List.copyOf(Objects.requireNonNull(required)));
        frozen = true;
    }
    public synchronized Optional<BoundBinding> lookup(PublicMethod method) {
        return Optional.ofNullable(bindings.get(Objects.requireNonNull(method)));
    }
    public synchronized List<PublicRoutes.Info> inventory() { return routes.inventory(); }
    public synchronized PublicRoutes.Info describe(PublicMethod method) { return routes.describe(method); }
    public synchronized Coverage coverage() {
        List<PublicMethod> installed = bindings.keySet().stream().toList();
        List<PublicMethod> retired = routes.inventory().stream().filter(value -> value.status() == PublicRoutes.Status.RETIRED)
                .map(PublicRoutes.Info::method).toList();
        List<PublicMethod> missing = routes.inventory().stream().filter(value -> value.status() == PublicRoutes.Status.UNIMPLEMENTED)
                .map(PublicRoutes.Info::method).toList();
        return new Coverage(installed, missing, retired);
    }
    public boolean frozen() { return frozen; }
    /** Missing is supplied by the protocol envelope; present null remains a separate semantic branch. */
    public static Arguments present(RawJson token) {
        Objects.requireNonNull(token);
        return isNull(token) ? new Null() : new Value(token);
    }
    private static boolean isNull(RawJson token) {
        return new String(token.bytes(), StandardCharsets.UTF_8).strip().equals("null");
    }
    private static void require(boolean condition, String reason) {
        if (!condition) throw new IllegalArgumentException(reason);
    }
}

