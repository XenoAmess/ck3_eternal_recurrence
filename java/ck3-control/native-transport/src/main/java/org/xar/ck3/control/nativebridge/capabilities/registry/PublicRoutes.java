package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;

/** Exact typed Root registrations. There is deliberately no invoke(String, JSON) or arbitrary DLL-step route. */
public final class PublicRoutes {
    public enum Status { IMPLEMENTED, DELEGATED, UNIMPLEMENTED, RETIRED }
    @FunctionalInterface public interface Handler<Q,R> { R invoke(Q request) throws InterruptedException; }
    public record Target(String actualClass, String actualMethod, ExactRef implementationSource) {
        public Target {
            RegistryJson.require(actualClass != null && actualClass.matches("[A-Za-z_$][A-Za-z0-9_.$]*"), "actual Java class required");
            RegistryJson.require(actualMethod != null && actualMethod.matches("[A-Za-z_$][A-Za-z0-9_$]*"), "actual Java method required");
            Objects.requireNonNull(implementationSource); RegistryJson.require(implementationSource.bytes() > 0, "actual Java source required");
        }
    }
    public record Info(PublicMethod method, Status status, Optional<Target> target, String scope) {
        public Info { Objects.requireNonNull(method); Objects.requireNonNull(status); Objects.requireNonNull(target);
            RegistryJson.require(scope != null && !scope.isEmpty(), "route coverage scope required"); }
    }
    /** Q and R stay attached to the direct method reference; the inventory cannot erase them into an untyped dispatcher. */
    public static final class TypedRoute<Q,R> {
        private final PublicMethod method;
        private final Class<Q> requestType;
        private final Handler<Q,R> handler;
        private final Info info;
        private TypedRoute(PublicMethod method, Class<Q> requestType, Handler<Q,R> handler, Info info) {
            this.method = method; this.requestType = requestType; this.handler = handler; this.info = info;
        }
        public PublicMethod method() { return method; }
        public Class<Q> requestType() { return requestType; }
        public Info info() { return info; }
        public R invoke(Q request) throws InterruptedException { return Objects.requireNonNull(handler.invoke(requestType.cast(Objects.requireNonNull(request))), "typed public result required"); }
    }
    private final EnumMap<PublicMethod,Info> inventory = new EnumMap<>(PublicMethod.class);
    private boolean frozen;
    public PublicRoutes() {
        for (PublicMethod method : PublicMethod.values()) inventory.put(method,
                new Info(method, method.retired() ? Status.RETIRED : Status.UNIMPLEMENTED, Optional.empty(),
                        method.retired() ? "retired user instruction; never register" : "no actual Root binding installed"));
    }
    /** Only a concrete Root method reference can install a public route; method-name strings grant no dispatch permission. */
    public synchronized <Q,R> TypedRoute<Q,R> register(PublicMethod method, Class<Q> requestType,
            Handler<Q,R> handler, Target target, Status status, String scope) {
        Objects.requireNonNull(method); Objects.requireNonNull(requestType); Objects.requireNonNull(handler); Objects.requireNonNull(target);
        RegistryJson.require(!frozen && !method.retired(), "frozen or retired public method cannot register");
        RegistryJson.require(status == Status.IMPLEMENTED || status == Status.DELEGATED, "only a concrete implementation can register");
        RegistryJson.require(inventory.get(method).status() == Status.UNIMPLEMENTED, "duplicate public method binding");
        Info info = new Info(method, status, Optional.of(target), scope); inventory.put(method, info);
        return new TypedRoute<>(method, requestType, handler, info);
    }
    /** Composition specifies the actual required scope. A missing binding prevents construction of that application. */
    public synchronized void freeze(List<PublicMethod> required) {
        Objects.requireNonNull(required);
        List<String> missing = new ArrayList<>();
        for (PublicMethod method : required) {
            Info info = inventory.get(Objects.requireNonNull(method));
            if (info.status() != Status.IMPLEMENTED && info.status() != Status.DELEGATED) missing.add(method.pythonName());
        }
        RegistryJson.require(missing.isEmpty(), "missing actual public bindings: " + missing); frozen = true;
    }
    public synchronized Info describe(PublicMethod exactMethod) { return inventory.get(Objects.requireNonNull(exactMethod)); }
    public synchronized List<Info> inventory() { return List.copyOf(inventory.values()); }
    public synchronized boolean frozen() { return frozen; }
}

