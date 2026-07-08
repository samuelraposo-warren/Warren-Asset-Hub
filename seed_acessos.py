# -*- coding: utf-8 -*-
"""Popula a camada de acessos do Centralizador com dados de teste.

Cria sub-setores (Acessos, Service Desk, Infra, Cyber), os módulos e alguns
usuários de exemplo com acessos por módulo. Idempotente (não duplica).

Rode DEPOIS do Atualizar_Banco.bat.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

SUBSECTORS = [
    ("Acessos", "acessos", "Gestão de acessos e identidades", "bi-key"),
    ("Service Desk", "service-desk", "Atendimento e chamados", "bi-headset"),
    ("Infra", "infra", "Infraestrutura e ativos", "bi-hdd-network"),
    ("Cyber", "cyber", "Segurança da informação", "bi-shield-lock"),
]

# (nome, slug, descricao, icone, endpoint|None, subsetor_slug, ordem)
MODULES = [
    ("Inventário de Máquinas", "inventario-maquinas",
     "Ativos de TI: máquinas, manutenções, movimentações", "bi-hdd-stack",
     "assets.list_assets", "infra", 10),
    ("Infraestrutura de Rede", "infraestrutura-rede",
     "Cabeamento, racks, salas e ocupação", "bi-diagram-3",
     "network.overview", "infra", 20),
    ("Certificados", "certificados",
     "Controle de certificados digitais e validades", "bi-file-earmark-lock",
     "certificates.list_certificates", "cyber", 10),
    ("Processos Críticos", "processos-criticos",
     "Histórico de processos críticos de TI", "bi-list-check",
     None, "service-desk", 10),
    ("Controle de Acessos", "controle-acessos",
     "Concessão e revisão de acessos", "bi-person-check",
     None, "acessos", 10),
]

# Usuários de exemplo: (nome, email, senha, role, subsetor_slug,
#                       [(modulo_slug, nivel VIEW|MANAGE), ...])
EXAMPLE_USERS = [
    ("Analista Infra", "analista.infra@warren.com", "infra123", "TI", "infra",
     [("inventario-maquinas", "MANAGE"), ("infraestrutura-rede", "VIEW")]),
    ("Consulta Service Desk", "consulta@warren.com", "consulta123", "VIEWER", "service-desk",
     [("inventario-maquinas", "VIEW")]),
]


def main():
    from app import create_app
    from app.extensions import db
    from app.models.access import ITSubsector, Module, UserModuleAccess
    from app.models.enums import ModuleAccessLevel, UserRole
    from app.models.user import User

    app = create_app()
    with app.app_context():
        db.create_all()  # garante as tabelas do módulo de acessos

        # Sub-setores
        subs = {}
        for name, slug, desc, icon in SUBSECTORS:
            s = ITSubsector.query.filter_by(slug=slug).first()
            if s is None:
                s = ITSubsector(name=name, slug=slug, description=desc, icon=icon)
                db.session.add(s)
                db.session.flush()
            subs[slug] = s

        # Módulos
        mods = {}
        for name, slug, desc, icon, endpoint, sub_slug, order in MODULES:
            m = Module.query.filter_by(slug=slug).first()
            if m is None:
                m = Module(name=name, slug=slug, description=desc, icon=icon,
                           endpoint=endpoint, sort_order=order,
                           subsector_id=subs[sub_slug].id)
                db.session.add(m)
                db.session.flush()
            mods[slug] = m
        db.session.commit()

        # Usuários de exemplo
        created_users = 0
        for name, email, pw, role_name, sub_slug, accesses in EXAMPLE_USERS:
            email = email.lower()
            u = User.query.filter_by(email=email).first()
            if u is None:
                u = User(name=name, email=email, role=UserRole[role_name],
                         is_active=True, must_change_password=True,
                         subsector_id=subs[sub_slug].id)
                u.set_password(pw)
                db.session.add(u)
                db.session.flush()
                created_users += 1
            # Acessos por módulo (idempotente)
            for mod_slug, level_name in accesses:
                mod = mods[mod_slug]
                exists = UserModuleAccess.query.filter_by(
                    user_id=u.id, module_id=mod.id
                ).first()
                if exists is None:
                    db.session.add(UserModuleAccess(
                        user_id=u.id, module_id=mod.id,
                        level=ModuleAccessLevel[level_name],
                    ))
        db.session.commit()

        gestores = User.query.filter_by(role=UserRole.ADMIN).count()
        print("Seed de acessos concluído:")
        print(f"  Sub-setores: {ITSubsector.query.count()}")
        print(f"  Módulos:     {Module.query.count()}")
        print(f"  Gestores (ADMIN): {gestores}")
        print(f"  Usuários de exemplo novos: {created_users}")
        if created_users:
            print("\n  Logins de teste (troque a senha no 1º acesso):")
            for _n, email, pw, *_ in EXAMPLE_USERS:
                print(f"    {email} / {pw}")


if __name__ == "__main__":
    main()
