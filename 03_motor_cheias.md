# Motor 03 · Cheias por freguesia

**Saída:** `ignispyro_cheias_freguesia` (polígonos CAOP, chave `DICOFRE`) · **Mapa:** 2D · **Cron:** `*/15 * * * *`

## Fontes

| Fonte | Variável | Nota |
|---|---|---|
| IPMA estações | precipitação acumulada 24 h (mm) | https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json |
| APA / InfoÁgua (SNIRH) | cota (m) | confirmar endpoint |
| VOST Portugal (RIOS) | caudal (m³/s) | confirmar endpoint |
| BGRI 2021 | população por freguesia | somar `N_INDIVIDUOS` por `DICOFRE` |
| Google Flood Hub | previsão | **só validação externa**, nunca decide o nível |

## Níveis

| Cor | Chuva (mm) | Caudal (m³/s) | % população exposta |
|---|---|---|---|
| Azul | ≤ 15 | < 200 | 0 |
| Verde | ≤ 50 | < 500 | 5 |
| Amarelo | ≤ 80 | < 1000 | 20 |
| Laranja | ≤ 110 | < 1400 | 50 |
| Vermelho | > 110 ou caudal ≥ 1400 | | 90 |

Percentagens de população exposta são **estimativas de planeamento**, não observação. O campo `pop_afetada` deve ser rotulado como "estimada".

## Problemas na lógica original

1. O operador `or` faz o nível seguir **o melhor dos dois indicadores**, não o pior. Chuva 120 mm com caudal 150 m³/s dá "Verde" (`caudal < 500`). Para risco, deve prevalecer o **pior** dos dois.
2. Os limiares de caudal são **absolutos**, mas cada rio tem escalas diferentes. Substituir por limiares por estação/sub-bacia assim que existirem.
3. O dado do exemplo é simulado. A tabela de produção deve ser lida das APIs.
4. O ficheiro original tinha `\t` corrompido nos símbolos `≤` (`\text`); corrigido aqui.

## Código (Python)

```python
import pandas as pd

ORDEM = ["Azul", "Verde", "Amarelo", "Laranja", "Vermelho"]
PCT = {"Azul": 0.0, "Verde": 0.05, "Amarelo": 0.20, "Laranja": 0.50, "Vermelho": 0.90}

def nivel_chuva(mm):
    if mm <= 15: return "Azul"
    if mm <= 50: return "Verde"
    if mm <= 80: return "Amarelo"
    if mm <= 110: return "Laranja"
    return "Vermelho"

def nivel_caudal(q):
    if q < 200: return "Azul"
    if q < 500: return "Verde"
    if q < 1000: return "Amarelo"
    if q < 1400: return "Laranja"
    return "Vermelho"

def classificar(row):
    n = max(nivel_chuva(row["Precip_Estacao_mm"]), nivel_caudal(row["Caudal_VOST_m3s"]), key=ORDEM.index)
    pop = int(row["Pop_Residente_BGRI"] * PCT[n])
    g = row["Google_Flood_Previsao"]
    if n == "Vermelho" and g == "Normal":
        v = "Divergência: estações indicam cheia, Google não (possível cheia rápida urbana)"
    elif n == "Azul" and g == "Perigo Extremo":
        v = "Divergência: Google prevê cheia, estações sem registo (possível onda a montante)"
    else:
        v = "Coerente"
    return pd.Series([n, pop, v])

def processar(df):
    df[["Cor Alerta", "População Afetada", "Validação Google"]] = df.apply(classificar, axis=1)
    return df
```

## Publicação

1. Juntar o resultado à CAOP por `DICOFRE`.
2. `updateFeatures` apenas das freguesias cujo nível mudou.
3. Layer simbolizada por `Cor Alerta`; *Refresh interval* 15 min.

## Experience Builder

- Mapa 2D de freguesias; lista lateral filtrada por nível ≥ Laranja.
- Indicadores: freguesias por nível, população estimada exposta, nº de divergências com o Flood Hub.
