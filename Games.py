import Database

teams = []

def menu():
    print("===== ATIVIDADES =====")

    print()

    print("1. Adicionar Time\n2. Deletar Time\n3. Adicionar Participante\n4. Deletar Participante\n5. Adicionar Pontos"
          "\n6. Tabela\n7. Sair")

    print()

    try:
        user_inpt = int(input())
        return user_inpt

    except ValueError:
        print("Insira um número válido.")


def team_creation():

    import Database

    while True:
        print()

        team = input("Nome do Time: ").lower().strip()
        leader = input("Nome do Capitao: ").lower().strip()
        color = input("Cor do time: ").lower().strip()

        time = {
            "equipe" : team,
            "lider" : leader,
            "cor" : color,
            "pessoas" : [],
            "score" : 0
        }

        teams.append(time)

        print()

        user = input("Quer adicionar outro time (N/S)? ").lower().strip()

        if user == 'n':

            Database.data_teams_write(teams)
            break


def participants_creation():

    while True:

        question_team = input("Nome da equipe: ").lower().strip()
        user = input("Nome do participante: ").lower().strip()

        found = False

        person = {

            "participante" : user

        }

        for people in teams:

            if people['equipe'] == question_team:

                people['pessoas'].append(person)
                Database.data_teams_write(teams)

                found = True

                print("Participante adicionado com sucesso!")

        if not found:
            print("Time não encontrado.")

        question = input("Voce quer adicionar outro (S/N)? ").lower().strip()

        if question == 'n':
            break


def remove_teams():

    import Database

    while True:

        user = input("Time que deseja excluir: ").lower().strip()

        counter = 0
        found = False

        while counter < len(teams):

            time = teams[counter]['equipe']

            if user == time:

                del teams[counter]

                Database.data_teams_write(teams)
                found = True

                print("Time removido com sucesso!")

                break

            else:
                counter += 1

        print()

        if not found:
            print("Equipe não listada")

        print()

        user2 = input("Deseja continuar (S/N)? ").lower().strip()

        if user2 == 'n':
            break


def remove_participants():

    import Database

    while True:

        team = input("Time da pessoa: ").lower().strip()
        person_list = input("Pessoa que deseja excluir: ").lower().strip()

        counter = 0
        found = False

        while counter < len(teams):

            equip = teams[counter]["equipe"]

            if team == equip:

                person_counter = 0
                people = teams[counter]["pessoas"]

                while person_counter < len(people):

                    person = people[person_counter]["participante"]

                    if person_list == person:

                        del people[person_counter]
                        Database.data_teams_write(teams)

                        found = True

                        print("Pessoa removida com sucesso!")
                        break

                    else:
                        person_counter += 1

                break

            else:
                counter += 1

        print()

        if not found:
            print("Pessoa e/ou equipe não listada(s).")

        print()

        user = input("Deseja continuar (S/N)? ").lower().strip()

        if user == 'n':
            break


def score_info():

    import Database

    while True:

        print("===== PONTUAÇÃO =====")

        print()

        print("1. Adicionar pontos\n2. Remover pontos\n3. Tabela de pontos\n4. Sair")

        print()

        try:

            user = int(input())

            if user == 1:

                equip_name = input("Nome da equipe: ").lower().strip()
                equip_score = int(input("Digite a pontuação: "))

                found = False

                for ponto in teams:
                    if ponto['equipe'] == equip_name:

                        add = ponto['score'] + equip_score
                        ponto['score'] = add
                        Database.data_teams_write(teams)

                        found = True

                        print()

                        print(f"{equip_score} pontos foram adicionados para a equipe '{equip_name}'!\nPontuacao final: {add}")

                        print()

                print()

                if not found:
                    print("Equipe nao listada. Tente novamente!")

                    print()

            if user == 2:

                equip_name = input("Nome da equipe: ").lower().strip()
                equip_score = int(input("Digite a pontuação: "))

                found = False

                for ponto in teams:
                    if ponto['equipe'] == equip_name:

                        subtract = ponto['score'] - equip_score
                        ponto['score'] = subtract
                        Database.data_teams_write(teams)

                        found = True

                        print()

                        print(f"{equip_score} pontos foram removidos da equipe '{equip_name}'!\nPontuacao final: {subtract}")

                        print()

                print()

                if not found:
                    print("Não há equipes com esse nome ou não há equipes.")

                    print()

            if user == 3:

                if teams:
                    for select in teams:

                        print(f"Time: {select['equipe']} = {select['score']}")

                    print()
                else:
                    print("Não há equipes.")
                    print()

            if user == 4:
                break

            if user > 4:
                print("Insira um número válido.")
                print()

        except ValueError:
            print("Insira um número válido.")

            print()
