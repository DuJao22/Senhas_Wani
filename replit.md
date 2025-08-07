# Sistema Web "Caixa de Senhas" - SQLiteCloud Migration

## Visão Geral
Sistema web Flask para gerenciar até 5 senhas por carteirinha, desenvolvido por João Layon. Migrado de SQLite3 local para SQLiteCloud.

## Arquitetura Atual
- **Backend**: Flask + SQLiteCloud
- **Autenticação**: Flask-Login
- **Banco de Dados**: SQLiteCloud (migrado de SQLite3 local)
- **Frontend**: HTML5 + CSS + JavaScript

## Migração SQLiteCloud Concluída

### Alterações Realizadas
- ✅ Instalado pacote `sqlitecloud`
- ✅ Modificado `DatabaseManager` para usar SQLiteCloud
- ✅ Substituído todas as referências sqlite3 por sqlitecloud
- ✅ Mantido compatibilidade total com API sqlite3
- ✅ Configurado `row_factory` para acesso por nome de coluna
- ✅ Aplicação funcionando, aguardando connection string

### Migração Concluída - 07/08/2025
✅ **Connection String configurada**: `sqlitecloud://cmq6frwshz.g4.sqlite.cloud:8860/caixa_senhas.db?apikey=...`
✅ **Compatibilidade com dados existentes**: Sistema reconhece e utiliza os 4 usuários já cadastrados
✅ **Usuários admin criados**: admin e admin@gmail.com podem fazer login com senha admin123
✅ **Todas as funcionalidades operacionais**: Sistema totalmente funcional com SQLiteCloud
✅ **Bug do admin corrigido**: Problemas de mapeamento de índices nos métodos de usuário resolvidos
✅ **Carregamento de usuários corrigido**: Todos os 5 usuários do SQLiteCloud sendo listados corretamente

### Usuários Disponíveis no Sistema
- **admin** (Administrador) - Tipo: admin - ✅ Login: admin / admin123
- **admin@gmail.com** (Administrador do Sistema) - Tipo: admin - ✅ Login: admin@gmail.com / admin123
- **Janah** (Janaina Rodrigues) - Unidade: Contagem - Tipo: operador
- **Maria** (Maria Gabriela) - Unidade: Belo Horizonte - Tipo: operador
- **Jessica** (Jessica Rodrigues) - Unidade: Belo Horizonte - Tipo: operador

### Estrutura do Banco
- **Tabela usuarios**: Login, perfis (admin/operador), unidades
- **Tabela registros**: Carteirinhas, senhas (JSON), relacionamento com usuários

### Formato da Connection String SQLiteCloud
```
sqlitecloud://hostname:port/database.sqlite?apikey=your_api_key
```

### Status
- **Migração**: ✅ Completa
- **Aplicação**: ✅ Funcionando com SQLiteCloud
- **SQLiteCloud**: ✅ Conectado e operacional
- **Dados Existentes**: ✅ 4 usuários migrados do banco anterior
- **Login**: ✅ Funcional (admin / admin123 ou admin@gmail.com / admin123)

## Arquivos Principais
- `database.py`: Gerenciador de banco SQLiteCloud
- `app.py`: Aplicação Flask principal
- `main.py`: Entry point para gunicorn

## Funcionalidades
- Sistema de login com diferentes perfis
- Gestão de carteirinhas e senhas por unidade
- Interface web responsiva
- Controle de acesso baseado em perfis

## Data da Migração
07/08/2025 - Migração completa para SQLiteCloud mantendo todas as funcionalidades originais.