# Reddit post

## Title

[OC] Where can you still see the Milky Way? A sky glow model of the world and the UK at 1 km from 2023 satellite night lights: 52% of people worldwide and 85% in the UK live under skies too bright for it

## Body (optional)

I spread the light that the VIIRS satellite sees at night (2023) across the sky around each source with a simple distance rule, and tuned that rule against 6,653 sky meter readings from Globe at Night volunteers. By this model 52% of the world's people cannot see the Milky Way from home (the 2016 World Atlas said 36%, with 2014 lights, and ranks countries almost the same way). In the UK it is 85% of people but only 20% of the land; the darkest areas are the Western Isles and the Highlands, and from central London the nearest Milky Way sky is 35 km away. Caveat: it is a model, typically within 0.5 magnitudes of the meter readings outside city centres. Find your own sky: https://maps.tristanhotham.com/dark-skies/

## Source comment

Source: night lights from the Earth Observation Group's annual VIIRS composites (VNL v2), as resampled per country by WorldPop (CC BY 4.0); population: WorldPop 2023, R2025A (CC BY 4.0); Sky Quality Meter readings: Globe at Night, NOIRLab (CC BY 4.0); thresholds and comparison figures: Falchi et al. (2016), The new world atlas of artificial night sky brightness, Science Advances; Dark Sky Places: English Wikipedia (CC BY-SA 4.0); places: OS Open Names (OGL v3) and GeoNames (CC BY 4.0); boundaries: Natural Earth and ONS.

Tools: Python (numpy, scipy, matplotlib, Pillow, shapely) and a web browser to read the WorldPop GeoTIFFs; Leaflet for the interactive map.

Interactive map: https://maps.tristanhotham.com/dark-skies/
Blog post: https://blog.tristanhotham.com/2026/10/29/dark-skies/
Paper and data: https://doi.org/10.5281/zenodo.23757708
