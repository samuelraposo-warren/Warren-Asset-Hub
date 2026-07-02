"""Configuração dos cadastros de apoio (CRUD genérico config-driven).

Cada entidade define o model, rótulos, ícone e a lista de campos. As rotas
genéricas em app/routes/registry.py e os templates registry/list.html e
registry/form.html usam essa config — assim, um novo cadastro simples é só
adicionar uma entrada aqui.

Tipos de campo: text | email | number | textarea | fk
  fk: {key, label, type='fk', model, display, rel, [list]}
    - model:   classe do alvo da FK (para popular o select)
    - display: atributo exibido de cada opção (ex.: 'name')
    - rel:     nome do relacionamento em Asset/entidade (para exibir na lista)
"""
from app.models.employee import Department, Employee
from app.models.location import Branch, Location
from app.models.supplier import Supplier


def _field(key, label, type_="text", required=False, list_=False, **extra):
    return {"key": key, "label": label, "type": type_,
            "required": required, "list": list_, **extra}


REGISTRY = {
    "suppliers": {
        "model": Supplier,
        "singular": "Fornecedor",
        "plural": "Fornecedores",
        "icon": "bi-truck",
        "fields": [
            _field("name", "Nome", required=True, list_=True),
            _field("cnpj", "CNPJ", list_=True),
            _field("contact_name", "Contato", list_=True),
            _field("phone", "Telefone"),
            _field("email", "E-mail", "email", list_=True),
            _field("notes", "Observações", "textarea"),
        ],
    },
    "branches": {
        "model": Branch,
        "singular": "Unidade",
        "plural": "Unidades",
        "icon": "bi-building",
        "fields": [
            _field("name", "Nome", required=True, list_=True),
            _field("address", "Endereço", list_=True),
        ],
    },
    "locations": {
        "model": Location,
        "singular": "Localização",
        "plural": "Localizações",
        "icon": "bi-geo-alt",
        "fields": [
            _field("name", "Nome", required=True, list_=True),
            _field("branch_id", "Unidade", "fk", model=Branch,
                   display="name", rel="branch", list_=True),
            _field("floor", "Andar", list_=True),
            _field("room", "Sala", list_=True),
        ],
    },
    "departments": {
        "model": Department,
        "singular": "Departamento",
        "plural": "Departamentos",
        "icon": "bi-diagram-3",
        "fields": [
            _field("name", "Nome", required=True, list_=True),
        ],
    },
    "employees": {
        "model": Employee,
        "singular": "Funcionário",
        "plural": "Funcionários",
        "icon": "bi-people",
        "fields": [
            _field("name", "Nome", required=True, list_=True),
            _field("employee_id", "Matrícula", required=True, list_=True),
            _field("email", "E-mail", "email", list_=True),
            _field("department_id", "Departamento", "fk", model=Department,
                   display="name", rel="department", list_=True),
        ],
    },
}
