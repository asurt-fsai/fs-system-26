#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x31f8185e, "module_layout" },
	{ 0x6bc3fbc0, "__unregister_chrdev" },
	{ 0x2d3385d3, "system_wq" },
	{ 0x85bd1608, "__request_region" },
	{ 0xb83d1abb, "netdev_info" },
	{ 0xf15cf49a, "kmalloc_caches" },
	{ 0xeb233a45, "__kmalloc" },
	{ 0xc4f0da12, "ktime_get_with_offset" },
	{ 0x1fdc7df2, "_mcount" },
	{ 0x450ea360, "register_candev" },
	{ 0x13d0adf7, "__kfifo_out" },
	{ 0x17b58ca1, "pci_free_irq_vectors" },
	{ 0x387b35d3, "pci_write_config_word" },
	{ 0x349cba85, "strchr" },
	{ 0x91d4c390, "single_open" },
	{ 0x77358855, "iomem_resource" },
	{ 0x98cf60b3, "strlen" },
	{ 0x4054e5, "alloc_can_err_skb" },
	{ 0xf8f761f, "dma_set_mask" },
	{ 0x255b8cec, "single_release" },
	{ 0x144a385f, "usb_reset_endpoint" },
	{ 0x20ea64c0, "pci_disable_device" },
	{ 0xad99b2ab, "i2c_transfer" },
	{ 0x79196c06, "netif_carrier_on" },
	{ 0x12a4e128, "__arch_copy_from_user" },
	{ 0x20000329, "simple_strtoul" },
	{ 0xffeedf6a, "delayed_work_timer_fn" },
	{ 0xaffef876, "seq_printf" },
	{ 0x56470118, "__warn_printk" },
	{ 0xb43f9365, "ktime_get" },
	{ 0x44410a3e, "usb_kill_urb" },
	{ 0x8c35b068, "remove_proc_entry" },
	{ 0x368ef15a, "device_destroy" },
	{ 0x5df5058e, "__register_chrdev" },
	{ 0x3ce06d55, "driver_for_each_device" },
	{ 0xeae3dfd6, "__const_udelay" },
	{ 0x73df629e, "pci_release_regions" },
	{ 0xc6f46339, "init_timer_key" },
	{ 0x9fa7184a, "cancel_delayed_work_sync" },
	{ 0x409bcb62, "mutex_unlock" },
	{ 0xf23cca80, "dma_free_attrs" },
	{ 0xdf3a8ba2, "device_create_with_groups" },
	{ 0x3c3ff9fd, "sprintf" },
	{ 0xd1a5d77f, "seq_read" },
	{ 0xe3149570, "dma_set_coherent_mask" },
	{ 0x15ba50a6, "jiffies" },
	{ 0xbd462b55, "__kfifo_init" },
	{ 0xe2d5255a, "strcmp" },
	{ 0xbfc086f1, "can_bus_off" },
	{ 0x1839f6c, "netif_rx" },
	{ 0xd9a5ea54, "__init_waitqueue_head" },
	{ 0xa6c12502, "dma_get_required_mask" },
	{ 0x9064a82, "param_ops_charp" },
	{ 0xb36a4d45, "pci_set_master" },
	{ 0x32964fea, "pci_alloc_irq_vectors_affinity" },
	{ 0x9f091b37, "_dev_warn" },
	{ 0xdcb764ad, "memset" },
	{ 0xdbdf6c92, "ioport_resource" },
	{ 0x5cca831a, "close_candev" },
	{ 0x1e1e140e, "ns_to_timespec64" },
	{ 0xd648eaeb, "netif_tx_wake_queue" },
	{ 0x4b0a3f52, "gic_nonsecure_priorities" },
	{ 0xd35cce70, "_raw_spin_unlock_irqrestore" },
	{ 0x37befc70, "jiffies_to_msecs" },
	{ 0xb31b3a6a, "usb_deregister" },
	{ 0x977f511b, "__mutex_init" },
	{ 0xc5850110, "printk" },
	{ 0xbcab6ee6, "sscanf" },
	{ 0xfef216eb, "_raw_spin_trylock" },
	{ 0xfcc20d06, "sysfs_remove_file_from_group" },
	{ 0x449ad0a7, "memcmp" },
	{ 0x9ec6ca96, "ktime_get_real_ts64" },
	{ 0x4711138f, "class_unregister" },
	{ 0x1edb69d6, "ktime_get_raw_ts64" },
	{ 0xdfe1f42d, "usb_set_interface" },
	{ 0xd2b7991a, "free_netdev" },
	{ 0x9166fada, "strncpy" },
	{ 0xfc8bf82c, "usb_control_msg" },
	{ 0x5a921311, "strncmp" },
	{ 0xc78bf76e, "pci_read_config_word" },
	{ 0xfdaf1e89, "dma_alloc_attrs" },
	{ 0x2ab7989d, "mutex_lock" },
	{ 0x1e6d26a8, "strstr" },
	{ 0xba9a5fc1, "alloc_candev_mqs" },
	{ 0x92d5838e, "request_threaded_irq" },
	{ 0x6b4b2933, "__ioremap" },
	{ 0x9b86aa9, "init_net" },
	{ 0x60408172, "__class_register" },
	{ 0xfe0a9207, "_dev_err" },
	{ 0xfe487975, "init_wait_entry" },
	{ 0x167c5967, "print_hex_dump" },
	{ 0xe76470b7, "can_change_mtu" },
	{ 0x3b263ea9, "i2c_del_adapter" },
	{ 0x777acd94, "_dev_info" },
	{ 0xd421b280, "usb_submit_urb" },
	{ 0x4fe069f4, "unregister_candev" },
	{ 0x137542db, "alloc_can_skb" },
	{ 0x12a38747, "usleep_range" },
	{ 0x6cbbfc54, "__arch_copy_to_user" },
	{ 0xb2fcb56d, "queue_delayed_work_on" },
	{ 0x86332725, "__stack_chk_fail" },
	{ 0x71c2bded, "usb_reset_device" },
	{ 0x9c6253c1, "usb_bulk_msg" },
	{ 0x1000e51, "schedule" },
	{ 0x8ddd8aad, "schedule_timeout" },
	{ 0x2aed3260, "kfree_skb" },
	{ 0x6a850a4d, "usb_clear_halt" },
	{ 0xbb53dfef, "cpu_hwcaps" },
	{ 0xe6911f10, "cpu_hwcap_keys" },
	{ 0x74fca7f9, "netdev_err" },
	{ 0x1035c7c2, "__release_region" },
	{ 0xcbd4898c, "fortify_panic" },
	{ 0xe105f7fd, "pci_unregister_driver" },
	{ 0xcc5005fe, "msleep_interruptible" },
	{ 0xe7871ed3, "__dev_get_by_name" },
	{ 0x9305d153, "open_candev" },
	{ 0xf53cbf87, "kmem_cache_alloc_trace" },
	{ 0x34db050b, "_raw_spin_lock_irqsave" },
	{ 0x1eac74b9, "param_ops_byte" },
	{ 0x7b59b82e, "pci_irq_vector" },
	{ 0x3eeb2322, "__wake_up" },
	{ 0xf6ebc03b, "net_ratelimit" },
	{ 0x28bda4ce, "netdev_warn" },
	{ 0x8c26d495, "prepare_to_wait_event" },
	{ 0x8c01d565, "seq_lseek" },
	{ 0x37a0cba, "kfree" },
	{ 0x4829a47e, "memcpy" },
	{ 0x3ff25767, "pci_request_regions" },
	{ 0x74f539d3, "param_array_ops" },
	{ 0x220611f8, "pci_msi_vec_count" },
	{ 0xaf56600a, "arm64_use_ng_mappings" },
	{ 0x6128b5fc, "__printk_ratelimit" },
	{ 0xedc03953, "iounmap" },
	{ 0xcad041ee, "__pci_register_driver" },
	{ 0x96848186, "scnprintf" },
	{ 0x9e9816b, "usb_register_driver" },
	{ 0x92540fbf, "finish_wait" },
	{ 0x3179211, "alloc_canfd_skb" },
	{ 0x35c0eecf, "sysfs_add_file_to_group" },
	{ 0xf23fcb99, "__kfifo_in" },
	{ 0x9701e565, "i2c_bit_add_bus" },
	{ 0x656e4a6e, "snprintf" },
	{ 0x5a9f1d63, "memmove" },
	{ 0x9b0ded73, "pci_iomap" },
	{ 0x369749e1, "consume_skb" },
	{ 0xf5fcd1a2, "param_ops_ushort" },
	{ 0xbd6970d2, "proc_create" },
	{ 0x5a8083dc, "usb_get_current_frame_number" },
	{ 0x5e515be6, "ktime_get_ts64" },
	{ 0x91391488, "pci_enable_device" },
	{ 0xd969a475, "param_ops_ulong" },
	{ 0xde1d6d02, "param_ops_uint" },
	{ 0x14b89635, "arm64_const_caps_ready" },
	{ 0x11d046af, "usb_free_urb" },
	{ 0x88db9f48, "__check_object_size" },
	{ 0x12ad6a3f, "usb_alloc_urb" },
	{ 0xc1514a3b, "free_irq" },
	{ 0x281823c5, "__kfifo_out_peek" },
	{ 0x30a80826, "__kfifo_from_user" },
};

MODULE_INFO(depends, "can-dev");

MODULE_ALIAS("pci:v0000001Cd00000001sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000003sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000004sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000005sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000006sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000007sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000008sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000009sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000002sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd0000000Asv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000010sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000013sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000014sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000016sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000017sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000018sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd00000019sv*sd*bc*sc*i*");
MODULE_ALIAS("pci:v0000001Cd0000001Asv*sd*bc*sc*i*");
MODULE_ALIAS("usb:v0C72p000Cd*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v0C72p000Dd*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v0C72p0012d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v0C72p0011d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v0C72p0013d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v0C72p0014d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v0C72p0030d*dc*dsc*dp*ic*isc*ip*in*");

MODULE_INFO(srcversion, "0D0EEA6B8B70BBEA32E8C93");
