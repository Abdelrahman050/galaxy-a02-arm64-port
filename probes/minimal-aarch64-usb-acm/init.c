/*
 * Isolated Minimal AArch64 boot probe with an optional USB CDC-ACM marker.
 * Freestanding PID 1: no libc, shell, Android init, or partition writes.
 */
#include "probe_identity.h"

#ifndef A02_USB_VID
#error "build.sh must generate a reviewed USB VID"
#endif
#ifndef A02_USB_PID
#error "build.sh must generate a reviewed USB PID"
#endif
#ifndef A02_USB_SERIAL
#error "build.sh must generate a unique USB serial string"
#endif

typedef unsigned long usize;

#define AT_FDCWD (-100)
#define O_RDONLY 0
#define O_WRONLY 1
#define O_NONBLOCK 0x800
#define O_DIRECTORY 0x10000
#define S_IFCHR 0x2000
#define MODE_CONSOLE (S_IFCHR | 0600)

struct timespec { long tv_sec, tv_nsec; };
struct utsname {
    char sysname[65], nodename[65], release[65], version[65], machine[65], domainname[65];
};
struct linux_dirent64 {
    unsigned long long ino;
    long long off;
    unsigned short reclen;
    unsigned char type;
    char name[];
};

static inline long sc1(long nr, long a0)
{
    register long x0 __asm__("x0") = a0;
    register long x8 __asm__("x8") = nr;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x8) : "memory");
    return x0;
}

static inline long sc2(long nr, long a0, long a1)
{
    register long x0 __asm__("x0") = a0;
    register long x1 __asm__("x1") = a1;
    register long x8 __asm__("x8") = nr;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x8) : "memory");
    return x0;
}

static inline long sc3(long nr, long a0, long a1, long a2)
{
    register long x0 __asm__("x0") = a0;
    register long x1 __asm__("x1") = a1;
    register long x2 __asm__("x2") = a2;
    register long x8 __asm__("x8") = nr;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8) : "memory");
    return x0;
}

static inline long sc4(long nr, long a0, long a1, long a2, long a3)
{
    register long x0 __asm__("x0") = a0;
    register long x1 __asm__("x1") = a1;
    register long x2 __asm__("x2") = a2;
    register long x3 __asm__("x3") = a3;
    register long x8 __asm__("x8") = nr;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x3), "r"(x8) : "memory");
    return x0;
}

static inline long sc5(long nr, long a0, long a1, long a2, long a3, long a4)
{
    register long x0 __asm__("x0") = a0;
    register long x1 __asm__("x1") = a1;
    register long x2 __asm__("x2") = a2;
    register long x3 __asm__("x3") = a3;
    register long x4 __asm__("x4") = a4;
    register long x8 __asm__("x8") = nr;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x8) : "memory");
    return x0;
}

static usize slen(const char *s)
{
    usize n = 0;
    while (s[n]) n++;
    return n;
}

static void write_fd(long fd, const char *s, usize n)
{
    while (n) {
        long r = sc3(64, fd, (long)s, (long)n);
        if (r <= 0) return;
        s += r;
        n -= (usize)r;
    }
}

static void console(const char *s)
{
    long fd = sc4(56, AT_FDCWD, (long)"/dev/console", O_WRONLY, 0);
    if (fd >= 0) {
        write_fd(fd, s, slen(s));
        sc1(57, fd);
    }
}

static long mkdir_path(const char *p)
{
    return sc3(34, AT_FDCWD, (long)p, 0755);
}

static long write_path(const char *p, const char *s)
{
    long fd = sc4(56, AT_FDCWD, (long)p, O_WRONLY, 0);
    if (fd < 0) return fd;
    usize n = slen(s);
    long r = sc3(64, fd, (long)s, (long)n);
    sc1(57, fd);
    return r == (long)n ? 0 : (r < 0 ? r : -5);
}

static int set_usb_id(const char *path, unsigned int value)
{
    static const char hex[] = "0123456789abcdef";
    char text[7];
    text[0] = '0';
    text[1] = 'x';
    text[2] = hex[(value >> 12) & 0xf];
    text[3] = hex[(value >> 8) & 0xf];
    text[4] = hex[(value >> 4) & 0xf];
    text[5] = hex[value & 0xf];
    text[6] = '\0';
    return write_path(path, text) == 0;
}

static long read_path(const char *p, char *buf, usize cap)
{
    long fd = sc4(56, AT_FDCWD, (long)p, O_RDONLY, 0);
    if (fd < 0) return fd;
    long n = sc3(63, fd, (long)buf, (long)(cap - 1));
    sc1(57, fd);
    if (n >= 0) buf[n] = '\0';
    return n;
}

static void nap(void)
{
    struct timespec t = {1, 0};
    (void)sc2(101, (long)&t, 0);
}

