# Artwork

The header is an original vector illustration using the same visual language as the accompanying [research website](https://engflaviomartins.github.io/).

Its source generator is maintained in [the website repository](https://github.com/EngFlavioMartins/EngFlavioMartins.github.io/blob/main/tools/generate_research_art.py). It requires NumPy, SciPy and Matplotlib. The cavity image additionally uses a local clone of the cavity solver.

The actuator header shows a square thrust surface containing two green vertical-force bands. Upward arrows match the band colour; expanding helical paths from both ends rise downstream, with an arrow marking wake lift. It is a conceptual interpretation, not a solved velocity field or a drawing of every shipped case. Original solver assets and historical images remain in their existing locations.

The front-oblique view is an orthographic projection from 30° off the rotor normal and 12° above horizontal. The rotor lies in y–z; horizontal x–y force strips intersect it. All arrows use the same camera basis as the surfaces. Forces on the fluid point −x for thrust and +z for strip loading; downstream is +x and vertical wake displacement is +z. IBM Plex Sans labels are outlined in the SVG. The generator includes normal/direction checks in `tools/test_art_geometry.py`.
