from src.utils import get_resource_value, get_resource_name

def get_label(resource):
    name = get_resource_name(resource)
    machine_type = get_resource_value(resource, "machine_type", "")
    zone = get_resource_value(resource, "zone", "")
    
    network_access = []
    
    exprs = resource.get('expressions', {})
    if 'network_interface' in exprs:
        nics = exprs['network_interface']
        if isinstance(nics, list) and len(nics) > 0:
            nic = nics[0]
            if 'access_config' in nic:
                ac = nic['access_config']
                if isinstance(ac, list) and len(ac) > 0:
                    if 'nat_ip' in ac[0]:
                        network_access.append("External IP: Static")
                    else:
                        network_access.append("External IP: Ephemeral")

    image = ""
    if 'boot_disk' in exprs:
        disks = exprs['boot_disk']
        if isinstance(disks, list) and len(disks) > 0:
            init_params = disks[0].get('initialize_params', [])
            if isinstance(init_params, list) and len(init_params) > 0:
                    img_val = init_params[0].get('image', {}).get('constant_value')
                    if img_val:
                        image = img_val.split('/')[-1]

    label = f"{name}"
    if machine_type:
        label += f"\n{machine_type}"
    if zone:
        label += f"\n{zone}"
    if image:
        label += f"\n{image}"
    if network_access:
        label += f"\n{', '.join(network_access)}"
        
    return label
