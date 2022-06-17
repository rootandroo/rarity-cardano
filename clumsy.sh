#!/bin/bash
python rarity.py ClumsyGhosts
cp -f collections/ClumsyGhosts.json CLUMSY/valley.json
cd CLUMSY
python valley.py

