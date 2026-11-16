#include <jni.h>
#include <jvmti.h>
#include <string.h>

/* JVMTI callbacks run without JNI. Only this fresh environment's private tags are touched. */
typedef struct {
    jint seen;
    jint maximum;
    jint overflow;
    jlong tag;
} discovery;

static jvmtiIterationControl JNICALL capture(jlong class_tag, jlong size, jlong *tag, void *opaque) {
    discovery *state = (discovery *)opaque;
    (void)class_tag;
    (void)size;
    if (++state->seen > state->maximum) {
        state->overflow = 1;
        return JVMTI_ITERATION_ABORT;
    }
    *tag = state->tag;
    return JVMTI_ITERATION_CONTINUE;
}

static void fail(JNIEnv *jni, const char *message) {
    jclass type = (*jni)->FindClass(jni, "java/io/IOException");
    if (type != NULL) (*jni)->ThrowNew(jni, type, message);
}

JNIEXPORT jobjectArray JNICALL
Java_org_xar_ck3_control_service_root_RootAwaitingOwnerStorageHandoffAgent_findInstances(
        JNIEnv *jni, jclass owner, jobjectArray classes, jint maximum) {
    JavaVM *vm = NULL;
    jvmtiEnv *tools = NULL;
    jvmtiCapabilities capabilities;
    jobject *objects = NULL;
    jobjectArray result = NULL;
    jlong tags[2] = {1, 2};
    jint count = 0, expected = 0, index;
    jsize class_count;
    jvmtiError error;
    (void)owner;
    if (classes == NULL || maximum < 1 || maximum > 32) {
        fail(jni, "bounded exact-class discovery required");
        return NULL;
    }
    class_count = (*jni)->GetArrayLength(jni, classes);
    if (class_count < 1 || class_count > 2 || (*jni)->GetJavaVM(jni, &vm) != JNI_OK
            || (*vm)->GetEnv(vm, (void **)&tools, JVMTI_VERSION_1_2) != JNI_OK || tools == NULL) {
        fail(jni, "live standard JVMTI environment unavailable");
        return NULL;
    }
    memset(&capabilities, 0, sizeof(capabilities));
    capabilities.can_tag_objects = 1;
    error = (*tools)->AddCapabilities(tools, &capabilities);
    if (error != JVMTI_ERROR_NONE) {
        fail(jni, "live can_tag_objects capability unavailable");
        goto done;
    }
    for (index = 0; index < class_count; ++index) {
        jclass type = (jclass)(*jni)->GetObjectArrayElement(jni, classes, index);
        discovery state;
        if (type == NULL) { fail(jni, "null exact discovery class"); goto done; }
        state.seen = 0; state.maximum = maximum - expected; state.overflow = 0; state.tag = tags[index];
        error = (*tools)->IterateOverInstancesOfClass(tools, type, JVMTI_HEAP_OBJECT_EITHER, capture, &state);
        (*jni)->DeleteLocalRef(jni, type);
        if (error != JVMTI_ERROR_NONE || state.overflow) {
            fail(jni, "instance discovery failed or exceeded its bound");
            goto done;
        }
        expected += state.seen;
    }
    /* Traversal has fully returned. JNI reference work is permitted again here. */
    error = (*tools)->GetObjectsWithTags(tools, class_count, tags, &count, &objects, NULL);
    if (error != JVMTI_ERROR_NONE || count < 0 || count > maximum || count != expected) {
        fail(jni, "tagged instance reference census changed");
        goto done;
    }
    {
        jclass object_type = (*jni)->FindClass(jni, "java/lang/Object");
        if (object_type == NULL) goto done;
        result = (*jni)->NewObjectArray(jni, count, object_type, NULL);
        (*jni)->DeleteLocalRef(jni, object_type);
        if (result == NULL) goto done;
    }
    for (index = 0; index < count; ++index) {
        (*jni)->SetObjectArrayElement(jni, result, index, objects[index]);
        if ((*jni)->ExceptionCheck(jni)) { result = NULL; break; }
    }
done:
    if (objects != NULL) {
        for (index = 0; index < count; ++index) (*jni)->DeleteLocalRef(jni, objects[index]);
        (*tools)->Deallocate(tools, (unsigned char *)objects);
    }
    if ((*tools)->DisposeEnvironment(tools) != JVMTI_ERROR_NONE && !(*jni)->ExceptionCheck(jni)) {
        fail(jni, "private discovery environment disposal failed");
        result = NULL;
    }
    return result;
}
