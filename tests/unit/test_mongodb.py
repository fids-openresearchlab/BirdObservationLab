def test_players(mongodb):
    assert 'flights' in mongodb.list_collection_names()
    #manuel = mongodb.players.find_one({'name': 'Manuel'})
    #assert manuel['surname'] == 'Neuer'