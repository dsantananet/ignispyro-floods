# IGNISPYRO · Monitorização em tempo real no ArcGIS Online

Organização: `alternative3.maps.arcgis.com` · Grupo: **IGNISPYRO · Catálogo de dados, mapas e aplicações Content**

## Princípios

- **Só mapas 2D** (sem WebGL) em todos os painéis operacionais. A única exceção é a cena 3D do Living Atlas, numa página separada do Experience Builder, para visualização.
- **Motores fora do ArcGIS**: cada motor corre em cron (QNAP/Asustor ou Azure VM), lê fontes abertas e **escreve numa Hosted Feature Layer**. O Experience Builder só lê essa layer.
- **Tempo real = intervalo de atualização da layer** no web map (propriedade *Refresh interval*, 1–5 min). Não há WebSockets no navegador.
- **Segredos nunca no código**: tokens e chaves vêm de variáveis de ambiente (`.env` fora do Git).
- IA e regras apoiam a decisão; **não substituem a decisão humana**. Cada produto guarda fonte, versão, hora e método.

## Fluxo comum

```
[Fontes abertas] -> [Motor (cron)] -> [Hosted Feature Layer] -> [Web Map 2D] -> [Experience Builder]
 IPMA/EMSC/APA        Node/Python       updateFeatures           refresh 1-5 min   dashboard + mapas
 VOST/Waze/Google     (delta apenas)    campos de estado
```

## Ficheiros

| Ficheiro | Motor | Camada de saída | Frequência |
|---|---|---|---|
| `01_motor_rotas.md` | Rotas Google + alertas Waze | `ignispyro_rotas_live` (linhas) | 2 min |
| `02_motor_sismos_bgri.md` | Matriz de risco sísmico | `ignispyro_sismos_live` (pontos) + `bgri_estado_sismo` | evento / 5 min |
| `03_motor_cheias.md` | Cheias por freguesia | `ignispyro_cheias_freguesia` (polígonos) | 15 min |
| `04_motor_landslides.md` | Movimentos de vertente | `bgri_estado_landslide` | 30 min |
| `05_experience_builder.md` | Estrutura do portal | n/a | n/a |

## Ligações de dados

| Fonte | URL | Uso |
|---|---|---|
| BGRI 2021 (INE) | https://gisserver.ine.pt/arcgis/rest/services/BGRI2021/BGRI/FeatureServer/0 | Subsecções, população |
| IPMA observações | https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json | Chuva por estação |
| IPMA estações | https://api.ipma.pt/open-data/observation/meteorology/stations/stations.json | Coordenadas das estações |
| IPMA sismos | https://api.ipma.pt/open-data/observation/seismic/7.json | Continente (3 = Açores) |
| EMSC (FDSN) | https://www.seismicportal.eu/fdsnws/event/1/query?format=json&limit=50&minmag=2 | Sismos Europa |
| Google Flood Hub | https://floodforecasting.googleapis.com | Validação externa (chave API) |
| Google Directions | https://maps.googleapis.com/maps/api/directions/json | Rotas com trânsito |
| OpenWeb Ninja (Waze) | https://api.openwebninja.com | Alertas de trânsito |
| APA / SNIRH, VOST | confirmar endpoint antes de usar | Cotas e caudais |

> Os endpoints IPMA acima são públicos. APA e VOST precisam de confirmação do endpoint exato antes de produção.

## Variáveis de ambiente comuns

```
ARCGIS_TOKEN=            # token de utilizador ou OAuth app, validade curta
GOOGLE_KEY=
NINJA_KEY=
```
