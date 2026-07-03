-- ============================================================
-- seed_demo.sql — Dados de demonstração para apresentação
-- Sistema Oficial de Inventário de Máquinas
--
-- Como rodar (a partir da pasta do projeto):
--   mysql -u root -p inventory_system < seed_demo.sql
-- ou dentro do cliente mysql:
--   USE inventory_system; SOURCE seed_demo.sql;
--
-- Observações:
--  * Inserção via SQL bruto NÃO gera registros em audit_logs
--    (os listeners de auditoria são da camada ORM). Ideal p/ seed.
--  * Não colide com o que já foi cadastrado pela tela (usa nomes,
--    matrículas e patrimônios novos).
--  * Datas de garantia foram calculadas em relação a CURDATE() para
--    o painel destacar "garantias vencendo" automaticamente.
-- ============================================================

SET NAMES utf8mb4;
START TRANSACTION;

-- Usuário que consta como criador dos registros (admin, se existir).
SET @admin_id := (SELECT id FROM users WHERE role = 'ADMIN' ORDER BY id LIMIT 1);

-- ------------------------------------------------------------
-- FORNECEDORES
-- ------------------------------------------------------------
INSERT INTO suppliers (name, cnpj, contact_name, phone, email, notes, is_active, created_at) VALUES
('Lenovo Tecnologia (Brasil) Ltda', '07.275.920/0001-61', 'Ricardo Tanaka', '(11) 3040-1000', 'corporativo@lenovo.com.br', 'Contrato de notebooks corporativos.', 1, NOW()),
('HP Brasil Indústria e Comércio',  '61.797.924/0001-55', 'Sandra Vieira',  '(11) 3030-2000', 'vendas@hp.com.br',        'Impressoras e desktops.', 1, NOW()),
('Positivo Tecnologia S.A.',         '81.243.735/0001-48', 'Marcos Bianchi', '(41) 3316-7000', 'b2b@positivo.com.br',     'Fornecedor nacional.', 1, NOW()),
('Intelbras S.A.',                   '82.901.000/0001-27', 'Paula Fernandes','(48) 2106-0000', 'comercial@intelbras.com.br','Redes e segurança.', 1, NOW()),
('Samsung Eletrônica da Amazônia',   '00.280.273/0001-37', 'Yuri Nakamura',  '(11) 3579-8000', 'corp@samsung.com.br',     'Monitores e SSDs.', 1, NOW()),
('TP-Link do Brasil',                '13.837.732/0001-40', 'Cléber Antunes', '(11) 2100-8800', 'vendas@tp-link.com.br',   'Switches e access points.', 1, NOW()),
('Kingston Brasil Distribuidora',    '05.545.222/0001-09', 'Renata Prado',   '(11) 4200-3000', 'canais@kingston.com.br',  'Memórias e armazenamento.', 1, NOW()),
('Multilaser Industrial S.A.',       '59.717.553/0001-02', 'Alan Rocha',     '(11) 4003-7070', 'b2b@multilaser.com.br',   'Periféricos diversos.', 1, NOW());

-- ------------------------------------------------------------
-- UNIDADES (BRANCHES)
-- ------------------------------------------------------------
INSERT INTO branches (name, address) VALUES
('Filial Rio de Janeiro',             'Av. Rio Branco, 156 - Centro, Rio de Janeiro/RJ'),
('Filial Belo Horizonte',             'Av. Afonso Pena, 1500 - Centro, Belo Horizonte/MG'),
('Filial Curitiba',                   'Rua XV de Novembro, 700 - Centro, Curitiba/PR'),
('Centro de Distribuição Campinas',   'Rod. Anhanguera, km 100 - Campinas/SP');

