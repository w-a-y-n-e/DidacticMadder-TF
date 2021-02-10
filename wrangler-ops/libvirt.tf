terraform {
 required_version = ">= 0.13"
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.6.3"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}

#provider "libvirt" {
#  alias = "server2"
#  uri   = "qemu+ssh://root@192.168.100.10/system"
#}

#variable "scenario_name" {
#  type    = string
#}

#variable "user_name" {
#  type    = string
#}

resource "random_uuid" "env_uuid" { }

resource "libvirt_volume" "deb10-qcow2" {
#  name = "${random_uuid.env_uuid.result}-deb10.qcow2"
  name = "${terraform.workspace}-deb10.qcow2"
  pool = "default"
  #source = "https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2"
  source = "packer-output/wrangler-ops.qcow2"
  format = "qcow2"
}

resource "libvirt_network" "test_net" {
	#name      = "${random_uuid.env_uuid.result}-test_net"
	name      = "${terraform.workspace}-test_name"
	mode      = "none"
}

# Define KVM domain to create
resource "libvirt_domain" "deb10" {
  name   = "${terraform.workspace}_deb10"
  memory = "1024"
  vcpu   = 1

  network_interface {
    network_name = "default"
    wait_for_lease = true
  }

  network_interface {
    network_name = libvirt_network.test_net.name
  }

  disk {
    volume_id = libvirt_volume.deb10-qcow2.id
  }

  console {
    type = "pty"
    target_type = "serial"
    target_port = "0"
  }

  graphics {
    type = "vnc"
    listen_type = "address"
    listen_address = "0.0.0.0"
    autoport = true
  }
}

#output "ip" {
#  value = libvirt_domain.deb10.network_interface[0].addresses[0]
#}

output "ip" {
   value = {(libvirt_domain.deb10.name):[libvirt_domain.deb10.network_interface[0].addresses[0],"22","ssh"]}
}

