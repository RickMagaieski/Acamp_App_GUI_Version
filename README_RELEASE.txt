ACAMP WBSDAC - Versão portátil para Windows
============================================

COMO ABRIR

1. Mantenha toda a pasta Acamp_App_GUI junta.
2. Abra Acamp_App_GUI.exe.

Python, PyCharm e um ambiente virtual não são necessários no computador de
destino. Esta é uma aplicação portátil: não há instalador nem atualização
automática.

CONFIGURAÇÃO DOS DADOS

Os arquivos privados permanecem fora do executável. Na primeira execução,
o assistente de configuração oferece duas opções:

1. Escolher uma pasta existente e usar os arquivos diretamente nela.
2. Selecionar um ou mais arquivos para importá-los para a pasta user_data
   desta aplicação.

Não é necessário copiar e colar arquivos manualmente pelo Explorador de
Arquivos. A configuração escolhida fica registrada em user_data e é
reutilizada nas próximas execuções, independentemente da pasta de trabalho
usada para abrir o programa. O arquivo de configuração registra somente o
modo de uso e, quando aplicável, o caminho absoluto da pasta escolhida; ele
não armazena credenciais nem o conteúdo dos participantes.

Os arquivos obrigatórios são:

- participants.json
- items.json
- teams.json

Os arquivos Google são opcionais:

- client_secret.json
- token.json (opcional, para reutilizar uma autorização existente)

Nunca publique, envie a terceiros ou coloque esses arquivos em um
repositório público. Nunca adicione token.json ao arquivo ZIP de
distribuição. Se um token existente não for selecionado para importação,
ele será criado ou atualizado na pasta de dados configurada após uma
autorização Google bem-sucedida.

ARQUIVOS AUSENTES

O aplicativo continua aberto quando participants.json, items.json ou
teams.json não existem e oferece novamente o assistente na próxima
inicialização. Confira o nome e a extensão do arquivo ou escolha outra
pasta pelo assistente.

GOOGLE SHEETS E USO OFFLINE

A sincronização com Google Sheets é sempre manual. Ela nunca começa ao
abrir o aplicativo. Para autorizar o Google, client_secret.json deve estar
na pasta de dados configurada. A primeira autorização pode abrir o navegador
padrão e criar token.json localmente; autorizações expiradas podem atualizar
esse token.

Sem internet e sem credenciais Google, os recursos locais continuam
disponíveis usando a pasta de dados configurada. Sincronização e exclusão
remota exigem conexão e uma ação manual do usuário. O aplicativo não exige
privilégios de administrador.

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
- Backups dos arquivos da pasta de dados são responsabilidade do usuário.
- A pasta portátil precisa permanecer completa; mover somente o executável
  pode impedir a inicialização.
