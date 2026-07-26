def general_values():

    print("==== VALORES GERAIS ====")

    print()

    print("Taxa de inscrição (Adulto - 14+): $135.00\nValor de Sábado apenas: $55.00\nInscrição com RV: 125.00"
          "\nCadastro da Infantil: $67.75\nSomente Sábado Infantil: $27.50")

    print()

def menu():
    print("===== FINANÇAS =====")

    print()

    print("1. Lista de Preços\n2. Contabilidade Geral\n3. Pagamentos\n4. Sair")

    print()

    try:
        user_inpt = int(input())
        return user_inpt

    except ValueError:
        print("Insira um número válido.")

def payments():
    from GoogleSheets import inscriptions

    if inscriptions:
        for person in inscriptions:

                print(f"{person['name']}: ${person['payment']:.2f} - {person['inscription']}")

                if person['inscription'] == 'adulto':
                    if person['payment'] == 135.00:
                        print("(Pago!)")
                    elif 135.00 > person['payment'] > 0.00:
                        print(f"(Parcial... Deve: ${135.00 - person['payment']:.2f})")
                    elif person['payment'] == 0.00:
                        print("(Pendente!)")

                if person['inscription'] == 'criança':
                    if person['payment'] == 67.75:
                        print("(Pago!)")
                    elif 67.75 > person['payment'] > 0.00:
                        print(f"(Parcial... Deve: ${67.75 - person['payment']:.2f})")
                    elif person['payment'] == 0.00:
                        print("(Pendente!)")

                if person['inscription'] == 'rv':
                    if person['payment'] == 125.00:
                        print("(Pago!)")
                    elif 125.00 > person['payment'] > 0.00:
                        print(f"(Parcial... Deve: ${125.00 - person['payment']:.2f})")
                    elif person['payment'] == 0.00:
                        print("(Pendente!)")

                if person['inscription'] == 'sábado adulto':
                    if person['payment'] == 55.00:
                        print("(Pago!)")
                    elif 55.00 > person['payment'] > 0.00:
                        print(f"(Parcial... Deve: ${55.00 - person['payment']:.2f})")
                    elif person['payment'] == 0.00:
                        print("(Pendente!)")

                if person['inscription'] == 'sábado infantil':
                    if person['payment'] == 27.50:
                        print("(Pago!)")
                    elif 27.50 > person['payment'] > 0.00:
                        print(f"(Parcial... Deve: ${27.50 - person['payment']:.2f})")
                    elif person['payment'] == 0.00:
                        print("(Pendente!)")
                if person['payment'] > 135:
                    print("(Pago!)")

    else:
        print("A lista está vazia.")

def account():
    from GoogleSheets import inscriptions
    from Inventory import list_inventory

    init_balance = 3700.00
    total_profit = 0
    total_loss = 0

    print(f"Saldo Inicial: {init_balance:.2f}")
    print()

    print("Entradas:")
    for amount in inscriptions:

        total_profit += amount['payment']

    print(f"Total Entradas: ${total_profit:.2f}")

    print()

    print("Saídas:")
    for saidas in list_inventory:

        total = saidas['value'] * saidas['quantity']
        total_loss += total

    print(f"Total Saídas: $-{total_loss:.2f}")

    print()

    print(f"Total Final: {init_balance + total_profit - total_loss:.2f}")

    print()