-- ------------------------------------------------------------
-- LOCALIZAÇÕES (LOCATIONS) — vinculadas às unidades por nome
-- "Matriz São Paulo" já existe (cadastrada pela tela).
-- ------------------------------------------------------------
INSERT INTO locations (name, branch_id, floor, room) VALUES
('Data Center Matriz',   (SELECT id FROM branches WHERE name='Matriz São Paulo'),           'Térreo', 'DC-01'),
('Diretoria SP',         (SELECT id FROM branches WHERE name='Matriz São Paulo'),           '10º',    '1001'),
('Recepção RJ',          (SELECT id FROM branches WHERE name='Filial Rio de Janeiro'),      'Térreo', 'REC'),
('Sala Comercial RJ',    (SELECT id FROM branches WHERE name='Filial Rio de Janeiro'),      '5º',     '502'),
('Sala de Reunião RJ',   (SELECT id FROM branches WHERE name='Filial Rio de Janeiro'),      '5º',     '505'),
('Financeiro BH',        (SELECT id FROM branches WHERE name='Filial Belo Horizonte'),      '3º',     '301'),
('Estoque BH',           (SELECT id FROM branches WHERE name='Filial Belo Horizonte'),      'Térreo', 'EST'),
('Suporte Curitiba',     (SELECT id FROM branches WHERE name='Filial Curitiba'),            '2º',     '201'),
('Almoxarifado CD',      (SELECT id FROM branches WHERE name='Centro de Distribuição Campinas'), 'Galpão', 'ALM-1');

-- ------------------------------------------------------------
-- DEPARTAMENTOS
-- "Tecnologia da Informação" já existe (cadastrado pela tela).
-- ------------------------------------------------------------
INSERT INTO departments (name) VALUES
('Financeiro'),
('Recursos Humanos'),
('Comercial'),
('Operações'),
('Diretoria'),
('Marketing');

-- ------------------------------------------------------------
-- FUNCIONÁRIOS
-- ------------------------------------------------------------
INSERT INTO employees (name, email, employee_id, department_id, is_active, created_at) VALUES
('Ana Souza',        'ana.souza@empresa.com',       'MAT-1001', (SELECT id FROM departments WHERE name='Financeiro'), 1, NOW()),
('Bruno Lima',       'bruno.lima@empresa.com',      'MAT-1002', (SELECT id FROM departments WHERE name='Financeiro'), 1, NOW()),
('Camila Rocha',     'camila.rocha@empresa.com',    'MAT-1003', (SELECT id FROM departments WHERE name='Recursos Humanos'), 1, NOW()),
('Diego Martins',    'diego.martins@empresa.com',   'MAT-1004', (SELECT id FROM departments WHERE name='Comercial'), 1, NOW()),
('Eduarda Alves',    'eduarda.alves@empresa.com',   'MAT-1005', (SELECT id FROM departments WHERE name='Comercial'), 1, NOW()),
('Felipe Costa',     'felipe.costa@empresa.com',    'MAT-1006', (SELECT id FROM departments WHERE name='Operações'), 1, NOW()),
('Gabriela Nunes',   'gabriela.nunes@empresa.com',  'MAT-1007', (SELECT id FROM departments WHERE name='Operações'), 1, NOW()),
('Henrique Dias',    'henrique.dias@empresa.com',   'MAT-1008', (SELECT id FROM departments WHERE name='Diretoria'), 1, NOW()),
('Isabela Ferreira', 'isabela.ferreira@empresa.com','MAT-1009', (SELECT id FROM departments WHERE name='Marketing'), 1, NOW()),
('João Pereira',     'joao.pereira@empresa.com',    'MAT-1010', (SELECT id FROM departments WHERE name='Marketing'), 1, NOW()),
('Karina Melo',      'karina.melo@empresa.com',     'MAT-1011', (SELECT id FROM departments WHERE name='Tecnologia da Informação'), 1, NOW()),
('Lucas Gomes',      'lucas.gomes@empresa.com',     'MAT-1012', (SELECT id FROM departments WHERE name='Tecnologia da Informação'), 1, NOW()),
('Mariana Ribeiro',  'mariana.ribeiro@empresa.com', 'MAT-1013', (SELECT id FROM departments WHERE name='Comercial'), 1, NOW()),
('Nathan Barbosa',   'nathan.barbosa@empresa.com',  'MAT-1014', (SELECT id FROM departments WHERE name='Operações'), 1, NOW()),
('Olívia Cardoso',   'olivia.cardoso@empresa.com',  'MAT-1015', (SELECT id FROM departments WHERE name='Recursos Humanos'), 1, NOW()),
('Paulo Henrique',   'paulo.henrique@empresa.com',  'MAT-1016', (SELECT id FROM departments WHERE name='Financeiro'), 1, NOW());

