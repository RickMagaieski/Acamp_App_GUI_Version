import Inscriptions
import Finance
import Inventory
import Database
import GoogleSheets
import Games
import Reports

Games.teams.clear()
Inventory.list_inventory = Database.data_item_load()
Games.teams = Database.data_teams_load()

#important to fix: Do not depend on the online data.

while True:
    print()

    print("======= ACAMP WBSDAC 2026 MENU =======")

    print()

    print("1. Inscrição\n2. Finanças\n3. Inventário\n4. Atividades\n5. Reports\n6. Atualizar Dados\n7. Sair")

    print()

    try:
        user = int(input("Selecione a opção desejada: "))

        if user == 1:

            while True:

                print()
                choice = Inscriptions.menu()

                """if choice == 1:
                    Inscriptions.add_participant()"""

                if choice == 1:
                    GoogleSheets.read_sheet_data()

                    if not GoogleSheets.inscriptions:
                        print("Não há inscritos.")

                    else:
                        for people in GoogleSheets.inscriptions:
                            print(people)

                if choice == 2:
                    Inscriptions.search_box()

                if choice == 3:
                    if not GoogleSheets.inscriptions:
                        print("Não há inscritos.")

                    else:
                        Inscriptions.user_deletion()

                if choice == 4:
                    break

        if user == 2:

            while True:

                print()
                choice = Finance.menu()

                if choice == 1:
                    Finance.general_values()

                if choice == 2:
                    Finance.account()

                if choice == 3:

                    if not GoogleSheets.inscriptions:
                        print("Não há inscritos.")
                    else:
                        Finance.payments()

                if choice == 4:
                    break

        if user == 3:

            while True:

                print()
                choice = Inventory.menu()

                if choice == 1:
                    Inventory.add_inventory()

                if choice == 2:
                    if not Inventory.list_inventory:
                        print("A lista está vazia.")

                    else:
                        for lista in Inventory.list_inventory:
                            print(lista, end='\n')

                if choice == 3:
                    if not Inventory.list_inventory:
                        print("O inventário está vazio.")

                    else:
                        Inventory.remove_items()

                if choice == 4:
                    Inventory.search()

                if choice == 5:
                    break

        if user == 4:

            while True:

                print()

                choice = Games.menu()

                if choice == 1:
                    Games.team_creation()

                if choice == 2:
                    Games.remove_teams()

                if choice == 3:
                    if not Games.teams:
                        print("Não há equipes.")
                    else:
                        Games.participants_creation()

                if choice == 4:
                    if not Games.teams:
                        print("Não há equipes.")
                    else:
                        Games.remove_participants()

                if choice == 5:
                    if not Games.teams:
                        print("Não há equipes.")
                    else:
                        Games.score_info()

                if choice == 6:
                    if not Games.teams:
                        print("Não há participantes.")

                    else:
                        for times in Games.teams:
                            print(times)

                if choice == 7:
                    break

        if user == 5:
            Reports.reports_use()

        if user == 6:
            GoogleSheets.read_sheet_data()

        if user == 7:
            break

        if user > 7:
            print("Insira um número válido.")

    except ValueError:
        print("Insira um número válido.")

        print()
