PVOID AllocateBuffer(SIZE_T Length) {
    UNREFERENCED_PARAMETER(Length);
    return ExAllocatePool(NonPagedPool, 256);
}
