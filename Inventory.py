list_inventory = []

def add_inventory():

    import Database

    while True:

        item_input = input("Digite o nome do item: ").lower().strip()
        value_input = float(input("Digite o valor do item: "))
        quantity_input = int(input("Digite a quantidade: "))
        description_input = input("Descrição/Detalhes: ").lower().strip()

        items = {
            'item': item_input,
            'quantity': int(quantity_input),
            'value': float(value_input),
            'description': description_input
        }

        list_inventory.append(items)
        Database.data_item_write(list_inventory)

        print()

        print("Item adicionado com sucesso!")

        print()

        user = input("Deseja adicionar outro item (S/N)? ").lower().strip()

        if user == 'n':
            break

def menu():
    print("===== INVENTÁRIO =====")

    print()

    print("1. Adicionar Item\n2. Acessar inventário\n3. Remover item\n4. Procurar item\n5. Sair")

    print()

    try:
        user_input = int(input())
        return user_input

    except ValueError:
        print("Insira um número válido.")

def remove_items():

    import Database

    user = input("Nome completo do item: ").lower().strip()

    counter = 0
    found = False

    while counter < len(list_inventory):

        item = list_inventory[counter]['item']

        if item == user:
            del list_inventory[counter]
            found = True
            Database.data_item_write(list_inventory)

            print("Item removido com sucesso!")
            break

        else:
            counter += 1

    if not found:
        print("Este item não está na lista.")

def search():
    while True:

        if list_inventory:
            user = input("Buscar item (para sair digite s): ").lower().strip()

            if user == 's':
                break

            counter = 0
            found = False

            while counter < len(list_inventory):

                item = list_inventory[counter]['item']

                if user in item:
                    print(list_inventory[counter])

                    found = True
                    counter += 1

                else:
                    counter += 1

            if not found:
                print("Este item não está na lista.")

        else:
            print("A lista está vazia.")
            break
