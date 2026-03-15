/*
 * KD-009 COMPLIANT: All handled IRP major functions explicitly registered.
 *
 * Unhandled IRPs are caught by a common stub that returns
 * STATUS_NOT_SUPPORTED, not by NULL.
 */

#include <ntddk.h>

NTSTATUS DriverCreate(PDEVICE_OBJECT, PIRP);
NTSTATUS DriverClose(PDEVICE_OBJECT, PIRP);
NTSTATUS DriverCleanup(PDEVICE_OBJECT, PIRP);
NTSTATUS DriverDeviceControl(PDEVICE_OBJECT, PIRP);
NTSTATUS DriverDefaultHandler(PDEVICE_OBJECT, PIRP);

NTSTATUS DriverEntry(
    _In_ PDRIVER_OBJECT  DriverObject,
    _In_ PUNICODE_STRING RegistryPath
)
{
    UNREFERENCED_PARAMETER(RegistryPath);

    /* All major functions explicitly assigned */
    DriverObject->MajorFunction[IRP_MJ_CREATE]         = DriverCreate;
    DriverObject->MajorFunction[IRP_MJ_CLOSE]          = DriverClose;
    DriverObject->MajorFunction[IRP_MJ_CLEANUP]        = DriverCleanup;
    DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = DriverDeviceControl;

    /* Unhandled major functions routed to a safe stub */
    for (ULONG i = 0; i <= IRP_MJ_MAXIMUM_FUNCTION; i++) {
        if (!DriverObject->MajorFunction[i]) {
            DriverObject->MajorFunction[i] = DriverDefaultHandler;
        }
    }

    return STATUS_SUCCESS;
}
