import ssl
import json
import os
import argparse
from datetime import datetime
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import yaml

# === CONFIG ===
with open("vars.yml", "r") as f:
    config = yaml.safe_load(f)

VCENTER_HOST = config["vcenter_hostname"]
VCENTER_USER = config["vcenter_username"]
VCENTER_PASS = config["vcenter_password"]
DATACENTER_NAME = config.get("datacenter_name", "Desconhecido")
ARQUIVO_ESTADO = "vms_atuais.json"
ARQUIVO_LOG_NOVAS = "novas_vms_detectadas.json"
DIRETORIO_SAIDA = "vm_data"

os.makedirs(DIRETORIO_SAIDA, exist_ok=True)

# === ARGS ===
parser = argparse.ArgumentParser()
parser.add_argument("--single", help="Nome de uma VM específica")
args = parser.parse_args()

# === CONEXÃO VCENTER ===
context = ssl._create_unverified_context()
si = SmartConnect(host=VCENTER_HOST, user=VCENTER_USER, pwd=VCENTER_PASS, sslContext=context)
content = si.RetrieveContent()

# === COLETAR VMs ===
vms = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view
vms = sorted(vms, key=lambda vm: vm.name)
nomes_atuais = [vm.name.replace("*", "").strip() for vm in vms]

# === MODO --single ===
if args.single:
    vm = next((vm for vm in vms if vm.name.replace("*", "").strip().lower() == args.single.lower()), None)
    if vm:
        def exportar_vm(vm_obj):
            nome_vm = vm_obj.name.replace("*", "").strip()
            summary = vm_obj.summary
            config = vm_obj.config
            runtime = vm_obj.runtime
            guest = vm_obj.guest

            interfaces = []
            if guest and hasattr(guest, "net"):
                for idx, dev in enumerate(guest.net):
                    ip_list = dev.ipAddress if dev.ipAddress else []
                    interfaces.append({
                        "name": f"eth{idx}",
                        "macaddress": dev.macAddress,
                        "ipaddresses": ip_list
                    })

            disco_gb = sum([
                dev.capacityInKB for dev in config.hardware.device
                if isinstance(dev, vim.vm.device.VirtualDisk)
            ]) / 1024 / 1024

            data = {
                "name": nome_vm,
                "uuid": config.uuid,
                "power_state": runtime.powerState,
                "memory": config.hardware.memoryMB,
                "vcpus": config.hardware.numCPU,
                "disk": round(disco_gb, 2),
                "cluster": vm_obj.resourcePool.owner.name if vm_obj.resourcePool else "Unknown",
                "datacenter": DATACENTER_NAME,
                "folder": vm_obj.parent.name if vm_obj.parent else "",
                "interfaces": interfaces,
                "status": "active" if runtime.powerState == "poweredOn" else "offline"
            }

            nome_arquivo = os.path.join(DIRETORIO_SAIDA, f"{nome_vm.lower().replace('_', '-').replace(' ', '-')}.json")
            with open(nome_arquivo, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[INFO] Exportado: {nome_arquivo}")

        exportar_vm(vm)
    Disconnect(si)
    exit(0)

# === COMPARAÇÃO COM ESTADO ANTERIOR ===
try:
    with open(ARQUIVO_ESTADO, "r") as f:
        nomes_anteriores = json.load(f)
except FileNotFoundError:
    nomes_anteriores = []

novas_vms = sorted(list(set(nomes_atuais) - set(nomes_anteriores)))

def exportar_vm(vm_obj):
    nome_vm = vm_obj.name.replace("*", "").strip()
    summary = vm_obj.summary
    config = vm_obj.config
    runtime = vm_obj.runtime
    guest = vm_obj.guest

    interfaces = []
    if guest and hasattr(guest, "net"):
        for idx, dev in enumerate(guest.net):
            ip_list = dev.ipAddress if dev.ipAddress else []
            interfaces.append({
                "name": f"eth{idx}",
                "macaddress": dev.macAddress,
                "ipaddresses": ip_list
            })

    disco_gb = sum([
        dev.capacityInKB for dev in config.hardware.device
        if isinstance(dev, vim.vm.device.VirtualDisk)
    ]) / 1024 / 1024

    data = {
        "name": nome_vm,
        "uuid": config.uuid,
        "power_state": runtime.powerState,
        "memory": config.hardware.memoryMB,
        "vcpus": config.hardware.numCPU,
        "disk": round(disco_gb, 2),
        "cluster": vm_obj.resourcePool.owner.name if vm_obj.resourcePool else "Unknown",
        "datacenter": DATACENTER_NAME,
        "folder": vm_obj.parent.name if vm_obj.parent else "",
        "interfaces": interfaces,
        "status": "active" if runtime.powerState == "poweredOn" else "offline"
    }

    nome_arquivo = os.path.join(DIRETORIO_SAIDA, f"{nome_vm.lower().replace('_', '-').replace(' ', '-')}.json")
    with open(nome_arquivo, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Exportado: {nome_arquivo}")

# === EXPORTAR SOMENTE AS NOVAS ===
log = []
if novas_vms:
    print("[INFO] Novas VMs detectadas:")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for nome in novas_vms:
        print(f" - {nome}")
        log.append({"nome": nome, "detectado_em": timestamp})
        vm_obj = next((vm for vm in vms if vm.name.replace("*", "").strip() == nome), None)
        if vm_obj:
            exportar_vm(vm_obj)

# === SALVAR ESTADO ATUAL E LOG DE NOVAS ===
with open(ARQUIVO_ESTADO, "w") as f:
    json.dump(nomes_atuais, f, indent=2)

with open(ARQUIVO_LOG_NOVAS, "w") as f:
    json.dump(log, f, indent=2)

Disconnect(si)
