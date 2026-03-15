/*
 * KD-006 VIOLATION: KMUTEX acquired at DISPATCH_LEVEL.
 *
 * ExAcquireFastMutex requires PASSIVE_LEVEL.
 * Calling it inside a spinlock-held (DISPATCH_LEVEL) region will
 * bugcheck with IRQL_NOT_LESS_OR_EQUAL.
 */

#include <ntddk.h>

FAST_MUTEX g_Mutex;
KSPIN_LOCK g_SpinLock;

VOID BadSyncRoutine(_In_ PDEVICE_OBJECT DeviceObject)
{
    KIRQL oldIrql;

    UNREFERENCED_PARAMETER(DeviceObject);

    /* Raises IRQL to DISPATCH_LEVEL */
    KeAcquireSpinLock(&g_SpinLock, &oldIrql);

    /* VIOLATION: ExAcquireFastMutex requires PASSIVE_LEVEL */
    ExAcquireFastMutex(&g_Mutex);
    ExReleaseFastMutex(&g_Mutex);

    KeReleaseSpinLock(&g_SpinLock, oldIrql);
}