-- ============================================================
-- ATIVOS + SPECS
-- Padrão: insere o ativo, captura o id em @aid e insere a spec.
-- ============================================================

-- ---------- NOTEBOOKS ----------
INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NB-1001','SN-LN-0001',(SELECT id FROM asset_types WHERE slug='notebook'),'Lenovo','ThinkPad E14','ACTIVE','GOOD','2023-08-10',DATE_ADD(CURDATE(), INTERVAL 13 DAY),4599.00,(SELECT id FROM suppliers WHERE name='Lenovo Tecnologia (Brasil) Ltda'),'NF-100201',(SELECT id FROM locations WHERE name='Sala Comercial RJ'),(SELECT id FROM employees WHERE employee_id='MAT-1004'),'Notebook do time comercial.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO notebook_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,screen_size,os,os_version,battery_health) VALUES (@aid,'Intel Core i5-1235U',16,512,'SSD','14"','Windows','11 Pro',91);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NB-1002','SN-DL-0002',(SELECT id FROM asset_types WHERE slug='notebook'),'Dell','Vostro 3520','ACTIVE','NEW','2024-11-02','2027-11-02',4200.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-100202',(SELECT id FROM locations WHERE name='Financeiro BH'),(SELECT id FROM employees WHERE employee_id='MAT-1001'),NULL,NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO notebook_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,screen_size,os,os_version,battery_health) VALUES (@aid,'Intel Core i7-1255U',16,512,'NVME','15.6"','Windows','11 Pro',99);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NB-1003','SN-HP-0003',(SELECT id FROM asset_types WHERE slug='notebook'),'HP','ProBook 440 G9','MAINTENANCE','FAIR','2022-05-19','2025-05-19',3899.00,(SELECT id FROM suppliers WHERE name='HP Brasil Indústria e Comércio'),'NF-100203',(SELECT id FROM locations WHERE name='Suporte Curitiba'),(SELECT id FROM employees WHERE employee_id='MAT-1013'),'Aguardando troca de teclado.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO notebook_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,screen_size,os,os_version,battery_health) VALUES (@aid,'Intel Core i5-1135G7',8,256,'SSD','14"','Windows','10 Pro',72);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NB-1004','SN-LN-0004',(SELECT id FROM asset_types WHERE slug='notebook'),'Lenovo','IdeaPad 3','LOANED','GOOD','2023-03-01','2026-03-01',3299.00,(SELECT id FROM suppliers WHERE name='Lenovo Tecnologia (Brasil) Ltda'),'NF-100204',(SELECT id FROM locations WHERE name='Sala de Reunião RJ'),(SELECT id FROM employees WHERE employee_id='MAT-1009'),'Emprestado para evento externo.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO notebook_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,screen_size,os,os_version,battery_health) VALUES (@aid,'AMD Ryzen 5 5500U',12,512,'SSD','15.6"','Windows','11 Home',85);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NB-1005','SN-PO-0005',(SELECT id FROM asset_types WHERE slug='notebook'),'Positivo','Motion Q464C','ACTIVE','GOOD','2024-01-15','2026-01-15',2599.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-100205',(SELECT id FROM locations WHERE name='Almoxarifado CD'),NULL,'Reserva técnica (sem responsável).',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO notebook_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,screen_size,os,os_version,battery_health) VALUES (@aid,'Intel Celeron N4020',4,128,'SSD','14"','Windows','11 Home',95);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NB-1006','SN-DL-0006',(SELECT id FROM asset_types WHERE slug='notebook'),'Dell','Latitude 3410','INACTIVE','POOR','2021-02-10','2024-02-10',3100.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-100206',(SELECT id FROM locations WHERE name='Estoque BH'),NULL,'Desativado, aguardando descarte.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO notebook_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,screen_size,os,os_version,battery_health) VALUES (@aid,'Intel Core i3-10110U',8,256,'HDD','14"','Windows','10 Pro',48);

