# 🏙️ Urban Infrastructure Lens

**National Space Hackathon 2025 - Urban Planning & Smart Cities Challenge**

Şəhər infrastrukturunu (kabellər, su boruları, qaz xətləri, binalar) vahid xəritədə göstərən, STAC API ilə işləyən interaktiv platforma.

![Urban Lens Demo](docs/demo.png)

## 🎯 Problem & Həll

### Problem
Şəhər infrastrukturu haqqında məlumatlar müxtəlif qurumlarda dağınıq şəkildə saxlanılır:
- Aztelekom, Baktelekom - telekommunikasiya kabelleri
- Azərsu - su və kanalizasiya boruları
- Azəriqaz - qaz xətləri
- Azərenerji - elektrik xətləri

Bu dağınıqlıq tikinti, təmir və planlaşdırma işlərini çətinləşdirir.

### Həll
**Urban Infrastructure Lens** - bütün infrastruktur məlumatlarını vahid platformada birləşdirən, STAC standartına uyğun API və interaktiv xəritə interfeysi.

## 🏗️ Arxitektura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ETL Job       │────▶│   PostgreSQL    │◀────│   STAC API      │
│   (Python)      │     │   + PostGIS     │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  React + Leaflet│
                                               │   (Frontend)    │
                                               └─────────────────┘
```

## 🚀 Quick Start

### Tələblər
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ with PostGIS
- Docker (opsional)

### 1. PostgreSQL + PostGIS quraşdırılması

```bash
# Docker ilə
docker run -d \
  --name urban-lens-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=urban_lens \
  -p 5432:5432 \
  postgis/postgis:14-3.3

# Schema yaratmaq
psql -h localhost -U postgres -d urban_lens -f scripts/01_create_schema.sql
```

### 2. Backend quraşdırılması

```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# .env faylını redaktə edin

# ETL Job - fake data generasiyası
python -m src.etl

# API Server
python -m src.main
```

API: http://localhost:8000
Docs: http://localhost:8000/api/docs

### 3. Frontend quraşdırılması

```bash
cd frontend

# Dependencies
npm install

# Development server
npm run dev
```

Frontend: http://localhost:3000

## 📚 API Endpoints

### STAC Core
| Endpoint | Method | Açıqlama |
|----------|--------|----------|
| `/api/stac/` | GET | Root catalog |
| `/api/stac/collections` | GET | Bütün kolleksiyalar |
| `/api/stac/collections/{id}` | GET | Kolleksiya detalları |
| `/api/stac/collections/{id}/items` | GET | Kolleksiya elementləri |
| `/api/stac/search` | GET/POST | STAC axtarışı |

### Custom Endpoints
| Endpoint | Method | Açıqlama |
|----------|--------|----------|
| `/api/stats` | GET | Dashboard statistikası |
| `/api/operators` | GET | Operatorların siyahısı |
| `/api/infrastructure-types` | GET | İnfrastruktur növləri |
| `/api/geojson/{collection}` | GET | GeoJSON format |

### Query Parameters
- `bbox` - Bounding box (min_lon,min_lat,max_lon,max_lat)
- `operator` - Operator kodu (aztelekom, azersu, etc.)
- `category` - Kateqoriya (telecom, water, gas, electricity)
- `limit` - Nəticə sayı limiti
- `offset` - Pagination offset

## 🗂️ Data Model

### Operators (Şirkətlər)
| Kod | Ad | Kateqoriya |
|-----|-----|------------|
| aztelekom | Aztelekom MMC | telecom |
| baktelekom | Baktelekom MMC | telecom |
| delta | Delta Telekom | telecom |
| azersu | Azərsu ASC | water |
| azeriqaz | Azəriqaz İB | gas |
| azerenerji | Azərenerji ASC | electricity |
| bna | Bakı Şəhər İcra Hakimiyyəti | government |

### Infrastructure Types
| Kod | Ad | Kateqoriya |
|-----|-----|------------|
| fiber_optic | Fiber Optik Kabel | telecom |
| copper_cable | Mis Kabel | telecom |
| water_main | Əsas Su Borusu | water |
| water_distribution | Su Paylanma Borusu | water |
| sewage | Kanalizasiya Borusu | water |
| gas_main | Əsas Qaz Xətti | gas |
| gas_distribution | Qaz Paylanma Xətti | gas |
| power_low | Aşağı Gərginlik Xətti | electricity |

## 🎨 Features

- ✅ **STAC-Compatible API** - OGC standartlarına uyğun
- ✅ **Interactive Map** - Leaflet əsaslı xəritə
- ✅ **Multi-layer Visualization** - İnfrastruktur + Binalar
- ✅ **Dynamic Filtering** - Operator, kateqoriya, bbox filterləri
- ✅ **Responsive Design** - Mobil uyğunluq
- ✅ **Real-time Stats** - Dashboard statistikası

## 🔮 Gələcək Planlar

- [ ] Real OSM data inteqrasiyası
- [ ] ML-based infrastructure detection from satellite imagery
- [ ] Real-time sensor data integration
- [ ] Mobile app (React Native)
- [ ] 3D visualization
- [ ] Conflict detection (infrastructure overlap)

## 👥 Komanda

**GeoMerge** - National Space Hackathon 2025

## 📄 License

MIT License - Hackathon Project

---

**Built with ❤️ for National Space Hackathon 2025 by Azercosmos**
