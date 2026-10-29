# Darkest skies: where you can still see the Milky Way

A sky glow map of the world and a 1 km map of the United Kingdom. Artificial zenith sky brightness is modelled from VIIRS annual night lights (Earth Observation Group, via WorldPop) with a simple distance kernel, fitted to and tested against 6,653 Sky Quality Meter readings from Globe at Night volunteers, and set against WorldPop's 2023 population grid. The page answers: who can still see the Milky Way from home, where are the darkest places in the UK, how far must city people travel for a dark sky, and are the UK's lights growing or shrinking?

**Interactive version:** https://maps.tristanhotham.com/dark-skies/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23757708

**Blog post:** https://blog.tristanhotham.com/2026/10/29/dark-skies/

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- By the model, 52% of the world's people (about 4.2 billion) live under skies where artificial glow hides the Milky Way (glow above 688 µcd/m², about four times the natural sky). Falchi et al. (2016) found 36% with 2014 lights; across 148 countries the two rankings agree closely (Spearman 0.94), with this model 11 points higher on average.
- In 82 of 160 countries of a million or more, most people cannot see the Milky Way from home; in 16, more than nine in ten (Hong Kong, Singapore, the Gulf, Israel, Egypt). China 66%, India 38%, United States 86%.
- United Kingdom at 1 km: 85% of people (57.7 million) but only 20% of land under a Milky Way hiding sky. England 87% of people, Scotland 75%, Wales 66%, Northern Ireland 62%.
- Darkest areas: the Western Isles, Highland, Orkney, Shetland, Argyll and Bute; in England Northumberland, Devon, Cumbria, Cornwall and Dorset. Darkest town: Hugh Town, Isles of Scilly. The Milky Way should show from 3% of UK city centres, 37% of towns and 67% of villages.
- Nearest Milky Way sky: 35 km from central London, 25 km from Birmingham, 22 km from Manchester; median 17 km for the world's 505 cities of a million or more, 74 km for New York.
- Radiance seen from space over Great Britain fell 13.5% from 2015 to 2023 (Ireland +10.3%), but VIIRS misses much of the blue light of white LEDs, so this probably overstates any real darkening.
- Model check: fitted to 5,775 Globe at Night Sky Quality Meter readings (2019 to 2025); cross-validated typical error 0.49 mag/arcsec², correlation 0.79.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Method in brief

- **Lights.** WorldPop's harmonised covariates include the Earth Observation Group's annual VIIRS night lights (VNL v2.1/2.2, flares and volcanoes removed) as 3 arc second GeoTIFFs for every country. I read all 246 country files for 2023 in the browser and averaged them to a 2.5 arc minute world grid, and the United Kingdom, Ireland and Isle of Man files for 2015 to 2023 to a 30 arc second grid.
- **Sky glow.** Each cell's upward light (radiance times lit area) spreads to its surroundings with a kernel f(d) = (d² + 1 km²)^(-alpha/2), cut off at 250 km. Brightness is k times the sum over all lit cells. On the coarse grid the kernel is averaged over 5 by 5 sub-points of each pair of cells.
- **Fitting.** alpha (and an optional extra fall-off with distance) and the scale k are fitted by least absolute error to the 5,775 Globe at Night Sky Quality Meter readings darker than 18.0 mag/arcsec² taken under clear skies after 20:00 local time, 2019 to 2025 (the 4.6 km grid cannot resolve bright city-centre streets), and chosen by spatial cross-validation (10 degree blocks in five folds). Best: alpha = 2.3, no extra fall-off; cross-validated typical error 0.49 mag/arcsec² (root mean square 0.75), correlation 0.79. Over all readings including city centres the root mean square error is 1.08.
- **Thresholds.** As in Falchi et al. (2016): natural sky 174 µcd/m² (22.0 mag/arcsec²); artificial glow above 13.9 µcd/m² (8%) counts as light polluted, above 688 µcd/m² hides the Milky Way, above 3,000 µcd/m² keeps eyes from full dark adaptation.
- **People.** WorldPop Global2 R2025A constrained population, 2023, 30 arc seconds, summed to the model grids.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (tables embedded; grids, search lists and borders load from `data/page/`). |
| `header.png` | Social card (1200 by 630). |
| `data/countries.csv` | Every country: population, shares of people and land in each sky class, median sky (mag/arcsec²), and Falchi et al. (2016) figures where they exist. |
| `data/cities.csv` | GeoNames places of 100,000 or more: modelled sky; for cities of a million or more, the distance and position of the nearest Milky Way sky and nearest unpolluted sky on land. |
| `data/uk_areas.csv` | UK counties (and Northern Ireland districts): median sky, shares of people and land who can see the Milky Way, change 2015 to 2023. |
| `data/uk_councils.csv` | The same for local authority districts. |
| `data/uk_towns.csv` | Every city, town, village and hamlet in OS Open Names (Great Britain) and GeoNames towns in Northern Ireland, with its modelled sky. |
| `data/dark_sky_places.csv` | Dark Sky Places from English Wikipedia ("Dark-sky preserve", CC BY-SA 4.0) and Wikidata, with the source of each position and the modelled sky there. |
| `data/page/` | Coded grids (PNG) and lists for the page. |
| `data/results.json` | Every number used anywhere. |
| `code/01_places.py` | Dark Sky Places and Globe at Night readings. |
| `code/02_grids.py` | Unpacks the browser bundle and rasterises countries and UK areas. |
| `code/skyglow.py`, `code/03_model.py` | The sky glow model, fitting and runs. |
| `code/04_stats.py`, `code/05_page_data.py`, `code/06_results.py` | Statistics, page files and results. |
| `code/07_build_site.py` to `code/11_release.py` | Page, figures, social card, paper and release files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Known limits

