
# tc-fiap-upload-video

Este projeto é uma API FastAPI responsável por realizar o upload de vídeos, armazená-los em um bucket S3 (AWS ou LocalStack em modo de desenvolvimento) e registrar suas informações em uma tabela DynamoDB.

---

## 🔧 Requisitos

- Python 3.10+
- Docker + Docker Compose (opcional, para usar o LocalStack)
- AWS CLI (para comandos auxiliares)
- FastAPI
- Boto3
- Uvicorn

---

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/FIAP-8SOAT/tc-fiap-upload-video.git
cd tc-fiap-upload-video
```

2. Instale as dependências:
```bash
pip install -r config/requirements.txt
```

---

## 🚀 Execução da API

### Ambiente de desenvolvimento (LocalStack)
```bash
$env:ENV="dev"  # Windows PowerShell
export ENV=dev  # Linux/macOS
uvicorn main:app --reload
```

### Ambiente de produção (AWS real)
```bash
$env:ENV="prod"
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🚀 Testes da API
### Testes unitários
```bash
pytest tests/
````

### Teste Coverage
```bash
python -m pytest --cov .
````
---

## 📤 Upload de Vídeos

- Endpoint: `POST /upload`
- Autenticação: via Header `Authorization: Bearer <token>`
- Máximo de 5 arquivos por requisição
- Tamanho máximo por vídeo: 50MB

### Exemplo com `curl`
```bash
curl --location 'http://localhost:8000/upload' \
--header 'authorization: Bearer <token>' \
--form 'files=@"/caminho/video1.mp4"' \
--form 'files=@"/caminho/video2.mp4"'
```

---

## 📁 Armazenamento

- **S3 Bucket**: `fiapeats-bucket-videos-s3`
    - Vídeos são enviados com chave única baseada no nome e email do usuário.
- **DynamoDB Table**: `table_name_test` (em dev/localstack)
    - Cada entrada contém: `id`, `user_email`, `file_name`, `s3_key`, `status`, `created_at`

---

## 🔒 Autenticação

- O token JWT deve conter o campo `email`.
- A extração do e-mail é feita via `TokenService.extract_user_email(token)`.

---

## 🛠️ LocalStack (para testes locais)

1. Suba o ambiente:
```bash
docker-compose up
```

2. Verifique arquivos enviados:
```bash
aws s3api list-objects --bucket fiapeats-bucket-videos-s3 --endpoint-url=http://localhost:4566
```

3. Limpe o bucket:
```bash
aws s3 rm s3://fiapeats-bucket-videos-s3 --recursive --endpoint-url=http://localhost:4566
```

**AWS COGNITO**
4. Criar um User Pool
```bash
aws cognito-idp create-user-pool --pool-name fiapeats-user-pool

```


---

## 📚 Estrutura do Projeto

```
.
├── adapters/
│   └── repository/
├── application/
│   └── use_cases/
├── domain/
│   └── entities/
├── infrastructure/
│   └── logging/
├── config/
├── main.py
```

---

## ✍️ Autor

Fabricio Ferreira Sousa — Grupo 58 — FIAP

---

## 📄 Licença

Projeto acadêmico — livre para fins educacionais.
