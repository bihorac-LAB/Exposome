# Docker Run Commands for `exposome-geocoder-pipeline`

## Container Name:
`sri052/exposome-geocoder-pipeline:multiarch`

## Docker pull:
```bash
docker pull sri052/exposome-geocoder-pipeline:multiarch
```

---

> **Note:** For Windows systems, run the commands from WSL root  
> **Note:** Make sure your `input_folder` is in the same directory as your working directory!

---

## Available Scripts

### Run `Address_to_FIPS.py`:
```bash
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  sri052/exposome-geocoder-pipeline:multiarch \
  /app/code/Address_to_FIPS.py -i input_folder -o 1
```
#### Command Usage

```bash
python Address_to_FIPS.py -i ./your_csv_folder -o <option>
```

#### Output Options (`-o` parameter):

| Option | Description |
|--------|-------------|
| `1` | Multi-column address |
| `2` | Single-column address |
| `3` | Latitude/Longitude input |

#### Example Commands:

```bash
# Option 1: Multi-column address
python Address_to_FIPS.py -i ./your_csv_folder -o 1

# Option 2: Single-column address
python Address_to_FIPS.py -i ./your_csv_folder -o 2

# Option 3: Latitude/Longitude input
python Address_to_FIPS.py -i ./your_csv_folder -o 3
```

### Run `OMOP_to_FIPS.py`:
```bash
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)":/workspace \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  sri052/exposome-geocoder-pipeline:multiarch \
  /app/code/OMOP_to_FIPS.py \
    --user <> \
    --password <> \
    --server <> \
    --port <> \
    --database <>
```

# 🛠️ For Developers

This repository is designed to run in a containerized environment and utilizes **Docker-in-Docker (DinD)** architecture, allowing Docker commands to be executed from within the container itself.

> ⚠️ **Important:** When running this containerized application, you **must mount the Docker socket** to enable nested Docker operations:  
> ```bash
> -v /var/run/docker.sock:/var/run/docker.sock
> ```

---

## 🐳 Docker Multi-Architecture Build Setup

### 1️⃣ Create and configure a new Buildx builder instance
```bash
docker buildx create --name mybuilder --use
```

### 2️⃣ Build and push multi-architecture Docker image
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/imagename:tag \
  --push .
```

## 🧱 Dockerfile Dependencies 

| Package/Dependency                           | Purpose                                                             |
|----------------------------------------------|---------------------------------------------------------------------|
| `python:3.10-slim`                           | Lightweight base Python image                                       |
| `apt-transport-https`, `ca-certificates`, `curl`, `gnupg2` | Enables secure downloads and package signing         |
| `unixodbc`, `unixodbc-dev`                   | ODBC support for database connectivity                              |
| `msodbcsql18`                                | Microsoft SQL Server ODBC Driver 18                                 |
| `lsb-release`                                | Helps determine Linux distribution info                             |
| `docker-ce-cli`                              | Docker CLI installed inside the container (enables Docker-in-Docker)|
| `requirements.txt`                           | Python dependencies are installed from this file                    |