-- ---------- DESKTOPS ----------
INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('DT-2001','SN-HP-2001',(SELECT id FROM asset_types WHERE slug='desktop'),'HP','EliteDesk 800 G6','ACTIVE','GOOD','2023-06-20','2026-06-20',3800.00,(SELECT id FROM suppliers WHERE name='HP Brasil Indústria e Comércio'),'NF-200201',(SELECT id FROM locations WHERE name='Financeiro BH'),(SELECT id FROM employees WHERE employee_id='MAT-1002'),NULL,NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO desktop_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,has_gpu,gpu_model,form_factor) VALUES (@aid,'Intel Core i5-10500',16,512,'SSD',0,NULL,'MINI');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('DT-2002','SN-DL-2002',(SELECT id FROM asset_types WHERE slug='desktop'),'Dell','OptiPlex 7010','ACTIVE','NEW','2024-07-30',DATE_ADD(CURDATE(), INTERVAL 28 DAY),4500.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-200202',(SELECT id FROM locations WHERE name='Diretoria SP'),(SELECT id FROM employees WHERE employee_id='MAT-1008'),'Estação da diretoria.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO desktop_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,has_gpu,gpu_model,form_factor) VALUES (@aid,'Intel Core i7-13700',32,1000,'NVME',1,'NVIDIA RTX 3060','TOWER');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('DT-2003','SN-PO-2003',(SELECT id FROM asset_types WHERE slug='desktop'),'Positivo','Master D340','ACTIVE','GOOD','2023-09-05','2026-09-05',2900.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-200203',(SELECT id FROM locations WHERE name='Recepção RJ'),NULL,'Uso compartilhado na recepção.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO desktop_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,has_gpu,gpu_model,form_factor) VALUES (@aid,'Intel Core i3-10105',8,256,'SSD',0,NULL,'MINI');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('DT-2004','SN-HP-2004',(SELECT id FROM asset_types WHERE slug='desktop'),'HP','ProDesk 400 G7','MAINTENANCE','FAIR','2022-04-12','2025-04-12',3200.00,(SELECT id FROM suppliers WHERE name='HP Brasil Indústria e Comércio'),'NF-200204',(SELECT id FROM locations WHERE name='Suporte Curitiba'),(SELECT id FROM employees WHERE employee_id='MAT-1014'),'Fonte com defeito intermitente.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO desktop_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,has_gpu,gpu_model,form_factor) VALUES (@aid,'Intel Core i5-10400',16,512,'SSD',0,NULL,'TOWER');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('DT-2005','SN-DL-2005',(SELECT id FROM asset_types WHERE slug='desktop'),'Dell','OptiPlex 3000','ACTIVE','GOOD','2024-02-28','2027-02-28',3600.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-200205',(SELECT id FROM locations WHERE name='Financeiro BH'),(SELECT id FROM employees WHERE employee_id='MAT-1016'),NULL,NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO desktop_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,has_gpu,gpu_model,form_factor) VALUES (@aid,'Intel Core i5-12400',16,512,'NVME',0,NULL,'MINI');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('DT-2006','SN-PO-2006',(SELECT id FROM asset_types WHERE slug='desktop'),'Positivo','Master C310','DISPOSED','DEFECTIVE','2020-08-01','2023-08-01',2400.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-200206',(SELECT id FROM locations WHERE name='Estoque BH'),NULL,'Descartado por obsolescência.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO desktop_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,has_gpu,gpu_model,form_factor) VALUES (@aid,'Intel Core i3-9100',4,500,'HDD',0,NULL,'TOWER');