- This is a model, not a measurement. It uses a single kernel everywhere: no terrain shading, no differences in air clarity or altitude, no allowance for the angle at which lamps shine, and no colour. Cross-validated, it misses a typical sky meter reading outside city centres by 0.49 magnitudes, and it badly underestimates the brightest city centres.
- VIIRS sees little of the blue light from white LEDs, so places that switched to LED street lighting can look dimmer from space than they look from the ground. The UK's falling radiance since 2015 is probably partly this.
- The world grid is 4.6 km; within a cell people cluster where the lights are, so world shares of people under bright skies are probably too low. The UK model at 1 km puts 85% of people under a Milky Way hiding sky; the same people on the coarse world grid give 82%.
- Globe at Night readings are made by volunteers, mostly in North America and Europe, with hand-held meters; clouds, the Moon and timing add noise.
- Kosovo has no light file of its own in the WorldPop set and is left out of country results.
- The Falchi et al. (2016) world atlas itself is not used: its GeoTIFF is distributed with a 2016 note that further distribution is prohibited, and under a non-commercial licence. Only the figures published in their paper are quoted for comparison. CPRE's Night Blight maps of England (2016) are not used either: I found no open licence for their data.

## Sources and licences

- Night lights: Earth Observation Group, Payne Institute for Public Policy, Colorado School of Mines, VNL v2.1/2.2 (Elvidge et al. 2021, Remote Sensing 13: 922), as resampled per country by WorldPop: Woods, D. et al. (2024) WorldPop high resolution, harmonised annual global geospatial covariates, doi:10.5258/SOTON/WP00772. CC BY 4.0. Read from data.worldpop.org on 2026-10-29.
- Population: Bondarenko, M. et al. (2025) The spatial distribution of population in 2015 to 2030 at 30 arc seconds, R2025A, doi:10.5258/SOTON/WP00845. CC BY 4.0.
- Sky meter readings: Globe at Night, NOIRLab, campaign data 2006 to 2025 (https://globeatnight.org/maps-data/). CC BY 4.0.
- Comparison figures: Falchi, F. et al. (2016) The new world atlas of artificial night sky brightness. Science Advances 2(6): e1600377, Tables 1 and 2.
- Dark Sky Places: English Wikipedia, "Dark-sky preserve" (CC BY-SA 4.0); Wikidata (CC0).
- Places: OS Open Names (contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0); GeoNames cities15000 (CC BY 4.0).
- Boundaries: Natural Earth (public domain); Office for National Statistics boundaries via onsvisual/uk-topojson (Open Government Licence v3).
- Base map and hill shading tiles on the page © Esri.

Text, figures and derived data: CC BY 4.0, except `data/dark_sky_places.csv` (CC BY-SA 4.0). Code: MIT (see `LICENSE`).

## How to rerun

The raw bundles were gathered in a browser and are read from `DS_DATA` (default `/home/claude/hist/_data18/dark-skies`): `darkskies_worldpop.bin.gz` (lights and population, reduced in the browser from WorldPop GeoTIFFs), `darkskies_gan.json.gz` (Globe at Night), `darkskies_places_wiki.json.gz` (Wikipedia and Wikidata) and `darkskies_falchi_tables.json.gz` (the published tables of Falchi et al. 2016). Then run `code/01_places.py` to `code/11_release.py` in order, and `reddit/collage.py`. Python 3 with numpy, scipy, shapely, Pillow and matplotlib; xelatex for the paper.

## Cite

Hotham, T. (2026) Darkest skies: where you can still see the Milky Way. A sky glow model of the world and the UK from VIIRS night lights. Zenodo. https://doi.org/10.5281/zenodo.23757708
