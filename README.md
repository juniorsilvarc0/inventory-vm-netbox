# Inventário de VMs e Sincronização com NetBox via AWX

Este projeto coleta informações de máquinas virtuais no vCenter, detecta novas VMs, gera arquivos JSON com os dados e sincroniza as VMs no NetBox automaticamente.

---

## 📦 Estrutura

```
.
├── playbooks/
│   └── main.yml
├── roles/
│   └── detectar_vms/
│       ├── files/
│       │   └── detectar_novas_vms.py
│       ├── tasks/
│       │   └── main.yml
│       └── vars/
│           └── main.yml
├── tasks/
│   └── sync_single_vm.yml
└── vars.yml
```

---

## ⚙️ Requisitos

- NetBox acessível via API
- vCenter acessível com usuário autorizado
- AWX configurado

---

## 🔐 Credenciais

Todas as credenciais são injetadas via AWX e **não estão no repositório**:

### 1. Credential Type (vCenter + NetBox)

Crie um tipo de credencial personalizado com os seguintes campos:

```yaml
fields:
  - id: VCENTER_HOST
    type: string
  - id: VCENTER_USER
    type: string
  - id: VCENTER_PASSWORD
    type: string
    secret: true
  - id: DATACENTER_NAME
    type: string
  - id: NETBOX_URL
    type: string
  - id: NETBOX_TOKEN
    type: string
    secret: true
```

```yaml
env:
  VCENTER_HOST: "{{ VCENTER_HOST }}"
  VCENTER_USER: "{{ VCENTER_USER }}"
  VCENTER_PASSWORD: "{{ VCENTER_PASSWORD }}"
  DATACENTER_NAME: "{{ DATACENTER_NAME }}"
  NETBOX_URL: "{{ NETBOX_URL }}"
  NETBOX_TOKEN: "{{ NETBOX_TOKEN }}"
```

---

## 🚀 Execução via AWX

1. Crie um Projeto apontando para este repositório Git.
2. Crie um Inventário (pode ser vazio ou apenas `localhost`).
3. Crie uma Credencial com os campos acima.
4. Crie um Job Template:
   - **Playbook:** `playbooks/main.yml`
   - **Inventário:** `localhost`
   - **Credencial:** a criada acima

---

## 📄 Resultado

- Novas VMs detectadas são registradas em:
  - `novas_vms_detectadas.json`
  - `vm_data/*.json`
- As VMs são criadas/atualizadas no NetBox com IPs e interfaces.

---

## 🧪 Teste local

Você pode testar localmente usando um `.env`:

```bash
export VCENTER_HOST="vcenter.local"
export VCENTER_USER="admin"
export VCENTER_PASSWORD="senha"
export DATACENTER_NAME="Datacenter1"
export NETBOX_URL="http://netbox.local"
export NETBOX_TOKEN="token"
python3 roles/detectar_vms/files/detectar_novas_vms.py
```

---

## ✅ Licença

Projeto interno para automação de inventário de infraestrutura com Ansible e AWX.
