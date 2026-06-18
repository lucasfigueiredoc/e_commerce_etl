import os
import pandas as pd
from minio import Minio
import io


NOME_BUCKET_BRONZE = "camada-bronze"
NOME_BUCKET_SILVER = "camada-silver"
PASTA_LOCAL_TEMP = "./dados_temporarios"

os.makedirs(PASTA_LOCAL_TEMP, exist_ok=True)

cliente_minio = Minio(
    "localhost:9000",
    access_key="admin_datalake",
    secret_key="senha_datalake",
    secure=False
)

## Cria o buker silver caso nao exista
if not cliente_minio.bucket_exists(NOME_BUCKET_SILVER):
    cliente_minio.make_bucket(NOME_BUCKET_SILVER)
    print(f"   Bucket '{NOME_BUCKET_SILVER}' criado.")


    # --- 2. LER DADOS DA CAMADA BRONZE ---
nome_arquivo_bronze = "olist/olist_geolocation_dataset.csv"
nome_arquivo_silver = "olist/olist_geolocation_dataset.parquet"

print(f"2. A descarregar '{nome_arquivo_bronze}' da Camada Bronze...")
resposta = cliente_minio.get_object(NOME_BUCKET_BRONZE, nome_arquivo_bronze)

df_generic = pd.read_csv(resposta)
resposta.close()
resposta.release_conn()

# --- 4. GUARDAR E ENVIAR PARA A CAMADA SILVER ---
caminho_local_parquet = os.path.join(PASTA_LOCAL_TEMP, "olist_geolocation_dataset.parquet")

print("4. A converter o DataFrame para o formato otimizado Parquet...")
# O formato Parquet reduz o tamanho do ficheiro e acelera as consultas
df_generic.to_parquet(caminho_local_parquet, index=False)

print(f"5. A fazer upload do ficheiro limpo para a {NOME_BUCKET_SILVER}...")
cliente_minio.fput_object(
    bucket_name=NOME_BUCKET_SILVER,
    object_name=nome_arquivo_silver,
    file_path=caminho_local_parquet
)