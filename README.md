py3d
====

Library for reading Arma's .p3d files in their unbinarized (MLOD) form.


## Installation

```bash
# pip3 install py3d
```


## Usage

```python
>>> import py3d
>>> with open("bwa3_mg4.p3d", "rb") as f:
...     mg4 = py3d.P3D(f)
...
>>> # get a set of all the textures used in a LOD
>>> set([x.texture for x in mg4.lods[0].faces])
{'', 'bwa3_machineguns\\data\\bwa3_mg4_kimme_co.paa', 'bwa3_machineguns\\data\\bwa3_mg4_co.paa'}
>>>
>>> # get a list of all proxies
>>> [x for x in mg4.lods[0].selections.keys() if "proxy:" in x]
['proxy:\\A3\\data_f\\proxies\\weapon_slots\\MUZZLE.001', 'proxy:\\A3\\data_f\\proxies\\weapon_slots\\SIDE.001', 'proxy:\\A3\\data_f\\proxies\\weapon_slots\\TOP.001', 'proxy:\\a3\\data_f\\proxies\\muzzle_flash\\muzzle_flash_rifle_Mk20.001']
>>>
>>> import copy
>>> mg4.lods.append(copy.deepcopy(mg4.lods[0])) # duplicate a LOD
>>> mg4.lods[-1].resolution = 25.0              # ... and change its resolution
>>>
>>> with open("new.p3d", "wb") as f:
...     mg4.write(f)
...
```
