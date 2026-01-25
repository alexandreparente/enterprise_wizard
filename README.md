# Enterprise Setup Wizard (QGIS Plugin)

Enterprise Setup Wizard is a QGIS plugin for installing predefined institutional resources into QGIS user profiles based on a centralized configuration structure.  
The configuration can be local or remote and defines which resources are available for installation.

---

## Purpose

The plugin connects a managed repository of resources to the local QGIS installation.  
It reads a configuration structure organized into Divisions and presents the available resources through a wizard interface, allowing users to select and install them.

Main characteristics:

- Supports local and remote configuration sources
- Uses JSON manifests to describe divisions and resources
- Downloads remote resources only when selected
- Handles name collisions and overwrite rules during installation

---

## Supported Resources

### Cartography and Visual Assets

- **Project templates:** `.qgz`, `.qgs`
- **Print layout templates:** `.qpt`
- **Style libraries:** `.xml`
- **Color palettes:** `.gpl`
- **SVG libraries:** `.zip`
- **Fonts:** `.ttf`, `.otf`, `.woff`

### Data and Connectivity

- **Service connections (XML):**
  - PostgreSQL / PostGIS
  - WFS / WMS / OWS
  - XYZ Tiles
  - ArcGIS Feature Server / REST
- **Kart and Git repositories:** cloning of version-controlled datasets and projects

### Environment and Extensions

- **Coordinate Reference Systems (CRS):** `.wkt`
- **PROJ transformation grids:** `.tif`, `.gsb`, `.gtx`
- **Processing models:** `.model3`
- **Expression functions:** Python scripts (`.py`)
- **QGIS plugins:** installation and update via the official QGIS plugin repository

---

### Organization and Operation

The plugin operates based on a centralized configuration structure organized into Divisions.

A Division represents a logical set of resources (for example, a department, project, or team).  
Each division defines which resources can be installed by the user.

The plugin identifies divisions in two ways:

- Through a `divisions.json` file, which explicitly lists the available divisions and their sources, or  
- By detecting subdirectories in the configuration root folder when the `divisions.json` file is not present.

Each division can obtain its resources from:

- A local folder in the file system  
- A local JSON configuration file  
- A remote JSON configuration file accessed via HTTP/HTTPS  

Within a folder-based division, resources may be:

- Local files located in the corresponding subdirectories, or  
- References to remote resources, defined through `.json` files that point to an external location.

In this way, the plugin allows local and remote resources to be combined within the same division while maintaining a single configuration structure.

---

## Directory Structure

The configuration root is organized by Division.  
Each division contains subdirectories scanned by the corresponding resource managers.

```text
divisions/
├── division_name/
│   ├── project_templates/      # .qgz, .qgs
│   ├── composer_templates/     # .qpt
│   ├── styles/                 # .xml
│   ├── palettes/               # .gpl
│   ├── svg/                    # .zip
│   ├── fonts/                  # .ttf, .otf, .woff
│   ├── crs/                    # .wkt, .json
│   ├── proj/                   # .tif, .gsb, .gtx
│   ├── connections/            # .xml
│   ├── processing/
│   │   └── models/             # .model3
│   ├── python/
│   │   └── expressions/        # .py
│   └── kart/
│       └── repositories.json   # Kart/Git repository definitions
│
└── divisions.json              # Optional explicit division definitions
```

Each subdirectory is optional and only processed if present.

---

## Notes

- Updating resources does not require changes to the plugin code
- Only the configuration repository needs to be updated
- The plugin reads and installs resources into the active QGIS user profile

---

## License

MIT License. See the LICENSE file for details.

---

## Author

Alexandre Parente Lima  
alexandre.parente@gmail.com