static int mkdir_ok(const char *p)
{
    long r = mkdir_path(p);
    return r == 0 || r == -17;
}

static int prepare_gadget(void)
{
    (void)mkdir_path("/sys");
    long m = sc5(40, (long)"sysfs", (long)"/sys", (long)"sysfs", 0, 0);
    if (m < 0 && m != -16)
        return 0;
    (void)mkdir_path("/sys/kernel/config");
    m = sc5(40, (long)"configfs", (long)"/sys/kernel/config", (long)"configfs", 0, 0);
    if (m < 0 && m != -16) return 0;

    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/strings")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/strings/0x409")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/configs")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/configs/c.1")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/configs/c.1/strings")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/configs/c.1/strings/0x409")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/functions")) return 0;
    if (!mkdir_ok("/sys/kernel/config/usb_gadget/a02probe/functions/acm.usb0")) return 0;

    if (!set_usb_id("/sys/kernel/config/usb_gadget/a02probe/idVendor", A02_USB_VID)) return 0;
    if (!set_usb_id("/sys/kernel/config/usb_gadget/a02probe/idProduct", A02_USB_PID)) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/bcdUSB", "0x0200") < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/bcdDevice", "0x0100") < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/strings/0x409/serialnumber", A02_USB_SERIAL) < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/strings/0x409/manufacturer", "Local boot proof") < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/strings/0x409/product", "A02 ARM64 probe") < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/configs/c.1/strings/0x409/configuration", "AArch64 init proof") < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/configs/c.1/MaxPower", "100") < 0) return 0;
    if (write_path("/sys/kernel/config/usb_gadget/a02probe/configs/c.1/bmAttributes", "0x80") < 0) return 0;

    long r = sc3(36, (long)"../../../../usb_gadget/a02probe/functions/acm.usb0",
                 AT_FDCWD, (long)"/sys/kernel/config/usb_gadget/a02probe/configs/c.1/acm.usb0");
    return r == 0 || r == -17;
}

static int bind_udc(void)
{
    char buf[768];
    long dir = sc4(56, AT_FDCWD, (long)"/sys/class/udc", O_RDONLY | O_DIRECTORY, 0);
    if (dir < 0) return 0;
    long n = sc3(61, dir, (long)buf, sizeof(buf));
    sc1(57, dir);
    if (n <= 0) return 0;
    for (long off = 0; off + 20 < n; ) {
        struct linux_dirent64 *d = (struct linux_dirent64 *)(buf + off);
        if (d->reclen < 20 || off + d->reclen > n) break;
        if (d->name[0] && d->name[0] != '.') {
            if (write_path("/sys/kernel/config/usb_gadget/a02probe/UDC", d->name) == 0)
                return 1;
        }
        off += d->reclen;
    }
    return 0;
}

static unsigned long parse_dec(const char **p)
{
    unsigned long v = 0;
    while (**p >= '0' && **p <= '9') { v = v * 10 + (unsigned long)(**p - '0'); (*p)++; }
    return v;
}

static void create_tty_node(void)
{
    char b[64];
    if (read_path("/sys/class/tty/ttyGS0/dev", b, sizeof(b)) <= 0) return;
    const char *p = b;
    unsigned long major = parse_dec(&p);
    if (*p++ != ':') return;
    unsigned long minor = parse_dec(&p);
    unsigned long dev = ((major & 0xfff) << 8) | (minor & 0xff) | ((minor & ~0xffUL) << 12);
    (void)sc4(33, AT_FDCWD, (long)"/dev/ttyGS0", MODE_CONSOLE, dev);
}

static void emit_probe(const char *machine)
{
    static const char prefix[] = "A02 ARM64 boot probe: PID 1 entered; uname.machine=";
    static const char suffix[] = "\n";
    long fd = sc4(56, AT_FDCWD, (long)"/dev/ttyGS0", O_WRONLY | O_NONBLOCK, 0);
    if (fd < 0) return;
    write_fd(fd, prefix, sizeof(prefix) - 1);
    write_fd(fd, machine, slen(machine));
    write_fd(fd, suffix, sizeof(suffix) - 1);
    sc1(57, fd);
}

__attribute__((noreturn)) void _start(void)
{
    struct utsname u;
    int prepared = 0, bound = 0, reported_setup = 0;
    u.machine[0] = '\0';
    console("A02 ARM64 boot probe: PID 1 entered\n");
    if (sc1(160, (long)&u) == 0) {
        console("uname.machine=");
        console(u.machine);
        console("\n");
    }
    for (;;) {
        if (!prepared) {
            prepared = prepare_gadget();
            if (!prepared && !reported_setup) {
                console("USB ACM configfs setup pending or unavailable\n");
                reported_setup = 1;
            }
        }
        if (prepared && !bound) bound = bind_udc();
        if (bound) {
            create_tty_node();
            emit_probe(u.machine);
        }
        nap();
    }
}
