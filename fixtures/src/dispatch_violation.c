/*
 * KD-009 VIOLATION: MajorFunction registration gaps in DriverEntry.
 *
 * IRP_MJ_CLEANUP and IRP_MJ_CLOSE are referenced in comments/logic
 * but never assigned in DriverObject->MajorFunction[].
 * IRP_MJ_DEVICE_CONTROL is assigned NULL instead of a handler.
 */

#include <ntddk.h>

NTSTATUS DriverEntry(
    _In_ PDRIVER_OBJECT  DriverObject,
    _In_ PUNICODE_STRING RegistryPath
)
{
    UNREFERENCED_PARAMETER(RegistryPath);

    /* VIOLATION: IRP_MJ_DEVICE_CONTROL assigned NULL */
    DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = NULL;
    DriverObject->MajorFunction[IRP_MJ_CREATE] = DriverCreate;

    /* IRP_MJ_CLEANUP and IRP_MJ_CLOSE intentionally omitted — gap */

    return STATUS_SUCCESS;
}
