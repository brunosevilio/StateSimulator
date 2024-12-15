import random
from simplekml import Kml
import pandas as pd
import math

# ==========================================
# Classe base para representar uma unidade hierárquica
# ==========================================
class Unidade:
    """Base class to represent a hierarchical unit."""
    def __init__(self, nome, nivel, id_unico, lat=None, lon=None, imagem=None, cargo_comando=None):
        self.nome = nome
        self.nivel = nivel
        self.id_unico = id_unico
        self.lat = lat
        self.lon = lon
        self.imagem = imagem  # Link to the image
        self.cargo_comando = cargo_comando  # Command role for the unit
        self.subordinados = []

    def adicionar_subordinado(self, unidade):
        """Adds a subordinate unit."""
        self.subordinados.append(unidade)

    def gerar_coordenadas(self, lat_base, lon_base, total_subordinados, raio):
        """Generates coordinates for subordinates arranged in a circle."""
        if total_subordinados > 0:
            coordenadas = gerar_coordenadas_circulo((lat_base, lon_base), total_subordinados, raio)
            for i, unidade in enumerate(self.subordinados):
                unidade.lat, unidade.lon = coordenadas[i]

# ==========================================
# Subclasses representing different levels of hierarchy
# ==========================================
class Forca(Unidade):
    """Represents a force (top level)."""
    def __init__(self, nome, id_unico, cargo_comando=None):
        super().__init__(nome, "Força", id_unico, cargo_comando=cargo_comando)

class Exercito(Unidade):
    """Represents an army."""
    def __init__(self, nome, id_unico, coord=None, imagem=None, cargo_comando=None):
        super().__init__(nome, "Exército", id_unico, imagem=imagem, cargo_comando=cargo_comando)
        if coord:
            self.lat = coord.get('lat')
            self.lon = coord.get('lon')

class Divisao(Unidade):
    """Represents a division."""
    def __init__(self, nome, id_unico, imagem=None, cargo_comando=None):
        super().__init__(nome, "Divisão", id_unico, imagem=imagem, cargo_comando=cargo_comando)

class Brigada(Unidade):
    """Represents a brigade."""
    def __init__(self, nome, id_unico, imagem=None, cargo_comando=None):
        super().__init__(nome, "Brigada", id_unico, imagem=imagem, cargo_comando=cargo_comando)

class Regimento(Unidade):
    """Represents a regiment."""
    def __init__(self, nome, id_unico, imagem=None, cargo_comando=None):
        super().__init__(nome, "Regimento", id_unico, imagem=imagem, cargo_comando=cargo_comando)

# ==========================================
# Utility function to generate circular coordinates
# ==========================================
def gerar_coordenadas_circulo(base_coord, total, raio):
    """Generates coordinates to position subordinates in a circle around a base coordinate."""
    lat_base, lon_base = base_coord
    angulo_incremento = 360 / total  # Divide the circle into equal parts

    coordenadas = []
    for i in range(total):
        angulo = math.radians(i * angulo_incremento)  # Convert angle to radians
        lat = lat_base + raio * math.sin(angulo)
        lon = lon_base + raio * math.cos(angulo)
        coordenadas.append((lat, lon))

    return coordenadas

# ==========================================
# Function to process the hierarchy from DataFrames
# ==========================================
def processar_hierarquia(df_ativas, cidades_df):
    """Processes DataFrames to build hierarchy using classes."""
    forcas = {}

    # Helper function to fetch city coordinates
    def buscar_coordenadas(cidade_nome):
        if pd.notna(cidade_nome):
            cidade_row = cidades_df[cidades_df['Nome'] == cidade_nome]
            if not cidade_row.empty:
                return {
                    'lat': cidade_row.iloc[0]['Latitude'],
                    'lon': cidade_row.iloc[0]['Longitude']
                }
        return None

    for _, row in df_ativas.iterrows():
        # Extract hierarchy levels
        forca_nome = row['Force']
        exercito_nome = row['Exercito']
        divisao_nome = row['Divizao']
        brigada_nome = row['Brigada']

        # Fetch coordinates for each level
        coords_ex = buscar_coordenadas(row.get('Cidade'))
        coords_div = buscar_coordenadas(row.get('Cidade_Div'))
        coords_brig = buscar_coordenadas(row.get('Cidade_Brig'))

        # Fetch image links
        ex_imagem = row.get('Exe_PNG')
        div_imagem = row.get('Div_PNG')
        bri_imagem = row.get('Bri_PNG')
        reg_imagem = row.get('Reg_PNG')

        regimentos = [row[col] for col in df_ativas.columns if col.startswith('Regimento_') and pd.notna(row[col])]

        # Add force if not exists
        if forca_nome not in forcas:
            forcas[forca_nome] = Forca(forca_nome, id_unico=len(forcas) + 1)

        # Add army
        exercito = next((e for e in forcas[forca_nome].subordinados if e.nome == exercito_nome), None)
        if not exercito:
            cargo_comando = f"{row['Cargo_Exercito']} {exercito_nome}" if 'Cargo_Exercito' in row else None
            exercito = Exercito(exercito_nome, id_unico=len(forcas[forca_nome].subordinados) + 1, coord=coords_ex, imagem=ex_imagem, cargo_comando=cargo_comando)
            forcas[forca_nome].adicionar_subordinado(exercito)

        # Add division
        divisao = next((d for d in exercito.subordinados if d.nome == divisao_nome), None)
        if not divisao:
            cargo_comando = f"{row['Cargo_Divizao']} {divisao_nome}" if 'Cargo_Divizao' in row else None
            divisao = Divisao(divisao_nome, id_unico=len(exercito.subordinados) + 1, imagem=div_imagem, cargo_comando=cargo_comando)
            if coords_div:
                divisao.lat, divisao.lon = coords_div['lat'], coords_div['lon']
            else:
                divisao.lat, divisao.lon = exercito.lat, exercito.lon
            exercito.adicionar_subordinado(divisao)

        # Add brigade
        brigada = next((b for b in divisao.subordinados if b.nome == brigada_nome), None)
        if not brigada:
            cargo_comando = f"{row['Cargo_Brigada']} {brigada_nome}" if 'Cargo_Brigada' in row else None
            brigada = Brigada(brigada_nome, id_unico=len(divisao.subordinados) + 1, imagem=bri_imagem, cargo_comando=cargo_comando)
            if coords_brig:
                brigada.lat, brigada.lon = coords_brig['lat'], coords_brig['lon']
            else:
                brigada.lat, brigada.lon = divisao.lat, divisao.lon
            divisao.adicionar_subordinado(brigada)

        # Add regiments
        for regimento_nome in regimentos:
            regimento = Regimento(regimento_nome, id_unico=len(brigada.subordinados) + 1, imagem=reg_imagem)
            regimento.lat, regimento.lon = brigada.lat, brigada.lon
            brigada.adicionar_subordinado(regimento)

    return forcas

