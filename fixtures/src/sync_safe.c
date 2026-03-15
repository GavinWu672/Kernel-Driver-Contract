/*
 * KD-006 COMPLIANT: Correct synchronization primitive for DISPATCH_LEVEL.
 *
 * At DISPATCH_LEVEL, use KSPIN_LOCK exclusively.
 * KMUTEX / FAST_MUTEX are reserved for PASSIVE_LEVEL callers.
 */

#include <ntddk.h>

KSPIN_LOCK g_SpinLock;
ULONG      g_SharedCounter;

VOID SafeSyncRoutine(_In_ PDEVICE_OBJECT DeviceObject)
{
    KIRQL oldIrql;

    UNREFERENCED_PARAMETER(DeviceObject);

    /* Correct: spinlock is valid at DISPATCH_LEVEL */
    KeAcquireSpinLock(&g_SpinLock, &oldIrql);
    g_SharedCounter++;
    KeReleaseSpinLock(&g_SpinLock, oldIrql);
}

VOID PassiveLevelRoutine(VOID)
{
    /* At PASSIVE_LEVEL a FAST_MUTEX is the right choice */
    FAST_MUTEX mutex;
    ExInitializeFastMutex(&mutex);
    ExAcquireFastMutex(&mutex);
    /* ... critical section ... */
    ExReleaseFastMutex(&mutex);
}
