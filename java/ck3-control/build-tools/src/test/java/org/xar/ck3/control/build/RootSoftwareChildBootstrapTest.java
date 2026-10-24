package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class RootSoftwareChildBootstrapTest {
    @TempDir Path root;

    private RootSoftwareChildBootstrap.Configuration configuration() throws IOException {
        var ref = ControlBuild.FileRef.measure(Files.writeString(root.resolve("source.json"), "{}"));
        return new RootSoftwareChildBootstrap.Configuration(RootSoftwareChildBootstrap.SCHEMA,
                RootSoftwareChildBootstrap.SCOPE, "software-test-machine", "metadata-roundtrip",
                new RootSoftwareChildBootstrap.ServiceProof(ref, ref, ref),
                new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32, ref, null),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.java_map_admission_client_v1", ref),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.current_saved_continuity_v1", ref),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", ref),
                ref, ref, ref, List.of(ref), List.of());
    }

    @Test void originalProducerReaderRetainsRequiredExplicitNullAndCustody() throws IOException {
        var configuration = configuration();
        var ref = RootSoftwareChildBootstrap.writeConfiguration(configuration, root.resolve("bootstrap.json"));
        assertEquals(configuration, RootSoftwareChildBootstrap.readConfiguration(ref));
        assertEquals(List.of(configuration.sdkLineageBinding().sdkFreezeRef()), RootSoftwareChildBootstrap.inputRefs(configuration));
        var tree = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(ref.path())));
        assertEquals(true, tree.required("sdk_lineage_binding").required("verified_emission_ref").isNull());
    }

    @Test void readerRejectsMissingBindingMissingNullableFieldAndWrongEnum() throws IOException {
        var configuration = configuration();
        var tree = (com.fasterxml.jackson.databind.node.ObjectNode) ControlBuild.strictMapper().valueToTree(configuration);
        var binding = (com.fasterxml.jackson.databind.node.ObjectNode) tree.required("sdk_lineage_binding");
        binding.remove("verified_emission_ref");
        Path missing = Files.write(root.resolve("missing.json"), ControlBuild.strictMapper().writeValueAsBytes(tree));
        assertThrows(IOException.class, () -> RootSoftwareChildBootstrap.readConfiguration(ControlBuild.FileRef.measure(missing)));
        binding.putNull("verified_emission_ref"); binding.put("kind", "derived_source32");
        Path wrong = Files.write(root.resolve("wrong.json"), ControlBuild.strictMapper().writeValueAsBytes(tree));
        assertThrows(IOException.class, () -> RootSoftwareChildBootstrap.readConfiguration(ControlBuild.FileRef.measure(wrong)));
        tree.remove("sdk_lineage_binding");
        Path absent = Files.write(root.resolve("absent.json"), ControlBuild.strictMapper().writeValueAsBytes(tree));
        assertThrows(IOException.class, () -> RootSoftwareChildBootstrap.readConfiguration(ControlBuild.FileRef.measure(absent)));
    }

    @Test void derivedRejectsUnqualifiedEmissionBeforeProducingAnInstaller() throws IOException {
        var configuration = configuration();
        var ref = configuration.sdkLineageBinding().sdkFreezeRef();
        var binding = new RootSoftwareChildBootstrap.SdkLineageBinding(
                RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32, ref, ref);
        assertThrows(IOException.class, () -> RootSoftwareChildBootstrap.sdkLineageInstallationPrefix(
                binding, configuration.machineId(), configuration.owner()));
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareChildBootstrap.SdkLineageBinding(
                RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32, ref, null));
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareChildBootstrap.SdkLineageBinding(
                RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32, ref, ref));
    }
}
