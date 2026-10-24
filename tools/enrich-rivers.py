import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
from shapely.geometry import shape
from shapely.strtree import STRtree
root=pathlib.Path('dist/data');b=json.loads((root/'basins.geojson').read_text());r=json.loads((root/'rivers.geojson').read_text());bg=[shape(f['geometry']) for f in b['features']];tree=STRtree(bg)
for f in r['features']:f['properties']['basin_ids']=[str(b['features'][int(i)]['properties']['objectid']) for i in tree.query(shape(f['geometry']),predicate='intersects')]
(root/'rivers.geojson').write_text(json.dumps(r,separators=(',',':')),encoding='utf-8');print('Rivers linked to basins',len(r['features']))
