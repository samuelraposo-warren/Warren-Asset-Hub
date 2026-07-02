"""Configuração das especificações por tipo de ativo.

Mapeia o slug do AssetType para o model de spec correspondente, o nome do
relacionamento em Asset e a lista de campos do formulário. Usado tanto para
renderizar o formulário dinâmico quanto para persistir os valores.

Cada campo: {key, label, type, enum?}
  type: "text" | "number" | "checkbox" | "select"
  enum: classe Enum (obrigatório quando type == "select")
"""
from app.models.enums import (
    ConnectionType,
    FormFactor,
    NetworkDeviceType,
    PanelType,
    PrinterType,
    StorageType,
)
from app.models.specs import (
    DesktopSpec,
    MonitorSpec,
    NetworkSpec,
    NotebookSpec,
    PeripheralSpec,
    PrinterSpec,
    ServerSpec,
)


def _f(key, label, type_, enum=None):
    return {"key": key, "label": label, "type": type_, "enum": enum}


SPEC_CONFIG = {
    "notebook": {
        "model": NotebookSpec,
        "rel": "notebook_spec",
        "label": "Especificações do notebook",
        "fields": [
            _f("cpu", "CPU", "text"),
            _f("ram_gb", "RAM (GB)", "number"),
            _f("storage_gb", "Armazenamento (GB)", "number"),
            _f("storage_type", "Tipo de armazenamento", "select", StorageType),
            _f("screen_size", "Tamanho da tela", "text"),
            _f("os", "Sistema operacional", "text"),
            _f("os_version", "Versão do SO", "text"),
            _f("battery_health", "Saúde da bateria (%)", "number"),
        ],
    },
    "desktop": {
        "model": DesktopSpec,
        "rel": "desktop_spec",
        "label": "Especificações do desktop",
        "fields": [
            _f("cpu", "CPU", "text"),
            _f("ram_gb", "RAM (GB)", "number"),
            _f("storage_gb", "Armazenamento (GB)", "number"),
            _f("storage_type", "Tipo de armazenamento", "select", StorageType),
            _f("has_gpu", "Possui GPU dedicada", "checkbox"),
            _f("gpu_model", "Modelo da GPU", "text"),
            _f("form_factor", "Formato", "select", FormFactor),
        ],
    },
    "monitor": {
        "model": MonitorSpec,
        "rel": "monitor_spec",
        "label": "Especificações do monitor",
        "fields": [
            _f("screen_size", "Tamanho da tela", "text"),
            _f("resolution", "Resolução", "text"),
            _f("panel_type", "Tipo de painel", "select", PanelType),
            _f("refresh_rate_hz", "Taxa de atualização (Hz)", "number"),
            _f("ports", "Portas", "text"),
        ],
    },
    "printer": {
        "model": PrinterSpec,
        "rel": "printer_spec",
        "label": "Especificações da impressora",
        "fields": [
            _f("printer_type", "Tipo", "select", PrinterType),
            _f("is_colorful", "Colorida", "checkbox"),
            _f("is_network", "Impressora de rede", "checkbox"),
            _f("ip_address", "Endereço IP", "text"),
        ],
    },
    "server": {
        "model": ServerSpec,
        "rel": "server_spec",
        "label": "Especificações do servidor",
        "fields": [
            _f("cpu", "CPU", "text"),
            _f("ram_gb", "RAM (GB)", "number"),
            _f("storage_gb", "Armazenamento (GB)", "number"),
            _f("storage_type", "Tipo de armazenamento", "select", StorageType),
            _f("raid_type", "Tipo de RAID", "text"),
            _f("os", "Sistema operacional", "text"),
            _f("os_version", "Versão do SO", "text"),
            _f("ip_address", "Endereço IP", "text"),
            _f("rack_position", "Posição no rack", "text"),
        ],
    },
    "network": {
        "model": NetworkSpec,
        "rel": "network_spec",
        "label": "Especificações do dispositivo de rede",
        "fields": [
            _f("device_type", "Tipo de dispositivo", "select", NetworkDeviceType),
            _f("ports_count", "Número de portas", "number"),
            _f("ip_address", "Endereço IP", "text"),
            _f("managed", "Gerenciável", "checkbox"),
        ],
    },
    "peripheral": {
        "model": PeripheralSpec,
        "rel": "peripheral_spec",
        "label": "Especificações do periférico",
        "fields": [
            _f("peripheral_type", "Tipo (Teclado, Mouse...)", "text"),
            _f("connection_type", "Tipo de conexão", "select", ConnectionType),
        ],
    },
}
