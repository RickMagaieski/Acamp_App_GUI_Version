ACAMP WBSDAC - Versão portátil para Windows
============================================

COMO ABRIR

1. Mantenha toda a pasta Acamp_App_GUI junta.
2. Abra Acamp_App_GUI.exe.

Python, PyCharm e um ambiente virtual não são necessários no computador de
destino. Esta é uma aplicação portátil: não há instalador nem atualização
automática.

PASTA user_data

Os arquivos privados ficam fora do executável, na pasta user_data ao lado
de Acamp_App_GUI.exe. Coloque manualmente nessa pasta, conforme necessário:

- participants.json
- items.json
- teams.json
- client_secret.json
- token.json (opcional, para reutilizar uma autorização existente)

Nunca publique, envie a terceiros ou coloque esses arquivos em um
repositório público. Nunca adicione token.json ao arquivo ZIP de
distribuição. Se um token existente não for transferido manualmente para
uma cópia local da pasta user_data, ele será criado ou atualizado nessa
pasta após uma autorização Google bem-sucedida.

ARQUIVOS AUSENTES

O aplicativo continua aberto quando participants.json, items.json ou
teams.json não existem e mostra o estado correspondente na interface.
Confira o nome do arquivo, a extensão e se ele está diretamente dentro de
user_data.

GOOGLE SHEETS E USO OFFLINE

A sincronização com Google Sheets é sempre manual. Ela nunca começa ao
abrir o aplicativo. Para autorizar o Google, client_secret.json deve estar
em user_data. A primeira autorização pode abrir o navegador padrão e criar
token.json localmente; autorizações expiradas podem atualizar esse token.

Sem internet, os recursos locais continuam disponíveis usando os dados já
presentes em user_data. Sincronização e exclusão remota exigem conexão.

WINDOWS SMARTSCREEN

Esta versão pessoal não é assinada digitalmente. O Windows SmartScreen pode
mostrar um aviso para um executável desconhecido. Confirme que a pasta veio
da fonte esperada e use as opções oferecidas pelo próprio Windows para
continuar apenas se você confiar no arquivo. Não desative as proteções do
Windows.

LIMITAÇÕES ATUAIS

- Não há instalador, assinatura digital ou atualização automática.
- A sincronização Google é manual e depende das credenciais e permissões
  configuradas.
- Backups dos arquivos em user_data são responsabilidade do usuário.
- A pasta portátil precisa permanecer completa; mover somente o executável
  pode impedir a inicialização.
