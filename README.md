# DidacticMadder-TF
## Instructions for installing on Proxmox (PVE) host
### Installing Proxmox
- Switch SATA mode to AHCI in BIOS if no drive detected

- While installing, click options at this screen (https://pve.proxmox.com/pve-docs/images/screenshot/pve-select-target-disk.png)
-- Set maxvz to 0

- `lvresize --extents +100%FREE /dev/pve/root`
- `resize2fs /dev/mapper/pve-root`
- reboot

- Edit `/etc/apt/sources.list.d/pve-enterprise.list`:
-- Comment out existing line
-- Add `deb http://download.proxmox.com/debian/pve buster pve-no-subscription`

- `apt update`
- `apt upgrade`

### Installing DidacticMadder-TF and required components

- `apt install libvirt-clients libvirt-daemon libvirt-daemon-system dnsmasq git terraform jq python3-pip`

- `curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -`
- Create `/etc/apt/sources.list.d/hashicorp.list` with the following line `deb [arch=amd64] https://apt.releases.hashicorp.com buster main`

- `apt update`


- `virsh net-autostart --network default`
- `virsh net-start --network default`

- `mkdir /dm-storage`
- `virsh pool-define-as default --type dir --target /dm-storage`

- `virsh pool-start --pool default`
- `virsh pool-autostart --pool default`

- Edit `/etc/apparmor.d/libvirt/TEMPLATE.qemu` and add the `file,` line to profile block:

```
profile LIBVIRT_TEMPLATE flags=(attach_disconnected) {
  #include <abstractions/libvirt-qemu>
  file,
}
```

- `git clone https://github.com/w-a-y-n-e/DidacticMadder-TF.git`

- `wget https://github.com/dmacvicar/terraform-provider-libvirt/releases/download/v0.6.3/terraform-provider-libvirt-0.6.3+git.1604843676.67f4f2aa.Ubuntu_20.04.amd64.tar.gz`
- `tar -xvf terraform-provider-libvirt-0.6.3+git.1604843676.67f4f2aa.Ubuntu_20.04.amd64.tar.gz`
- `mkdir -p ~/.local/share/terraform/plugins/registry.terraform.io/dmacvicar/libvirt/0.6.3/linux_amd64`
- `mv terraform-provider-libvirt ~/.local/share/terraform/plugins/registry.terraform.io/dmacvicar/libvirt/0.6.3/linux_amd64`

- `pip3 install flask`

### Adding scenario

- Make subdirectory in DidacticMadder-TF for scenario
- Copy `DidacticMadder-TF/template/libvirt.tf` to directory
- Modify copied file
- Copy disk image to created directory (probably rename as well)
- Run `terraform init` in scenario subdirector 

