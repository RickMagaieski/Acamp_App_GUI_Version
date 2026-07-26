from Database import open_data
import Database

def reports_use():

    print()

    print("======== REPORTS ========")

    print()

    print(f"TOTAL DE INSCRIÇÕES: {len(open_data())}")

    print()

    print("SUPORTE COM TRANSPORTE: ")

    car = False

    for transport in open_data():
        if 'sim' in transport['transportation']:
            car = True
            print(f"{transport['name']}")

    if not car:
        print("Não há ninguém")

    print()

    print("FAIXAS ETÁRIAS PRESENTES:")

    print()
    count = 0

    baby = 0
    kid = 0
    teen = 0
    youth = 0
    adult = 0
    old = 0

    for age in open_data():
        if 5 >= age['age']:
            baby += 1
        elif 12 >= age['age']:
            kid += 1
        elif 17 >= age['age']:
            teen += 1
        elif 29 >= age['age']:
            youth += 1
        elif 59 >= age['age']:
            adult += 1
        elif 119 >= age['age']:
            old += 1

    print(f"Bebes: {baby}\nCriancas: {kid}\nAdolescentes: {teen}\nJovens: {youth}\nAdultos: {adult}\nTerceira-Idade: {old}")

    print()

    vege = 0
    not_vege = 0

    for veg in open_data():
        if veg['food'] == 'sim':
            not_vege += 1
        elif veg['food'] == 'não':
            vege += 1

    print(f"VEGETARIANOS: {vege}\nNÃO VEGETARIANOS: {not_vege}")

    print()

    tent = 0
    rv = 0
    cabin = 0

    for acc in open_data():
        if acc['accommodation'] == 'barraca':
            tent += 1
        elif acc['accommodation'] == 'rv':
            rv += 1
        elif acc['accommodation'] == 'cabine':
            cabin += 1

    print(f"BARRACAS: {tent}\nRV: {rv}\nCABINES: {cabin}")

    print()

    entries = 0.0
    loss = 0.0
    profit = 0.0

    for person in open_data():
        entries += person['payment']

    for item in Database.data_item_load():
        item_cost = item['value'] * item['quantity']
        loss += item_cost


    print(f"ENTRADAS: ${entries:.2f}")
    print(f"GASTOS: ${loss:.2f}")
    print(f"LUCRO: ${entries - loss:.2f}")
    print(f"TOTAL: ${3700.00 + (entries - loss):.2f}")

    print()

    paid = 0
    not_paid = 0
    pendent = 0
    cabin = 0
    special = 0

    for pag in open_data():

        if pag["accommodation"] == "flag" and pag["payment"] == 0.0:
            special += 1
        elif pag['accommodation'] == 'cabine' and pag['payment'] == 0.0:
            cabin += 1
        elif pag['accommodation'] == 'cabine':
            cabin += 1
        elif pag['inscription'] == 'adulto':
            if pag['payment'] == 135.00:
                paid += 1
            elif 135.00 > pag['payment'] > 0.00:
                pendent += 1
            elif pag['payment'] == 0.00:
                not_paid += 1
        elif pag['inscription'] == 'criança':
            if pag['payment'] == 67.75:
                paid += 1
            elif 67.75 > pag['payment'] > 0.00:
                pendent += 1
            elif pag['payment'] == 0.00:
                not_paid += 1
        elif pag['inscription'] == 'rv':
            if pag['payment'] == 125.00:
                paid += 1
            elif 125.00 > pag['payment'] > 0.00:
                pendent += 1
            elif pag['payment'] == 0.00:
                not_paid += 1
        elif pag['inscription'] == 'sábado adulto':
            if pag['payment'] == 55.00:
                paid += 1
            elif 55.00 > pag['payment'] > 0.00:
                pendent += 1
            elif pag['payment'] == 0.00:
                not_paid += 1
        elif pag['inscription'] == 'sábado infantil':
            if pag['payment'] == 27.50:
                paid += 1
            elif 27.50 > pag['payment'] > 0.00:
                pendent += 1
            elif pag['payment'] == 0.00:
                not_paid += 1

    print(f"PAGAMENTOS COMPLETOS: {paid}")
    print(f"PAGAMENTOS PENDENTES: {pendent}")
    print(f"PAGAMENTOS NAO EFETUADOS: {not_paid}")
    print(f"CABINE: {cabin}")
    print(f"ESPECIAIS: {special}")
