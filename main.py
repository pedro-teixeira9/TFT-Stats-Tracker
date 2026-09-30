import os
import pandas as pd
import requests
from dotenv import load_dotenv

print("--- ETAPA 1: ACESSANDO A API ---")
load_dotenv() # carrega os arquivos .env

chave_api = os.getenv("RIOT_API_KEY") # Chama a CHAVE DA API do .env


#  ***!!!***  Altere seu nickname e tag aqui
nickname = "pedrobatista"
tag = "777"
#  ***!!!***


url_puuid = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{nickname}/{tag}"

# Mostra o token para a API
senha_entrada = { 
    "X-Riot-Token": chave_api
}
# obtém a URL do PUUID usando a Chave da API
resposta = requests.get(url_puuid, headers=senha_entrada)

dados = resposta.json() # Traduz a resposta .json para um dicionário python
print(dados)

#--------------------------------------------------------------

print("--- ETAPA 2: BUSCANDO OS IDs DAS PARTIDAS ---")

meu_puuid = dados["puuid"]

# 'matches' = histórico | 'ids' = pega apenas o ID das partidas | '?count=100' = pega as últimas 100 partidas |
url_partidas = f"https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/{meu_puuid}/ids?count=100"

# Guarda os IDs das últimas x partidas jogadas
resposta_partidas = requests.get(url_partidas, headers=senha_entrada)

# Tradução json --> python
lista_partidas = resposta_partidas.json()

print(f"Minhas últimas {len(lista_partidas)} partidas no TFT foram:")
print(lista_partidas)

#--------------------------------------------------------------

print(f"\n--- ETAPA 3: PEGANDO AS INFOs DAS {len(lista_partidas)} PARTIDAS ---")

# Insere uma tabela em branco
dados_tabela = []

meta_de_partidas = 30
partidas_salvas = 0

# Busca cada partida na lista de IDs
for partida_id in lista_partidas:
    
    if partidas_salvas == meta_de_partidas:
        # Verifica se o número de partidas atingiu o limite
        break

        # 1. Busca os dados de uma partida específica com base no seu ID
    url = f"https://americas.api.riotgames.com/tft/match/v1/matches/{partida_id}"
    resposta = requests.get(url, headers=senha_entrada)
    dados = resposta.json()
    
    tipo_partida = dados["info"]["queue_id"]

    # Se não for ranqueada, pula para o próximo ID ----> | 1100 == Solo Ranked | 1160 == Double up |
    if tipo_partida != 1100:
        continue

    # 2. Chama a lista de 8 jogadores
    jogadores = dados["info"]["participants"]
    
    # 3. Procura nos jogadores o PUUID == meu_PUUID e caso igual puxa as infos da partida específica
    for jogador in jogadores:
          if jogador["puuid"] == meu_puuid:
            colocacao = jogador["placement"]
            dano = jogador["total_damage_to_players"]
            
            # Cria a linha com os dados na planilha
            linha = {
                "ID_Partida": partida_id,
                "Colocação": colocacao,
                "Dano_Causado": dano
            }
            
            # Insere uma linha na tabela em branco
            dados_tabela.append(linha)

            partidas_salvas+= 1
            
            # 4. Mostra o Resultado e termina a busca nessa partida
            print(f"Partida {partida_id} | Fiquei em {colocacao}º lugar (Dano causado: {dano})")
            break

#--------------------------------------------------------------

print("\n--- ETAPA 4: GERANDO ARQUIVO CSV ---")

# Transforma a lista de python em pandas
tabela_final = pd.DataFrame(dados_tabela)

media_colocacao = tabela_final["Colocação"].mean()
media_dano_causado = tabela_final["Dano_Causado"].mean()


# Serve para descobrir o número da última linha vazia
tabela_final.loc[len(tabela_final)] = {
    #Cria a linha de Média no arquivo .csv
    "ID_Partida": "MÉDIA TOTAL", 
    "Colocação": round(media_colocacao, 1), # round() arredonda para 1 casa decimal
    "Dano_Causado": round(media_dano_causado, 0) # Arredonda sem casas decimais
}

# Exporta a tabela para um arquivo .csv na mesma pasta do seu projeto | "Index" retira a numeração automática que o pandas faz na planilha
tabela_final.to_csv("meu_historico_tft.csv", index=False, sep=";", encoding ="utf-8-sig", decimal =',')
print("O arquivo 'meu_historico_tft.csv' foi gerado.")
