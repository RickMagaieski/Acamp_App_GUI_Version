# ACAMP WBSDAC Desktop

A PySide6 desktop application for managing camp registrations, inventory,
finances, teams, activities, reports, and indicators. The interface shares a
single state across all pages and keeps financial and reporting rules
centralized.

## Main Features

* Dashboard with indicators and navigation shortcuts
* Registration viewing, searching, pagination, and safe removal
* Inventory item registration and removal
* Financial summary and payment classification
* Team, participant, and score management
* Aggregated reports and resizable charts
* Manual registration synchronization with Google Sheets

## Requirements

* Windows with Python 3.11 or newer
* Dependencies listed in `requirements.txt`

Current development and testing use Python 3.13. The portable Windows
executable is built separately using PyInstaller.

## Development Environment

In PowerShell, from the project folder:

```powershell
py -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

To launch the interface:

```powershell
python gui_main.py
```

The terminal’s current working directory is not used to locate data files.
During development, local files are resolved relative to the application
folder.

## Private Local Files

The following files must remain in the application folder and must never be
added to Git:

* `participants.json`
* `items.json`
* `teams.json`
* `client_secret.json`
* `token.json`

The three JSON files store local data. `client_secret.json` contains the OAuth
configuration provided for the application, while `token.json` is created or
updated after successful authorization.

Do not copy real data, credentials, or tokens into tests, source code,
documentation, reports, screenshots, or distributed packages.

Na execução empacotada, um assistente é aberto quando a localização dos
dados ainda não foi configurada ou quando falta algum dos três arquivos
obrigatórios. O usuário pode escolher uma pasta existente ou importar
explicitamente arquivos selecionados para `user_data`. A estratégia fica
registrada em `data_location.json`, que contém apenas o modo escolhido e,
quando aplicável, o caminho da pasta.

## Google Sheets

Synchronization is always started manually using the Dashboard button.
No connection, authentication, or browser launch occurs automatically during
application startup.

During the first authorized synchronization, the browser may open for the
Google OAuth flow. Connection or authentication failures preserve the existing
local state.

## Tests

The tests use only fictional records, temporary directories, and mocked Google
services:

```powershell
python -m unittest discover -s tests
```

## Windows Packaging

Development dependencies are listed in `requirements-dev.txt`. To run the
tests and create the portable one-folder distribution:

```powershell
python -m pip install -r requirements-dev.txt
& .\scripts\build_windows.ps1
```

Use `-SkipTests` only when the tests have already been run on the same revision.
The executable is created at
`dist\Acamp_App_GUI\Acamp_App_GUI.exe`, and the portable archive is created at
`release\Acamp_App_GUI_Windows.zip`.

=======
In the packaged application, private data and credentials are resolved only
from the `user_data` folder located next to the executable. They are not copied
from the project and are not included in the distribution. The
`README_RELEASE.txt` file contains instructions for users of the portable
version.
>>>>>>> cd56f5de3fd50f82a81e0a57a1bb5e0013a4a6f4
>>>>>>>
>>>>>>> The GUI version was mainly developed using Codex AI (OpenAI). The code here was mainly AI generated for learning purposes. If you want to see the version where mostly of the code was made by me directly you should look for Acamp_App_Terminal_Version.  
