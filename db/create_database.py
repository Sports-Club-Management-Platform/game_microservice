import asyncio
import os

from fastapi import UploadFile
from sqlalchemy.orm import Session

from crud.imageRepo import create_image
from db.database import engine
from models.club import Club
from models.game import Game
from models.pavilion import Pavilion


def create_tables():
    Pavilion.metadata.create_all(bind=engine)
    Club.metadata.create_all(bind=engine)
    Game.metadata.create_all(bind=engine)

async def populate_db(session: Session):
    # Verifica se a tabela de clubes já tem dados
    if not session.query(Club).first():
        print("Populando a base de dados...")
        # Cria pavilhões (substitua com os dados reais)
        pavilions = [
            {"name": "Pavilhão de Desportos da Candelária", "location": "Largo Cardeal Costa Nunes, Madalena (Ilha do Pico)", "location_link": "https://maps.app.goo.gl/gmk6U25h8QeTtUxC7", "image": ""},
            {"name": "Pavilhão Gimnodesportivo de Murches", "location": "R. Fernando Pessoa 23, 2755-223 Alcabideche", "location_link": "https://maps.app.goo.gl/wHnyqvUiFHEisnMr8", "image": ""},
            {"name": "Pavilhão Multidesportivo Sporting", "location": "Rua Professor Fernando da Fonseca 1501-806, 1600-616 Lisboa", "location_link": "https://maps.app.goo.gl/WM8VnbsJuUwud9527", "image": ""},
            {"name": "Pavilhão das Goladas", "location": "Rua Professora, R. Adelina Caravana, 4710-500 Braga", "location_link": "https://maps.app.goo.gl/8sVTH6EEYaeHa7yV6", "image": ""},
            {"name": "Pavilhão Municipal de Valongo", "location": "Avenida dos Desportos, 4440-181 Valongo", "location_link": "https://maps.app.goo.gl/4KWwdb3Sn8jYzPZN7", "image": ""},
            {"name": "Pavilhão Municipal José Natário", "location": "Avenida do Atlântico, 4900-350 Viana do Castelo", "location_link": "https://maps.app.goo.gl/GCmSm4ay1qApzkS56", "image": ""},
            {"name": "Clube Desportivo e Cultural Juventude Pacense", "location": "Av. Dr. Jaime Barros 135, 4590-892 Meixomil", "location_link": "https://maps.app.goo.gl/ZwvTJVcf1BwhdEWC8", "image": ""},
            {"name": "Pavilhão Fidelidade", "location": "Av. Eusébio da Silva Ferreira, 1500-313 Lisboa", "location_link": "https://maps.app.goo.gl/WuhPJxGTEyHJWrhZ8", "image": ""},
            {"name": "Pavilhão Dr. Salvador Machado", "location": "Praceta da União Desportiva Oliveirense Aptd. 1153, Oliveira de Azeméis", "location_link": "https://maps.app.goo.gl/RECvX53oXkYdGsSF7", "image": ""},
            {"name": "Riba d'Ave Hóquei Clube", "location": "Av. das Tilias 94, Riba d'Ave", "location_link": "https://maps.app.goo.gl/HJXLcZ3Mq1PJZYnk9", "image": ""},
            {"name": "Pavilhão Municipal Patrícia Sampaio", "location": "R. Centro Republicano 50, 2300-593 Tomar", "location_link": "https://maps.app.goo.gl/dv34MzMWFUave9kp8", "image": ""},
            {"name": "Pavilhão da Associação Desportiva Sanjoanense (ADS)", "location": "Av. Benjamim Araújo, 3700-127 São João da Madeira", "location_link": "https://maps.app.goo.gl/u6HUvwvmqepMJePt7", "image": ""},
            {"name": "Pavilhão Municipal de Barcelos", "location": "R. Cândido da Cunha 100, 4750-333 Barcelos", "location_link": "https://maps.app.goo.gl/ZyM26Em8wbiU8RjbA", "image": ""},
            {"name": "Dragão Arena", "location": "Via Futebol Clube do Porto, 4350-415 Porto", "location_link": "https://maps.app.goo.gl/eH8oczjmxQbUPw9k7", "image": ""}
        ]
        populate_pavilions_folder = "static/pavilions_populate/"
        for file_name in os.listdir(populate_pavilions_folder):
            pavilion_id_str, file_ext = os.path.splitext(file_name)
            pavilion_id = int(pavilion_id_str) 
            # Encontra o pavilhão correspondente na lista
            if 1 <= pavilion_id <= len(pavilions):
                pavilion_data = pavilions[pavilion_id - 1]  # Pega o pavilhão correspondente (índice começa em 0)
                file_path = os.path.join(populate_pavilions_folder, file_name)
                with open(file_path, "rb") as image_file:
                    image = UploadFile(filename=file_name, file=image_file)
                    img_path = await create_image(image, f"pavilions/{pavilion_id}")
                    pavilion_data["image"] = img_path
        # Adiciona pavilhões
        for pavilion_data in pavilions:
            pavilion = Pavilion(**pavilion_data)
            session.add(pavilion)
        session.commit()
        # Cria os clubes
        clubs = [
            {"name": "Candelária SC", "image": "", "pavilion_id": 1},
            {"name": "GRF Murches", "image": "", "pavilion_id": 2},
            {"name": "Sporting CP", "image": "", "pavilion_id": 3},
            {"name": "HC Braga", "image": "", "pavilion_id": 4},
            {"name": "AD Valongo", "image": "", "pavilion_id": 5},
            {"name": "Ass. Juv. Viana", "image": "", "pavilion_id": 6},
            {"name": "Juventude Pacense", "image": "", "pavilion_id": 7},
            {"name": "SL Benfica", "image": "", "pavilion_id": 8},
            {"name": "UD Oliveirense", "image": "", "pavilion_id": 9},
            {"name": "Riba d'Ave HC", "image": "", "pavilion_id": 10},
            {"name": "SC Tomar", "image": "", "pavilion_id": 11},
            {"name": "AD Sanjoanense", "image": "", "pavilion_id": 12},
            {"name": "OC Barcelos", "image": "", "pavilion_id": 13},
            {"name": "FC Porto", "image": "", "pavilion_id": 14}
        ]
        populate_clubs_folder = "static/clubs_populate/"
        for file_name in os.listdir(populate_clubs_folder):
            club_id_str, file_ext = os.path.splitext(file_name)
            club_id = int(club_id_str) 
            # Encontra o clube correspondente na lista
            if 1 <= club_id <= len(clubs):
                club_data = clubs[club_id - 1]  # Pega o clube correspondente (índice começa em 0)
                file_path = os.path.join(populate_clubs_folder, file_name)
                with open(file_path, "rb") as image_file:
                    image = UploadFile(filename=file_name, file=image_file)
                    img_path = await create_image(image, f"clubs/{club_id}")
                    club_data["image"] = img_path
        # Adiciona clubes ao banco de dados
        for club_data in clubs:
            club = Club(**club_data)
            session.add(club)
        games = [
                {
                    "jornada": 1,
                    "date_time": "2024-10-19 22:00:00",
                    "club_home_id": 1, 
                    "club_visitor_id": 2, 
                    "pavilion_id": 1, 
                    "finished": False
                },
                {
                    "jornada": 2,
                    "date_time": "2024-10-26 17:00:00", 
                    "club_home_id": 4,  
                    "club_visitor_id": 2, 
                    "pavilion_id": 4,  
                    "finished": False 
                },
                {
                    "jornada": 3,
                    "date_time": "2024-11-01 22:00:00",
                    "club_home_id": 1,
                    "club_visitor_id": 8,
                    "pavilion_id": 1,
                    "finished": False
                },
                {
                    "jornada": 4,
                    "date_time": "2024-11-03 21:30:00",
                    "club_home_id": 6,
                    "club_visitor_id": 1,
                    "pavilion_id": 6,
                    "finished": False
                },
                {
                    "jornada": 5,
                    "date_time": "2024-11-09 22:00:00",
                    "club_home_id": 1,
                    "club_visitor_id": 12,
                    "pavilion_id": 1,
                    "finished": False
                },
            ]
        # Adiciona jogos ao banco de dados
        for game_data in games:
            game = Game(**game_data)
            session.add(game)
        session.commit()
        print("Base de dados populada com sucesso!")
