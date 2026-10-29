package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.planning.family.FamilyInitialData;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataPin;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole;

/** Three initial automation DATA originals. Publication is immutable input I/O, never a live domain import. */
public final class RootFamilyInitialDataProducer {
    private RootFamilyInitialDataProducer() { }
    public record Targets(Path family, Path childMatrilineal, Path defaultMarriage) {
        public Targets {
            absolute(family); absolute(childMatrilineal); absolute(defaultMarriage);
            StrictJson.require(List.of(family, childMatrilineal, defaultMarriage).stream().distinct().count() == 3,
                    "three distinct immutable family DATA targets required");
        }
        public List<Path> paths() { return List.of(family, childMatrilineal, defaultMarriage); }
        public Path path(Slot slot) {
            return switch (slot) {
                case FAMILY -> family;
                case CHILD_MATRILINEAL -> childMatrilineal;
                case DEFAULT_MARRIAGE -> defaultMarriage;
                default -> throw new IllegalArgumentException("not a family DATA target");
            };
        }
    }
    public record Planned(DataRole role, Path target, long bytes, String sha256) {
        public Planned { Objects.requireNonNull(role); absolute(target); StrictJson.require(bytes > 0 && bytes <= ContinuityJson.DOMAIN_MAX_BYTES,
                "bounded initial family DATA output required"); StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "initial DATA digest required"); }
    }
    public static final class Prepared {
        private final Targets targets;
        private final FamilyInitialData.Documents documents;
        private boolean attempted;
        private Prepared(Targets targets, FamilyInitialData.Documents documents) {
            this.targets = Objects.requireNonNull(targets); this.documents = Objects.requireNonNull(documents);
            for (var body : documents.bodies()) FamilyInitialData.decode(body.slot(), FamilyInitialData.encode(body));
        }
        public FamilyInitialData.Documents documents() { return documents; }
        public List<Planned> outputs() {
            return documents.bodies().stream().map(body -> {
                byte[] bytes = FamilyInitialData.encode(body);
                return new Planned(role(body.slot()), targets.path(body.slot()), bytes.length,
                        org.xar.ck3.control.application.action.ActionCodec.sha256(bytes));
            }).toList();
        }
        /** Existing sealed bootstrap/runtime input authority supplies the exact immutable file port and allocation scope. */
        public synchronized Published createNew(RootBootstrapInputFiles authority) throws IOException {
            Objects.requireNonNull(authority);
            if (attempted) throw new IOException("initial family DATA publication already attempted; retain possible partial originals");
            authority.requireTargets(targets.paths());
            var files = authority.files();
            for (Path target : targets.paths()) if (files.observe(target).isPresent())
                throw new IOException("initial family DATA target already exists; existing originals cannot be replaced");
            attempted = true;
            var created = new ArrayList<FileWitness>();
            for (var body : documents.bodies()) {
                Path target = targets.path(body.slot()); byte[] expected = FamilyInitialData.encode(body);
                FileWitness actual = files.createNew(target, expected);
                if (!Path.of(actual.reference().path()).toAbsolutePath().normalize().equals(target))
                    throw new IOException("initial family DATA publication returned another path");
                files.verify(actual); byte[] observed = files.read(actual, ContinuityJson.DOMAIN_MAX_BYTES);
                if (!Arrays.equals(expected, observed) || !FamilyInitialData.decode(body.slot(), observed).equals(body))
                    throw new IOException("initial family DATA original differs from its typed producer");
                files.verify(actual); created.add(actual);
            }
            authority.requireTargets(targets.paths());
            for (FileWitness actual : created) files.verify(actual);
            return new Published(created.get(0).reference(), created.get(1).reference(), created.get(2).reference());
        }
    }
    public record Published(ExactRef family, ExactRef childMatrilineal, ExactRef defaultMarriage) {
        public Published { Objects.requireNonNull(family); Objects.requireNonNull(childMatrilineal); Objects.requireNonNull(defaultMarriage); }
        /** The real Definitions producer selects these DATA pins; no Definitions, admission or imported ledger is synthesized. */
        public List<DataPin> definitionInputs() {
            return List.of(pin(DataRole.FAMILY_DOMAIN, family), pin(DataRole.CHILD_MATRILINEAL_DOMAIN, childMatrilineal),
                    pin(DataRole.DEFAULT_MARRIAGE_DOMAIN, defaultMarriage));
        }
        public RootNativeFamilySourcesFactory.OriginalDocuments originalDocuments() {
            return new RootNativeFamilySourcesFactory.OriginalDocuments(family, childMatrilineal, defaultMarriage);
        }
    }
    public static Prepared prepare(Targets targets, FamilyInitialData.Documents initial) { return new Prepared(targets, initial); }
    private static DataPin pin(DataRole role, ExactRef original) {
        return new DataPin(role, new FileRef(original.path(), original.bytes(), original.sha256()));
    }
    private static DataRole role(Slot slot) {
        return switch (slot) {
            case FAMILY -> DataRole.FAMILY_DOMAIN;
            case CHILD_MATRILINEAL -> DataRole.CHILD_MATRILINEAL_DOMAIN;
            case DEFAULT_MARRIAGE -> DataRole.DEFAULT_MARRIAGE_DOMAIN;
            default -> throw new IllegalArgumentException("not a family DATA slot");
        };
    }
    private static void absolute(Path path) {
        Objects.requireNonNull(path);
        StrictJson.require(path.isAbsolute() && path.normalize().equals(path) && path.getParent() != null,
                "explicit absolute normalized initial DATA path required");
    }
}
