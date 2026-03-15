/*
 * KD-008 VIOLATION: PAGED_CODE() missing from a PAGE-section function,
 * and PAGED_CODE() incorrectly placed in a non-pageable context.
 *
 * Case A: DriverReadHandler is in the PAGE section but has no PAGED_CODE().
 * Case B: DispatchHandler calls PAGED_CODE() while holding a spinlock
 *         (at DISPATCH_LEVEL), which will bugcheck at runtime.
 */

#include <ntddk.h>

KSPIN_LOCK g_Lock;

/* Case A: declared pageable, but PAGED_CODE() is missing */
#pragma alloc_text(PAGE, DriverReadHandler)
NTSTATUS DriverReadHandler(
    _In_ PDEVICE_OBJECT DeviceObject,
    _In_ PIRP           Irp
)
{
    UNREFERENCED_PARAMETER(DeviceObject);
    /* VIOLATION: PAGED_CODE() absent — if called at DISPATCH_LEVEL, bugcheck */
    Irp->IoStatus.Status = STATUS_SUCCESS;
    Irp->IoStatus.Information = 0;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}

/* Case B: spinlock raises IRQL, then PAGED_CODE() is encountered */
NTSTATUS DispatchHandler(
    _In_ PDEVICE_OBJECT DeviceObject,
    _In_ PIRP           Irp
)
{
    KIRQL oldIrql;
    UNREFERENCED_PARAMETER(DeviceObject);

    KeAcquireSpinLock(&g_Lock, &oldIrql);

    /* VIOLATION: PAGED_CODE at DISPATCH_LEVEL triggers KeBugCheck */
    PAGED_CODE();

    KeReleaseSpinLock(&g_Lock, oldIrql);

    Irp->IoStatus.Status = STATUS_SUCCESS;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}
