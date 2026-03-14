PVOID AllocateBuffer(SIZE_T Length) {
    UNREFERENCED_PARAMETER(Length);
    return ExAllocatePoolWithTag(NonPagedPool, 256, 'buf1');
}
