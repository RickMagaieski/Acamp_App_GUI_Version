# ACAMP WBSDAC Desktop

Aplicação desktop em PySide6 para administrar inscrições, inventário,
finanças, equipes, atividades, relatórios e indicadores do acampamento.
A interface compartilha um único estado entre as páginas e mantém as regras
financeiras e de relatórios centralizadas.

## Recursos principais

- Dashboard com indicadores e atalhos de navegação
- Consulta, pesquisa, paginação e remoção segura de inscrições
- Cadastro e remoção de itens do inventário
- Resumo financeiro e classificação de pagamentos
- Gerenciamento de equipes, participantes e pontuação
- Relatórios agregados e gráficos redimensionáveis
- Sincronização manual de inscrições com Google Sheets

## Requisitos

- Windows com Python 3.11 ou mais recente
- Dependências listadas em `requirements.txt`

O desenvolvimento e os testes atuais usam Python 3.13. A criação do
executável do Windows será realizada separadamente na Fase 4B.

## Ambiente de desenvolvimento

No PowerShell, a partir da pasta do projeto:

```powershell
py -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Para iniciar a interface:

```powershell
python gui_main.py
```

O diretório atual do terminal não é usado para localizar os dados. Durante
o desenvolvimento, os arquivos locais são resolvidos a partir da pasta da
aplicação.

## Arquivos locais privados

Os arquivos abaixo devem permanecer na pasta da aplicação e nunca devem ser
adicionados ao Git:

- `participants.json`
- `items.json`
- `teams.json`
- `client_secret.json`
- `token.json`

Os três arquivos JSON armazenam os dados locais. `client_secret.json`
contém a configuração OAuth fornecida para o aplicativo, e `token.json` é
criado ou atualizado após uma autorização bem-sucedida.

Não copie dados reais, credenciais ou tokens para testes, código-fonte,
documentação, relatórios, capturas de tela ou pacotes distribuídos.

## Google Sheets

A sincronização é sempre iniciada manualmente pelo botão do Dashboard.
Nenhuma conexão, autenticação ou abertura de navegador ocorre
automaticamente na inicialização.

Na primeira sincronização autorizada, o navegador pode ser aberto para o
fluxo OAuth do Google. Falhas de conexão ou autenticação preservam o estado
local existente.

## Testes

Os testes usam apenas registros inventados, diretórios temporários e serviços
Google simulados:

```powershell
python -m unittest discover -s tests
```

## Estado do projeto

A Fase 4A cobre testes integrados, correções, limpeza e preparação para
empacotamento. O projeto ainda é executado por `gui_main.py`; nenhum
executável é criado nesta fase. O empacotamento para Windows será tratado na
Fase 4B.
