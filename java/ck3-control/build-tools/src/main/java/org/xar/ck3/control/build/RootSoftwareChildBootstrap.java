package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** One mechanical before-import adapter for the existing Python consumers, never a business runner. */
public final class RootSoftwareChildBootstrap {
    public static final String SCHEMA = "xar.root-software-child-bootstrap/v2";
    public static final String SCOPE = "SOFTWARE_FIXTURE_ONLY";
    private static final String CLIENT = "tools.g2_saved_campaign.java_map_admission_client_v1";
    private static final String CONTINUITY = "tools.g2_saved_campaign.current_saved_continuity_v1";
    private static final String OWNER = "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1";
    private static final Set<String> ENVIRONMENT = Set.of("XAR_CROWN_JAVA_RUNTIME_SOURCE_ROOT",
            "XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE", "XAR_CROWN_ORIGINAL_REPOSITORY", "CK3_M7_FORMAL_NATIVE_WIRE_DIR",
            "XAR_CURRENT_SAVED_BASIS_TEST_SOURCE_ROOT", "XAR_CURRENT_SAVED_CLOSURE_TEST_SOURCE_ROOT",
            "XAR_CURRENT_SAVED_CONTINUITY_TEST_SOURCE_ROOT");
    private static final ObjectMapper JSON = com.fasterxml.jackson.databind.json.JsonMapper.builder(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
            .enable(DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES)
            .disable(com.fasterxml.jackson.databind.MapperFeature.ALLOW_COERCION_OF_SCALARS).build();
    private RootSoftwareChildBootstrap() { }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ModuleSource(String module, ControlBuild.FileRef source) {
        public ModuleSource { Objects.requireNonNull(module); Objects.requireNonNull(source); }
    }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ServiceProof(ControlBuild.FileRef serviceEvidenceRef, ControlBuild.FileRef readerSourceRef,
            ControlBuild.FileRef clientSourceRef) {
        public ServiceProof { Objects.requireNonNull(serviceEvidenceRef); Objects.requireNonNull(readerSourceRef); Objects.requireNonNull(clientSourceRef); }
    }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Environment(String name, String value) {
        public Environment {
            if (!ENVIRONMENT.contains(name) || value == null || value.isBlank() || value.length() > 32_768 || value.indexOf('\0') >= 0) {
                throw new IllegalArgumentException("closed before-import fixture environment required");
            }
        }
    }
    public enum SdkLineageKind { ORIGINAL_SOURCE32, DERIVED_SOURCE32 }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record SdkLineageBinding(SdkLineageKind kind, ControlBuild.FileRef sdkFreezeRef,
            ControlBuild.FileRef verifiedEmissionRef) {
        public SdkLineageBinding {
            Objects.requireNonNull(kind); Objects.requireNonNull(sdkFreezeRef);
            if ((kind == SdkLineageKind.ORIGINAL_SOURCE32) != (verifiedEmissionRef == null)) {
                throw new IllegalArgumentException("Original requires explicit null emission; derived requires an exact Java emission");
            }
        }
    }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Configuration(String schema, String scope, String machineId, String bootstrapId,
            ServiceProof serviceProof, SdkLineageBinding sdkLineageBinding, ModuleSource client, ModuleSource continuity, ModuleSource owner,
            ControlBuild.FileRef fixtureOriginRef, ControlBuild.FileRef probeRequestRef, ControlBuild.FileRef probePayloadRef,
            List<ControlBuild.FileRef> originalFixtureRefs,
            List<Environment> environment) {
        public Configuration {
            if (!SCHEMA.equals(schema) || !SCOPE.equals(scope) || machineId == null || !machineId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
                    || bootstrapId == null || !bootstrapId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")) {
                throw new IllegalArgumentException("explicit software fixture bootstrap identity required");
            }
            Objects.requireNonNull(serviceProof); Objects.requireNonNull(sdkLineageBinding); Objects.requireNonNull(client); Objects.requireNonNull(continuity);
            Objects.requireNonNull(owner); Objects.requireNonNull(fixtureOriginRef);
            Objects.requireNonNull(probeRequestRef); Objects.requireNonNull(probePayloadRef);
            originalFixtureRefs = List.copyOf(originalFixtureRefs); environment = List.copyOf(environment);
            if (!CLIENT.equals(client.module()) || !CONTINUITY.equals(continuity.module()) || !OWNER.equals(owner.module())
                    || !client.source().equals(serviceProof.clientSourceRef()) || !owner.source().equals(serviceProof.readerSourceRef())
                    || originalFixtureRefs.isEmpty() || originalFixtureRefs.size() > 4096
                    || environment.stream().map(Environment::name).distinct().count() != environment.size()) {
                throw new IllegalArgumentException("one canonical client/continuity/owner and original fixture sources required");
            }
            for (Environment value : environment) {
                if (value.name().equals("XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE")
                        && !Path.of(value.value()).toAbsolutePath().normalize().equals(Path.of(client.source().path()).toAbsolutePath().normalize())) {
                    throw new IllegalArgumentException("Crown must use the same canonical client source");
                }
            }
        }
    }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ProcessEvidence(long pid, String creationFiletimeDecimal, String executable) {
        public ProcessEvidence {
            if (pid < 1 || pid > 0xffff_ffffL || creationFiletimeDecimal == null
                    || !creationFiletimeDecimal.matches("[1-9][0-9]{0,19}")
                    || new java.math.BigInteger(creationFiletimeDecimal).bitLength() > 64
                    || executable == null || !Path.of(executable).isAbsolute()) {
                throw new IllegalArgumentException("actual bounded child/host process identity required");
            }
        }
    }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ChildEvidence(String schema, String scope, String machineId, String observedAtUtc,
            String bootstrapId, ControlBuild.FileRef bootstrapRef,
            ControlBuild.FileRef fixtureOriginRef, ProcessEvidence childProcess, ProcessEvidence hostProcess,
            List<ModuleSource> modules) {
        public ChildEvidence {
            Objects.requireNonNull(bootstrapRef); Objects.requireNonNull(fixtureOriginRef);
            Objects.requireNonNull(childProcess); Objects.requireNonNull(hostProcess); modules = List.copyOf(modules);
            if (machineId == null || machineId.isBlank() || observedAtUtc == null || !observedAtUtc.endsWith("Z")) { throw new IllegalArgumentException("explicit machine/time evidence required"); }
            java.time.Instant.parse(observedAtUtc);
        }
    }
    public static Configuration readConfiguration(ControlBuild.FileRef reference) throws IOException {
        if (reference.bytes() < 1 || reference.bytes() > 1_048_576) { throw new IOException("bounded explicit child bootstrap required"); }
        reference.verify(); byte[] raw = Files.readAllBytes(Path.of(reference.path()));
        if (raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf) { throw new IOException("UTF8 bootstrap without BOM required"); }
        for (byte value : raw) { if (value == 0) { throw new IOException("UTF8 bootstrap without raw NUL required"); } }
        String text = java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(raw)).toString();
        // In particular, FileRef bytes, PID and counts may not be bool/float-coerced by a mapper.
        JsonNode tree = JSON.readTree(text); requireIntegerRefs(tree);
        Configuration result = JSON.treeToValue(tree, Configuration.class);
        validateSdkLineage(result); reference.verify(); return result;
    }
    /** Actual Root lifecycle constructs this from measured host/source proofs, then retains one new input. */
    public static ControlBuild.FileRef writeConfiguration(Configuration configuration, Path destination) throws IOException {
        for (ControlBuild.FileRef input : inputRefs(configuration)) { input.verify(); }
        byte[] raw = JSON.writeValueAsBytes(configuration);
        if (raw.length > 1_048_576) { throw new IOException("bootstrap exceeds finite shared input budget"); }
        SharedSourceFiles.plainAncestors(destination);
        Files.write(destination, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        ControlBuild.FileRef result = ControlBuild.FileRef.measure(destination);
        if (!configuration.equals(readConfiguration(result))) { throw new IOException("bootstrap serialization roundtrip differs"); }
        return result;
    }
    public static List<ControlBuild.FileRef> inputRefs(Configuration configuration) throws IOException {
        ArrayList<ControlBuild.FileRef> refs = new ArrayList<>(List.of(configuration.serviceProof().serviceEvidenceRef(),
                configuration.serviceProof().readerSourceRef(), configuration.serviceProof().clientSourceRef(),
                configuration.client().source(), configuration.continuity().source(), configuration.owner().source(),
                configuration.fixtureOriginRef(), configuration.probeRequestRef(), configuration.probePayloadRef()));
        refs.addAll(configuration.originalFixtureRefs());
        refs.add(configuration.sdkLineageBinding().sdkFreezeRef());
        if (configuration.sdkLineageBinding().kind() == SdkLineageKind.DERIVED_SOURCE32) {
            SdkDerivedSource32.Verified verified = validateSdkLineage(configuration);
            ControlBuild.FileRef emissionRef = configuration.sdkLineageBinding().verifiedEmissionRef();
            refs.add(emissionRef);
            SdkDerivedSource32.VerifiedEmission emission = ControlBuild.strictMapper().readValue(
                    Files.readAllBytes(Path.of(emissionRef.path())), SdkDerivedSource32.VerifiedEmission.class);
            refs.addAll(List.of(emission.qualifiedToolsBuildRef(), emission.producerSourceRef(), emission.compiledProducerSourceRef(),
                    verified.parentFreezeRef(), verified.parentAnchorRef(), verified.assemblyActualRef(), verified.sdkNativeDriverRef()));
            refs.addAll(emission.producerRuntimeRefs());
            for (var source : SdkSourceAssembly.readActual(verified.assemblyActualRef()).actualSourceClosure()) refs.add(source.actual());
            emissionRef.verify();
        }
        LinkedHashMap<String, ControlBuild.FileRef> unique = new LinkedHashMap<>();
        for (ControlBuild.FileRef ref : refs) {
            String key = Path.of(ref.path()).toAbsolutePath().normalize().toString().toLowerCase(java.util.Locale.ROOT);
            ControlBuild.FileRef prior = unique.putIfAbsent(key, ref);
            if (prior != null && !prior.equals(ref)) { throw new IllegalArgumentException("conflicting bootstrap input reference"); }
        }
        return List.copyOf(unique.values());
    }
    private static SdkDerivedSource32.Verified validateSdkLineage(Configuration configuration) throws IOException {
        return validateSdkLineage(configuration.sdkLineageBinding(), configuration.machineId());
    }
    private static SdkDerivedSource32.Verified validateSdkLineage(SdkLineageBinding binding, String machine) throws IOException {
        binding.sdkFreezeRef().verify();
        if (binding.kind() == SdkLineageKind.ORIGINAL_SOURCE32) return null;
        SdkDerivedSource32.Verified verified = SdkDerivedSource32.readVerifiedEmission(binding.verifiedEmissionRef());
        if (!verified.machineId().equals(machine) || !verified.lineageRef().equals(binding.sdkFreezeRef()) || verified.nativeRestoreAdmitted()) {
            throw new IOException("Bootstrap must use this same-machine actual Java-verified derived SDK lineage");
        }
        return verified;
    }
    /** Existing independent cold producer processes use the same source reader and installation code. */
    public static String sdkLineageInstallationPrefix(SdkLineageBinding binding, String machineId, ModuleSource owner) throws IOException {
        if (!OWNER.equals(owner.module()) || machineId == null || !machineId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")) {
            throw new IllegalArgumentException("Same canonical cold owner and explicit machine required");
        }
        validateSdkLineage(binding, machineId); owner.source().verify();
        return SOURCE_PREFIX + "_xar_root_install_sdk(_xar_root_load(_xar_root_json.loads("
                + JSON.writeValueAsString(JSON.writeValueAsString(owner)) + ")), _xar_root_json.loads("
                + JSON.writeValueAsString(JSON.writeValueAsString(binding)) + "), " + JSON.writeValueAsString(machineId) + ")\n";
    }
    public static void requireEvidence(Configuration configuration, ChildEvidence evidence) throws IOException {
        if (evidence == null || !"xar.root-software-child-bootstrap-evidence/v1".equals(evidence.schema())
                || !SCOPE.equals(evidence.scope()) || !configuration.bootstrapId().equals(evidence.bootstrapId())
                || !configuration.machineId().equals(evidence.machineId())
                || !configuration.fixtureOriginRef().equals(evidence.fixtureOriginRef())
                || !List.of(configuration.client(), configuration.continuity(), configuration.owner()).equals(evidence.modules())) {
            throw new IOException("actual child canonical source/config installation evidence differs");
        }
        evidence.bootstrapRef().verify();
        if (!readConfiguration(evidence.bootstrapRef()).equals(configuration)) { throw new IOException("child bootstrap reference differs"); }
    }
    private static void requireIntegerRefs(JsonNode node) throws IOException {
        if (node == null) { throw new IOException("bootstrap object required"); }
        if (node.isObject()) {
            if (node.has("bytes") && (!node.get("bytes").isIntegralNumber() || !node.get("bytes").canConvertToLong()
                    || node.get("bytes").longValue() < 0)) { throw new IOException("exact integer FileRef bytes required"); }
            var fields = node.elements(); while (fields.hasNext()) { requireIntegerRefs(fields.next()); }
        } else if (node.isArray()) { for (JsonNode child : node) { requireIntegerRefs(child); } }
    }
    /** Enclosing observer defines root_bootstrap_ref; this prefix never assumes an argv position. */
    public static String pythonPrefix() { return SOURCE_PREFIX + SOFTWARE_PREFIX; }
    private static final String SOURCE_PREFIX = """
        import contextlib as _xar_root_contextlib, datetime as _xar_root_datetime, hashlib as _xar_root_hashlib, importlib as _xar_root_importlib, importlib.util as _xar_root_util, json as _xar_root_json, os as _xar_root_os, pathlib as _xar_root_pathlib, re as _xar_root_re, sys as _xar_root_sys
        _xar_root_stack = _xar_root_contextlib.ExitStack()
        _xar_root_bootstrap_evidence = None
        def _xar_root_require(value, message):
            if not value: raise RuntimeError('Root SOFTWARE fixture bootstrap: '+message)
        def _xar_root_pairs(pairs):
            result={}
            for key,value in pairs:
                _xar_root_require(key not in result,'duplicate JSON field'); result[key]=value
            return result
        def _xar_root_read(ref, maximum):
            _xar_root_require(type(ref) is dict and set(ref)=={'path','bytes','sha256'},'exact reference fields')
            _xar_root_require(type(ref['path']) is str and type(ref['bytes']) is int and 0 < ref['bytes'] <= maximum and type(ref['sha256']) is str and _xar_root_re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None,'exact bounded reference types')
            path=_xar_root_pathlib.Path(ref['path']); _xar_root_require(path.is_absolute(),'absolute source path')
            for part in (path,*path.parents):
                stat=part.lstat(); _xar_root_require(not part.is_symlink() and not (getattr(stat,'st_file_attributes',0)&1024),'ordinary source ancestors')
            before=path.stat()
            with path.open('rb') as stream:
                held=_xar_root_os.fstat(stream.fileno()); raw=stream.read(maximum+1); after=_xar_root_os.fstat(stream.fileno())
            identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,getattr(s,'st_birthtime_ns',s.st_ctime_ns))
            version=lambda s:identity(s)+(s.st_ctime_ns,)
            post=path.stat()
            _xar_root_require(version(before)==version(post) and version(held)==version(after) and identity(before)==identity(held)==identity(after)==identity(post) and len(raw)==ref['bytes'] and _xar_root_hashlib.sha256(raw).hexdigest()==ref['sha256'],'stable exact original bytes')
            return raw
        def _xar_root_load(spec):
            _xar_root_require(type(spec) is dict and set(spec)=={'module','source'},'canonical module/source fields')
            name=spec['module']; _xar_root_read(spec['source'],2097152)
            prior=_xar_root_sys.modules.get(name)
            if prior is not None:
                _xar_root_require(getattr(prior,'__file__',None) is not None and _xar_root_pathlib.Path(prior.__file__).resolve()==_xar_root_pathlib.Path(spec['source']['path']).resolve(),'preloaded canonical module has another origin')
                return prior
            _xar_root_importlib.import_module(name.rpartition('.')[0])
            loader=_xar_root_util.spec_from_file_location(name,spec['source']['path']); _xar_root_require(loader is not None and loader.loader is not None,'canonical source loader')
            module=_xar_root_util.module_from_spec(loader); _xar_root_sys.modules[name]=module
            loader.loader.exec_module(module); setattr(_xar_root_sys.modules[name.rpartition('.')[0]],name.rpartition('.')[2],module)
            _xar_root_read(spec['source'],2097152)
            return module
        def _xar_root_install_sdk(owner, binding, machine):
            _xar_root_require(type(binding) is dict and set(binding)=={'kind','sdk_freeze_ref','verified_emission_ref'},'closed SDK lineage binding')
            _xar_root_read(binding['sdk_freeze_ref'],2097152)
            if binding['kind']=='ORIGINAL_SOURCE32':
                _xar_root_require(binding['verified_emission_ref'] is None,'original requires explicit null Java emission')
                return
            _xar_root_require(binding['kind']=='DERIVED_SOURCE32' and binding['verified_emission_ref'] is not None,'derived requires actual Java emission')
            emission=_xar_root_json.loads(_xar_root_read(binding['verified_emission_ref'],2097152).decode('utf-8'),object_pairs_hook=_xar_root_pairs)
            _xar_root_require(emission['schema']=='xar.sdk-derived-source32-java-verification/v2' and emission['machine_id']==machine,'same-machine Java verification emission')
            verified=emission['verified']
            _xar_root_require(verified['schema']=='xar.sdk-derived-source32-verified/v2' and verified['machine_id']==machine and verified['lineage_ref']==binding['sdk_freeze_ref'] and verified['runtime_admitted'] is False and verified['native_restore_admitted'] is False and verified['source_purpose'] in {'PARENT_NATIVE_UNCHANGED','FULL_SOFTWARE'},'exact source-only installed Java result')
            owner.install_java_verified_sdk_source_v1(machine_id=machine,derived_lineage_ref=owner.parse_ref(verified['lineage_ref']),java_verified_ref=owner.parse_ref(binding['verified_emission_ref']),parent_freeze_ref=owner.parse_ref(verified['parent_freeze_ref']),parent_anchor_ref=owner.parse_ref(verified['parent_anchor_ref']),sdk_root=_xar_root_pathlib.Path(verified['sdk_root']),sdk_native_driver_ref=owner.parse_ref(verified['sdk_native_driver_ref']),source_purpose=verified['source_purpose'])
        """;
    private static final String SOFTWARE_PREFIX = """
        _xar_root_cfg=_xar_root_json.loads(_xar_root_read(root_bootstrap_ref,1048576).decode('utf-8'),object_pairs_hook=_xar_root_pairs)
        _xar_root_require(type(_xar_root_cfg) is dict and set(_xar_root_cfg)=={'schema','scope','machine_id','bootstrap_id','service_proof','sdk_lineage_binding','client','continuity','owner','fixture_origin_ref','probe_request_ref','probe_payload_ref','original_fixture_refs','environment'},'closed bootstrap contract')
        _xar_root_require(_xar_root_cfg['schema']=='xar.root-software-child-bootstrap/v2' and _xar_root_cfg['scope']=='SOFTWARE_FIXTURE_ONLY','software fixture capability only')
        _xar_root_require(_xar_root_cfg['client']['module']=='tools.g2_saved_campaign.java_map_admission_client_v1' and _xar_root_cfg['continuity']['module']=='tools.g2_saved_campaign.current_saved_continuity_v1' and _xar_root_cfg['owner']['module']=='tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1','unique canonical modules')
        _xar_root_proof=_xar_root_cfg['service_proof']
        _xar_root_require(type(_xar_root_proof) is dict and set(_xar_root_proof)=={'service_evidence_ref','reader_source_ref','client_source_ref'} and _xar_root_proof['reader_source_ref']==_xar_root_cfg['owner']['source'] and _xar_root_proof['client_source_ref']==_xar_root_cfg['client']['source'],'actual reader/client source proof')
        _xar_root_names=set()
        for item in _xar_root_cfg['environment']:
            _xar_root_require(type(item) is dict and set(item)=={'name','value'} and item['name'] in {'XAR_CROWN_JAVA_RUNTIME_SOURCE_ROOT','XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE','XAR_CROWN_ORIGINAL_REPOSITORY','CK3_M7_FORMAL_NATIVE_WIRE_DIR','XAR_CURRENT_SAVED_BASIS_TEST_SOURCE_ROOT','XAR_CURRENT_SAVED_CLOSURE_TEST_SOURCE_ROOT','XAR_CURRENT_SAVED_CONTINUITY_TEST_SOURCE_ROOT'} and item['name'] not in _xar_root_names and type(item['value']) is str and item['value'] and '\\x00' not in item['value'],'closed before-import environment')
            _xar_root_names.add(item['name']); _xar_root_os.environ[item['name']]=item['value']
        if 'XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE' in _xar_root_names:
            _xar_root_require(_xar_root_pathlib.Path(_xar_root_os.environ['XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE']).resolve()==_xar_root_pathlib.Path(_xar_root_cfg['client']['source']['path']).resolve(),'Crown canonical client source differs')
        _xar_root_os.environ['XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE']=_xar_root_cfg['client']['source']['path']
        _xar_root_os.environ['XAR_CROWN_JAVA_SERVICE_EVIDENCE']=_xar_root_json.dumps(_xar_root_proof,separators=(',',':'))
        _xar_root_require(type(_xar_root_cfg['original_fixture_refs']) is list and 0 < len(_xar_root_cfg['original_fixture_refs']) <=4096,'original producer fixtures required')
        for ref in _xar_root_cfg['original_fixture_refs']: _xar_root_read(ref,8388608)
        _xar_root_read(_xar_root_cfg['probe_request_ref'],8388608)
        _xar_root_probe_payload=_xar_root_read(_xar_root_cfg['probe_payload_ref'],8388608)
        _xar_root_origin=_xar_root_json.loads(_xar_root_read(_xar_root_cfg['fixture_origin_ref'],1048576).decode('utf-8'),object_pairs_hook=_xar_root_pairs)
        _xar_root_client=_xar_root_load(_xar_root_cfg['client'])
        _xar_root_continuity=_xar_root_load(_xar_root_cfg['continuity'])
        _xar_root_owner=_xar_root_load(_xar_root_cfg['owner'])
        _xar_root_install_sdk(_xar_root_owner,_xar_root_cfg['sdk_lineage_binding'],_xar_root_cfg['machine_id'])
        _xar_root_reader=_xar_root_owner.LocalBasisReaderV1()
        _xar_root_config=_xar_root_client.load_java_projection_service_v1(service_evidence_ref=_xar_root_client.parse_ref(_xar_root_proof['service_evidence_ref']),machine_id=_xar_root_cfg['machine_id'],reader=_xar_root_reader,reader_source_ref=_xar_root_client.parse_ref(_xar_root_proof['reader_source_ref']),client_source_ref=_xar_root_client.parse_ref(_xar_root_proof['client_source_ref']),purpose='FULL_SOFTWARE')
        _xar_root_require(_xar_root_origin.get('schema')=='xar.g2-software-fixture-origin/v1' and _xar_root_origin.get('scope')=='SOFTWARE_FIXTURE_ONLY' and _xar_root_origin.get('machine_id')==_xar_root_cfg['machine_id'] and _xar_root_origin.get('original_fixture_refs')==_xar_root_cfg['original_fixture_refs'] and _xar_root_origin.get('program_ref')==_xar_root_config.service.program_ref.to_wire() and _xar_root_origin.get('probe_request_ref')==_xar_root_cfg['probe_request_ref'] and _xar_root_origin.get('probe_payload_ref')==_xar_root_cfg['probe_payload_ref'],'qualified host/software fixture original source binding')
        _xar_root_client.install_projection_config_v1(_xar_root_config,purpose='FULL_SOFTWARE')
        _xar_root_supplier=_xar_root_client.G2HostCallContextSupplierV1(_xar_root_config)
        _xar_root_client.install_g2_context_supplier_v1(config=_xar_root_config,supplier=_xar_root_supplier)
        _xar_root_probe=_xar_root_supplier.context(milestone=_xar_root_client.G2MilestoneV1(_xar_root_origin['probe_milestone']),payload=_xar_root_probe_payload)
        _xar_root_require(_xar_root_probe.source.source_ref.to_wire()==_xar_root_cfg['fixture_origin_ref'] and _xar_root_probe.source.exact_build=='SOFTWARE_FIXTURE@sha256:'+_xar_root_config.service.program_ref.sha256,'actual host software provider must be explicitly installed')
        _xar_root_reducer=_xar_root_continuity.SourceBoundJavaSavedContinuityHttpV1(service=_xar_root_config.service,reader=_xar_root_reader,consumer=_xar_root_owner,consumer_source_ref=_xar_root_client.parse_ref(_xar_root_cfg['owner']['source']),machine_id=_xar_root_cfg['machine_id'])
        _xar_root_stack.enter_context(_xar_root_continuity.using_java_saved_continuity_reducer_v1(_xar_root_reducer))
        _xar_root_host=_xar_root_client.qualify_projection_service_v1(_xar_root_config).process.to_wire()
        _xar_root_child=_xar_root_reader.process_identity(_xar_root_os.getpid())
        def _xar_root_process(value): return {'pid':value['pid'],'creation_filetime_decimal':value['creation_filetime'],'executable':value['executable']}
        _xar_root_bootstrap_evidence={'schema':'xar.root-software-child-bootstrap-evidence/v1','scope':'SOFTWARE_FIXTURE_ONLY','machine_id':_xar_root_cfg['machine_id'],'observed_at_utc':_xar_root_datetime.datetime.now(_xar_root_datetime.timezone.utc).isoformat().replace('+00:00','Z'),'bootstrap_id':_xar_root_cfg['bootstrap_id'],'bootstrap_ref':root_bootstrap_ref,'fixture_origin_ref':_xar_root_cfg['fixture_origin_ref'],'child_process':_xar_root_process(_xar_root_child),'host_process':_xar_root_process(_xar_root_host),'modules':[_xar_root_cfg['client'],_xar_root_cfg['continuity'],_xar_root_cfg['owner']]}
        """;
}
