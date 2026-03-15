/*
 * KD-008 COMPLIANT: Correct pageable section annotation.
 *
 * - PAGED_CODE() is present at the entry of every PAGE-section function.
 * - Non-pageable dispatch path does NOT contain PAGED_CODE().
 */

#include <ntddk.h>

/* Pageable read handler — called only at PASSIVE_LEVEL */
#pragma alloc_text(PAGE, DriverReadHandler)
NTSTATUS DriverReadHandler(
    _In_ PDEVICE_OBJECT DeviceObject,
    _In_ PIRP           Irp
)
{
    PAGED_CODE();   /* Correct: asserts IRQL <= APC_LEVEL at runtime */
    UNREFERENCED_PARAMETER(DeviceObject);

    Irp->IoStatus.Status = STATUS_SUCCESS;
    Irp->IoStatus.Information = 0;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}

/* Non-pageable dispatch handler — no PAGED_CODE() */
NTSTATUS DispatchHandler(
    _In_ PDEVICE_OBJECT DeviceObject,
    _In_ PIRP           Irp
)
{
    UNREFERENCED_PARAMETER(DeviceObject);
    /* Correct: no PAGED_CODE(), runs at any IRQL */
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}