# ==========================================
# Function to generate a KML file with hierarchical layers
# ==========================================
def gerar_kml_com_camadas(forcas, niveis, output_file):
    """Generates a single KML containing layers (folders) for each specified level."""
    kml = Kml()

    def adicionar_unidades_por_nivel(unidade, nivel, folder, hierarquia_superior=None):
        if hierarquia_superior is None:
            hierarquia_superior = []

        if unidade.nivel == nivel and unidade.lat is not None and unidade.lon is not None:
            ponto = folder.newpoint(
                name=f"{unidade.nome} (ID: {unidade.id_unico})",
                coords=[(unidade.lon, unidade.lat)]
            )
            subordinados = [sub.nome for sub in unidade.subordinados]

            description = (
                f"<b>Unit:</b> {unidade.nome}<br>"
                f"<b>ID:</b> {unidade.id_unico}<br>"
                f"<b>Comandante:</b> {unidade.cargo_comando if unidade.cargo_comando else 'None'}<br>"
                f"<b>Superior Units:</b><br>{' > '.join(hierarquia_superior) if hierarquia_superior else 'None'}<br>"
            )

            if subordinados:
                description += "<b>Subordinate Units:</b><br>" + "<br>".join(subordinados) + "<br>"
            else:
                description += "<b>Subordinate Units:</b> Batalhão<br>"

            if unidade.imagem:
                caminho_completo = f"Main/military_sistem/{unidade.imagem}"
                description += f"<br><img src='{caminho_completo}' width='200'/>"

                ponto.style.iconstyle.icon.href = caminho_completo
                ponto.style.iconstyle.scale = 1.0
            ponto.description = description

        for subordinado in unidade.subordinados:
            adicionar_unidades_por_nivel(subordinado, nivel, folder, hierarquia_superior + [unidade.nome])

    for nivel in niveis:
        folder = kml.newfolder(name=f"Level: {nivel}")
        for forca in forcas.values():
            adicionar_unidades_por_nivel(forca, nivel, folder)

    kml.save(output_file)
    print(f"KML '{output_file}' generated with specified levels.")

# ==========================================
# Function to generate coordinates for all hierarchical levels
# ==========================================
def gerar_coordenadas_todos_niveis(forcas, raio_inicial=0.01):
    """Generates coordinates for all units in all hierarchical levels."""
    for forca in forcas.values():
        if forca.lat is None or forca.lon is None:
            forca.lat, forca.lon = 0.0, 0.0

        for exercito in forca.subordinados:
            if exercito.lat is None or exercito.lon is None:
                exercito.lat, exercito.lon = forca.lat, forca.lon
            exercito.gerar_coordenadas(exercito.lat, exercito.lon, len(exercito.subordinados), raio_inicial)

            for divisao in exercito.subordinados:
                if divisao.lat is None or divisao.lon is None:
                    divisao.lat, divisao.lon = exercito.lat, exercito.lon
                divisao.gerar_coordenadas(divisao.lat, divisao.lon, len(divisao.subordinados), raio_inicial / 2)

                for brigada in divisao.subordinados:
                    if brigada.lat is None or brigada.lon is None:
                        brigada.lat, brigada.lon = divisao.lat, divisao.lon
                    brigada.gerar_coordenadas(brigada.lat, brigada.lon, len(brigada.subordinados), raio_inicial / 3)

                    for regimento in brigada.subordinados:
                        if regimento.lat is None or regimento.lon is None:
                            regimento.lat, regimento.lon = brigada.lat, brigada.lon
                        regimento.gerar_coordenadas(regimento.lat, regimento.lon, len(regimento.subordinados), raio_inicial / 4)

# ==========================================
# Load data and process the hierarchy
# ==========================================
df_ativas = pd.read_excel('Main/military_sistem/Data_Military_Units.ods', sheet_name='Ativas')
cidades_df = pd.read_excel('Main/citizen_generator/Filtered_Pop_Municipio.ods', sheet_name='Main')

# Fix coordinate format in city DataFrame
cidades_df['Latitude'] = cidades_df['Latitude'].apply(lambda x: float(str(x).replace(',', '.')))
cidades_df['Longitude'] = cidades_df['Longitude'].apply(lambda x: float(str(x).replace(',', '.')))

# Process the hierarchy and generate KML
forcas = processar_hierarquia(df_ativas, cidades_df)
gerar_coordenadas_todos_niveis(forcas)

# Specify levels for KML
niveis = ["Exército", "Divisão", "Brigada", "Regimento"]

gerar_kml_com_camadas(forcas, niveis, output_file="unidades.kml")
