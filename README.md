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

O desenvolvimento e os testes atuais usam Python 3.13. O executável
portátil do Windows é criado separadamente com PyInstaller.

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

Na execução empacotada, um assistente é aberto quando a localização dos
dados ainda não foi configurada ou quando falta algum dos três arquivos
obrigatórios. O usuário pode escolher uma pasta existente ou importar
explicitamente arquivos selecionados para `user_data`. A estratégia fica
registrada em `data_location.json`, que contém apenas o modo escolhido e,
quando aplicável, o caminho da pasta.

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

## Empacotamento para Windows

As dependências de desenvolvimento ficam em `requirements-dev.txt`. Para
executar os testes e criar a distribuição portátil em modo one-folder:

```powershell
python -m pip install -r requirements-dev.txt
& .\scripts\build_windows.ps1
```

Use `-SkipTests` somente quando os testes já tiverem sido executados na
mesma revisão. O executável é criado em
`dist\Acamp_App_GUI\Acamp_App_GUI.exe`, e o arquivo portátil em
`release\Acamp_App_GUI_Windows.zip`.

Na execução empacotada, dados e credenciais privados permanecem externos.
O assistente pode usar diretamente uma pasta escolhida ou copiar somente
os arquivos selecionados pelo usuário para `user_data`. Nenhum arquivo
privado é copiado automaticamente do projeto ou incluído na distribuição.
O arquivo `README_RELEASE.txt` contém as instruções destinadas ao usuário
da versão portátil.