-- ---------- IMPRESSORAS ----------
INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('PR-4001','SN-HP-4001',(SELECT id FROM asset_types WHERE slug='printer'),'HP','LaserJet Pro M404dn','ACTIVE','GOOD','2023-04-05','2026-04-05',1900.00,(SELECT id FROM suppliers WHERE name='HP Brasil Indústria e Comércio'),'NF-400201',(SELECT id FROM locations WHERE name='Financeiro BH'),NULL,'Impressora de rede do setor financeiro.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO printer_specs (asset_id,printer_type,is_colorful,is_network,ip_address) VALUES (@aid,'LASER',0,1,'10.20.30.40');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('PR-4002','SN-EP-4002',(SELECT id FROM asset_types WHERE slug='printer'),'Epson','EcoTank L3250','ACTIVE','NEW','2024-06-10','2026-06-10',1400.00,(SELECT id FROM suppliers WHERE name='Multilaser Industrial S.A.'),'NF-400202',(SELECT id FROM locations WHERE name='Sala Comercial RJ'),NULL,'Multifuncional colorida.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO printer_specs (asset_id,printer_type,is_colorful,is_network,ip_address) VALUES (@aid,'INKJET',1,1,'10.10.5.22');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('PR-4003','SN-BR-4003',(SELECT id FROM asset_types WHERE slug='printer'),'Brother','HL-1202','MAINTENANCE','POOR','2021-01-20','2023-01-20',700.00,(SELECT id FROM suppliers WHERE name='Multilaser Industrial S.A.'),'NF-400203',(SELECT id FROM locations WHERE name='Estoque BH'),NULL,'Tracionador de papel com problema.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO printer_specs (asset_id,printer_type,is_colorful,is_network,ip_address) VALUES (@aid,'LASER',0,0,NULL);

-- ---------- SERVIDORES ----------
INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('SV-5001','SN-DL-5001',(SELECT id FROM asset_types WHERE slug='server'),'Dell','PowerEdge R650','ACTIVE','NEW','2024-05-02','2029-05-02',48000.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-500201',(SELECT id FROM locations WHERE name='Data Center Matriz'),NULL,'Servidor de virtualização principal.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO server_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,raid_type,os,os_version,ip_address,rack_position) VALUES (@aid,'2x Intel Xeon Gold 6338',256,4000,'NVME','RAID 10','VMware ESXi','8.0','10.0.0.11','U20-U22');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('SV-5002','SN-HP-5002',(SELECT id FROM asset_types WHERE slug='server'),'HPE','ProLiant DL380','ACTIVE','GOOD','2022-06-15',DATE_ADD(CURDATE(), INTERVAL 23 DAY),39000.00,(SELECT id FROM suppliers WHERE name='HP Brasil Indústria e Comércio'),'NF-500202',(SELECT id FROM locations WHERE name='Data Center Matriz'),NULL,'Servidor de arquivos e backup.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO server_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,raid_type,os,os_version,ip_address,rack_position) VALUES (@aid,'2x Intel Xeon Silver 4210',128,8000,'SSD','RAID 6','Windows Server','2019','10.0.0.12','U16-U18');

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('SV-5003','SN-DL-5003',(SELECT id FROM asset_types WHERE slug='server'),'Dell','PowerEdge T340','MAINTENANCE','FAIR','2021-03-08','2024-03-08',22000.00,(SELECT id FROM suppliers WHERE name='Positivo Tecnologia S.A.'),'NF-500203',(SELECT id FROM locations WHERE name='Data Center Matriz'),NULL,'Disco 2 do RAID reportando falha.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO server_specs (asset_id,cpu,ram_gb,storage_gb,storage_type,raid_type,os,os_version,ip_address,rack_position) VALUES (@aid,'Intel Xeon E-2224',64,4000,'HDD','RAID 5','Ubuntu Server','20.04 LTS','10.0.0.13','U08');

-- ---------- REDE ----------
INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NW-6001','SN-TP-6001',(SELECT id FROM asset_types WHERE slug='network'),'TP-Link','TL-SG1024','ACTIVE','GOOD','2023-02-11','2028-02-11',1300.00,(SELECT id FROM suppliers WHERE name='TP-Link do Brasil'),'NF-600201',(SELECT id FROM locations WHERE name='Data Center Matriz'),NULL,'Switch core do rack principal.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO network_specs (asset_id,device_type,ports_count,ip_address,managed) VALUES (@aid,'SWITCH',24,'10.0.0.2',1);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NW-6002','SN-IN-6002',(SELECT id FROM asset_types WHERE slug='network'),'Intelbras','ACtion RG1200','ACTIVE','NEW','2024-08-19','2027-08-19',420.00,(SELECT id FROM suppliers WHERE name='Intelbras S.A.'),'NF-600202',(SELECT id FROM locations WHERE name='Recepção RJ'),NULL,'Roteador Wi-Fi da filial RJ.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO network_specs (asset_id,device_type,ports_count,ip_address,managed) VALUES (@aid,'ROUTER',4,'192.168.10.1',0);

INSERT INTO assets (asset_tag, serial_number, asset_type_id, brand, model, status, `condition`, purchase_date, warranty_expiry_date, purchase_price, supplier_id, invoice_number, location_id, assigned_to_id, notes, created_at, updated_at, created_by_id, is_active) VALUES
('NW-6003','SN-IN-6003',(SELECT id FROM asset_types WHERE slug='network'),'Intelbras','Firewall NextGen','ACTIVE','GOOD','2023-12-01','2026-12-01',8900.00,(SELECT id FROM suppliers WHERE name='Intelbras S.A.'),'NF-600203',(SELECT id FROM locations WHERE name='Data Center Matriz'),NULL,'Appliance de firewall de borda.',NOW(),NOW(),@admin_id,1);
SET @aid := LAST_INSERT_ID();
INSERT INTO network_specs (asset_id,device_type,ports_count,ip_address,managed) VALUES (@aid,'FIREWALL',8,'10.0.0.1',1);

-- ============================================================
-- MANUTENÇÕES (algumas em aberto p/ o painel destacar)
-- ============================================================
INSERT INTO maintenance_records (asset_id, type, description, performed_by, started_at, finished_at, cost, created_by_id, created_at) VALUES
((SELECT id FROM assets WHERE asset_tag='NB-1003'),'CORRECTIVE','Troca do teclado interno.','Assistência Lenovo', DATE_SUB(NOW(), INTERVAL 5 DAY), NULL, 350.00, @admin_id, NOW()),
((SELECT id FROM assets WHERE asset_tag='DT-2004'),'CORRECTIVE','Substituição da fonte de alimentação.','TI Interno', DATE_SUB(NOW(), INTERVAL 3 DAY), NULL, 220.00, @admin_id, NOW()),
((SELECT id FROM assets WHERE asset_tag='SV-5003'),'CORRECTIVE','Diagnóstico de falha no RAID.','Suporte Dell ProSupport', DATE_SUB(NOW(), INTERVAL 8 DAY), NULL, 0.00, @admin_id, NOW()),
((SELECT id FROM assets WHERE asset_tag='PR-4003'),'PREVENTIVE','Limpeza e revisão do tracionador.','TI Interno', DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 28 DAY), 120.00, @admin_id, NOW()),
((SELECT id FROM assets WHERE asset_tag='SV-5001'),'UPGRADE','Expansão de memória para 256GB.','TI Interno', DATE_SUB(NOW(), INTERVAL 60 DAY), DATE_SUB(NOW(), INTERVAL 59 DAY), 5200.00, @admin_id, NOW());

-- ============================================================
-- MOVIMENTAÇÕES (histórico / cadeia de custódia)
-- ============================================================
INSERT INTO asset_movements (asset_id, from_employee_id, to_employee_id, from_location_id, to_location_id, moved_by_id, moved_at, reason, notes) VALUES
((SELECT id FROM assets WHERE asset_tag='NB-1004'), NULL, (SELECT id FROM employees WHERE employee_id='MAT-1009'), NULL, (SELECT id FROM locations WHERE name='Sala de Reunião RJ'), @admin_id, DATE_SUB(NOW(), INTERVAL 10 DAY), 'Empréstimo para evento', 'Devolução prevista em 30 dias.'),
((SELECT id FROM assets WHERE asset_tag='DT-2005'), NULL, (SELECT id FROM employees WHERE employee_id='MAT-1016'), (SELECT id FROM locations WHERE name='Almoxarifado CD'), (SELECT id FROM locations WHERE name='Financeiro BH'), @admin_id, DATE_SUB(NOW(), INTERVAL 20 DAY), 'Alocação de novo colaborador', NULL);

COMMIT;

-- Conferência rápida:
SELECT
  (SELECT COUNT(*) FROM suppliers)            AS fornecedores,
  (SELECT COUNT(*) FROM branches)             AS unidades,
  (SELECT COUNT(*) FROM locations)            AS localizacoes,
  (SELECT COUNT(*) FROM departments)          AS departamentos,
  (SELECT COUNT(*) FROM employees)            AS funcionarios,
  (SELECT COUNT(*) FROM assets)               AS ativos,
  (SELECT COUNT(*) FROM maintenance_records)  AS manutencoes,
  (SELECT COUNT(*) FROM asset_movements)      AS movimentacoes;
