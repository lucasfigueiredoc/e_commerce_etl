import os
from dotenv import load_dotenv

# --- 0. CREDENCIAIS KAGGLE ---
# Carrega as variáveis de ambiente do arquivo .env ANTES de importar o Kaggle
load_dotenv()

from kaggle.api.kaggle_api_extended import KaggleApi
from minio import Minio

# --- CONFIGURAÇÕES ---
NOME_DATASET_KAGGLE = "olistbr/brazilian-ecommerce"
NOME_BUCKET = "camada-bronze"
PASTA_LOCAL_TEMP = "./dados_temporarios"

# --- 1. AUTENTICAÇÃO NO KAGGLE ---
print("1. Autenticando na API do Kaggle usando o token do .env...")
# Como o load_dotenv() já jogou o token para o ambiente, a biblioteca reconhece automaticamente.
api = KaggleApi()
api.authenticate()

# --- 2. DOWNLOAD DOS DADOS ---
print(f"2. Baixando o dataset {NOME_DATASET_KAGGLE}...")
# Cria a pasta temporária se não existir
os.makedirs(PASTA_LOCAL_TEMP, exist_ok=True)
api.dataset_download_files(NOME_DATASET_KAGGLE, path=PASTA_LOCAL_TEMP, unzip=True)
print("   Download concluído e arquivos descompactados!")

# --- 3. CONEXÃO COM O NOSSO DATA LAKE LOCAL (MINIO) ---
print("3. Conectando ao MinIO (nosso Data Lake)...")
cliente_minio = Minio(
    "localhost:9000", # A porta da API que configuramos no Docker
    access_key="admin_datalake",
    secret_key="senha_datalake",
    secure=False # Falso porque estamos usando localhost sem certificado SSL
)

# Verifica se o bucket 'camada-bronze' existe, se não, cria.
if not cliente_minio.bucket_exists(NOME_BUCKET):
    cliente_minio.make_bucket(NOME_BUCKET)
    print(f"   Bucket '{NOME_BUCKET}' criado.")

# --- 4. UPLOAD PARA O DATA LAKE ---
print("4. Iniciando upload dos arquivos para a Camada Bronze...")
arquivos_baixados = os.listdir(PASTA_LOCAL_TEMP)

for arquivo in arquivos_baixados:
    caminho_completo_local = os.path.join(PASTA_LOCAL_TEMP, arquivo)
    
    # Se for um arquivo CSV (ignora outras pastas)
    if os.path.isfile(caminho_completo_local) and arquivo.endswith('.csv'):
        nome_no_datalake = f"olist/{arquivo}" # Salva dentro de uma subpasta 'olist'
        
        print(f"   Subindo {arquivo}...")
        cliente_minio.fput_object(
            bucket_name=NOME_BUCKET,
            object_name=nome_no_datalake,
            file_path=caminho_completo_local
        )

print("\n Ingestão concluída com sucesso! Verifique a interface do MinIO.")