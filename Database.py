import json

#first data set is for participants

def save_data(data):

    with open("participants.json", "w") as file:
        json.dump(data, file, indent= 4)

def open_data():

    try:
        with open("participants.json", "r") as file:
            data = json.load(file)
            return data

    except FileNotFoundError:
        return[]

    except json.JSONDecodeError:
        return[]


def data_item_write(item_data):

    with open("items.json", 'w') as file:
        json.dump(item_data,file, indent= 4)

def data_item_load():

    try:
        with open("items.json", 'r') as file:
            item_data = json.load(file)
            return item_data

    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def data_teams_write(teams):

    with open('teams.json', 'w') as file:
        json.dump(teams, file, indent= 4)

def data_teams_load():

    try:
        with open('teams.json', 'r') as file:
            teams_data = json.load(file)
            return teams_data

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        return []
