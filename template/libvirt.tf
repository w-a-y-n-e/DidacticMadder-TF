# Update the values in CAPS below. Values that have PLACEHOLDER in the name only need to be unique in this file as they are the names used by Terraform.
# The other values in CAPS are part of values that should already have a unique component and are mostly the names used by libvirt.
# There can be multiple domains (i.e. Virtual Machines), just pay attention to the braces
# This is just the beginning of what is capable. See https://github.com/dmacvicar/terraform-provider-libvirt/blob/master/website/docs/r/

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


resource "random_uuid" "env_uuid" { }

resource "libvirt_volume" "DISK-PLACEHOLDER" {
#  name = "${random_uuid.env_uuid.result}-MACHINE-DISK-NAME.qcow2"
  name = "${terraform.workspace}-MACHINE-DISK-NAME.qcow2"
  pool = "default"
  source = "PATH-TO/SOURCE-DISK.qcow2"
  format = "qcow2"
}

# Uncomment the following if you need to add a network between machines (i.e. Not the one they access directly)
#resource "libvirt_network" "NETWORK-PLACEHOLDER" {
#	#name      = "${random_uuid.env_uuid.result}-NETWORK-NAME"
#	name      = "${terraform.workspace}-NETWORK-NAME"
#	mode      = "none"
#}

# Define KVM domain to create
resource "libvirt_domain" "MACHINE-PLACEHOLDER" {
  name   = "${terraform.workspace}_MACHINE_NAME"
  memory = "1024"
  vcpu   = 1



  network_interface {
    network_name = "default"
    wait_for_lease = true # Make sure this is only set to true for interfaces connected to the default network
    # also make sure that this matches the configuration in the guest. If this is set to true for an interface that is not using dhcp, it will not work
    #mac    = "52:54:00:b2:2f:86"
  }

  network_interface {
    network_name = libvirt_network.NETWORK-PLACEHOLDER.name
    # Should this be id and be the PLACEHOLDER for the network?
  }

  disk {
    volume_id = libvirt_volume.DISK-PLACEHOLDER.id
    #scsi = "true"
  }

  console {
    type = "pty"
    target_type = "serial"
    target_port = "0"
  }

  # Keep this block for every machine as this is what will be accessible to administrators for troubleshooting
  graphics {
    type = "vnc"
    listen_type = "address"
    listen_address = "0.0.0.0"
    autoport = true
  }
}

# Use the following to define the ports/protocols that should be accessible through guacamole by the student
# These should all be ports that are on the interface connected to the "default" network
# This is a map with keys that identify the machine and a value that is a list containing the address, port, and protocol
# Update the interface number to one that is connected to the "default" network

output "ip" {
   value = {(libvirt_domain.MACHINE-PLACEHOLDER.name):[libvirt_domain.MACHINE-PLACEHOLDER.network_interface[0].addresses[0],"22","ssh"]}
}
